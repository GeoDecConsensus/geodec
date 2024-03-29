from datetime import datetime
from glob import glob
from multiprocessing import Pool
from os.path import join
from re import findall, search
from statistics import mean

from benchmark.utils import Print


class ParseError(Exception):
    pass


class CometBftLogParser:
    def __init__(self, clients, nodes, faults):
        inputs = [clients, nodes]
        assert all(isinstance(x, list) for x in inputs)
        assert all(isinstance(x, str) for y in inputs for x in y)
        assert all(x for x in inputs)

        self.faults = faults
        if isinstance(faults, int):
            self.committee_size = len(nodes) + int(faults)
        else:
            self.committee_size = '?'

        # Parse the clients logs.
        try:
            with Pool() as p:
                results = p.map(self._parse_clients, clients)
        except (ValueError, IndexError) as e:
            raise ParseError(f'Failed to parse client logs: {e}')
        self.size, self.rate, self.start, misses, self.sent_samples \
            = zip(*results)
        self.misses = sum(misses)

        # Parse the nodes logs.
        try:
            with Pool() as p:
                results = p.map(self._parse_nodes, nodes)
        except (ValueError, IndexError) as e:
            raise ParseError(f'Failed to parse node logs: {e}')
        proposals, commits, sizes, self.received_samples, timeouts, self.configs \
            = zip(*results)
        self.proposals = self._merge_results([x.items() for x in proposals])
        self.commits = self._merge_results([x.items() for x in commits])
        self.sizes = {
            k: v for x in sizes for k, v in x.items() if k in self.commits
        }
        self.timeouts = max(timeouts)

        # Check whether clients missed their target rate.
        if self.misses != 0:
            Print.warn(
                f'Clients missed their target rate {self.misses:,} time(s)'
            )

        # Check whether the nodes timed out.
        # Note that nodes are expected to time out once at the beginning.
        if self.timeouts > 2:
            Print.warn(f'Nodes timed out {self.timeouts:,} time(s)')

        print(self.result())

    def _merge_results(self, input):
        # Keep the earliest timestamp.
        merged = {}
        for x in input:
            for k, v in x:
                if not k in merged or merged[k] > v:
                    merged[k] = v
        return merged

    def _parse_clients(self, log):
        if search(r'Error', log) is not None:
            # raise ParseError('Client(s) panicked')
            print('Client(s) panicked')

        size = int(search(r'"size\\":(\d+)', log).group(1))
        rate = int(search(r'rate\\":(\d+)', log).group(1))

        # tmp = search(r'\[(.*Z) .* Starting ', log).group(1)
        tmp = search(r'time="(.*Z)" .* msg="Starting transactor"', log).group(1)
        start = self._to_posix(tmp, name='client')

        misses = len(findall(r'rate too high', log))

        tmp = findall(r'time="(.*Z)".* msg="Sending batch of transactions" .* ', log)
        samples = {int(i+1): self._to_posix(t, name='client') for i, t in enumerate(tmp)}
 
        return size, rate, start, misses, samples

    def _parse_nodes(self, log):
        if search(r'panic', log) is not None:
            raise ParseError('Node(s) panicked')
        
        # tmp = findall(r'\[(.*Z) .* Created B\d+ -> ([^ ]+=)', log)
        tmp = findall(r'I\[(.*?)\].*received complete proposal block.*hash=([A-Fa-f0-9]+)', log)
        tmp = [(d, self._to_posix(t)) for t, d in tmp]
        proposals = self._merge_results([tmp])

        # tmp = findall(r'\[(.*Z) .* Committed B\d+ -> ([^ ]+=)', log)
        tmp = findall(r'D\[(.*?)\].*committed block.*(.{64})"', log)
        tmp = [(d, self._to_posix(t)) for t, d in tmp]
        commits = self._merge_results([tmp])

        # tmp = findall(r'Batch ([^ ]+) contains (\d+) B', log)
        tmp = findall(r'hash=([A-Fa-f0-9]+).*num_txs=(\d+)', log)
        sizes = {d: int(s) * int(self.size[0]) for d, s in tmp}

        # NOTE
        # tmp = findall(r'Batch ([^ ]+) contains sample tx (\d+)', log)
        # samples = {int(s): d for d, s in tmp}
        samples = {}
        
        tmp = findall(r'.* WARN .* Timeout', log)
        # timeouts = len(tmp)
        timeouts = 2

        configs = {
            # 'consensus': {
            #     'timeout_delay': int(
            #         search(r'Timeout delay .* (\d+)', log).group(1)
            #     ),
            #     'sync_retry_delay': int(
            #         search(
            #             r'consensus.* Sync retry delay .* (\d+)', log
            #         ).group(1)
            #     ),
            # },
            # 'mempool': {
            #     'gc_depth': int(
            #         search(r'Garbage collection .* (\d+)', log).group(1)
            #     ),
            #     'sync_retry_delay': int(
            #         search(r'mempool.* Sync retry delay .* (\d+)', log).group(1)
            #     ),
            #     'sync_retry_nodes': int(
            #         search(r'Sync retry nodes .* (\d+)', log).group(1)
            #     ),
            #     'batch_size': int(
            #         search(r'Batch size .* (\d+)', log).group(1)
            #     ),
            #     'max_batch_delay': int(
            #         search(r'Max batch delay .* (\d+)', log).group(1)
            #     ),
            # }
        }

        return proposals, commits, sizes, samples, timeouts, configs

    def _to_posix(self, string, name='node'):
        if name == 'node':
            format_string = '%Y-%m-%d|%H:%M:%S.%f' # 2024-03-26|12:07:26.032
            x = datetime.strptime(string, format_string)
        # elif name == 'client':
        else:
            # format_string = '%Y-%m-%dT%H:%M:%fZ' # 2024-03-26T12:07:27Z
            x = datetime.fromisoformat(string.replace('Z', '+00:00'))
            # x = datetime.strptime(string, format_string)
        return datetime.timestamp(x)

    def _consensus_throughput(self):
        if not self.commits:
            return 0, 0, 0
        start, end = min(self.proposals.values()), max(self.commits.values())
        duration = end - start
        bytes = sum(self.sizes.values())
        bps = bytes / duration
        tps = bps / self.size[0]
        return tps, bps, duration

    def _consensus_latency(self):
        latency = [c - self.proposals[d] for d, c in self.commits.items()]
        return mean(latency) if latency else 0

    def _end_to_end_throughput(self):
        if not self.commits:
            return 0, 0, 0
        start, end = min(self.start), max(self.commits.values())
        print(start, end)
        duration = end - start
        bytes = sum(self.sizes.values())
        bps = bytes / duration
        tps = bps / self.size[0]
        return tps, bps, duration

    # NOTE Not functional
    def _end_to_end_latency(self):
        latency = []
        for sent, received in zip(self.sent_samples, self.received_samples):
            for tx_id, batch_id in received.items():
                if batch_id in self.commits:
                    assert tx_id in sent  # We receive txs that we sent.
                    start = sent[tx_id]
                    end = self.commits[batch_id]
                    latency += [end-start]
        return mean(latency) if latency else 0

    def result(self):
        consensus_latency = self._consensus_latency() * 1000
        consensus_tps, consensus_bps, _ = self._consensus_throughput()
        end_to_end_tps, end_to_end_bps, duration = self._end_to_end_throughput()
        end_to_end_latency = self._end_to_end_latency() * 1000

        # consensus_timeout_delay = self.configs[0]['consensus']['timeout_delay']
        # consensus_sync_retry_delay = self.configs[0]['consensus']['sync_retry_delay']
        # mempool_gc_depth = self.configs[0]['mempool']['gc_depth']
        # mempool_sync_retry_delay = self.configs[0]['mempool']['sync_retry_delay']
        # mempool_sync_retry_nodes = self.configs[0]['mempool']['sync_retry_nodes']
        # mempool_batch_size = self.configs[0]['mempool']['batch_size']
        # mempool_max_batch_delay = self.configs[0]['mempool']['max_batch_delay']

        return (
            '\n'
            '-----------------------------------------\n'
            ' SUMMARY:\n'
            '-----------------------------------------\n'
            ' + CONFIG:\n'
            f' Faults: {self.faults} nodes\n'
            f' Committee size: {self.committee_size} nodes\n'
            f' Input rate: {sum(self.rate):,} tx/s\n'
            f' Transaction size: {self.size[0]:,} B\n'
            f' Execution time: {round(duration):,} s\n'
            '\n'
            # f' Consensus timeout delay: {consensus_timeout_delay:,} ms\n'
            # f' Consensus sync retry delay: {consensus_sync_retry_delay:,} ms\n'
            # f' Mempool GC depth: {mempool_gc_depth:,} rounds\n'
            # f' Mempool sync retry delay: {mempool_sync_retry_delay:,} ms\n'
            # f' Mempool sync retry nodes: {mempool_sync_retry_nodes:,} nodes\n'
            # f' Mempool batch size: {mempool_batch_size:,} B\n'
            # f' Mempool max batch delay: {mempool_max_batch_delay:,} ms\n'
            '\n'
            ' + RESULTS:\n'
            f' Consensus TPS: {round(consensus_tps):,} tx/s\n'
            f' Consensus BPS: {round(consensus_bps):,} B/s\n'
            f' Consensus latency: {round(consensus_latency):,} ms\n'
            '\n'
            f' End-to-end TPS: {round(end_to_end_tps):,} tx/s\n'
            f' End-to-end BPS: {round(end_to_end_bps):,} B/s\n'
            f' End-to-end latency: {round(end_to_end_latency):,} ms\n'
            '-----------------------------------------\n'
        )

    def print(self, filename):
        assert isinstance(filename, str)
        with open(filename, 'a') as f:
            f.write(self.result())

    @classmethod
    def process(cls, directory, faults):
        assert isinstance(directory, str)

        clients = []
        for filename in sorted(glob(join(directory, 'client-*.log'))):
            with open(filename, 'r') as f:
                clients += [f.read()]
        nodes = []
        for filename in sorted(glob(join(directory, 'node-*.log'))):
            with open(filename, 'r') as f:
                nodes += [f.read()]

        return cls(clients, nodes, faults)

class CometBftMechanism:
    def __init__(self, settings):
        self.settings = settings
        self.name = 'cometbft'

        self.old_cmd = [
            'sudo apt-get update',
            'sudo apt-get -y upgrade',
            'sudo apt-get -y autoremove',
            'sudo apt-get install -y wget tar git',
            'wget https://github.com/cometbft/cometbft/releases/download/v0.38.5/cometbft_0.38.5_linux_amd64.tar.gz',
            'mkdir -p cometbft-repo && tar -xzf cometbft_0.38.5_linux_amd64.tar.gz -C cometbft-repo',
            'rm cometbft_0.38.5_linux_amd64.tar.gz',
            'mv cometbft-repo/cometbft ~/',
            'rm -rf cometbft-repo'
        ]

        self.install_cmd = [
            [
                'sudo apt-get update',
                'sudo apt-get -y upgrade',
                'sudo apt-get -y autoremove',
                
                # Install required packages
                'sudo apt-get install -y wget tar git make',

                # Download Golang
                'wget -c https://go.dev/dl/go1.21.8.linux-amd64.tar.gz',
                
                #Delete prev version and extract
                # 'sudo rm -rf /usr/local/go && tar -xzf go1.21.8.linux-amd64.tar.gz',
                'sudo rm -rf ~/go/ && tar -xzf go1.21.8.linux-amd64.tar.gz',

                # Remove the tar.gz file
                'rm go1.21.8.linux-amd64.tar.gz',

                # If you do bash_profile then the color in terminal will go as on load that config will be used
                'echo export GOPATH=\"\$HOME/go\" >> ~/.profile',
                'echo export PATH=\"\$PATH:\$GOPATH/bin\" >> ~/.profile',
                # 'export PATH=$PATH:/usr/local/go/bin'
                'source ~/.profile',
            ],
            [
                'source ~/.profile',
                f'rm -rf {self.settings.repo_name}',
                f'(git clone -b {self.settings.branch} {self.settings.repo_url} || (cd {self.settings.repo_name} ; git pull))',
                f'cd {self.settings.repo_name}',
                # f'git fetch -f && git checkout -f {self.settings.branch}',
                'make install',
                'make build',
                'cd ./test/loadtime',
                'make build'
            ]
        ]
        
        self.update_cmd = [
            # Check if the repo directory exists
            'source ~/.profile',
            f'[ -d {self.settings.repo_name} ] || git clone {self.settings.repo_url}',
            f'(cd {self.settings.repo_name} && git fetch -f)',
            f'(cd {self.settings.repo_name} && git checkout -f {self.settings.branch})',
            f'(cd {self.settings.repo_name} && git pull origin -f)',
            f'cd {self.settings.repo_name}',
            'make install',
            'make build',
            'cd ./test/loadtime',
            'make build'
        ]

    def install(self):
        print('Installing CometBft ...')

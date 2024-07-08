from datetime import datetime
from glob import glob
from multiprocessing import Pool
from os.path import join
from re import findall, search
from statistics import mean

from benchmark.utils import Print
from benchmark.commands import CommandMaker

class ParseError(Exception):
    pass


class CometBftLogParser:
    def __init__(self, clients, nodes, latency, faults):
        self.result_str = ""
        self.latency = latency
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
        proposals, commits, sizes, timeouts, self.configs \
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

        self.result_str = self.result()

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

        tmp = search(r'time="(.*Z)" .* msg="Starting transactor"', log).group(1)
        start = self._to_posix(tmp, name='client')

        misses = len(findall(r'rate too high', log))

        tmp = findall(r'time="(.*Z)".* msg="Sending batch of transactions" .* ', log)
        samples = {int(i+1): self._to_posix(t, name='client') for i, t in enumerate(tmp)}
 
        return size, rate, start, misses, samples

    def _parse_nodes(self, log):
        if search(r'panic', log) is not None:
            raise ParseError('Node(s) panicked')
        
        tmp = findall(r'I\[(.*?)\].*received complete proposal block.*hash=([A-Fa-f0-9]+)', log)
        tmp = [(d, self._to_posix(t)) for t, d in tmp]
        proposals = self._merge_results([tmp])

        tmp = findall(r'D\[(.*?)\].*committed block.*block=([A-Fa-f0-9]+).*', log)
        tmp = [(d, self._to_posix(t)) for t, d in tmp]
        commits = self._merge_results([tmp])

        tmp = findall(r'hash=([A-Fa-f0-9]+).*num_txs=(\d+)', log)
        sizes = {d: int(s) * int(self.size[0]) for d, s in tmp}
        
        tmp = findall(r'.* WARN .* Timeout', log)
        timeouts = len(tmp)

        configs = {
        }

        return proposals, commits, sizes, timeouts, configs

    def _to_posix(self, string, name='node'):
        if name == 'node':
            format_string = '%Y-%m-%d|%H:%M:%S.%f' # 2024-03-26|12:07:26.032
            x = datetime.strptime(string, format_string)
        else:
            x = datetime.fromisoformat(string.replace('Z', '+00:00'))
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
        # print(start, end)
        duration = end - start
        bytes = sum(self.sizes.values())
        bps = bytes / duration
        tps = bps / self.size[0]
        return tps, bps, duration

    def _end_to_end_latency(self):
        result = []
        output = 0
        for log in self.latency:
            tmp = findall(r'Average Latency: (\d+\.\d+)', log)
            latency = [float(t) for t in tmp]
            if latency:
                result.append(mean(latency))
        if result:
            output = mean(result)
        if output > 100:
            output = round(output)
        return output if output else 0

    def result(self):
        consensus_latency = self._consensus_latency() * 1000
        consensus_tps, consensus_bps, _ = self._consensus_throughput()
        end_to_end_tps, end_to_end_bps, duration = self._end_to_end_throughput()
        end_to_end_latency = self._end_to_end_latency() * 1000

        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    
        return (
            '-----------------------------------------\n'
            ' COMETBFT SUMMARY:\n'
            '-----------------------------------------\n'
            f' Date and Time: {current_time}\n'
            '-----------------------------------------\n'
            ' + CONFIG:\n'
            f' Faults: {self.faults} nodes\n'
            f' Committee size: {self.committee_size} nodes\n'
            f' Input rate: {sum(self.rate):,} tx/s\n'
            f' Transaction size: {self.size[0]:,} B\n'
            f' Execution time: {round(duration):,} s\n'
            
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
            f.write(self.result_str)

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
        latency = []
        for filename in sorted(glob(join(directory, 'latency-*.log'))):
            with open(filename, 'r') as f:
                latency += [f.read()]

        return cls(clients, nodes, latency, faults)

class CometBftMechanism:
    def __init__(self, settings):
        self.settings = settings
        self.name = 'cometbft'

        self.install_cmd = [
                'sudo apt-get update',
                'sudo apt-get -y upgrade',
                'sudo apt-get -y autoremove',
                
                # Install required packages
                'sudo apt-get install -y wget tar git make',

                # Download Golang
                'wget -c https://go.dev/dl/go1.21.8.linux-amd64.tar.gz',
                
                #Delete prev version and extract
                'sudo rm -rf ~/go/ && tar -xzf go1.21.8.linux-amd64.tar.gz',

                # Remove the tar.gz file
                'rm go1.21.8.linux-amd64.tar.gz',

                # If you do bash_profile then the color in terminal will go as on load that config will be used
                'echo export GOPATH=\"\$HOME/go\" >> ~/.profile',
                'echo export PATH=\"\$PATH:\$GOPATH/bin\" >> ~/.profile',
                # 'export PATH=$PATH:/usr/local/go/bin'
                'source ~/.profile',
                f'(git clone {self.settings.repo_url} || (cd {self.settings.repo_name} ; git pull))'
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
            'make build',
            'cd',
            CommandMaker.alias_binaries('', self.settings.repo_name)
        ]
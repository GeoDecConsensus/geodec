from fabric import Connection, ThreadingGroup as Group
from fabric.exceptions import GroupException
from paramiko import RSAKey
from paramiko.ssh_exception import PasswordRequiredException, SSHException
from os.path import basename, splitext
from time import sleep
from math import ceil
from os.path import join
from json import dump, load

import csv
import subprocess
# import pandas as pd

from benchmark.config import Committee, Key, NodeParameters, BenchParameters, ConfigError
from benchmark.utils import BenchError, Print, PathMaker, progress_bar
from benchmark.commands import CommandMaker
from benchmark.logs import LogParser, ParseError
from benchmark.instance import InstanceManager
# from benchmark.geodec import GeoDec
# from benchmark.geo_logs import GeoLogParser

from benchmark.mechanisms.cometbft import CometBftMechanism
from benchmark.mechanisms.hotstuff import HotStuffMechanism

class FabricError(Exception):
    ''' Wrapper for Fabric exception with a meaningfull error message. '''

    def __init__(self, error):
        assert isinstance(error, GroupException)
        message = list(error.result.values())[-1]
        super().__init__(message)


class ExecutionError(Exception):
    pass


class Bench:
    def __init__(self, ctx, mechanism):
        consensusMechanisms = ["cometbft", "hotstuff"]
        if mechanism not in consensusMechanisms:
            raise BenchError('Consensus mechanism support not available', e)

        self.manager = InstanceManager.make(mechanism)
        self.settings = self.manager.settings

        if mechanism == "cometbft":
            self.mechanism = CometBftMechanism(self.settings)
        elif mechanism == "hotstuff":
            self.mechanism = HotStuffMechanism(self.settings)   

        try:
            ctx.connect_kwargs.pkey = RSAKey.from_private_key_file(
                self.manager.settings.key_path
            )
            self.connect = ctx.connect_kwargs
        except (IOError, PasswordRequiredException, SSHException) as e:
            raise BenchError('Failed to load SSH key', e)

    def _check_stderr(self, output):
        if isinstance(output, dict):
            for x in output.values():
                if x.stderr:
                    Print("ERROR in an instance")
                    raise ExecutionError(x.stderr)
        else:
            if output.stderr:
                raise ExecutionError(output.stderr)

    def install(self):
        Print.info(f'Installing {self.settings.testbed}')
        cmd = self.mechanism.cmd

        hosts = self._select_hosts(4)

        # hosts = self.manager.hosts(flat=True)

        try:
            g = Group(*hosts, user=self.settings.key_name, connect_kwargs=self.connect)
            g.run(' && '.join(cmd), hide=False)
            Print.heading(f'Initialized testbed of {len(hosts)} nodes')
        except (GroupException, ExecutionError) as e:
            e = FabricError(e) if isinstance(e, GroupException) else e
            raise BenchError('Failed to install repo on testbed', e)

    def kill(self, hosts=[], delete_logs=False):
        assert isinstance(hosts, list)
        assert isinstance(delete_logs, bool)
        hosts = hosts if hosts else self.manager.hosts(flat=True)
        delete_logs = CommandMaker.clean_logs() if delete_logs else 'true'
        cmd = [delete_logs, f'({CommandMaker.kill()} || true)']
        try:
            g = Group(*hosts, user=self.settings.key_name, connect_kwargs=self.connect)
            g.run(' && '.join(cmd), hide=True)
        except GroupException as e:
            raise BenchError('Failed to kill nodes', FabricError(e))

    def _select_hosts(self, num):
        addrs = [] 
        # Retrieve values based on your scripts, note we use Internal IP addresses
        with open(self.settings.ip_file, 'r') as f:
            # If you used the GCP scripts from here https://github.com/sm86/gcp-scripts      
            if(self.settings.provider == "google_compute_engine"):
                reader = csv.DictReader(f)
                for row in reader:
                    addrs.append(row['Internal IP'])
            else:
                 addrs = [line.strip() for line in f.readlines()]
        return addrs[:num]
        # # Ensure there are enough hosts.
        # hosts = self.manager.hosts()
        # if sum(len(x) for x in hosts.values()) < nodes:
        #     return []

        # # Select the hosts in different data centers.
        # ordered = zip(*hosts.values())
        # ordered = [x for y in ordered for x in y]
        # return ordered[:nodes]

    def _background_run(self, host, command, log_file):
        name = splitext(basename(log_file))[0]
        if self.mechanism.name == 'hotstuff':
            cmd = f'tmux new -d -s "{name}" "{command} |& tee {log_file}"'
            # NOTE: Here the cmd is ran on a single instance
            c = Connection(host, user=self.settings.key_name, connect_kwargs=self.connect)
            output = c.run(cmd, hide=True)
            self._check_stderr(output)
        
        elif self.mechanism.name == 'cometbft':
            cmd = f'tmux new -d -s "{name}" "{command} |& tee {log_file}"'
            c = Connection(host, user=self.settings.key_name, connect_kwargs=self.connect)
            output = c.run(cmd, hide=True)
            self._check_stderr(output)

    def _update(self, hosts):
        Print.info(
            f'Updating {len(hosts)} nodes (branch "{self.settings.branch}")...'
        )
        # Check if the repo directory exists
        check_repo_cmd = f'[ -d {self.settings.repo_name} ] || git clone {self.settings.repo_url}'

        cmd = [
            check_repo_cmd,
            f'(cd {self.settings.repo_name} && git fetch -f)',
            f'(cd {self.settings.repo_name} && git checkout -f {self.settings.branch})',
            f'(cd {self.settings.repo_name} && git pull origin -f)',
            'source $HOME/.cargo/env',
            f'(cd {self.settings.repo_name}/node && {CommandMaker.compile()})',
            CommandMaker.alias_binaries(
                f'./{self.settings.repo_name}/target/release/'
            )
        ]
        g = Group(*hosts, user=self.settings.key_name, connect_kwargs=self.connect)
        g.run(' && '.join(cmd), hide=True)

    def _config(self, hosts, node_parameters):
        Print.info('Generating configuration files...')

        if self.mechanism.name == 'hotstuff':

            # Cleanup all local configuration files.
            cmd = CommandMaker.cleanup()
            subprocess.run([cmd], shell=True, stderr=subprocess.DEVNULL)

            # Recompile the latest code.
            cmd = CommandMaker.compile().split()
            # FIXME: breaking here when standalone benchmark folder
            subprocess.run(cmd, check=True, cwd=PathMaker.node_crate_path())

            # Create alias for the client and nodes binary.
            cmd = CommandMaker.alias_binaries(PathMaker.binary_path())
            subprocess.run([cmd], shell=True)

            # Generate configuration files.
            keys = []
            key_files = [PathMaker.key_file(i) for i in range(len(hosts))]
            for filename in key_files:
                cmd = CommandMaker.generate_key(filename).split()
                subprocess.run(cmd, check=True)
                keys += [Key.from_file(filename)]

            names = [x.name for x in keys]
            consensus_addr = [f'{x}:{self.settings.consensus_port}' for x in hosts]
            front_addr = [f'{x}:{self.settings.front_port}' for x in hosts]
            mempool_addr = [f'{x}:{self.settings.mempool_port}' for x in hosts]
            committee = Committee(names, consensus_addr, front_addr, mempool_addr)
            committee.print(PathMaker.committee_file())

            node_parameters.print(PathMaker.parameters_file())

            # NOTE Cleanup all nodes.
            cmd = f'{CommandMaker.cleanup()} || true'
            g = Group(*hosts, user=self.settings.key_name, connect_kwargs=self.connect)
            g.run(cmd, hide=True)

            # NOTE Upload configuration files.
            progress = progress_bar(hosts, prefix='Uploading config files:')
            for i, host in enumerate(progress):
                c = Connection(host, user=self.settings.key_name, connect_kwargs=self.connect)
                c.put(PathMaker.committee_file(), '.')
                c.put(PathMaker.key_file(i), '.')
                c.put(PathMaker.parameters_file(), '.')

            return committee

        elif self.mechanism.name == 'cometbft':

            # NOTE: Need to test # Cleanup node configuration files on hosts
            # for i, host in enumerate(hosts):
            #     cmd = CommandMaker.clean_node_config(i)
            #     c = Connection(host, user=self.settings.key_name, connect_kwargs=self.connect)
            #     c.run([cmd], shell=True, stderr=subprocess.DEVNULL)

            # Create persistent peers
            PathMaker.persistent_peers()

            hosts_string = " ".join(hosts)
            Print.info("Combined hosts: " + hosts_string)

            # cmd = [f'~/cometbft show_node_id --home ./mytestnet/node{i}']
            with open('persistent_peer.txt', 'w') as f:
                f.write("")
                f.close()

            # Create testnet config files
            cmd = [f'~/cometbft testnet --v {len(hosts)}']
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL)
            
            # Run the bash file and store the ouput in this file
            cmd = [
                # 'chmod u+x ./persistent.sh',
                f'./persistent.sh {hosts_string}'
            ]
            subprocess.run(cmd, shell=True)

            progress = progress_bar(hosts, prefix='Uploading config files:')
            for i, host in enumerate(hosts):
                Print.info("Sent node config file to " + host)
                # NOTE: Path of the node config files
                cmd = [f'scp -i {self.settings.key_path} -r {self.settings.key_name}@206.12.100.21:./geodec-hotstuff/benchmark/mytestnet/node{i} ubuntu@{host}:~/']
                subprocess.run(cmd, shell=True)

    def _run_single(self, hosts, rate, bench_parameters, node_parameters, debug=False):
        Print.info('Booting testbed...')

        # Kill any potentially unfinished run and delete logs.
        self.kill(hosts=hosts, delete_logs=True)

        if self.mechanism.name == 'hotstuff':
            # Run the clients (they will wait for the nodes to be ready).
            # Filter all faulty nodes from the client addresses (or they will wait
            # for the faulty nodes to be online).
            committee = Committee.load(PathMaker.committee_file())
            addresses = [f'{x}:{self.settings.front_port}' for x in hosts]
            rate_share = ceil(rate / committee.size())  # Take faults into account.
            timeout = node_parameters.timeout_delay
            client_logs = [PathMaker.client_log_file(i) for i in range(len(hosts))]
            for host, addr, log_file in zip(hosts, addresses, client_logs):
                cmd = CommandMaker.run_client(
                    addr,
                    bench_parameters.tx_size,
                    rate_share,
                    timeout,
                    nodes=addresses
                )
                self._background_run(host, cmd, log_file)

            # Run the nodes.
            key_files = [PathMaker.key_file(i) for i in range(len(hosts))]
            dbs = [PathMaker.db_path(i) for i in range(len(hosts))]
            node_logs = [PathMaker.node_log_file(i) for i in range(len(hosts))]
            for host, key_file, db, log_file in zip(hosts, key_files, dbs, node_logs):
                cmd = CommandMaker.run_node(
                    key_file,
                    PathMaker.committee_file(),
                    db,
                    PathMaker.parameters_file(),
                    debug=debug
                )
                self._background_run(host, cmd, log_file)

            # Wait for the nodes to synchronize
            Print.info('Waiting for the nodes to synchronize...')
            sleep(2 * node_parameters.timeout_delay / 1000)

            # Wait for all transactions to be processed.
            duration = bench_parameters.duration
            for _ in progress_bar(range(20), prefix=f'Running benchmark ({duration} sec):'):
                sleep(ceil(duration / 20))
            self.kill(hosts=hosts, delete_logs=False)

        elif self.mechanism.name == 'cometbft':
            persistent_peers = []
            
            with open('persistent_peer.txt', 'r') as f:
                persistent_peers = f.read()
                persistent_peers = persistent_peers[:-1]
            print(persistent_peers)

            node_logs = [PathMaker.node_log_file(i) for i in range(len(hosts))]
            for i, (host, log_file) in enumerate(zip(hosts, node_logs)):
                cmd = f'~/cometbft node --home ~/node{i} --proxy_app=kvstore --p2p.persistent_peers="{persistent_peers}"'
                self._background_run(host, cmd, log_file)
            
            # Wait for the nodes to synchronize
            Print.info('Waiting for the nodes to synchronize...')
            sleep(2 * node_parameters.timeout_delay / 1000)

            self.kill(hosts=hosts, delete_logs=False)


    def _logs(self, hosts, faults): #, servers, run_id):
        # Delete local logs (if any).
        cmd = CommandMaker.clean_logs()
        subprocess.run([cmd], shell=True, stderr=subprocess.DEVNULL)

        if self.mechanism.name == "hotstuff":
            # Download log files.
            progress = progress_bar(hosts, prefix='Downloading logs:')
            for i, host in enumerate(progress):
                c = Connection(host, user=self.settings.key_name, connect_kwargs=self.connect)
                c.get(PathMaker.node_log_file(i), local=PathMaker.node_log_file(i))
                c.get(
                    PathMaker.client_log_file(i), local=PathMaker.client_log_file(i)
                )

            # Parse logs and return the parser.
            Print.info('Parsing logs and computing performance...')
            return LogParser.process(PathMaker.logs_path(), faults=faults)
        
        elif self.mechanism.name == "cometbft":
            # Download log files.
            progress = progress_bar(hosts, prefix='Downloading logs:')
            for i, host in enumerate(progress):
                c = Connection(host, user=self.settings.key_name, connect_kwargs=self.connect)
                c.get(PathMaker.node_log_file(i), local=PathMaker.node_log_file(i))

            # Parse logs and return the parser.
            Print.info('Parsing logs and computing performance...')
            # return LogParser.process(PathMaker.logs_path(), faults=faults)

        # # Delete local logs (if any).
        # cmd = CommandMaker.clean_logs()
        # subprocess.run([cmd], shell=True, stderr=subprocess.DEVNULL)

        # hosts_df = pd.DataFrame(columns=['ip', 'node_num'])

        # # Download log files.
        # progress = progress_bar(hosts, prefix='Downloading logs:')
        # for i, host in enumerate(progress):
        #     c = Connection(host, user='ubuntu', connect_kwargs=self.connect)
        #     c.get(PathMaker.node_log_file(i), local=PathMaker.node_log_file(i))
        #     c.get(
        #         PathMaker.client_log_file(i), local=PathMaker.client_log_file(i)
        #     )
        #     # mapping HOST <---> i 
        #     new_data = pd.DataFrame({'ip':host, 'node_num':i},  index=[0])
        #     hosts_df = pd.concat([hosts_df, new_data], ignore_index = True)
        
        # servers = pd.merge(servers, hosts_df, on='ip')
        # # Parse logs and return the parser.
        # Print.info('Parsing logs and computing performance...')
        # return LogParser.process(PathMaker.logs_path(), faults=faults, servers=servers, run_id =run_id)

    def run(self, bench_parameters_dict, node_parameters_dict, geoInput, debug=False):
        assert isinstance(debug, bool)
        Print.heading('Starting remote benchmark')

        try:
            bench_parameters = BenchParameters(bench_parameters_dict)
            node_parameters = NodeParameters(node_parameters_dict)
        except ConfigError as e:
            raise BenchError('Invalid nodes or bench parameters', e)
        
        isGeoRemote = True
        if not geoInput:
            isGeoRemote = False
            
        # geodec = GeoDec()
        # servers = geodec.getAllServers(geoInput, "/home/ubuntu/data/servers-2020-07-19.csv", self.settings.)
        # pingDelays = geodec.getPingDelay(geoInput, "/home/ubuntu/data/pings-2020-07-19-2020-07-20-grouped.csv", "/home/ubuntu/data/pings-2020-07-19-2020-07-20.csv")

        # Select which hosts to use.
        selected_hosts = self._select_hosts(bench_parameters.nodes[0])

        if len(selected_hosts) < bench_parameters.nodes[0]:
            Print.warn('There are not enough instances available')
            return


        # Update nodes.
        # NOTE: Leaving this out because cometbft doest need a repo
        # try:
        #     self._update(selected_hosts)
        # except (GroupException, ExecutionError) as e:
        #     e = FabricError(e) if isinstance(e, GroupException) else e
        #     raise BenchError('Failed to update nodes', e)
        
        # # # Set delay parameters.
        # try:
        #     self._configDelay(selected_hosts)
        #     print("configured delays")
        #     self._addDelays(servers, pingDelays, self.settings.interface)
        # except (subprocess.SubprocessError, GroupException) as e:
        #     e = FabricError(e) if isinstance(e, GroupException) else e
        #     Print.error(BenchError('Failed to initalize delays', e))
         
        # Run benchmarks.
        for n in bench_parameters.nodes:
            for r in bench_parameters.rate:
                Print.heading(f'\nRunning {n} nodes (input rate: {r:,} tx/s)')
                hosts = selected_hosts[:n]

                # Upload all configuration files.
                try:
                    self._config(hosts, node_parameters)
                except (subprocess.SubprocessError, GroupException) as e:
                    e = FabricError(e) if isinstance(e, GroupException) else e
                    Print.error(BenchError('Failed to configure nodes', e))
                    continue

                # Do not boot faulty nodes.
                faults = bench_parameters.faults
                hosts = hosts[:n-faults]
                
                # run_id_array = []
                
                # Run the benchmark.
                for i in range(bench_parameters.runs):
        #             run_id = GeoLogParser.get_new_run_id()
        #             Print.heading(f'Run {i+1}/{bench_parameters.runs} with run_id {run_id}')
                    try:
                        self._run_single(
                            hosts, r, bench_parameters, node_parameters, debug
                        )
                        if self.mechanism.name == "hotstuff":
                            self._logs(hosts, faults).print(PathMaker.result_file(
                                faults, n, r, bench_parameters.tx_size
                            ))
                        elif self.mechanism.name == "cometbft":
                            self._logs(hosts, faults)
        #                 run_id_array.append(run_id)
                    except (subprocess.SubprocessError, GroupException, ParseError) as e:
                        self.kill(hosts=hosts)
                        if isinstance(e, GroupException):
                            e = FabricError(e)
                        Print.error(BenchError('Benchmark failed', e))
                        continue
                
        #         aggregated_results = GeoLogParser.aggregate_runs(run_id_array)
        #         print(aggregated_results)
        #         aggregated_results.to_csv('/home/ubuntu/results/64node-fixed-mean-geo-dec-metrics.csv', mode='a', index=False, header=False)

        # # Delte delay parameters.
        # try:
        #     self._deleteDelay(selected_hosts)
        # except (subprocess.SubprocessError, GroupException) as e:
        #     e = FabricError(e) if isinstance(e, GroupException) else e
        #     Print.error(BenchError('Failed to initalize delays', e))
            
    ################ GEODEC Emulator methods #########################
    def _configDelay(self, hosts):
        Print.info('Delay qdisc initalization...')
        cmd = CommandMaker.initalizeDelayQDisc(self.settings.interface)
        g = Group(*hosts, user=self.settings.key_name, connect_kwargs=self.connect)
        g.run(cmd, hide=True)

    def _deleteDelay(self, hosts):
        Print.info('Delete qdisc configurations...')
        cmd = CommandMaker.deleteDelayQDisc(self.settings.interface)
        g = Group(*hosts, user=self.settings.key_name, connect_kwargs=self.connect)
        g.run(cmd, hide=True)

    def _addDelays(self, servers, pingDelays, interface):
        for index, source in servers.iterrows():
            source_commands = ''
            counter = 1
            for index, destination in servers.iterrows():
                if source['id'] != destination['id']:
                    query = 'source == ' + str(source['id']) + ' and destination == '+ str(destination['id'])
                    delay_data = pingDelays.query(query) 
                    delay = delay_data['avg'].values.astype(float)[0]
                    delay_dev = delay_data['mdev'].values.astype(float)[0]
                    cmd = self._getDelayCommand(counter, destination['ip'], interface, delay/2, delay_dev/2)
                    source_commands = source_commands + cmd
                    counter = counter + 1
            host = source['ip']
            # execute the command for source IP
            c = Connection(host, user=self.settings.key_name, connect_kwargs=self.connect)
            c.run(source_commands, hide=True)

    def _getDelayCommand(self, n, ip, interface, delay, delay_dev):
        return (f'sudo tc class add dev {interface} parent 1:0 classid 1:{n+1} htb rate 1000kbit; sudo tc filter add dev {interface} parent 1:0 protocol ip u32 match ip dst {ip} flowid 1:{n+1}; sudo tc qdisc add dev {interface} parent 1:{n+1} handle {n*10}:0 netem delay {delay}ms {delay_dev}ms; ')

# from fabric import Group
# from fabric.exceptions import GroupException
# from paramiko import RSAKey
# from paramiko.ssh_exception import PasswordRequiredException, SSHException
# from benchmark.utils import BenchError, Print
# from benchmark.commands import CommandMaker
# from benchmark.instance import InstanceManager
# from benchmark.logs import LogParser, ParseError
# from benchmark.config import Committee, Key, NodeParameters, BenchParameters, ConfigError
# from benchmark.errors import FabricError, ExecutionError
# from os.path import join

class CometBftMechanism:
    def __init__(self, settings):
        self.settings = settings
        self.name = 'cometbft'
        print("Inside CometBft")

        self.cmd = [
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

        self.old_cmd = [
            'sudo apt-get update',
            'sudo apt-get -y upgrade',
            'sudo apt-get -y autoremove',
            
            # Install required packages
            'sudo apt-get install -y wget tar git make',

            # Download and install Golang
            'wget -c https://golang.org/dl/go1.21.6.linux-amd64.tar.gz',
            'tar -xzf go1.21.6.linux-amd64.tar.gz',
            #'sudo mv go /usr/local',

            # Remove the tar.gz file
            'rm go1.21.6.linux-amd64.tar.gz',

            # 'echo export GOPATH=\"\$HOME/go\" >> ~/.profile',
            # 'echo export PATH=\"\$PATH:\$GOPATH/bin\" >> ~/.profile',
            # 'source ~/.profile',

            'echo \'export PATH=\$PATH:/usr/local/go/bin\' >> ~/.bashrc',
            'source ~/.bashrc',

            f'(git clone {self.settings.repo_url} || (cd {self.settings.repo_name} ; git pull))',

            # 'make install',
            # 'make build',

            # 'source ~/.profile'
        ]

        self.rev_cmd = [
            'rm -rf cometbft cometbft-repo',
            'cd',
            f'rm -rf {self.settings.repo_name}',
        ]

        self.test_cmd = [
            # 'rm go1.21.6.linux-amd64.tar.gz',
            # 'rm -rf geodec'
            'rm -rf test123'
        ]

        self.make_cmd = [
            'cd',
            f'cd {self.settings.repo_name}',
            'make install',
            'make build'
        ]
    def install(self):
        print('Installing CometBft ...')

#     @staticmethod
#     def print_result(result: Result):
#         print(result.stdout)

# class FabricError(Exception):
#     pass

# class BenchError(Exception):
#     pass

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

        self.cmd = [
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

                 f'(git clone -b {self.settings.branch} {self.settings.repo_url} || (cd {self.settings.repo_name} ; git pull))',
            ],
            [
                'source ~/.profile',
                f'cd {self.settings.repo_name}',
                # f'git fetch -f && git checkout -f {self.settings.branch}',
                'make install',
                'make build',
                'cd ./test/loadtime',
                'make build'
            ]
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

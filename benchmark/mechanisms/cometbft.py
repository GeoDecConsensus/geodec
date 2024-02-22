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
        print("Inside CometBft")

        self.cmd = [
            'sudo apt-get update',
            'sudo apt-get -y upgrade',
            'sudo apt-get -y autoremove',
            
            # Install required packages
            'sudo apt-get install -y wget tar git make',

            # Download and install Golang
            'wget -c https://golang.org/dl/go1.21.6.linux-amd64.tar.gz',
            'tar -xvzf go1.21.6.linux-amd64.tar.gz',
            'sudo mv go /usr/local',

            # Remove the tar.gz file
            'rm go1.21.6.linux-amd64.tar.gz',

            'echo export GOPATH=\"\$HOME/go\" >> ~/.profile',
            'echo export PATH=\"\$PATH:\$GOPATH/bin\" >> ~/.profile',
            'source ~/.profile',

            f'(git clone {self.settings.repo_url} || (cd {self.settings.repo_name} ; git pull))',

            'make install',
            'make build',

            'source ~/.profile'
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

import glob
from os.path import join
from benchmark.mechanisms.cometbft import CometBftLogParser
from benchmark.mechanisms.hotstuff import HotStuffLogParser
from benchmark.mechanisms.bullshark import BullsharkLogParser

class ParseError(Exception):
    pass
class LogParser:
    def __init__(self):
        self.result_str = ""

    @classmethod
    def process(cls, directory, faults):
        assert isinstance(directory, str)

        clients = []
        for filename in sorted(glob.glob(join(directory, 'client-*.log'))):
            with open(filename, 'r') as f:
                clients.append(f.read())
        nodes = []
        for filename in sorted(glob.glob(join(directory, 'node-*.log'))):
            with open(filename, 'r') as f:
                nodes.append(f.read())
        latency = []
        for filename in sorted(glob.glob(join(directory, 'latency-*.log'))):
            with open(filename, 'r') as f:
                latency.append(f.read())

        return cls(clients, nodes, latency, faults)
    
    def result(self):
        return self.result_str

    def print(self, filename):
        assert isinstance(filename, str)
        with open(filename, 'a') as f:
            f.write(self.result_str)

    def log_parser(self, mechanism_name, directory, faults=0):
        if mechanism_name == "hotstuff":
            result =  HotStuffLogParser.process(directory, faults).result_str
        elif mechanism_name == "cometbft":
            result = CometBftLogParser.process(directory, faults).result_str
        elif mechanism_name == "bullshark":
            result = BullsharkLogParser.process(directory, faults).result_str
        
        self.result_str = result
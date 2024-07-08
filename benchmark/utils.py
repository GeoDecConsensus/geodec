import csv
import json
from os.path import join


class BenchError(Exception):
    def __init__(self, message, error):
        assert isinstance(error, Exception)
        self.message = message
        self.cause = error
        super().__init__(message)


class PathMaker:
    @staticmethod
    def persistent_peers():
        return 'persistent_peers.json'
        
    @staticmethod
    def binary_path(repo_name):
        return join('..', f'{repo_name}', 'target', 'release')

    @staticmethod
    def node_crate_path(repo_name):
        return join('..', f'{repo_name}', 'node')

    @staticmethod
    def committee_file():
        return '.committee.json'

    @staticmethod
    def parameters_file():
        return '.parameters.json'

    @staticmethod
    def key_file(i):
        assert isinstance(i, int) and i >= 0
        return f'.node-{i}.json'

    @staticmethod
    def db_path(i):
        assert isinstance(i, int) and i >= 0
        return f'.db-{i}'
    
    @staticmethod
    def db_path(i, j=None):
        assert isinstance(i, int) and i >= 0
        assert (isinstance(j, int) and i >= 0) or j is None
        worker_id = f'-{j}' if j is not None else ''
        return f'.db-{i}{worker_id}'
        
    @staticmethod
    def logs_path():
        return 'logs'
    
    @staticmethod
    def latency_log_file(i):
        assert isinstance(i, int) and i >= 0
        return join(PathMaker.logs_path(), f'latency-{i}.log')

    @staticmethod
    def node_log_file(i):
        assert isinstance(i, int) and i >= 0
        return join(PathMaker.logs_path(), f'node-{i}.log')

    @staticmethod
    def client_log_file(i):
        assert isinstance(i, int) and i >= 0
        return join(PathMaker.logs_path(), f'client-{i}.log')
    
    @staticmethod
    def primary_log_file(i):
        assert isinstance(i, int) and i >= 0
        return join(PathMaker.logs_path(), f'primary-{i}.log')

    @staticmethod
    def worker_log_file(i, j):
        assert isinstance(i, int) and i >= 0
        assert isinstance(j, int) and i >= 0
        return join(PathMaker.logs_path(), f'worker-{i}-{j}.log')

    @staticmethod
    def client_log_file_bull(i, j):
        assert isinstance(i, int) and i >= 0
        assert isinstance(j, int) and i >= 0
        return join(PathMaker.logs_path(), f'client-{i}-{j}.log')

    @staticmethod
    def results_path():
        return 'results'

    @staticmethod
    def result_file(mechanism, nodes, rate, tx_size, faults):
        return join(
            PathMaker.results_path(), 
            f'bench-{mechanism}-{nodes}-{rate}-{tx_size}-{faults}.txt'
        )

    @staticmethod
    def plots_path():
        return 'plots'

    @staticmethod
    def agg_file(type, faults, nodes, rate, tx_size, max_latency):
        return join(
            PathMaker.plots_path(),
            f'{type}-{faults}-{nodes}-{rate}-{tx_size}-{max_latency}.txt'
        )

    @staticmethod
    def plot_file(name, ext):
        return join(PathMaker.plots_path(), f'{name}.{ext}')


class Color:
    HEADER = '\033[95m'
    OK_BLUE = '\033[94m'
    OK_GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Print:
    @staticmethod
    def heading(message):
        assert isinstance(message, str)
        print(f'{Color.OK_GREEN}{message}{Color.END}')

    @staticmethod
    def info(message):
        assert isinstance(message, str)
        print(message)

    @staticmethod
    def warn(message):
        assert isinstance(message, str)
        print(f'{Color.BOLD}{Color.WARNING}WARN{Color.END}: {message}')

    @staticmethod
    def error(e):
        assert isinstance(e, BenchError)
        print(f'\n{Color.BOLD}{Color.FAIL}ERROR{Color.END}: {e}\n')
        causes, current_cause = [], e.cause
        while isinstance(current_cause, BenchError):
            causes += [f'  {len(causes)}: {e.cause}\n']
            current_cause = current_cause.cause
        causes += [f'  {len(causes)}: {type(current_cause)}\n']
        causes += [f'  {len(causes)}: {current_cause}\n']
        print(f'Caused by: \n{"".join(causes)}\n')


def progress_bar(iterable, prefix='', suffix='', decimals=1, length=30, fill='█', print_end='\r'):
    total = len(iterable)

    def printProgressBar(iteration):
        formatter = '{0:.'+str(decimals)+'f}'
        percent = formatter.format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end)

    printProgressBar(0)
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    print()

def set_weight_cometbft(geo_input_file):
    # Get the stake values
    stakes = []
    with open(geo_input_file, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if row['stake'] and row['id']:
                stakes.append(row['stake'])

    def get_path(i):
        return './mytestnet/node{i}/config/genesis.json'.format(i=i)
    
    # Set the weights
    for i in range(len(stakes)):
        path = get_path(i)
        with open(path, 'r') as file:
            data = json.load(file)
            for j, validator in enumerate(data['validators']):
                validator['power'] = stakes[j]  # New value for the "power" field

        with open(path, 'w') as file:
            json.dump(data, file, indent=4)
            
def set_weight_hotstuff(geo_input_file):
    # Get the stake values
    stakes = []
    with open(geo_input_file, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if row['stake'] and row['id']:
                stakes.append(int(row['stake']))

    def get_path():
        return './.committee.json'
    
    # Set the weights
    path = get_path()
    with open(path, 'r') as file:
        data = json.load(file)
        # Update consensus authorities stakes
        for i, authority in enumerate(data['consensus']['authorities'].values()):
            authority['stake'] = stakes[i]
        
        # Update mempool authorities stakes
        for i, authority in enumerate(data['mempool']['authorities'].values()):
            authority['stake'] = stakes[i]

    with open(path, 'w') as file:
        json.dump(data, file, indent=4)

def set_weight_bullshark(geo_input_file):
    # Get the stake values
    stakes = []
    with open(geo_input_file, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if row['stake'] and row['id']:
                stakes.append(int(row['stake']))

    def get_path():
        return './.committee.json'
    
    # Set the weights
    path = get_path()
    with open(path, 'r') as file:
        data = json.load(file)
        for i, authority in enumerate(data['authorities'].values()):
            authority['stake'] = stakes[i]

    with open(path, 'w') as file:
        json.dump(data, file, indent=4)
        
def set_weight(mechanism, geo_input_file):
    if mechanism == 'cometbft':
        set_weight_cometbft(geo_input_file)
    elif mechanism == 'hotstuff':
        set_weight_hotstuff(geo_input_file)
    elif mechanism == 'bullshark':
        set_weight_bullshark(geo_input_file)
from fabric import Connection, ThreadingGroup as Group
from benchmark.utils import Print

class LatencySetter:
    def __init__(self, settings, connect):
        self.settings = settings
        self.connect = connect
        
    @staticmethod
    def _initalizeDelayQDisc(interface):
        return (f'sudo tc qdisc add dev {interface} parent root handle 1:0 htb default 100')
    
    @staticmethod
    def _deleteDelayQDisc(interface):
        return (f'sudo tc qdisc del dev {interface} parent root')

    def configDelay(self, hosts):
        Print.info('Delay qdisc initalization...')
        cmd = LatencySetter._initalizeDelayQDisc(self.settings.interface)
        g = Group(*hosts, user=self.settings.key_name, connect_kwargs=self.connect)
        g.run(cmd, hide=True)

    def deleteDelay(self, hosts):
        Print.info('Delete qdisc configurations...')
        cmd = LatencySetter._deleteDelayQDisc(self.settings.interface)
        g = Group(*hosts, user=self.settings.key_name, connect_kwargs=self.connect)
        g.run(cmd, hide=True)

    def addDelays(self, servers, pingDelays, interface):
        for index, source in servers.iterrows():
            source_commands = ''
            counter = 1
            for index, destination in servers.iterrows():
                if source['id'] != destination['id']:
                    query = 'source == ' + str(source['id']) + ' and destination == '+ str(destination['id'])
                    delay_data = pingDelays.query(query) 
                    delay = delay_data['avg'].values.astype(float)[0]
                    delay_dev = delay_data['mdev'].values.astype(float)[0]
                    cmd = LatencySetter._getDelayCommand(counter, destination['ip'], interface, delay/2, delay_dev/2)
                    source_commands = source_commands + cmd
                    counter = counter + 1
            host = source['ip']
            # execute the command for source IP
            c = Connection(host, user=self.settings.key_name, connect_kwargs=self.connect)
            c.run(source_commands, hide=True)

    @staticmethod
    def _getDelayCommand(n, ip, interface, delay, delay_dev):
        return (f'sudo tc class add dev {interface} parent 1:0 classid 1:{n+1} htb rate 1gbit;' 
                f'sudo tc filter add dev {interface} parent 1:0 protocol ip u32 match ip dst {ip} flowid 1:{n+1};' 
                f'sudo tc qdisc add dev {interface} parent 1:{n+1} handle {n*10}:0 netem delay {delay}ms {delay_dev}ms; ')

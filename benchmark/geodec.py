import haversine as hs
import math
import numpy as np
import os.path
import pandas as pd
import csv

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

class GeoDec:
    
    @staticmethod
    def getGeoInput(geo_input_file):
        geo_input = {}
        with open(geo_input_file, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row['id']:  # Ensure id is not empty
                    geo_input[int(row['id'])] = 1
                if row['count'] and row['id']:
                    geo_input[int(row['id'])] = int(row['count'])
        return geo_input
       
    def _getServers(geoInput, servers_file):
        geoLocations = list(geoInput.keys())
        servers = pd.read_csv(servers_file)[['id', 'name', 'latitude', 'longitude']]
        selected_servers = servers[servers['id'].isin(geoLocations)]
        return selected_servers
    
    @staticmethod
    def getAllServers(geoInput, servers_file, ip_file):
        servers = GeoDec._getServers(geoInput, servers_file)
        updated = servers
        for key in geoInput:
            num = geoInput[key]
            while num > 1 :
                data = servers.query(f'id == {key}').copy()
                data['name'] = data['name']+str(num)
                updated = pd.concat([updated, data], ignore_index=True)
                num -= 1
        updated = GeoDec._addIPtoServers(updated, ip_file)
        valGDI = GeoDec._calculateGDI(updated)
        return pd.merge(updated, valGDI, on='name')

    def _addIPtoServers(servers, ip_file):
        serversIP = servers
        data = pd.read_csv(ip_file)
        lines = data['Internal IP'].tolist()
        if len(lines) < len(servers):
            print("ERROR: NEED MORE IP ADDRESSES")
            return 
        serversIP = servers.assign(ip=lines[:len(servers)])
        return serversIP 

    def _getDistanceMatrix(df):
        dist = pd.DataFrame(columns=df["name"], index=df["name"])
        for source in df.index:
            s_addr = df["name"][source]
            s = (df['latitude'][source], df['longitude'][source])
            for destination in df.index:
                d_addr = df["name"][destination]
                d = (df['latitude'][destination], df['longitude'][destination])
                dist[s_addr][d_addr] = hs.haversine(s, d)
        return dist

    def _calculateGDI(servers): 
        dist_matrix = GeoDec._getDistanceMatrix(servers)
        servers_list = list(dist_matrix.columns)
        two_third_threshold = math.ceil(len(servers_list) * (2/3))
        one_third_threshold = math.ceil(len(servers_list) / 3)
        
        dist_df = pd.DataFrame(columns=['name', 'one_third_dist', 'two_third_dist', 'total_dist', 'rms_one_third_dist', 'rms_two_third_dist', 'rms_total_dist'])
        for addr in servers_list:
            i = 0
            j = 0 
            total_dist = 0
            two_third_sum = 0
            one_third_sum = 0
            rms_total_dist = 0
            rms_two_third_sum = 0
            rms_one_third_sum = 0
            for num in sorted(dist_matrix[addr]):
                total_dist += num
                rms_total_dist += pow(num, 2)
                if i < two_third_threshold:
                    two_third_sum += num
                    rms_two_third_sum += pow(num, 2)
                if j < one_third_threshold:
                    one_third_sum += num
                    rms_one_third_sum += pow(num, 2)
                i += 1
                j += 1
            rms_total_dist = math.sqrt(rms_total_dist)   
            rms_one_third_sum = math.sqrt(rms_one_third_sum)
            rms_two_third_sum = math.sqrt(rms_two_third_sum)
            new_data = pd.DataFrame({'name': addr, 'one_third_dist': one_third_sum, 'two_third_dist': two_third_sum, 'total_dist': total_dist, 'rms_one_third_dist': rms_one_third_sum, 'rms_two_third_dist': rms_two_third_sum, 'rms_total_dist': rms_total_dist}, index=[0])
            dist_df = pd.concat([dist_df, new_data], ignore_index=True)
        return dist_df
    
    def _aggregatePingDelays(pings_file, pings_grouped_file):
        pings = pd.read_csv(pings_file)
        pings_grouped = pings.groupby(['source', 'destination']).median()
        pings_grouped.to_csv(pings_grouped_file)

    @staticmethod
    def getPingDelay(geoInput, pings_grouped_file, pings_file):
        if not os.path.exists(pings_grouped_file):
            GeoDec._aggregatePingDelays(pings_file, pings_grouped_file)
        pingsDelays = pd.read_csv(pings_grouped_file)
        id = list(geoInput.keys())
        pingsDelays = pingsDelays[pingsDelays.source.isin(id) & pingsDelays.destination.isin(id)].query('source != destination')
        return pingsDelays
   
    def _check_if_quorum(dist_matrix, server, target, quorum_threshold):
        distance = dist_matrix[target][server]
        quorum_distances = sorted(dist_matrix[target])[:quorum_threshold]
        return (distance in quorum_distances)

    @staticmethod
    def calculateGDI_updated(data): 
        dist_matrix = GeoDec._getDistanceMatrix(data)
        servers = list(dist_matrix.columns)
        two_third_threshold = math.ceil(len(servers) * (2/3))
        GDI_df = pd.DataFrame(columns=['name', 'quorum_counter'])
        for addr in servers:
            quorum_counter = 0
            for target in servers:
                if GeoDec._check_if_quorum(dist_matrix, addr, target, two_third_threshold):
                    quorum_counter += 1 
            new_data = pd.DataFrame({'name': addr, 'quorum_counter': quorum_counter}, index=[0])
            GDI_df = pd.concat([GDI_df, new_data], ignore_index=True)
        GDI_df = GDI_df.merge(data, on='name', how='right')
        return GDI_df

# if __name__ == "__main__":
#     geoInput = {1:1, 2:1, 3:1, 4:1}

#     geodec = GeoDec()

#     selected_servers = geodec.getAllServers(geoInput, "/Users/namangarg/code/geodec/rundata/servers.csv", '/Users/namangarg/code/geodec/rundata/ip_file.csv')
#     pingDelays = geodec.getPingDelay(geoInput, '/Users/namangarg/code/geodec/rundata/ping_grouped.csv', '/Users/namangarg/code/geodec/rundata/pings.csv')

#     # Printing selected_servers in proper format
#     selected_servers = selected_servers[['ip', 'id', 'name', 'latitude', 'longitude']]
#     print(selected_servers.to_string(index=False))

#     # Printing pingDelays
#     pingDelays = pingDelays[['source', 'destination', 'avg', 'mdev']]
#     print(pingDelays.to_string(index=False))

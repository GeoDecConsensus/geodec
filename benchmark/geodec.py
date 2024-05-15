import haversine as hs
import math
import numpy as np
import os.path
import pandas as pd

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

#########################################################################################
#########################################################################################
#### GeoDec emulator to study impacts of geospatial diversity on blockchain networks ####
############# Created by Shashank Motepalli, Arno Jacobsen ##############################
#########################################################################################
#########################################################################################

class GeoDec:
       
    # get servers based on location from list of all servers
    def _getServers(self, geoInput, servers_file):
        geoLocations = list(geoInput.keys())
        servers = pd.read_csv(servers_file)[['id', 'name', 'latitude', 'longitude']]
        selected_servers = servers[ servers['id'].isin(geoLocations)]
        return selected_servers
    
    # get all servers based on count and location 
    def getAllServers(self, geoInput, servers_file, ip_file):

        servers = self._getServers(geoInput, servers_file)
        updated = servers
        for key in geoInput:
            num = geoInput[key]
            while num > 1 :
                data = servers.query(f'id == {key}').copy()
                data['name'] = data['name']+str(num)
                updated = pd.concat([updated, data], ignore_index = True)
                num = num - 1
        # adding IP address to servers
        updated = self._addIPtoServers(updated, ip_file)
        # calculate geospatial diversity index
        valGDI = self._calculateGDI(updated)
        return pd.merge(updated, valGDI, on='name')


    def _addIPtoServers(self, servers, ip_file):
        serversIP = servers
        data = pd.read_csv(ip_file)
        lines = data['Internal IP'].tolist()
        
        # check the total available IP addresses less than or more than total servers
        if(len(lines) < len(servers)):
            print.WARN("ERROR: NEED MORE IP ADDRESSES")
            return 
        
        serversIP = servers.assign(ip=lines[:len(servers)])
        return serversIP 

    # get distance between two points in 2D array
    # calculates distance in km using Haversine formulae
    def _getDistanceMatrix(self, df):
        dist = pd.DataFrame(columns=df["name"], index=df["name"])
        for source in df.index:
            s_addr = df["name"][source]
            s = (df['latitude'][source], df['longitude'][source])
            for destination in df.index:
                d_addr = df["name"][destination]
                d = (df['latitude'][destination], df['longitude'][destination])
                dist[s_addr][d_addr] = hs.haversine(s, d)         
        return dist


    ### GDI (GeoSpatial Diversity Index) CALCULATION
    def _calculateGDI(self, servers): 
        dist_matrix = self._getDistanceMatrix(servers)
        servers = list(dist_matrix.columns)
        two_third_threshold = math.ceil(len(servers) * (2/3))
        one_third_threshold = math.ceil(len(servers)/3)
        
        dist_df = pd.DataFrame(columns=['name', 'one_third_dist', 'two_third_dist', 'total_dist', 'rms_one_third_dist', 'rms_two_third_dist', 'rms_total_dist'])
        for addr in servers:
            i =0
            j =0 
            total_dist = 0
            two_third_sum = 0
            one_third_sum = 0
            rms_total_dist = 0
            rms_two_third_sum = 0
            rms_one_third_sum = 0
            for num in sorted(dist_matrix[addr]):
                total_dist = total_dist + num
                rms_total_dist = rms_total_dist + pow(num,2)
                if(i < two_third_threshold):
                    two_third_sum = two_third_sum + num
                    rms_two_third_sum = rms_two_third_sum + pow(num,2)
                if(j< one_third_threshold):
                    one_third_sum = one_third_sum + num
                    rms_one_third_sum = rms_one_third_sum + pow(num,2)
                i = i +1
                j = j +1
            rms_total_dist = math.sqrt(rms_total_dist)   
            rms_one_third_sum = math.sqrt(rms_one_third_sum)
            rms_two_third_sum = math.sqrt(rms_two_third_sum)
            new_data = pd.DataFrame({'name':addr, 'one_third_dist':one_third_sum, 'two_third_dist':two_third_sum, 'total_dist': total_dist, 'rms_one_third_dist': rms_one_third_sum, 'rms_two_third_dist': rms_two_third_sum, 'rms_total_dist' : rms_total_dist },  index=[0])
            dist_df = pd.concat([dist_df, new_data], ignore_index = True)
        return dist_df
    
    def _aggregatePingDelays(self, pings_file, pings_grouped_file):
        pings = pd.read_csv(pings_file)
        # took median to ensure extreme values do not affect the mean
        pings_grouped = pings.groupby(['source', 'destination']).median()
        pings_grouped.to_csv(pings_grouped_file)

    def getPingDelay(self, geoInput, pings_grouped_file, pings_file):
        if os.path.exists(pings_grouped_file) == False:
            self._aggregatePingDelays(pings_file, pings_grouped_file)
        pingsDelays = pd.read_csv(pings_grouped_file)
        id = list(geoInput.keys())
        pingsDelays = pingsDelays[pingsDelays.source.isin(id) & pingsDelays.destination.isin(id)].query('source != destination')
        return pingsDelays
   
    def _check_if_quorum(self, dist_matrix, server, target, quorum_threshold):
        # get the distance from server to target
        distance = dist_matrix[target][server]
        # get sorted list 
        quorum_distances = sorted(dist_matrix[target])[:quorum_threshold]
        return (distance in quorum_distances)
  
  ### GDI (GeoSpatial Diversity Index) CALCULATION
  ### UTILITIES 
    def calculateGDI_updated(self, data): 
        dist_matrix = self._getDistanceMatrix(data)
        
        servers = list(dist_matrix.columns)
        
        two_third_threshold = math.ceil(len(servers) * (2/3))
        
        GDI_df = pd.DataFrame(columns=['name', 'quorum_counter'])
        for addr in servers:
            quorum_counter = 0
            for target in servers:
                if self._check_if_quorum(dist_matrix, addr, target, two_third_threshold):
                    quorum_counter = quorum_counter + 1 
            new_data = pd.DataFrame({'name':addr, 'quorum_counter':quorum_counter},  index=[0])
            GDI_df = pd.concat([GDI_df, new_data], ignore_index = True)
        GDI_df = GDI_df.merge(data,  on='name',  how='right')
        return GDI_df
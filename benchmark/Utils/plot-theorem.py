import pandas as pd
from scipy.stats import pearsonr, spearmanr
##### This is the processing for the plot in Theorem section of the paper. 
### we take the data and create a single output for each run.
all_data = pd.read_csv("/home/ubuntu/results/one-minority-mean-geo-dec-metrics.csv")
run_ids = list(set(all_data['run_id'].values.tolist()))

results_df = pd.DataFrame(columns=['name', 'run_id', 'liveliness_avg', 'id', 'latitude', 'longitude', 'minority_count', 'is_minority'])
    

for run_id in run_ids:
    data = all_data[all_data['run_id'] == run_id]
    locations = data['id'].values.tolist()
    locations_dict = {i:locations.count(i) for i in locations}

    # count number of minority validators
    minority_count = 0
    ### if there is only one location, we have no minority, so zero
    if(len(locations_dict)>1):
        # get minimum of all the values
        minority_count = 16
        for key in locations_dict:
             minority_count = min(locations_dict[key], minority_count)

    for loc_id in locations_dict.keys():
        loc_data = data[data['id']==loc_id].sort_values('node_num')
        is_minority = 0
        if(minority_count == len(loc_data)):
            is_minority = 1
        liveliness_avg = loc_data['liveliness_avg'].mean()
        new_data = pd.DataFrame({'id' : loc_data['id'].iloc[0], 'is_minority' : is_minority, 'name':loc_data['name'].iloc[0], 'run_id': loc_data['run_id'].iloc[0], 'latitude': loc_data['latitude'].iloc[0], 'longitude' : loc_data['longitude'].iloc[0], 'minority_count' : minority_count, 'liveliness_avg': liveliness_avg},  index=[0])  
        results_df = pd.concat([results_df, new_data], ignore_index = True)
        
results_df.to_csv('/home/ubuntu/results/theorem-geo-dec-metrics.csv', index=False)
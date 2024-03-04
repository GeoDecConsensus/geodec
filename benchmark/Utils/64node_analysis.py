import numpy
import pandas as pd

MARKED_SERVERS_FILE = '/home/ubuntu/data/servers-2020-07-19-us-europe-filter-2.csv'

def count_minority(GDI_67, data):
    return sum(data['two_third_dist']>GDI_67)

def is_minority(GDI_67, GDI):
    return GDI > GDI_67

# is jailed
def is_jailed(liveliness, threshold):
    return liveliness < threshold

# saved from jailing
def is_minory_and_jailed(liveliness, GDI, threshold, GDI_67):
    return is_minority(GDI_67, GDI) and is_jailed(liveliness, threshold)


def non_us_europe_count(data):
    servers = pd.read_csv(MARKED_SERVERS_FILE)
    servers_data = pd.merge(data, servers, on ='id', how ="inner")
    count = servers_data['is_US_Europe'].sum()
    # print(servers_data[servers_data['is_US_Europe'] == 0])
    return (64-count)

all_data = pd.read_csv("/home/ubuntu/results/64node-random-mean-geo-dec-metrics.csv")
fixed_data = pd.read_csv("/home/ubuntu/results/64node-fixed-mean-geo-dec-metrics.csv")
# check_data = pd.read_csv("/home/ubuntu/results/64node-check-mean-geo-dec-metrics.csv")
all_data = all_data.append(fixed_data)
# all_data = all_data.append(check_data)
run_ids = list(set(all_data['run_id'].values.tolist()))

results_df = pd.DataFrame(columns=['run_id', 'minority_count', 'minority_jailed_5', 'total_jailed_5', 'non_us_europe_count', 'GDI_before', 'GDI_after', 'GDI_solution', 'GDI_percent_decrease', 'GDI_percent_decrease_sol' ]) #, 'total_jailed_10', 'minority_jailed_20', 'total_jailed_20', 'minority_jailed_30', 'total_jailed_30', 'is_not_minority_jailed'])
for run_id in run_ids:
    data = all_data[all_data['run_id'] == run_id]
    GDI_67 = numpy.percentile(list(set(data['two_third_dist'].values.tolist())), 67)
    print(len(list(set(data['two_third_dist'].values.tolist()))))
    data['is_minority'] = data.apply(lambda x: is_minority(GDI_67, x['two_third_dist']), axis=1) 
    data['is_jailed'] = data.apply(lambda x: is_jailed(x['liveliness_avg'], 5), axis=1) 
    data['is_minory_and_jailed'] = data.apply(lambda x: is_minory_and_jailed(x['liveliness_avg'], x['two_third_dist'], 5, GDI_67), axis=1) 
    

    minority_count = count_minority(GDI_67, data)
    num = non_us_europe_count(data)
    
    GDI_before = data['two_third_dist'].mean()
    GDI_after = data[data['is_jailed'] == False]['two_third_dist'].mean()
    GDI_ours = data[(data['is_jailed'] == False) | (data['is_minory_and_jailed'] == True)]['two_third_dist'].mean()
    
    GDI_percent_decrease = ((GDI_before - GDI_after)/GDI_before)*100
   
    cities = list(set(data['name'].values.tolist()))
    print(data[data['is_minority']==True])
    GDI_percent_decrease_solution = ((GDI_before - GDI_ours)/GDI_before)*100
    new_data = pd.DataFrame({'run_id' : run_id, 'non_us_europe_count':non_us_europe_count(data), 'minority_count' : data['is_minority'].values.sum(), 'minority_jailed_5': data['is_minory_and_jailed'].values.sum(),
                                'total_jailed_5': data['is_jailed'].values.sum(),'GDI_before': GDI_before, 'GDI_after': GDI_after, 'GDI_solution': GDI_ours,
                                'GDI_percent_decrease': GDI_percent_decrease, 'GDI_percent_decrease_sol' : GDI_percent_decrease_solution} , index=[0]) #   'minority_jailed_10': data['is_minory_and_jailed_10'].values.sum(),
                                # 'total_jailed_10': data['is_jailed_10'].values.sum(), 'minority_jailed_20': data['is_minory_and_jailed_20'].values.sum(),
                                # 'total_jailed_20': data['is_jailed_20'].values.sum(), 'minority_jailed_30': data['is_minory_and_jailed_30'].values.sum(),
                                # 'total_jailed_30': data['is_jailed_30'].values.sum(), 'is_not_minority_jailed': is_not_minority_jailed}, index=[0])  

    results_df = pd.concat([results_df, new_data], ignore_index = True)


# results_df.to_csv('/home/ubuntu/results/minority_jailed_16node.csv', index=False)
# minority_count_array = list(set(results_df['minority_count'].values.tolist()))
summary = results_df.groupby('minority_jailed_5').mean()
# summary.to_csv('/home/ubuntu/results/summary_minority_jailed_16node.csv', index=True)
print(summary)

print(results_df)
summary.to_csv('/home/ubuntu/results/64node-results.csv')
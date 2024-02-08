import numpy
import pandas as pd

######### 
# we evaluate the solution presented to see what is its impact on how many minorities we saved in our approach. 

# STEP 1: identify minority
def is_minority(GDI_67, GDI):
    return GDI > GDI_67

# STEP 2: is jailed
def is_jailed(liveliness, threshold):
    return liveliness < threshold

# STEP 3: saved from jailing
def is_minory_and_jailed(liveliness, GDI, threshold, GDI_67):
    return is_minority(GDI_67, GDI) and is_jailed(liveliness, threshold)

# STEP 3: saved from jailing
def is_not_minory_and_jailed(liveliness, GDI, threshold, GDI_67):
    return (~is_minority(GDI_67, GDI)) and is_jailed(liveliness, threshold)

all_data = pd.read_csv("/home/ubuntu/results/one-minority-mean-geo-dec-metrics.csv")
run_ids = list(set(all_data['run_id'].values.tolist()))

results_df = pd.DataFrame(columns=['run_id', 'minority_count', 'minority_jailed_5', 'total_jailed_5', 'minority_jailed_10', 'total_jailed_10', 'minority_jailed_20', 'total_jailed_20', 'minority_jailed_30', 'total_jailed_30', 'is_not_minority_jailed'])
for run_id in run_ids:
    data = all_data[all_data['run_id'] == run_id]
    
    GDI_67 = numpy.percentile(all_data['one_third_dist'], 67)
    data['is_minority'] = data.apply(lambda x: is_minority(GDI_67, x['two_third_dist']), axis=1) #is_minority(GDI_67, data['one_third_dist'])
    data['is_jailed'] = data.apply(lambda x: is_jailed(x['liveliness_avg'], 5), axis=1) 
    data['is_minory_and_jailed'] = data.apply(lambda x: is_minory_and_jailed(x['liveliness_avg'], x['two_third_dist'], 5, GDI_67), axis=1) 

    data['is_jailed_10'] = data.apply(lambda x: is_jailed(x['liveliness_avg'], 10), axis=1) 
    data['is_minory_and_jailed_10'] = data.apply(lambda x: is_minory_and_jailed(x['liveliness_avg'], x['two_third_dist'], 10, GDI_67), axis=1) 
    
    data['is_jailed_20'] = data.apply(lambda x: is_jailed(x['liveliness_avg'], 20), axis=1) 
    data['is_minory_and_jailed_20'] = data.apply(lambda x: is_minory_and_jailed(x['liveliness_avg'], x['two_third_dist'], 20, GDI_67), axis=1) 
    
    data['is_jailed_30'] = data.apply(lambda x: is_jailed(x['liveliness_avg'], 30), axis=1) 
    data['is_minory_and_jailed_30'] = data.apply(lambda x: is_minory_and_jailed(x['liveliness_avg'], x['two_third_dist'], 30, GDI_67), axis=1) 
  
    data['is_not_minority_jailed'] = data.apply(lambda x: is_not_minory_and_jailed(x['liveliness_avg'], x['two_third_dist'], 25, GDI_67), axis=1) 
    
    minority_count = data['is_minority'].values.sum()
    is_not_minority_jailed = data['is_not_minority_jailed'].values.sum()
    if(minority_count==len(data)):
        print('bitch there is no minority')
    else:
        new_data = pd.DataFrame({'run_id' : run_id, 'minority_count' : data['is_minority'].values.sum(), 'minority_jailed_5': data['is_minory_and_jailed'].values.sum(),
                                'total_jailed_5': data['is_jailed'].values.sum(), 'minority_jailed_10': data['is_minory_and_jailed_10'].values.sum(),
                                'total_jailed_10': data['is_jailed_10'].values.sum(), 'minority_jailed_20': data['is_minory_and_jailed_20'].values.sum(),
                                'total_jailed_20': data['is_jailed_20'].values.sum(), 'minority_jailed_30': data['is_minory_and_jailed_30'].values.sum(),
                                'total_jailed_30': data['is_jailed_30'].values.sum(), 'is_not_minority_jailed': is_not_minority_jailed}, index=[0])  

        results_df = pd.concat([results_df, new_data], ignore_index = True)

# results_df.to_csv('/home/ubuntu/results/minority_jailed_16node.csv', index=False)
print(results_df['is_not_minority_jailed'].values.sum())
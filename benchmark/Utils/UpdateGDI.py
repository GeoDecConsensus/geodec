import pandas as pd
from geodec import GeoDec
from scipy.stats import pearsonr, spearmanr
######### UTILS ###############
##### THis file is used for adding updated GDI metric. 

data = pd.read_csv("/home/ubuntu/results/mean-geo-dec-metrics.csv")
# print(data)


# get data by run_Id
for run_id in set(data['run_id'].values.tolist()):
    print(run_id)
    run_data = data[data['run_id']==run_id]
    # print(run_data)
    geodec = GeoDec()
    output = geodec.calculateGDI_updated(run_data)
    print(output)
    output.to_csv('/home/ubuntu/results/updatedGDI-mean-geo-dec-metrics.csv', mode='a', index=False, header=False)
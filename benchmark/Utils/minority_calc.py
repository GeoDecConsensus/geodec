import pandas as pd
import seaborn as sns
data = pd.read_csv("/home/ubuntu/results/theorem-geo-dec-metrics.csv")
# data = data[data['run_id']==1647]

# data['liveliness_avg'].hist()
print(data)

print(len(set(data['run_id'].values.tolist())))


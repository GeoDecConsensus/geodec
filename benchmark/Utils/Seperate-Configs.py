## we ran with two minorities, this data has to be seperated out in to a new file for analysis and plots
import pandas as pd
from scipy.stats import pearsonr, spearmanr


data = pd.read_csv("/home/ubuntu/results/minority-mean-geo-dec-metrics.csv")

# runs = [2397, 2392, 2387, 2382]

# data = data[~data['run_id'].isin(runs)]

# data.to_csv('/home/ubuntu/results/two-minorities-mean-geo-dec-metrics.csv', index = True)

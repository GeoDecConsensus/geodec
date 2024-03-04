import seaborn as sns
import pandas as pd
from scipy.stats import pearsonr, spearmanr

data = pd.read_csv("/home/ubuntu/results/minority-mean-geo-dec-metrics.csv")
cols = ['liveliness_avg', 'two_third_dist', 'total_dist']
df = data[cols]
print(df)

df.rename(columns={'liveliness_avg' : 'liveliness'}, inplace=True)

df.rename(columns={'two_third_dist' : '$GDI^\mathbb{Q}$'}, inplace=True)

df.rename(columns={'total_dist' : '$GDI^{V}$'}, inplace=True)

# calculate the correlation matrix
corr = df.corr()
# plot the heatmap
with sns.plotting_context("talk"):
        plot = sns.heatmap(corr, cmap="Blues",
                xticklabels=corr.columns,
                yticklabels=corr.columns, annot=True)
        fig = plot.get_figure()
        fig.savefig("benchmark/Utils/correlation-plot.png") 

print(corr)
print(pearsonr(data['liveliness_avg'], data['two_third_dist']))
print(pearsonr(data['liveliness_avg'], data['total_dist']))

# x = ('r\N{SUPERSCRIPT V}')
# print(x)

print(spearmanr(data['liveliness_avg'], data['two_third_dist']))
print(spearmanr(data['liveliness_avg'], data['total_dist']))

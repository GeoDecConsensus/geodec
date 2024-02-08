import matplotlib.pyplot as plt
import pandas as pd

data_5 = pd.read_csv('/home/ubuntu/results/summary_minority_jailed_16node.csv')

# line 1 points
x = data_5['minority_count']
y1 = data_5['total_jailed_5']
# plotting the line 1 points 
plt.plot(x, y1, label = "π = 5")

y2 = data_5['total_jailed_10']
plt.plot(x, y2, label = "π = 10")

y3 = data_5['total_jailed_20']
plt.plot(x, y3, label = "π = 20")

y4 = data_5['total_jailed_30']
plt.plot(x, y4, label = "π = 30")

# # line 2 points
# data_10 = pd.read_csv('/home/ubuntu/results/64node-results_10.csv')
# data_10 = data_10[data_10['minority_jailed_5'] < 10]
# # line 1 points
# x2 = data_10['minority_jailed_5']
# y2 = data_10['GDI_percent_decrease']
# # plotting the line 2 points 
# plt.plot(x2, y2, label = "π = 10")
  
# naming the x axis
plt.xlabel('No. of minority validators', fontsize = 18.0)
# naming the y axis
plt.ylabel('No. of jailed validators (average)', fontsize = 18.0)

  
# show a legend on the plot
plt.legend(fontsize=18)
plt.ylim(ymin=0)  # this line
plt.xlim(xmin=0)  # this line
 
# function to show the plot
plt.show()
plt.savefig("benchmark/Utils/32node-plot.png") 
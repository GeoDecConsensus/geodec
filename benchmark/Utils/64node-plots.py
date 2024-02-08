import matplotlib.pyplot as plt
import pandas as pd

data_5 = pd.read_csv('/home/ubuntu/results/64node-results.csv')

# line 1 points
x1 = data_5['minority_jailed_5']
y1 = data_5['GDI_percent_decrease']
# plotting the line 1 points 
plt.plot(x1, y1, label = "π = 5")
  
# line 2 points
data_10 = pd.read_csv('/home/ubuntu/results/64node-results_10.csv')
data_10 = data_10[data_10['minority_jailed_5'] < 10]
# line 1 points
x2 = data_10['minority_jailed_5']
y2 = data_10['GDI_percent_decrease']
# plotting the line 2 points 
plt.plot(x2, y2, label = "π = 10")
  
# naming the x axis
plt.xlabel('Number of minority jailed', fontsize = 18.0)
# naming the y axis
plt.ylabel('% decrease in GDI', fontsize = 18.0)
  
# show a legend on the plot
plt.legend(fontsize=18)
plt.ylim(ymin=0)  # this line
plt.xlim(xmin=0)  # this line
 
# function to show the plot
plt.show()
plt.savefig("benchmark/Utils/64node-plot.png") 
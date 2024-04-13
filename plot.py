import matplotlib.pyplot as plt

# Test names
tests = ['Test 1', 'Test 2', 'Test 3', 'Test 4']

# Number of broadcasts and gossips for each test
broadcasts = [5, 7, 3, 6]
gossips = [4, 6, 2, 5]

# Method names
methods = ['Broadcast', 'Gossip']

# Bar width
bar_width = 0.35

# Set position for bars
index = range(len(tests))

# Plotting bars for broadcasts and gossips
plt.bar(index, broadcasts, bar_width, label='Broadcast')
plt.bar([i + bar_width for i in index], gossips, bar_width, label='Gossip')

# Adding labels and title
plt.xlabel('Tests')
plt.ylabel('Numbers')
plt.title('Comparison of Broadcast and Gossip Methods for Different Tests')
plt.xticks([i + bar_width / 2 for i in index], tests)
plt.legend()

# Showing the plot
plt.show()

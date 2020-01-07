import matplotlib.pyplot as plt, mpld3

fig = plt.figure()
fig = plt.plot([3,1,4,1,5], 'ks-', mec='w', mew=5, ms=20)
mpld3.fig_to_dict(fig)


print(hello)
#mpld3.show()
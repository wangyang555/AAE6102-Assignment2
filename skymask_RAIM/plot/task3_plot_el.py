import matplotlib.pyplot as plt
from collections import defaultdict


# task3 plot the elevations of satellites

filename = r"..\result\Opensky\opensky_az_el.txt"
data = defaultdict(lambda: {'el': [], 'epochs': []})

with open(filename, 'r') as f:
    for epoch, line in enumerate(f):
        values = list(map(float, line.strip().split()))
        for i in range(0, len(values), 3):
            prn = int(values[i])
            el = values[i+2]
            data[prn]['el'].append(el)
            data[prn]['epochs'].append(epoch)

plt.figure(figsize=(8, 4.5))
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 12

for prn, sat_data in data.items():
    plt.plot(
        sat_data['epochs'],
        sat_data['el'],
        linestyle='-',
        linewidth=1,
        marker='o',
        markersize=3,
        alpha=0.8,
        label=f'G%02d' % (prn)
    )
plt.xlabel('Epoch', fontsize=12)
plt.ylabel('Elevation (degree)', fontsize=12)
plt.title('Satellite Elevation Time Series', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.3)
plt.ylim(0, 90)
plt.yticks(range(0, 91, 10))
plt.legend(
    ncol=3,
    loc='upper center',
    frameon=True,
    fontsize=12
)
plt.tight_layout()
plt.show()

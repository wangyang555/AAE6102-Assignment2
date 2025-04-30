import numpy as np
import matplotlib.pyplot as plt


# task3 plot the stanford chart
# positioning error and protection levels

def read_filename(filename):
    position_errors = []
    protection_levels = []
    with open(filename) as fopen:
        lines = fopen.readlines()
        for line in lines:
            line_data = line.split()
            position_errors.append(float(line_data[4]))
            protection_levels.append(float(line_data[5]))
    return position_errors, protection_levels

def generate_stanford_chart(position_errors, protection_levels, alarm_limit=50.0):
    """
    Generate Stanford Chart for integrity analysis
    """
    plt.figure(figsize=(9, 6))
    plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['font.size'] = 12
    plt.scatter(position_errors,protection_levels, alpha=0.5)

    max_val = max(np.max(position_errors), np.max(protection_levels), alarm_limit)*1.1
    plt.plot([0, max_val], [0, max_val], 'r--')  # PE = PL line
    plt.axhline(y=alarm_limit, color='g', linestyle='--')  # AL horizontal line
    plt.axvline(x=alarm_limit, color='g', linestyle='--')  # AL vertical line

    plt.fill_between([0, alarm_limit], [0, 0], [alarm_limit, alarm_limit],
                     color='green', alpha=0.2, label='Normal Operation')
    plt.fill_between([alarm_limit, max_val], [0, 0], [alarm_limit, alarm_limit],
                     color='yellow', alpha=0.2, label='Misleading Information')
    plt.fill_between([0, alarm_limit], [alarm_limit, alarm_limit], [max_val, max_val],
                     color='orange', alpha=0.2, label='System Unavailable')
    plt.fill_between([alarm_limit, max_val], [alarm_limit, alarm_limit], [max_val, max_val],
                     color='red', alpha=0.2, label='Hazardous Misleading Information')

    normal = np.sum((position_errors < alarm_limit) & (protection_levels < alarm_limit))
    mi = np.sum((position_errors < alarm_limit) & (protection_levels >= alarm_limit))
    unavailable = np.sum((position_errors >= alarm_limit) & (protection_levels >= alarm_limit))
    hmi = np.sum((position_errors >= alarm_limit) & (protection_levels < alarm_limit))

    total_points = len(position_errors)
    legend_labels = [
        f'Normal Operation: {normal} ({normal / total_points * 100:.2f}%)',
        f'Misleading Information: {mi} ({mi / total_points * 100:.2f}%)',
        f'System Unavailable: {unavailable} ({unavailable / total_points * 100:.2f}%)',
        f'Hazardous Misleading Information: {hmi} ({hmi / total_points * 100:.2f}%)'
    ]

    plt.legend(legend_labels)

    plt.grid(True)
    plt.ylabel('Protection Level (m)')
    plt.xlabel('Position Error (m)')
    plt.title('Stanford Chart for GNSS Integrity Monitoring')

    plt.show()

filename = r"..\result\Opensky\task3_raim.txt"
position_errors, protection_levels = read_filename(filename)
generate_stanford_chart(np.array(position_errors), np.array(protection_levels), alarm_limit=50.0)

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# task2 plot the skymask of observer

df = pd.read_csv(r'..\data\Urban\skymask_A1_urban.csv')
azimuth = df['Azimuth_angle_deg'].values
elevation = df['Elevation_angle_deg'].values

theta = np.radians(azimuth)
r = 90 - elevation

plt.figure(figsize=(6.5, 5))
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 12
ax = plt.subplot(111, polar=True)
ax.plot(theta, r, color='red', linewidth=1, label='Sky Mask Boundary')
ax.fill_between(theta, 0, r, color='gray', alpha=0.5, label='Obstructed Area')

# 设置极坐标参数
ax.set_theta_zero_location('N')  # 0度方位角指向北
ax.set_theta_direction(-1)       # 顺时针方向增加角度
ax.set_rmax(90)                  # 半径范围为0-90（对应仰角0-90度）
ax.set_rlabel_position(180)
ax.grid(linestyle='--', alpha=0.6)

plt.title('Urban Sky Mask', pad=20)
plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.15))
plt.show()

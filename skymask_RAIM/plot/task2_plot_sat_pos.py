import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# task2 plot the satellite pos in sky

df = pd.read_csv(r'..\data\Urban\skymask_A1_urban.csv')
azimuth = df['Azimuth_angle_deg'].values
elevation = df['Elevation_angle_deg'].values
theta = np.radians(azimuth)
r = 90 - elevation

satellites = [
    ["G01", 58.092, 74.016],
    ["G07", 207.456, 60.170],
    ["G11", 21.707, 60.106],
    ["G18", 41.689, 47.095]
]
prn = [sat[0] for sat in satellites]
az_sat = [sat[1] for sat in satellites]
el_sat = [sat[2] for sat in satellites]
theta_sat = np.radians(az_sat)
r_sat = 90 - np.array(el_sat)


plt.figure(figsize=(6.5, 5))
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 12
ax = plt.subplot(111, polar=True)
ax.plot(theta, r, color='red', linewidth=1, label='Sky Mask Boundary')
ax.fill_between(theta, 0, r, color='gray', alpha=0.5, label='Obstructed Area')

# 绘制卫星位置
scatter = ax.scatter(
    theta_sat, r_sat,
    c='lime',          # 卫星点颜色
    s=80,              # 点大小
    edgecolor='black', # 边框颜色
    linewidth=1,       # 边框粗细
    zorder=10,         # 确保卫星点在顶层
    label='Satellites'
)

# 添加卫星标签（自动避开重叠）
for i, (t, r, p) in enumerate(zip(theta_sat, r_sat, prn)):
    offset = 0.6
    ax.annotate(
        p,
        (t, r),
        textcoords="offset points",
        xytext=(10*offset, 10*offset),  # 偏移量
        ha='center',
        fontsize=10,
        color='blue'
    )

# 设置极坐标参数
ax.set_theta_zero_location('N')  # 0度方位角指向北
ax.set_theta_direction(-1)       # 顺时针方向增加角度
ax.set_rmax(90)                  # 半径范围为0-90（对应仰角0-90度）
ax.set_rlabel_position(180)
ax.grid(linestyle='--', alpha=0.6)

plt.title('Urban Sky Mask', pad=20)
plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.15))
plt.show()

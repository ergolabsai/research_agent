import matplotlib.pyplot as plt
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Create figure and axis
fig, ax = plt.subplots(figsize=(10, 7))

# Generate data points based on the description
# High cluster at tau ≈ -0.05 to 0, B/B0 ≈ 0.75-0.90
cluster_high = np.column_stack([
    np.random.uniform(-0.05, 0.02, 15),
    np.random.uniform(0.75, 0.90, 15)
])

# Vertical band near tau = 0, B/B0 from ~0.05 to 0.28
band_vertical = np.column_stack([
    np.random.normal(0, 0.02, 20),
    np.random.uniform(0.05, 0.28, 20)
])

# Low B/B0 values (below 0.2) scattered across tau range from -0.15 to 1.1
low_scattered = np.column_stack([
    np.random.uniform(-0.15, 1.1, 60),
    np.random.uniform(0.01, 0.20, 60)
])

# A few isolated points at negative tau in lower left
isolated_points = np.column_stack([
    np.random.uniform(-0.15, -0.05, 5),
    np.random.uniform(0.01, 0.10, 5)
])

# Combine all data points
all_data = np.vstack([cluster_high, band_vertical, low_scattered, isolated_points])
tau = all_data[:, 0]
B_B0 = all_data[:, 1]

# Plot all data points as black filled circles
ax.scatter(tau, B_B0, c='black', s=40, zorder=2)

# Add red circles highlighting specific points
# Three overlapping circles in upper left cluster
highlight_indices_upper = np.where((tau >= -0.05) & (tau <= 0.0) & (B_B0 >= 0.75) & (B_B0 <= 0.90))[0][:3]
for idx in highlight_indices_upper:
    circle = plt.Circle((tau[idx], B_B0[idx]), 0.035, color='red', fill=False, linewidth=2, zorder=3)
    ax.add_patch(circle)

# Add two red circles at specified locations (approximate points)
# Find points near tau=0.35, B/B0=0.18
distances_1 = np.sqrt((tau - 0.35)**2 + (B_B0 - 0.18)**2)
if np.min(distances_1) < 0.15:
    idx_1 = np.argmin(distances_1)
    circle1 = plt.Circle((tau[idx_1], B_B0[idx_1]), 0.035, color='red', fill=False, linewidth=2, zorder=3)
    ax.add_patch(circle1)

# Find points near tau=0.6, B/B0=0.17
distances_2 = np.sqrt((tau - 0.6)**2 + (B_B0 - 0.17)**2)
if np.min(distances_2) < 0.15:
    idx_2 = np.argmin(distances_2)
    circle2 = plt.Circle((tau[idx_2], B_B0[idx_2]), 0.035, color='red', fill=False, linewidth=2, zorder=3)
    ax.add_patch(circle2)

# Add vertical dashed lines at tau = 0 and tau = 1.0
ax.axvline(x=0, color='black', linestyle='--', linewidth=1.5, zorder=1)
ax.axvline(x=1.0, color='black', linestyle='--', linewidth=1.5, zorder=1)

# Add text label box in upper right
textstr = r'$r_{inner}$ = 7.5 cm'
props = dict(boxstyle='square', facecolor='white', edgecolor='black', linewidth=1)
ax.text(0.95, 0.95, textstr, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', horizontalalignment='right', bbox=props)

# Set axis limits
ax.set_xlim(-0.2, 1.2)
ax.set_ylim(0, 1.0)

# Set labels
ax.set_xlabel(r'$\tau$', fontsize=14)
ax.set_ylabel(r'B/B$_0$', fontsize=14)

# Configure the plot appearance
ax.spines['top'].set_visible(True)
ax.spines['right'].set_visible(True)
ax.spines['bottom'].set_visible(True)
ax.spines['left'].set_visible(True)

# Set background
ax.set_facecolor('white')
fig.patch.set_facecolor('white')

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Save the figure
plt.savefig('reconstructed_figure.jpg', dpi=300, bbox_inches='tight', facecolor='white')
print("Figure saved as reconstructed_figure.jpg")

plt.close()

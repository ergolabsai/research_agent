import matplotlib.pyplot as plt
import numpy as np

# Create figure and axis
fig, ax = plt.subplots(figsize=(8, 6))

# Data points based on the description
# 1. Vertical cluster near τ = -0.2, B₁/B₀ from 0.1 to 0.4
tau_cluster1 = np.full(8, -0.2) + np.random.uniform(-0.02, 0.02, 8)
b_cluster1 = np.linspace(0.1, 0.4, 8) + np.random.uniform(-0.02, 0.02, 8)

# 2. Two points near τ = 0, B₁/B₀ close to 1.0
tau_top = np.array([0.0, 0.02])
b_top = np.array([0.98, 0.95])

# 3. Scattered points between τ = 0 and τ = 1.0, B₁/B₀ between 0 and 0.2
tau_middle = np.random.uniform(0.05, 0.95, 25)
b_middle = np.random.uniform(0.0, 0.2, 25)

# 4. Prominent point near τ = 1.1, B₁/B₀ ≈ 0.83
tau_prominent = np.array([1.1])
b_prominent = np.array([0.83])

# 5. Cluster near τ = 1.0 and beyond
tau_cluster2 = np.array([0.98, 1.0, 1.02, 1.05, 1.08, 1.15, 1.2, 1.25, 1.3, 1.35])
b_cluster2 = np.array([0.35, 0.45, 0.25, 0.60, 0.75, 0.50, 0.30, 0.65, 0.40, 0.20])

# Combine all data points
tau_all = np.concatenate([tau_cluster1, tau_top, tau_middle, tau_prominent, tau_cluster2])
b_all = np.concatenate([b_cluster1, b_top, b_middle, b_prominent, b_cluster2])

# Create scatter plot
ax.scatter(tau_all, b_all, color='black', s=20, zorder=3)

# Add vertical dashed lines at τ = 0 and τ = 1.0
ax.axvline(x=0, color='black', linestyle='--', linewidth=1, zorder=2)
ax.axvline(x=1.0, color='black', linestyle='--', linewidth=1, zorder=2)

# Set axis limits
ax.set_xlim(-0.5, 1.5)
ax.set_ylim(0, 1.0)

# Set labels
ax.set_xlabel('τ', fontsize=14)
ax.set_ylabel('B₁/B₀', fontsize=14)

# Add text label "5800 Torr" in top right corner
ax.text(0.95, 0.95, '5800 Torr', transform=ax.transAxes, 
        fontsize=12, verticalalignment='top', horizontalalignment='right')

# Set frame style
ax.spines['top'].set_color('black')
ax.spines['bottom'].set_color('black')
ax.spines['left'].set_color('black')
ax.spines['right'].set_color('black')

# Ensure tick marks are visible
ax.tick_params(direction='in', length=6, width=1, colors='black')

# Add grid (optional, can be removed if not desired)
ax.grid(False)

# Tight layout
plt.tight_layout()

# Save figure
plt.savefig('reconstructed_figure.jpg', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print("Figure saved as reconstructed_figure.jpg")

plt.close()

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
from scipy.ndimage import gaussian_filter

# Set random seed for reproducibility
np.random.seed(42)

# Create grid
tau = np.linspace(-0.5, 1.5, 400)
r = np.linspace(-20, 20, 300)
TAU, R = np.meshgrid(tau, r)

# Create base intensity field
intensity = np.zeros_like(TAU)

# Left region (tau < 0.5): Complex turbulent-like structures
left_mask = TAU < 0.5
# Create turbulent structures using multiple noise layers
for i in range(5):
    noise = np.random.randn(*TAU.shape) * 10000
    noise = gaussian_filter(noise, sigma=[3 + i*2, 3 + i*2])
    intensity += noise * left_mask

# Add some organized structures in left region
for i in range(-3, 4):
    intensity += left_mask * 15000 * np.exp(-((R - i*7)**2 / 50 + (TAU + 0.2)**2 / 0.05))

# Right region (tau > 0.5): Higher values, more uniform yellow-orange
right_mask = TAU > 0.5
base_right = 80000 + 20000 * np.exp(-(R**2) / 300)
# Add some variation
noise_right = np.random.randn(*TAU.shape) * 5000
noise_right = gaussian_filter(noise_right, sigma=[5, 5])
intensity += right_mask * (base_right + noise_right)

# Create transition zone around tau = 0.5-1.0 with blue intermediate values
transition_width = 0.3
transition_center = 0.7
transition_profile = np.exp(-((TAU - transition_center)**2) / (2 * transition_width**2))

# Add diagonal feature (upper right to lower right)
diagonal_effect = np.exp(-((TAU - 0.7 - R/40)**2) / 0.05)
intensity += diagonal_effect * 30000 * (1 - right_mask * 0.5)

# Create sharp transition with blue contours
transition_zone = (TAU > 0.4) & (TAU < 1.0)
intensity[transition_zone] = intensity[transition_zone] * 0.6 + 25000 * transition_profile[transition_zone]

# Ensure values are in reasonable range (0 to ~1.2e5)
intensity = np.clip(intensity, 0, 120000)

# Smooth the data slightly
intensity = gaussian_filter(intensity, sigma=[1.5, 1.5])

# Create the figure
fig, ax = plt.subplots(figsize=(10, 7))

# Create custom colormap: black/brown -> red -> orange -> yellow with blue for intermediate
from matplotlib.colors import LinearSegmentedColormap
colors_list = [
    (0.0, '#000000'),   # black
    (0.05, '#1a0a00'),  # dark brown
    (0.15, '#4a0000'),  # dark red
    (0.25, '#1a1a4a'),  # blue (intermediate values)
    (0.35, '#2a2a8a'),  # blue
    (0.45, '#8a0000'),  # red
    (0.6, '#ff4500'),   # orange-red
    (0.75, '#ff8c00'),  # dark orange
    (0.85, '#ffa500'),  # orange
    (0.95, '#ffff00'),  # yellow
    (1.0, '#ffff99')    # light yellow
]
n_bins = 256
cmap = LinearSegmentedColormap.from_list('custom', colors_list, N=n_bins)

# Create contour plot
levels = np.linspace(0, 120000, 50)
contour = ax.contourf(TAU, R, intensity, levels=levels, cmap=cmap, extend='neither')

# Add contour lines for better definition
contour_lines = ax.contour(TAU, R, intensity, levels=15, colors='black', alpha=0.2, linewidths=0.5)

# Add colorbar
cbar = plt.colorbar(contour, ax=ax, label='')
# Format colorbar ticks in scientific notation
cbar.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e4:.1f}'))
cbar.set_label('×10⁴', rotation=0, labelpad=20, y=1.05)

# Set axis labels
ax.set_xlabel('τ', fontsize=14)
ax.set_ylabel('r (mm)', fontsize=14)

# Set axis limits
ax.set_xlim(-0.5, 1.5)
ax.set_ylim(-20, 20)

# Add pressure label in bottom right corner
ax.text(1.35, -16, '3500 Torr', fontsize=12, 
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Add grid
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

# Tight layout
plt.tight_layout()

# Save the figure
plt.savefig('reconstructed_figure.jpg', dpi=300, bbox_inches='tight', format='jpg')
print("Figure saved as reconstructed_figure.jpg")

# Also display some statistics
print(f"Intensity range: {intensity.min():.2e} to {intensity.max():.2e}")
print(f"Figure dimensions: {fig.get_size_inches()}")


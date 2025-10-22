import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter

# Create the figure and axis
fig, ax = plt.subplots(figsize=(10, 8))

# Define grid
tau = np.linspace(-0.5, 1.5, 500)
r = np.linspace(-20, 20, 400)
TAU, R = np.meshgrid(tau, r)

# Create the data with the described features
Z = np.zeros_like(TAU)

# Create a localized high-intensity region with the characteristic shape
# The peak occurs around tau = 0.5-0.8, centered vertically
tau_center = 0.65
r_center = -5

# Create the main feature with an elongated, sinuous shape
for i, t in enumerate(tau):
    if t < 0.3:
        # Very low values on the left
        intensity = 0.0
    elif 0.3 <= t < 0.5:
        # Gradual increase
        intensity = (t - 0.3) / 0.2 * 0.3
    elif 0.5 <= t <= 0.8:
        # Peak region with characteristic shape
        intensity = 1.0
    else:
        # Gradual decrease on the right
        intensity = max(0, 0.8 - (t - 0.8) * 0.8)
    
    for j, r_val in enumerate(r):
        # Create elongated vertical feature with sinuous shape
        if 0.5 <= t <= 0.8:
            # Create the narrow, elongated shape
            tau_offset = (t - 0.5) * 15  # Shifts the center as tau increases
            r_mod = r_center + tau_offset * np.sin((t - 0.5) * 8)
            
            # Elongated Gaussian in r direction, narrow in tau direction
            width_r = 12 + 5 * np.sin((t - 0.5) * 10)
            width_tau = 0.15
            
            dist_r = (r_val - r_mod) / width_r
            dist_tau = (t - tau_center) / width_tau
            
            Z[j, i] = intensity * np.exp(-(dist_r**2 + dist_tau**2))
        else:
            # Outside peak region, create smoother background
            dist_r = (r_val - r_center) / 15
            dist_tau = (t - tau_center) / 0.3
            Z[j, i] = intensity * np.exp(-(dist_r**2 + dist_tau**2))

# Apply smoothing for better contours
Z = gaussian_filter(Z, sigma=2)

# Scale to match the colorbar range (0 to 1.0E+05)
Z = Z * 1.0e5

# Create custom colormap (black -> dark red -> red -> orange -> yellow)
colors = ['#000000', '#1a0000', '#330000', '#4d0000', '#660000', '#800000', 
          '#990000', '#b30000', '#cc0000', '#e60000', '#ff0000', 
          '#ff3300', '#ff6600', '#ff9900', '#ffcc00', '#ffff00']
n_bins = 256
cmap = LinearSegmentedColormap.from_list('thermal', colors, N=n_bins)

# Create the filled contour plot
levels = np.linspace(0, 1.0e5, 50)
contourf = ax.contourf(TAU, R, Z, levels=levels, cmap=cmap, extend='neither')

# Add the distinctive blue contour line at a specific level
blue_level = 0.5e5  # Middle of the range
contour_line = ax.contour(TAU, R, Z, levels=[blue_level], colors='#0066cc', linewidths=2.5)

# Create colorbar with scientific notation
cbar = plt.colorbar(contourf, ax=ax, format='%.1E')
cbar.ax.tick_params(labelsize=10)

# Set axis labels
ax.set_xlabel('τ', fontsize=14, fontweight='bold')
ax.set_ylabel('r (mm)', fontsize=14, fontweight='bold')

# Set axis limits
ax.set_xlim(-0.5, 1.5)
ax.set_ylim(-20, 20)

# Add grid for better readability
ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5)

# Add the pressure label in bottom right corner
ax.text(1.35, -17, '3500 Torr', fontsize=12, fontweight='bold', 
        color='white', bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))

# Adjust tick parameters
ax.tick_params(labelsize=11)

# Tight layout
plt.tight_layout()

# Save the figure
plt.savefig('reconstructed_figure_2nd_try.jpg', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print("Figure saved successfully as 'reconstructed_figure_2nd_try.jpg'")

plt.close()

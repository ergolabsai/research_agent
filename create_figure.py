import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib import cm
from scipy.ndimage import gaussian_filter

# Set up the grid
radius = np.linspace(-15, 15, 200)  # mm
tau = np.linspace(-0.5, 1.5, 300)  # normalized time

R, T = np.meshgrid(radius, tau)

# Create velocity field
velocity = np.zeros_like(R)

for i, t in enumerate(tau):
    for j, r in enumerate(radius):
        r_abs = abs(r)
        
        if t < 0:
            # Before quiescent period: high uniform velocity
            velocity[i, j] = 1.0e5
            
        elif 0 <= t <= 1:
            # During quiescent period: sheared flow structure
            # High velocity at edges, lower at core
            
            # Define the pinch radius (edge location)
            pinch_radius = 10.0  # mm
            
            # Create sheared profile
            if r_abs < 3:
                # Core region: lower velocity
                core_velocity = 5e4
                velocity[i, j] = core_velocity
            elif r_abs < pinch_radius:
                # Transition region: gradient from core to edge
                # Velocity increases with radius
                core_velocity = 5e4
                edge_velocity = 1.0e5
                
                # Smooth transition
                weight = (r_abs - 3) / (pinch_radius - 3)
                velocity[i, j] = core_velocity + weight * (edge_velocity - core_velocity)
            else:
                # Edge region: high velocity
                edge_velocity = 1.0e5
                velocity[i, j] = edge_velocity * np.exp(-0.3 * (r_abs - pinch_radius))
            
            # Add temporal evolution during quiescent period
            if t > 0.4:
                # Edge velocity slows down around tau ~ 0.5
                slowdown_factor = 1 - 0.5 * (t - 0.4) / 0.6
                if r_abs > 7:
                    velocity[i, j] *= slowdown_factor
                    
        else:  # t > 1
            # After quiescent period: low uniform velocity
            decay = np.exp(-3 * (t - 1))
            velocity[i, j] = 2e4 * decay

# Apply smoothing for realistic appearance
velocity = gaussian_filter(velocity, sigma=2)

# Create the figure
fig, ax = plt.subplots(figsize=(10, 8))

# Create contour plot
levels = np.linspace(0, 1.2e5, 25)
contourf = ax.contourf(R, T, velocity, levels=levels, cmap='jet')

# Add contour lines for clarity
contour_lines = ax.contour(R, T, velocity, levels=10, colors='black', 
                            linewidths=0.5, alpha=0.3)

# Colorbar
cbar = plt.colorbar(contourf, ax=ax, label='Axial Velocity (m/s)')
cbar.ax.tick_params(labelsize=11)

# Mark the quiescent period boundaries
ax.axhline(y=0, color='white', linestyle='--', linewidth=2, alpha=0.7, label='Quiescent period start')
ax.axhline(y=1, color='white', linestyle='--', linewidth=2, alpha=0.7, label='Quiescent period end')

# Mark the pinch radius
ax.axvline(x=10, color='white', linestyle=':', linewidth=1.5, alpha=0.5)
ax.axvline(x=-10, color='white', linestyle=':', linewidth=1.5, alpha=0.5)

# Labels and title
ax.set_xlabel('Radius (mm)', fontsize=14, fontweight='bold')
ax.set_ylabel('Normalized Time τ', fontsize=14, fontweight='bold')
ax.set_title('Axial Velocity Profile vs. Radius and Time\n5800 Torr, z = 0', 
             fontsize=15, fontweight='bold', pad=15)

# Grid
ax.grid(True, alpha=0.2, linestyle='--')

# Tick parameters
ax.tick_params(labelsize=11)

# Add text annotations for key features
ax.text(0, -0.3, 'High uniform velocity', ha='center', va='center', 
        fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
ax.text(0, 0.5, 'Sheared flow', ha='center', va='center', 
        fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
ax.text(11, 0.5, 'Edge:\nHigh v', ha='left', va='center', 
        fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
ax.text(0, 1.3, 'Low velocity', ha='center', va='center', 
        fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

plt.tight_layout()

# Save the figure
plt.savefig('reconstructed_figure.jpg', dpi=300, bbox_inches='tight', 
            format='jpg', pil_kwargs={'quality': 95})
print("Figure saved as 'reconstructed_figure.jpg'")


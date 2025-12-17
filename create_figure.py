import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from scipy.ndimage import gaussian_filter

# Create the data grid
radius = np.linspace(-15, 15, 200)  # mm
tau = np.linspace(-0.3, 1.5, 300)  # normalized time

R, T = np.meshgrid(radius, tau)

# Create axial velocity field based on the description
velocity = np.zeros_like(R)

for i, t in enumerate(tau):
    for j, r in enumerate(radius):
        r_abs = abs(r)
        
        if t < 0:
            # Before quiescent period: high uniform flow
            velocity[i, j] = 1.0e5
            
        elif 0 <= t <= 1:
            # During quiescent period: sheared flow structure
            # Edge velocity decreases over time, core stays constant
            
            # Define edge and core regions
            r_pinch = 10  # mm, approximate pinch radius
            
            if r_abs < 5:
                # Core region: constant ~5e4 m/s
                velocity[i, j] = 5.0e4 + 0.5e4 * np.random.randn() * 0.1
            elif r_abs < r_pinch:
                # Transition region
                # Interpolate between core and edge
                blend = (r_abs - 5) / (r_pinch - 5)
                
                # Edge velocity decreases from 1e5 to 5e4 over quiescent period
                edge_vel = 1.0e5 - (0.5e5) * t
                core_vel = 5.0e4
                
                velocity[i, j] = core_vel * (1 - blend) + edge_vel * blend
            else:
                # Edge region beyond pinch radius
                # Velocity decreases from 1e5 to 5e4 during quiescent period
                velocity[i, j] = 1.0e5 - (0.5e5) * t
                
        else:
            # After quiescent period: low uniform flow
            velocity[i, j] = 4.0e4 + 0.5e4 * (1.5 - t)

# Add some smooth variations
velocity = gaussian_filter(velocity, sigma=3)

# Add small-scale noise for realism
noise = np.random.randn(*velocity.shape) * 2e3
velocity = velocity + noise
velocity = gaussian_filter(velocity, sigma=1.5)

# Create the figure
fig, ax = plt.subplots(figsize=(10, 8))

# Create contour plot
levels = np.linspace(4e4, 1.05e5, 25)
contourf = ax.contourf(R, T, velocity, levels=levels, cmap='jet', extend='both')
contour_lines = ax.contour(R, T, velocity, levels=10, colors='k', alpha=0.3, linewidths=0.5)

# Add colorbar
cbar = plt.colorbar(contourf, ax=ax, label='Axial Velocity (m/s)')
cbar.ax.tick_params(labelsize=10)

# Add horizontal lines to mark key periods
ax.axhline(y=0, color='white', linestyle='--', linewidth=2, alpha=0.7, label='Start of quiescent period')
ax.axhline(y=1, color='white', linestyle='--', linewidth=2, alpha=0.7, label='End of quiescent period')

# Labels and formatting
ax.set_xlabel('Radius (mm)', fontsize=14, fontweight='bold')
ax.set_ylabel('Normalized Time τ', fontsize=14, fontweight='bold')
ax.set_title('Figure 4: Axial Velocity vs. Radius and Normalized Time\n5800 Torr, z = 0', 
             fontsize=14, fontweight='bold')

# Set axis limits
ax.set_xlim(-15, 15)
ax.set_ylim(-0.3, 1.5)

# Grid
ax.grid(True, alpha=0.2, linestyle=':', color='white')

# Add text annotations for key regions
ax.text(0, -0.15, 'Assembly\nPeriod', ha='center', va='center', 
        fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
ax.text(0, 0.5, 'Quiescent Period\n(Sheared Flow)', ha='center', va='center', 
        fontsize=10, bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
ax.text(0, 1.3, 'Post-Quiescent', ha='center', va='center', 
        fontsize=10, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

# Legend
ax.legend(loc='upper right', fontsize=9, framealpha=0.8)

# Tight layout
plt.tight_layout()

# Save the figure
plt.savefig('reconstructed_figure.jpg', dpi=300, bbox_inches='tight')
print("Figure saved as 'reconstructed_figure.jpg'")

# Display information
print(f"\nFigure characteristics:")
print(f"- Radius range: {radius.min():.1f} to {radius.max():.1f} mm")
print(f"- Normalized time range: {tau.min():.2f} to {tau.max():.2f}")
print(f"- Velocity range: {velocity.min():.2e} to {velocity.max():.2e} m/s")
print(f"- Velocity at τ=0.5, r=0: {velocity[np.argmin(np.abs(tau-0.5)), np.argmin(np.abs(radius-0))]:.2e} m/s")
print(f"- Velocity at τ=0.5, r=10: {velocity[np.argmin(np.abs(tau-0.5)), np.argmin(np.abs(radius-10))]:.2e} m/s")


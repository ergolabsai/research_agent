import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

# Create grid for radius and normalized time
radius = np.linspace(-10, 10, 200)  # mm
tau = np.linspace(-0.5, 1.5, 200)   # normalized time

R, T = np.meshgrid(radius, tau)

# Create velocity field based on the description
velocity = np.zeros_like(R)

for i, t in enumerate(tau):
    for j, r in enumerate(radius):
        r_abs = abs(r)
        
        if t < 0:
            # Before quiescent period: high uniform flow
            velocity[i, j] = 1e5
            
        elif 0 <= t <= 1:
            # During quiescent period: sheared flow structure
            # High velocity at edge, lower in core
            
            # Create smooth transition from core to edge
            # Core velocity around 5e4, edge velocity depends on time
            core_velocity = 5e4
            
            # Edge velocity decreases around tau = 0.5
            if t < 0.5:
                edge_velocity = 1e5
            else:
                # Edge slows down after tau = 0.5
                edge_velocity = 1e5 - (t - 0.5) * (1e5 - 5e4) / 0.5
            
            # Smooth transition from core to edge using tanh
            # Transition region around r = 7-8 mm
            transition_sharpness = 0.5
            transition_center = 8
            
            blend = 0.5 * (1 + np.tanh((r_abs - transition_center) * transition_sharpness))
            velocity[i, j] = core_velocity * (1 - blend) + edge_velocity * blend
            
        else:
            # After quiescent period: low uniform flow
            # Smooth transition from final quiescent state to low flow
            final_core = 5e4
            final_low = 2e4
            transition_time = (t - 1.0) / 0.5
            transition_time = min(transition_time, 1.0)
            
            velocity[i, j] = final_core * (1 - transition_time) + final_low * transition_time

# Add some realistic noise/variations
np.random.seed(42)
noise = np.random.normal(0, 2e3, velocity.shape)
velocity += noise

# Create the figure
fig, ax = plt.subplots(figsize=(10, 8))

# Create contour plot
levels = np.linspace(2e4, 1.1e5, 30)
contour = ax.contourf(R, T, velocity, levels=levels, cmap='jet')

# Add contour lines
contour_lines = ax.contour(R, T, velocity, levels=10, colors='k', alpha=0.3, linewidths=0.5)

# Add colorbar
cbar = plt.colorbar(contour, ax=ax, label='Axial Velocity (m/s)')
cbar.ax.tick_params(labelsize=10)

# Mark the quiescent period boundaries
ax.axhline(y=0, color='white', linestyle='--', linewidth=2, alpha=0.7)
ax.axhline(y=1, color='white', linestyle='--', linewidth=2, alpha=0.7)

# Add text annotation for quiescent period
ax.text(0, 0.5, 'Quiescent Period', fontsize=12, color='white', 
        ha='center', va='center', weight='bold',
        bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))

# Set labels and title
ax.set_xlabel('Radius (mm)', fontsize=14, weight='bold')
ax.set_ylabel('Normalized Time τ', fontsize=14, weight='bold')
ax.set_title('Figure 4: Axial Velocity vs Radius and Normalized Time\n5800 Torr, z=0 location', 
             fontsize=14, weight='bold', pad=20)

# Set axis limits
ax.set_xlim(-10, 10)
ax.set_ylim(-0.5, 1.5)

# Add grid
ax.grid(True, alpha=0.2, color='white', linestyle='-', linewidth=0.5)

# Improve tick labels
ax.tick_params(labelsize=11)

# Add axis line at r=0
ax.axvline(x=0, color='white', linestyle='-', linewidth=1, alpha=0.5)

plt.tight_layout()

# Save the figure
plt.savefig('reconstructed_figure.jpg', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print("Figure saved as 'reconstructed_figure.jpg'")

# Display information about the data
print("\nFigure characteristics:")
print(f"Velocity range: {velocity.min():.2e} to {velocity.max():.2e} m/s")
print(f"Core velocity (τ=0.5, r=0): {velocity[np.argmin(np.abs(tau-0.5)), np.argmin(np.abs(radius))]:.2e} m/s")
print(f"Edge velocity (τ=0.2, r=10): {velocity[np.argmin(np.abs(tau-0.2)), -1]:.2e} m/s")
print(f"Edge velocity (τ=0.8, r=10): {velocity[np.argmin(np.abs(tau-0.8)), -1]:.2e} m/s")

plt.close()

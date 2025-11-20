import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Set up the figure
fig, ax1 = plt.subplots(figsize=(10, 6))

# Time axis (microseconds)
time = np.linspace(0, 100, 1000)

# Create plasma current curve (dashed line)
# Current rises during assembly, plateaus during quiescent period, then changes
current = np.zeros_like(time)
for i, t in enumerate(time):
    if t < 20:
        # Rising phase
        current[i] = 30 * (1 - np.exp(-t/8))
    elif t < 34:
        # Transition to quiescent
        current[i] = 30 + 45 * (t - 20) / 14
    elif t < 78:
        # Quiescent period - approximately 75 kA
        current[i] = 75 + 2 * np.sin((t - 34) * 0.3)
    else:
        # Post-quiescent
        current[i] = 75 - 10 * (t - 78) / 22

# Create m=1 fluctuation (solid line)
m1_fluct = np.zeros_like(time)
for i, t in enumerate(time):
    if t < 34:
        # Large fluctuations during assembly
        base = 0.4 + 0.1 * np.sin(t * 0.5)
        noise = 0.15 * np.sin(t * 2.0) + 0.1 * np.sin(t * 3.5)
        m1_fluct[i] = base + noise
    elif t < 78:
        # Quiescent period - low fluctuations (below 0.2)
        base = 0.08
        noise = 0.05 * np.sin((t - 34) * 0.8) + 0.03 * np.sin((t - 34) * 1.5)
        m1_fluct[i] = base + noise
    else:
        # Post-quiescent - increased fluctuations
        base = 0.25 + 0.05 * (t - 78) / 22
        noise = 0.15 * np.sin((t - 78) * 1.5) + 0.1 * np.sin((t - 78) * 2.8)
        m1_fluct[i] = base + noise

# Create m=2 fluctuation (solid line, different pattern)
m2_fluct = np.zeros_like(time)
for i, t in enumerate(time):
    if t < 34:
        # Large fluctuations during assembly
        base = 0.3 + 0.08 * np.sin(t * 0.7)
        noise = 0.12 * np.sin(t * 2.5) + 0.08 * np.sin(t * 4.0)
        m2_fluct[i] = base + noise
    elif t < 78:
        # Quiescent period - low fluctuations
        base = 0.05
        noise = 0.04 * np.sin((t - 34) * 1.0) + 0.02 * np.sin((t - 34) * 2.0)
        m2_fluct[i] = base + noise
    else:
        # Post-quiescent - increased fluctuations
        base = 0.20 + 0.04 * (t - 78) / 22
        noise = 0.12 * np.sin((t - 78) * 1.8) + 0.08 * np.sin((t - 78) * 3.2)
        m2_fluct[i] = base + noise

# Plot magnetic fluctuations on left y-axis
ax1.plot(time, m1_fluct, 'b-', linewidth=2, label='m=1 mode')
ax1.plot(time, m2_fluct, 'r-', linewidth=2, label='m=2 mode')

# Add horizontal line at 0.2 threshold
ax1.axhline(y=0.2, color='gray', linestyle=':', linewidth=1, alpha=0.7)
ax1.text(55, 0.21, 'threshold = 0.2', fontsize=9, color='gray')

ax1.set_xlabel('Time (μs)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Normalized Magnetic Fluctuation', fontsize=12, fontweight='bold', color='black')
ax1.tick_params(axis='y', labelcolor='black')
ax1.set_ylim(0, 0.7)
ax1.grid(True, alpha=0.3)

# Create second y-axis for plasma current
ax2 = ax1.twinx()
ax2.plot(time, current, 'k--', linewidth=2.5, label='Plasma Current', alpha=0.7)
ax2.set_ylabel('Plasma Current (kA)', fontsize=12, fontweight='bold')
ax2.set_ylim(0, 85)

# Highlight quiescent period
ax1.axvspan(34, 78, alpha=0.15, color='green', label='Quiescent Period')

# Add vertical lines and annotations for quiescent period
ax1.axvline(x=34, color='green', linestyle='--', linewidth=1.5, alpha=0.7)
ax1.axvline(x=78, color='green', linestyle='--', linewidth=1.5, alpha=0.7)
ax1.text(34, 0.65, 'τ = 0\n(34 μs)', fontsize=10, ha='center', 
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
ax1.text(78, 0.65, 'τ = 1\n(78 μs)', fontsize=10, ha='center',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Add annotations for the three regions
ax1.text(17, 0.60, 'Pinch\nAssembly', fontsize=11, ha='center', 
         style='italic', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
ax1.text(56, 0.60, 'Quiescent Period\n(~75 kA)', fontsize=11, ha='center',
         style='italic', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
ax1.text(89, 0.60, 'Post-\nQuiescent', fontsize=11, ha='center',
         style='italic', bbox=dict(boxstyle='round', facecolor='orange', alpha=0.3))

# Set x-axis limits
ax1.set_xlim(0, 100)

# Combine legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10, framealpha=0.9)

# Add title
plt.title('Plasma Current and Magnetic Field Fluctuations\n(Modified ZaP Configuration: 0.15 m Inner Electrode)', 
          fontsize=13, fontweight='bold', pad=15)

# Adjust layout
plt.tight_layout()

# Save figure
plt.savefig('reconstructed_figure.jpg', dpi=300, bbox_inches='tight', format='jpg')
print("Figure saved as 'reconstructed_figure.jpg'")

# Also display it
plt.savefig('reconstructed_figure.jpg', dpi=300, bbox_inches='tight')
plt.close()

print("\nFigure characteristics:")
print("- Time range: 0-100 μs")
print("- Quiescent period: 34-78 μs (τ=0 to τ=1)")
print("- Plasma current during quiescent period: ~75 kA")
print("- m=1 and m=2 fluctuations below 0.2 threshold during quiescent period")
print("- Large fluctuations before and after quiescent period")


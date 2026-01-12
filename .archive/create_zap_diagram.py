import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, Wedge, Circle
import numpy as np

# Create figure and axis
fig, ax = plt.subplots(1, 1, figsize=(16, 10))

# Set up the coordinate system (using meters)
ax.set_xlim(-0.3, 2.2)
ax.set_ylim(-0.4, 0.4)
ax.set_aspect('equal')

# Colors
electrode_color = '#666666'
port_color = '#888888'
text_color = '#000000'

# 1. Draw outer electrode (0.2 m diameter = 0.1 m radius)
outer_radius = 0.1
inner_radius = 0.05  # 0.1 m diameter = 0.05 m radius
accel_length = 1.0

# Outer electrode walls (top and bottom)
ax.add_patch(Rectangle((-1.0, outer_radius), accel_length, 0.02, 
                       facecolor=electrode_color, edgecolor='black', linewidth=1.5))
ax.add_patch(Rectangle((-1.0, -outer_radius-0.02), accel_length, 0.02, 
                       facecolor=electrode_color, edgecolor='black', linewidth=1.5))

# Inner electrode (top and bottom)
ax.add_patch(Rectangle((-1.0, inner_radius), accel_length, 0.015, 
                       facecolor=electrode_color, edgecolor='black', linewidth=1.5))
ax.add_patch(Rectangle((-1.0, -inner_radius-0.015), accel_length, 0.015, 
                       facecolor=electrode_color, edgecolor='black', linewidth=1.5))

# Left end caps
ax.add_patch(Rectangle((-1.02, -outer_radius-0.02), 0.02, 2*outer_radius+0.04, 
                       facecolor=electrode_color, edgecolor='black', linewidth=1.5))

# 2. Assembly/Z-pinch region (extending to the right)
z_pinch_length = 0.8
z_pinch_radius = 0.08

# Top and bottom walls of Z-pinch region
ax.add_patch(Rectangle((0, z_pinch_radius), z_pinch_length, 0.015, 
                       facecolor=electrode_color, edgecolor='black', linewidth=1.5))
ax.add_patch(Rectangle((0, -z_pinch_radius-0.015), z_pinch_length, 0.015, 
                       facecolor=electrode_color, edgecolor='black', linewidth=1.5))

# 3. Mark z=0 location with a vertical dashed line
ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='z=0')
ax.text(0, -0.35, 'z = 0', fontsize=12, ha='center', color='red', fontweight='bold')

# 4. Diagnostic ports at z=0
port_width = 0.05
port_height = 0.08

# Top ports at z=0
# Interferometer port
ax.add_patch(Rectangle((-port_width/2, z_pinch_radius+0.015), port_width, port_height, 
                       facecolor=port_color, edgecolor='black', linewidth=1.2))
ax.annotate('Interferometer', xy=(0, z_pinch_radius+0.015+port_height), 
            xytext=(0.15, 0.25), fontsize=9,
            arrowprops=dict(arrowstyle='->', lw=1.5), ha='left')

# Spectrometer port
ax.add_patch(Rectangle((-port_width/2-0.08, z_pinch_radius+0.015), port_width, port_height, 
                       facecolor=port_color, edgecolor='black', linewidth=1.2))
ax.annotate('Spectrometer\n(Ion Doppler)', xy=(-0.08, z_pinch_radius+0.015+port_height), 
            xytext=(-0.2, 0.28), fontsize=9,
            arrowprops=dict(arrowstyle='->', lw=1.5), ha='center')

# Fast framing camera port
ax.add_patch(Rectangle((port_width/2+0.03, z_pinch_radius+0.015), port_width, port_height, 
                       facecolor=port_color, edgecolor='black', linewidth=1.2))
ax.annotate('Fast Framing Camera\n(Thomson Scattering)', xy=(0.08, z_pinch_radius+0.015+port_height), 
            xytext=(0.35, 0.28), fontsize=9,
            arrowprops=dict(arrowstyle='->', lw=1.5), ha='center')

# 5. Lower oblique port for velocity measurements
oblique_angle = -35  # degrees
oblique_length = 0.12
oblique_x = 0.02
oblique_y = -z_pinch_radius - 0.015

# Draw oblique port as a rectangle at an angle
from matplotlib.transforms import Affine2D
oblique_rect = Rectangle((oblique_x, oblique_y-0.03), oblique_length, 0.04, 
                         facecolor=port_color, edgecolor='black', linewidth=1.2)
t = Affine2D().rotate_deg_around(oblique_x, oblique_y, oblique_angle) + ax.transData
oblique_rect.set_transform(t)
ax.add_patch(oblique_rect)

ax.annotate('20-chord Spectrometer\n(Velocity Profile)', 
            xy=(oblique_x, oblique_y), 
            xytext=(0.15, -0.28), fontsize=9,
            arrowprops=dict(arrowstyle='->', lw=1.5), ha='left')

# 6. Smaller side ports in acceleration region
small_port_positions = [-0.7, -0.4, -0.2]
for pos in small_port_positions:
    # Top port
    ax.add_patch(Rectangle((pos-0.02, outer_radius+0.02), 0.04, 0.05, 
                           facecolor=port_color, edgecolor='black', linewidth=1))
    
ax.annotate('Density measurement\nports (acceleration region)', 
            xy=(-0.4, outer_radius+0.02+0.05), 
            xytext=(-0.65, 0.25), fontsize=9,
            arrowprops=dict(arrowstyle='->', lw=1.5), ha='center')

# 7. Electrode end wall with 10mm radius hole
end_wall_x = z_pinch_length
hole_radius = 0.01  # 10mm = 0.01m

# Draw end wall (with gap for hole)
ax.add_patch(Rectangle((end_wall_x, hole_radius+0.005), 0.025, z_pinch_radius-hole_radius-0.005+0.015, 
                       facecolor=electrode_color, edgecolor='black', linewidth=1.5))
ax.add_patch(Rectangle((end_wall_x, -z_pinch_radius-0.015), 0.025, z_pinch_radius-hole_radius-0.005, 
                       facecolor=electrode_color, edgecolor='black', linewidth=1.5))

# Draw the hole edges
ax.plot([end_wall_x, end_wall_x], [hole_radius, hole_radius+0.005], 'k-', linewidth=1.5)
ax.plot([end_wall_x, end_wall_x], [-hole_radius-0.005, -hole_radius], 'k-', linewidth=1.5)

# Label the hole
ax.annotate('10 mm hole\n(axial flow)', xy=(end_wall_x, 0), 
            xytext=(1.0, 0.12), fontsize=9,
            arrowprops=dict(arrowstyle='->', lw=1.5), ha='center')

# Surge volume indication
ax.annotate('Surge\nVolume', xy=(end_wall_x+0.025, 0), 
            xytext=(1.15, 0), fontsize=10, ha='left', va='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', edgecolor='black'))

# 8. Add 1 meter scale bar
scale_y = -0.32
scale_x_start = -1.0
scale_x_end = 0.0
ax.plot([scale_x_start, scale_x_end], [scale_y, scale_y], 'k-', linewidth=3)
ax.plot([scale_x_start, scale_x_start], [scale_y-0.01, scale_y+0.01], 'k-', linewidth=3)
ax.plot([scale_x_end, scale_x_end], [scale_y-0.01, scale_y+0.01], 'k-', linewidth=3)
ax.text((scale_x_start+scale_x_end)/2, scale_y-0.04, '1 meter', fontsize=11, 
        ha='center', fontweight='bold')

# 9. Add z-direction arrow
arrow_y = 0.35
ax.annotate('', xy=(1.8, arrow_y), xytext=(1.5, arrow_y),
            arrowprops=dict(arrowstyle='->', lw=3, color='blue'))
ax.text(1.65, arrow_y+0.03, '+z', fontsize=12, ha='center', color='blue', fontweight='bold')

# Add labels for main components
ax.text(-0.5, 0.16, 'Coaxial Accelerator', fontsize=11, ha='center', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='lightblue', edgecolor='black'))

ax.text(0.4, 0.16, 'Assembly/Z-Pinch Region', fontsize=11, ha='center', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', edgecolor='black'))

# Add dimension annotations
# Outer electrode diameter
ax.annotate('', xy=(-1.05, outer_radius), xytext=(-1.05, -outer_radius),
            arrowprops=dict(arrowstyle='<->', lw=1.5))
ax.text(-1.12, 0, '0.2 m', fontsize=9, ha='center', rotation=90, va='center')

# Inner electrode diameter
ax.annotate('', xy=(-0.85, inner_radius), xytext=(-0.85, -inner_radius),
            arrowprops=dict(arrowstyle='<->', lw=1.5))
ax.text(-0.92, 0, '0.1 m', fontsize=9, ha='center', rotation=90, va='center')

# Title
ax.text(0.4, 0.38, 'ZaP Experimental Apparatus - Side View', fontsize=14, 
        ha='center', fontweight='bold')

# Add grid for reference (light)
ax.grid(True, alpha=0.2, linestyle=':', linewidth=0.5)

# Remove axis labels but keep grid
ax.set_xlabel('Axial Position (m)', fontsize=11, fontweight='bold')
ax.set_ylabel('Radial Position (m)', fontsize=11, fontweight='bold')

# Add minor ticks
ax.set_xticks(np.arange(-1.0, 2.2, 0.2), minor=True)
ax.set_yticks(np.arange(-0.4, 0.4, 0.1), minor=True)

plt.tight_layout()
plt.savefig('reconstructed_figure.jpg', dpi=300, bbox_inches='tight', facecolor='white')
print("Figure saved as reconstructed_figure.jpg")
plt.close()


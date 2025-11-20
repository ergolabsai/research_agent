import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from scipy.stats import norm

# Set random seed for reproducibility
np.random.seed(42)

# Physical constants and parameters
k_B = 1.38064852e-23  # Boltzmann constant in J/K
eV_to_K = 11604.5  # Conversion factor from eV to K
T_e = 64  # Electron temperature in eV
lambda_0 = 694.0  # Ruby laser wavelength in nm
c = 3e8  # Speed of light in m/s

# Calculate the Doppler width based on electron temperature
# For Thomson scattering: Δλ/λ₀ ≈ sqrt(2kT_e/m_e c²)
# This gives us the standard deviation of the Gaussian
m_e = 9.10938356e-31  # Electron mass in kg
T_kelvin = T_e * eV_to_K

# Calculate wavelength spread (standard deviation)
# Doppler broadening: Δλ/λ = sqrt(2kT/mc²) for thermal motion
delta_lambda = lambda_0 * np.sqrt(2 * k_B * T_kelvin / (m_e * c**2))
sigma = delta_lambda  # Standard deviation in nm

# Create wavelength axis (spread around the laser wavelength)
wavelength = np.linspace(lambda_0 - 4*sigma, lambda_0 + 4*sigma, 1000)

# Create the Gaussian fit curve (theoretical)
gaussian_fit = norm.pdf(wavelength, lambda_0, sigma)
# Normalize to a reasonable peak intensity
gaussian_fit = gaussian_fit / np.max(gaussian_fit) * 100

# Create simulated PMT channel data (5 channels with significant signal)
# Channels positioned at different wavelengths
n_channels = 5
channel_positions = np.linspace(lambda_0 - 2.5*sigma, lambda_0 + 2.5*sigma, n_channels)

# Calculate expected intensity at each channel position from Gaussian
channel_intensities = norm.pdf(channel_positions, lambda_0, sigma)
channel_intensities = channel_intensities / np.max(channel_intensities) * 100

# Add realistic noise to the measurements (Poisson-like noise)
noise_level = 5
measured_intensities = channel_intensities + np.random.normal(0, noise_level, n_channels)
# Add error bars
intensity_errors = np.abs(np.random.normal(noise_level, 1, n_channels))

# Create the figure
fig, ax = plt.subplots(figsize=(10, 7))

# Plot the Gaussian fit curve
ax.plot(wavelength, gaussian_fit, 'r-', linewidth=2, 
        label=f'Gaussian fit (T$_e$ = {T_e} eV)', zorder=2)

# Plot the experimental data points with error bars
ax.errorbar(channel_positions, measured_intensities, yerr=intensity_errors,
            fmt='bo', markersize=10, capsize=5, capthick=2, 
            linewidth=2, label='PMT channel data', zorder=3)

# Add labels and title
ax.set_xlabel('Wavelength (nm)', fontsize=14, fontweight='bold')
ax.set_ylabel('Intensity (arbitrary units)', fontsize=14, fontweight='bold')
ax.set_title('Thomson Scattering Spectrum\nRuby Laser (694 nm)', 
             fontsize=16, fontweight='bold', pad=20)

# Add grid
ax.grid(True, alpha=0.3, linestyle='--')

# Add legend
ax.legend(fontsize=12, loc='upper right', framealpha=0.9)

# Add text annotation with temperature
textstr = f'Electron Temperature: {T_e} eV\nλ₀ = {lambda_0} nm'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=11,
        verticalalignment='top', bbox=props)

# Set y-axis to start at 0
ax.set_ylim(bottom=0, top=max(measured_intensities.max(), gaussian_fit.max()) * 1.15)

# Improve tick labels
ax.tick_params(axis='both', which='major', labelsize=11)

# Tight layout
plt.tight_layout()

# Save the figure
plt.savefig('reconstructed_figure.jpg', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print("Figure saved as 'reconstructed_figure.jpg'")

# Display some information
print(f"\nFigure parameters:")
print(f"Electron temperature: {T_e} eV")
print(f"Central wavelength: {lambda_0} nm")
print(f"Gaussian width (σ): {sigma:.4f} nm")
print(f"Number of PMT channels with data: {n_channels}")
print(f"Channel positions: {channel_positions}")


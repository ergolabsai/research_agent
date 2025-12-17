import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# Set random seed for reproducibility
np.random.seed(42)

# Parameters for the Thomson scattering spectrum
central_wavelength = 694.0  # Ruby laser wavelength in nm
Te = 64  # Electron temperature in eV

# Calculate the Doppler broadening
# The width is related to temperature: Δλ/λ ≈ sqrt(kT/mc²)
# For Te = 64 eV, this gives a reasonable width
k_B = 1.38e-23  # Boltzmann constant
eV_to_J = 1.602e-19
m_e = 9.109e-31  # electron mass
c = 3e8

# Calculate FWHM from temperature
# For Thomson scattering: Δλ ≈ λ * sqrt(2kT/(m_e*c²))
thermal_velocity = np.sqrt(2 * Te * eV_to_J / m_e)
width_nm = central_wavelength * thermal_velocity / c  # Approximate Doppler width
sigma = width_nm / 2.355  # Convert FWHM to standard deviation

# Five wavelength channels (typical for a polychromator)
# Spread around the central wavelength
channel_wavelengths = np.array([
    central_wavelength - 1.5 * width_nm,
    central_wavelength - 0.75 * width_nm,
    central_wavelength,
    central_wavelength + 0.75 * width_nm,
    central_wavelength + 1.5 * width_nm
])

# Generate intensity data for each channel with some noise
# True Gaussian profile
true_intensity = norm.pdf(channel_wavelengths, central_wavelength, sigma)
# Normalize to a reasonable peak value
true_intensity = true_intensity / np.max(true_intensity) * 100

# Add realistic experimental noise (Poisson-like)
noise_level = 5
measured_intensity = true_intensity + np.random.normal(0, noise_level, len(channel_wavelengths))
# Add error bars
intensity_errors = np.random.uniform(3, 7, len(channel_wavelengths))

# Generate smooth Gaussian fit curve
wavelength_fine = np.linspace(channel_wavelengths[0] - 0.5, 
                               channel_wavelengths[-1] + 0.5, 200)
gaussian_fit = norm.pdf(wavelength_fine, central_wavelength, sigma)
gaussian_fit = gaussian_fit / np.max(gaussian_fit) * 100

# Create the figure
plt.figure(figsize=(10, 7))

# Plot the experimental data points with error bars
plt.errorbar(channel_wavelengths, measured_intensity, yerr=intensity_errors,
             fmt='o', markersize=10, capsize=5, capthick=2,
             color='#2E86AB', ecolor='#2E86AB', 
             label='Experimental Data (5 Channels)', linewidth=2, markeredgewidth=1.5,
             markeredgecolor='darkblue', markerfacecolor='#2E86AB')

# Plot the Gaussian fit
plt.plot(wavelength_fine, gaussian_fit, 'r-', linewidth=2.5, 
         label=f'Gaussian Fit (Te = {Te} eV)', alpha=0.8)

# Formatting
plt.xlabel('Wavelength (nm)', fontsize=14, fontweight='bold')
plt.ylabel('Scattered Light Intensity (arb. units)', fontsize=14, fontweight='bold')
plt.title('Thomson Scattering Spectrum', fontsize=16, fontweight='bold', pad=20)
plt.legend(fontsize=12, loc='upper right', framealpha=0.9)
plt.grid(True, alpha=0.3, linestyle='--')

# Add a text box with measurement info
textstr = f'Ruby Laser: λ₀ = {central_wavelength} nm\nElectron Temperature: {Te} eV\nSpectral Width: {width_nm:.2f} nm'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=11,
         verticalalignment='top', bbox=props)

# Set y-axis to start from 0 for better visualization
plt.ylim(bottom=-5, top=max(measured_intensity) * 1.15)

# Adjust layout
plt.tight_layout()

# Save the figure
plt.savefig('reconstructed_figure.jpg', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print("Figure saved successfully as reconstructed_figure.jpg")

# Display some info
print(f"\nFigure details:")
print(f"- Central wavelength: {central_wavelength} nm")
print(f"- Electron temperature: {Te} eV")
print(f"- Number of channels: {len(channel_wavelengths)}")
print(f"- Spectral width (FWHM): {width_nm:.3f} nm")
print(f"- Channel wavelengths: {channel_wavelengths}")

plt.close()

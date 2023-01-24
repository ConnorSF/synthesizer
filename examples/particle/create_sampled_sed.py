
# --- this example generates a sample of star particles from a 2D SFZH. In this case it is generated from a parametric star formation history with constant star formation.


import numpy as np
import matplotlib.pyplot as plt
from unyt import yr, Myr

from synthesizer.grid import Grid
from synthesizer.parametric.sfzh import SFH, ZH, generate_sfzh
from synthesizer.particle.stars import sample_sfhz
from synthesizer.particle.stars import Stars
from synthesizer.galaxy.particle import ParticleGalaxy


# --- define the grid (normally this would be defined by an SPS grid)
log10ages = np.arange(6., 10.5, 0.1)
metallicities = 10**np.arange(-5., -1.5, 0.1)

# --- define the parameters of the star formation and metal enrichment histories

Z_p = {'Z': 0.01}
Zh = ZH.deltaConstant(Z_p)

sfh_p = {'duration': 100 * Myr}
sfh = SFH.Constant(sfh_p)  # constant star formation
sfzh = generate_sfzh(log10ages, metallicities, sfh, Zh)
sfzh.summary()
# sfzh.plot()


# --- create stars object

N = 100  # number of particles for sampling
stars = sample_sfhz(sfzh, N)


# --- open grid

grid_name = 'bpass-v2.2.1-bin_chab-100_cloudy-v17.03_log10Uref-2'
grid = Grid(grid_name)

# --- create galaxy object

galaxy = ParticleGalaxy(stars=stars)

# --- this generates stellar and intrinsic spectra
# galaxy.generate_intrinsic_spectra(grid, fesc=0.0) # calculate only integrated SEDs
# calculates for every star particle, slow but necessary for LOS.
galaxy.generate_intrinsic_spectra(grid, fesc=0.0, integrated=False)

# --- generate dust screen
# galaxy.get_screen(0.5) # tauV

# --- generate CF00 variable dust screen
# galaxy.get_CF00(grid, 0.5, 0.5) # grid, tauV_BC, tauV_ISM

# --- generate for los model
tauVs = np.ones(N) * 0.5
galaxy.get_los(tauVs)  # grid, tauV_BC, tauV_ISM

for sed_type, sed in galaxy.spectra.items():
    plt.plot(np.log10(sed.lam), np.log10(sed.lnu), label=sed_type)

plt.legend()
plt.xlim([2, 5])
plt.ylim([10, 22])
plt.show()
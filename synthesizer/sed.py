import numpy as np

from scipy.integrate import simps
from scipy.stats import linregress
from scipy import integrate

from unyt import c, h, nJy, erg, s, Hz

from .igm import Inoue14


class Sed:

    """
    A class representing a spectral energy distribution (SED).

    Attributes
    ----------
    lam : ndarray
        the wavelength grid in \AA
    lam_m : ndarray
        the wavelength grid in m
    nu : ndarray
        frequency in Hz
    lnu: ndarray
        the spectral luminosity density


    Methods
    -------
    return_beta:
        Calculate beta using two wavelength points
    return_beta_spec:
        Calculate beta using linear regression to the spectra over a wavelength range
    """

    def __init__(self, lam, lnu=None, description=False):
        """ Initialise an empty spectral energy distribution object """

        self.description = description

        self.lam = lam  # \AA
        self.lam_m = lam * 1E10  # m

        if lnu is None:
            self.lnu = np.zeros(self.lam.shape)  # luminosity ers/s/Hz
        else:
            self.lnu = lnu

        self.nu = c.value/(self.lam_m)  # Hz

    def return_beta(self, wv=[1500., 2500.]):
        """ Return the UV continuum slope (\beta) based on measurements at two wavelength. """

        f0 = np.interp(wv[0], self.lam, self.lnu)
        f1 = np.interp(wv[1], self.lam, self.lnu)

        return np.log10(f0/f1)/np.log10(wv[0]/wv[1])-2.0

    def return_beta_spec(self, wv=[1250., 3000.]):
        """ Return the UV continuum slope (\beta) based on linear regression to the spectra over a wavelength range. """

        s = (self.lam > wv[0]) & (self.lam < wv[1])

        slope, intercept, r, p, se = linregress(np.log10(self.lam[s]), np.log10(self.lnu[s]))

        return slope - 2.0

    def get_balmer_break(self):
        """ Return the Balmer break strength """

        T = (self.lam > 3400) & (self.lam < 3600)
        T = T.astype(float)
        b = integrate.trapezoid(
            self.lnu * T/self.nu, self.nu) / integrate.trapezoid(T/self.nu, self.nu)  # numerator

        T = (self.lam > 4150) & (self.lam < 4250)
        T = T.astype(float)
        r = integrate.trapezoid(
            self.lnu * T/self.nu, self.nu) / integrate.trapezoid(T/self.nu, self.nu)  # numerator

        return np.log10(r/b)

        """ measure the balmer break strength """

    def get_broadband_luminosities(self, fc):  # broad band flux/nJy
        """
        Calculate broadband luminosities using a FilterCollection object

        arguments
        fc: a FilterCollection object
        """

        self.get_broadband_luminosities = {}

        for f in fc.filters:

            # --- calculate broadband fluxes by multiplying the observed spetra by the filter transmission curve and dividing by the normalisation

            int_num = integrate.trapezoid(self.lnu * fc.filter[f].t/self.nu, self.nu)  # numerator
            int_den = integrate.trapezoid(fc.filter[f].t/self.nu, self.nu)  # denominator

            self.get_broadband_luminosities[f] = (int_num / int_den) * erg/s/Hz

        return self.get_broadband_luminosities

    def get_fnu0(self):
        """
        Calculate a dummy observed frame spectral energy distribution. Useful when you want rest-frame quantities.
        """

        self.lamz = self.lam
        self.fnu = self.lnu

    def get_fnu(self, cosmo, z, igm=Inoue14()):
        """
        Calculate the observed frame spectral energy distribution in nJy
        """

        self.lamz = self.lam * (1. + z)  # observed frame wavelength
        luminosity_distance = cosmo.luminosity_distance(
            z).to('cm').value  # the luminosity distance in cm
        self.fnu = self.lnu * (1.+z) / (4 * np.pi * luminosity_distance**2)  # erg/s/Hz/cm2
        self.fnu *= 1E23  # convert to Jy
        self.fnu *= 1E9  # convert to nJy

        if igm:
            self.fnu *= igm.T(z, self.lamz)

    def get_broadband_fluxes(self, fc):  # broad band flux/nJy
        """
        Calculate broadband luminosities using a FilterCollection object

        arguments
        fc: a FilterCollection object
        """

        self.broadband_fluxes = {}

        for f in fc.filters:

            # --- check whether the filter transmission curve wavelength grid and the spectral grid are the same array
            if not np.array_equal(fc.filter[f].lam, self.lamz):
                print('WARNING: filter wavelength grid is not the same as the SED wavelength grid.')

            # --- calculate broadband fluxes by multiplying the observed spetra by the filter transmission curve and dividing by the normalisation

            # --- all of these versions seem to work. I suspect the first one won't work for different wavelength grids.

            # int_num = integrate.trapezoid(self.fnu * fc.filter[f].t) # numerator
            # int_den = integrate.trapezoid(fc.filter[f].t) # denominator

            int_num = integrate.trapezoid(self.fnu * fc.filter[f].t/self.nu, self.nu)  # numerator
            int_den = integrate.trapezoid(fc.filter[f].t/self.nu, self.nu)  # denominator

            # int_num = integrate.simpson(self.fnu * fc.filter[f].t/self.nu, self.nu) # numerator
            # int_den = integrate.simpson(fc.filter[f].t/self.nu, self.nu) # denominator

            self.broadband_fluxes[f] = int_num / int_den * nJy

        return self.broadband_fluxes

    def c(self, f1, f2):
        """
        Calculate broadband colours using the broad_band fluxes
        """

        return 2.5*np.log10(self.broadband_fluxes[f2]/self.broadband_fluxes[f1])

    # def return_log10Q(self):
    #     """
    #     measure the ionising photon luminosity
    #     :return:
    #     """
    #
    #     llam = self.lnu * c.value / (self.lam**2*1E-10)  # erg s^-1 \AA^-1
    #     nlam = (llam*self.lam*1E-10) / (h.to('erg/Hz').value * c.value)  # s^-1 \AA^-1
    #     s = ((self.lam >= 0) & (self.lam < 912)).nonzero()[0]
    #     Q = simps(nlam[s], self.lam[s])
    #
    #     return np.log10(Q)


def convert_flam_to_fnu(lam, flam):
    """ convert f_lam to f_nu

    arguments:
    lam -- wavelength/\AA
    flam -- spectral luminosity density/erg/s/\AA
    """

    lam_m = lam * 1E-10

    return flam * lam/(c.value/lam_m)


def convert_fnu_to_flam(lam, fnu):
    """ convert f_nu to f_lam

    arguments:
    lam -- wavelength/\AA
    flam -- spectral luminosity density/erg/s/\AA
    """

    lam_m = lam * 1E-10

    return fnu * (c.value/lam_m)/lam


def calculate_Q(lam, lnu):
    """ calculate the ionising photon luminosity

    arguments:
    lam -- wavelength/\AA
    lnu -- spectral luminosity density/erg/s/Hz
    """

    # --- check lam is increasing and if not reverse
    if lam[1] < lam[0]:
        lam = lam[::-1]

    lam_m = lam * 1E-10  # m
    lnu *= 1E-7  # convert to W s^-1 Hz^-1
    llam = lnu * c.value / (lam * lam_m)  # convert to l_lam (W s^-1 \AA^-1)
    nlam = (llam * lam_m) / (h.value * c.value)  # s^-1 \AA^-1

    def f(l): return np.interp(l, lam, nlam)
    Q = integrate.quad(f, 10.0, 912.0)[0]

    return Q


def rebin(l, f, n):  # rebin SED [currently destroys original]

    n_len = int(np.floor(len(l)/n))
    l = l[:n_len*n]
    f = f[:n_len*n]
    nl = np.mean(l.reshape(n_len, n), axis=1)
    nf = np.sum(f.reshape(n_len, n), axis=1)/n

    return nl, nf

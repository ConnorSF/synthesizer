"""
Survey functionality
"""
import numpy as np

from astropy.cosmology import Planck18

import synthesizer.exceptions as exceptions
from synthesizer.galaxy.particle import ParticleGalaxy
from synthesizer.galaxy.parametric import ParametricGalaxy
from synthesizer.utils import m_to_flux, flux_to_luminosity
from synthesizer.sed import Sed
from synthesizer.igm import Inoue14


class Instrument:
    """
    This class describes an instrument used to make a set of observations.
    Attributes
    ----------
    Methods
    -------
    """

    def __init__(
        self,
        resolution,
        filters,
        psfs=None,
        depths=None,
        aperture=None,
        snrs=None,
        noises=None,
        resolving_power=None,
        lam=None,
    ):
        """
        Initialise the Observatory.
        Parameters
        ----------
        """

        # Basic metadata
        self.instrument = filters.filter_codes[0].split(".")[0]

        # Store some basic instrument properties
        self.resolution = resolution
        self.filters = filters
        self.psfs = psfs

        # Store some basic spectral information for this observation.
        self.resolving_power = resolving_power
        self.lams = None

        # Intilaise noise properties which can be populated by the outside.
        self.aperture = aperture
        self.depths = depths
        self.noises = noises
        self.snrs = snrs

        # Unit information
        if resolution is not None:
            self.spatial_unit = resolution.units
        else:
            self.spatial_unit = None

    def _check_obs_args(self):
        """
        Ensures we have valid inputs.
        Parameters
        ----------
        Raises
        ------
        """
        pass

    def get_lam_from_R(self):
        """
        Calculates the wavelengths of a spectrum based on this observations
        resolving power.
        Parameters
        ----------
        Raises
        ------
        """
        pass


class Survey:
    """
    A Survey helper object which defines all the properties of a survey. This
    enables the defintion of a survey approach and then the production of
    photometry and/or images based on that instruments/filters making up the
    survey. This can handle PSFs and depths which vary across bands and
    instruments.

    Attributes
    ----------
    Methods
    -------
    """

    def __init__(self, galaxies=(), fov=None, super_resolution_factor=None,
                 cosmo=Planck18):
        """
        Initialise the Survey.
        Parameters
        ----------
        """

        # Basic information
        self.ninstruments = 0
        self.nfilters = 0
        self.ngalaxies = 0
        self.cosmo = cosmo

        # Information about the field/collection of images being observered
        self.fov = fov
        self.super_resolution_factor = super_resolution_factor

        # Observation configurations are held in a dict, initialise it.
        self.instruments = {}

        # Store the galaxies we are making images of
        self.galaxies = galaxies

        # Intialise somewhere to keep survey images, this is populated later
        self.imgs = None

        # Intialise where we will store the Survey's SEDs
        self.seds = {}

        # Initialise somewhere to keep galaxy photometry. This is the
        # integrated flux/luminosity in each band in Survey.filters.
        self.photometry = {}

    def _check_survey_args(self):
        """
        Ensures we have valid inputs.
        Parameters
        ----------
        Raises
        ------
        """
        pass

    def add_photometric_instrument(
        self,
        filters,
        label,
        resolution=None,
        psfs=None,
        depths=None,
        apertures=None,
        snrs=None,
        noises=None,
    ):
        """
        Adds an instrument and all it's filters to the Survey.
        Parameters
        ----------
        Raises
        ------
        InconsistentArguments
            If the arguments do not constitute a valid combination for an
            instrument an error is thrown.
        """

        # How many filters do we have?
        nfilters = len(filters)

        # Check our inputs match the number of filters we have
        if isinstance(psfs, dict):
            if nfilters != len(psfs):
                raise exceptions.InconsistentArguments(
                    "Inconsistent number of entries in instrument dictionaries"
                    " len(filters)=%d, len(psfs)=%d)" % (nfilters, len(psfs))
                )
        if isinstance(depths, dict):
            if nfilters != len(depths):
                raise exceptions.InconsistentArguments(
                    "Inconsistent number of entries in instrument dictionaries"
                    " len(filters)=%d, len(depths)=%d)"
                    % (nfilters, len(depths))
                )
        if isinstance(apertures, dict):
            if nfilters != len(apertures):
                raise exceptions.InconsistentArguments(
                    "Inconsistent number of entries in instrument dictionaries"
                    " len(filters)=%d, len(apertures)=%d)"
                    % (nfilters, len(apertures))
                )
        if isinstance(snrs, dict):
            if nfilters != len(snrs):
                raise exceptions.InconsistentArguments(
                    "Inconsistent number of entries in instrument dictionaries"
                    " len(filters)=%d, len(snrs)=%d)" % (nfilters, len(snrs))
                )
        if isinstance(noises, dict):
            if nfilters != len(noises):
                raise exceptions.InconsistentArguments(
                    "Inconsistent number of entries in instrument dictionaries"
                    " len(filters)=%d, len(noises)=%d)"
                    % (nfilters, len(noises))
                )

        # Create this observation configurations
        self.instruments[label] = Instrument(
            resolution=resolution,
            filters=filters,
            psfs=psfs,
            depths=depths,
            aperture=apertures,
            snrs=snrs,
            noises=noises,
        )

        # Record that we included another insturment and count the filters
        self.ninstruments += 1
        self.nfilters += len(filters)

    def add_spectral_instrument(
        self, resolution, resolving_power, psf=None, depth=None, aperture=None
    ):
        pass

    def add_galaxies(self, galaxies):
        """
        Adds galaxies to this survey
        Parameters
        ----------
        galaxies : list
            The galaxies to include in this Survey.
        """

        # If we have no galaxies just add them
        if len(self.galaxies) == 0:
            self.galaxies = galaxies

        # Otherwise, we have to add them on to what we have, handling whether
        # we are adding 1 galaxy...
        elif len(self.galaxies) > 0 and (
            isinstance(galaxies, ParticleGalaxy)
            or isinstance(galaxies, ParametricGalaxy)
        ):

            # Double check galaxies is a list
            self.galaxies = list(self.galaxies)

            # Include the new galaxies
            self.galaxies.append(galaxies)

        # ... or multiple galaxies
        else:

            # Double check galaxies is a list
            self.galaxies = list(self.galaxies)

            # Include the new galaxies
            self.galaxies.extend(galaxies)

        # Count how many galaxies we have
        self.ngalaxies = len(self.galaxies)

    def convert_mag_depth_to_fnu0(self, redshift):
        """
        Converts depths defined in absolute magnitude to the units of
        luminosity (erg / s /Hz).
        This is a helpful wrapper to handle the use of different terminology in
        the SED object.
        Parameters
        ----------
        redshift : float
            The redshift of the observation.
        """
        self.convert_mag_depth_to_lnu(redshift, self.cosmo)

    def convert_mag_depth_to_lnu(self, redshift):
        """
        Converts depths defined in apparent magnitude to the units of
        luminosity (erg / s /Hz).
        Parameters
        ----------
        redshift : float
            The redshift of the observation.
        """

        # Convert the depths, looping over them if we have to.
        for inst in self.instruments:
            if isinstance(self.instruments[inst].depths, dict):
                for key in self.instruments[inst].depths:
                    flux = m_to_flux(self.instruments[inst].depths[key])
                    self.instruments[inst].depths[key] = flux_to_luminosity(
                        flux, self.cosmo, redshift
                    )
            else:
                flux = m_to_flux(self.instruments[inst].depths)
                self.instruments[inst].depths = flux_to_luminosity(
                    flux, self.cosmo, redshift
                )

    def convert_mag_depth_to_fnu(self):
        """
        Converts depths defined in apparent magnitude to the units of
        flux (nJy).
        """

        # Convert the depths, looping over them if we have to.
        for inst in self.instruments:
            if isinstance(self.instruments[inst].depths, dict):
                for key in self.instruments[inst].depths:
                    self.instruments[inst].depths[key] = m_to_flux(
                        self.instruments[inst].depths[key]
                    )
            else:
                self.instruments[inst].depths = m_to_flux(
                    self.instruments[inst].depths
                )

    def get_integrated_stellar_spectra(self, grid, redshift=None, igm=Inoue14):
        """
        Compute the integrated stellar spectra of each galaxy.

        Args:
        -----
        - grid (obj): synthesizer grid object
        - redshift (float): array of galaxy redshifts. If `None` (default),
                            all galaxies assumed to be in the rest frame
        - igm (obj): synthesizer IGM object, defaults to Inoue+14

        Returns:
        --------
        None
        """

        _specs = np.zeros((self.ngalaxies, grid.lam.size))

        for ind, gal in enumerate(self.galaxies):

            # Are we getting a flux or rest frame?
            _specs[ind, :] = gal.generate_intrinsic_spectra(
                grid, sed_object=False)

        # Create and store an SED object for these SEDs
        self.seds["stellar"] = Sed(lam=grid.lam, lnu=_specs)

        # Get the flux
        # TODO: if galaxies differ in redshift this does not work!
        # TODO: catch error if improper arguments are handed
        if redshift is None:
            self.seds["stellar"].get_fnu0()
        else:
            self.seds["stellar"].get_fnu(self.cosmo, redshift, igm)

    def get_integrated_spectra_screen(self, tauV, redshift=None,
                                      igm=None, name='attenuated'):
        """
        Compute the attenuated spectra of each galaxy using a dust screen model

        Args:
        -----
        - tauV (array, float): V-band optical depth
        - redshift (float): array of galaxy redshifts. If `None` (default),
                            all galaxies assumed to be in the rest frame
        - igm (obj): synthesizer IGM object, defaults to Inoue+14

        Returns:
        --------
        None
        """

        _lam = self.seds['stellar']._lam
        _specs = np.zeros((self.ngalaxies, _lam.size))

        for ind, gal in enumerate(self.galaxies):

            # Are we getting a flux or rest frame?
            _specs[ind, :] = gal.apply_screen(tauV, sed_object=False)

        # Create and store an SED object for these SEDs
        self.seds[name] = Sed(lam=_lam, lnu=_specs)

        # Get the flux
        # TODO: if galaxies differ in redshift this does not work!
        # TODO: catch error if improper arguments are handed
        if redshift is None:
            self.seds[name].get_fnu0()
        else:
            self.seds[name].get_fnu(self.cosmo, redshift, igm)

    def get_integrated_spectra_charlot_fall_00(self, grid, tauV_ISM, tauV_BC,
                                               redshift=None, igm=None,
                                               name='attenuated'):
        """
        Compute the attenuated spectra of each galaxy using a dust screen model

        Args:
        -----
        - grid (obj): synthesizer grid object
        - tauV_ISM (array): V-band optical depth in the interstellar medium
        - tauV_BC (array): birth cloud V-band optical depth
        - redshift (float): array of galaxy redshifts. If `None` (default),
                            all galaxies assumed to be in the rest frame
        - igm (obj): synthesizer IGM object, defaults to Inoue+14

        Returns:
        --------
        None
        """

        _specs = np.zeros((self.ngalaxies, grid.lam.size))

        for ind, gal in enumerate(self.galaxies):

            # Are we getting a flux or rest frame?
            _specs[ind, :] = gal.apply_charlot_fall_00(grid, tauV_ISM, tauV_BC,
                                                       sed_object=False)

        # Create and store an SED object for these SEDs
        self.seds[name] = Sed(lam=grid.lam, lnu=_specs)

        # Get the flux
        # TODO: if galaxies differ in redshift this does not work!
        # TODO: catch error if improper arguments are handed
        if redshift is None:
            self.seds[name].get_fnu0()
        else:
            self.seds[name].get_fnu(self.cosmo, redshift, igm)

    def get_particle_stellar_spectra(self, grid, redshift=None, igm=None):
        """
        Compute the integrated stellar spectra of each galaxy.
        """

        for ind, gal in enumerate(self.galaxies):

            # Are we getting a flux or rest frame?
            sed = gal.generate_intrinsic_particle_spectra(grid,
                                                          sed_object=True)
            gal.spectra_array["stellar"] = sed

            # Get the flux
            # TODO: catch error if improper arguments are handed
            if redshift is None:
                gal.spectra_array["stellar"].get_fnu0()
            else:
                gal.spectra_array["stellar"].get_fnu(
                    self.cosmo, redshift, igm)
            # do we want to use redshift defined on the galaxy object?
            # need to update a lot of things to check this (and alow override)
            #         self.cosmo, gal.redshift, igm)

    def get_photometry(self, spectra_type, redshift=None, igm=None):
        """
        Parameters
        ----------
        """

        # We need to handle whether different types of spectra exist.
        if spectra_type == "intrinsic":
            pass
        elif spectra_type == "stellar":
            pass
        elif spectra_type == "attenuated":
            pass
            # raise exceptions.UnimplementedFunctionality(
            #     "Attenuated spectra coming soon!"
            # )
        else:
            # TODO: make a UnknownSpectralType error
            raise exceptions.InconsistentArguments(
                "Unrecognised spectra_type!")

        # Loop over each instrument
        for key in self.instruments:

            _photometry = self.seds[spectra_type].\
                get_broadband_fluxes(self.instruments[key].filters)

            for _k, _v in _photometry.items():
                self.photometry[_k] = _v

            # Loop over filters in this instrument
            # for f in self.instruments[key].filters:
            #
            #    # Make an entry in the photometry dictionary for this filter
            #    self.photometry[f.filter_code] = f.apply_filter(
            #        self.seds[spectra_type]._fnu,
            #        xs=self.seds[spectra_type].nuz
            #    )

        return self.photometry

    def make_field_image(self, centre):
        """
        Parameters
        ----------
        """
        pass

    def make_images(
            self,
            img_type,
            spectra_type,
            kernel_func=None,
            rest_frame=False,
            cosmo=None,
            igm=None,
    ):
        """
        Parameters
        ----------
        """

        # Make a dictionary in which to store our image objects, within
        # this dictionary imgs are stored in list ordered by galaxy.
        self.imgs = {}

        # Loop over instruments and make images for each galaxy using each
        # instrument
        for key in self.instruments:

            # Extract the instrument
            inst = self.instruments[key]

            # Create entry in images dictionary
            self.imgs[inst] = []

            # Loop over galaxies
            for gal in self.galaxies:

                # Get images of this galaxy with this instrument
                img = gal.make_image(
                    inst.resolution,
                    fov=self.fov,
                    img_type=img_type,
                    sed=gal.spectra_array[spectra_type],
                    filters=inst.filters,
                    psfs=inst.psfs,
                    depths=inst.depths,
                    aperture=inst.aperture,
                    snrs=inst.snrs,
                    kernel_func=kernel_func,
                    rest_frame=rest_frame,
                    cosmo=cosmo,
                    igm=igm,
                    super_resolution_factor=self.super_resolution_factor,
                )

                # Store this result
                self.imgs[inst].append(img)

        return self.imgs

    def make_field_ifu(self, centre):
        """
        Parameters
        ----------
        """
        pass

    def make_ifus(self):
        """
        Parameters
        ----------
        """
        pass
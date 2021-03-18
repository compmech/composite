"""
Composites Core Utils Module (:mod:`composites.utils`)
==============================================================

.. currentmodule:: composites.utils

"""
import numpy as np

from .core import (MatLamina, Lamina, Laminate, LaminationParameters,
        laminate_from_lamination_parameters)

def read_laminaprop(laminaprop, rho=0):
    """Returns a :class:`.MatLamina` object based on an input ``laminaprop`` tuple

    Parameters
    ----------
    laminaprop : list or tuple
        Tuple containing the folliwing entries:

            (e1, e2, nu12, g12, g13, g23, e3, nu13, nu23)

        for othotropic materials the user can only supply:

            (e1, e2, nu12, g12, g13, g23)

        for isotropic materials the user can only supply:

            (e, nu) # new

            (e1, e2, nu12) # legacy, kept for compatibility with old codes

        ======  ==============================
        symbol  value
        ======  ==============================
        e1      Young Module in direction 1
        e2      Young Module in direction 2
        nu12    12 Poisson's ratio
        g12     12 Shear Modulus
        g13     13 Shear Modulus
        g23     13 Shear Modulus
        e3      Young Module in direction 3
        nu13    13 Poisson's ratio
        nu23    23 Poisson's ratio
        ======  ==============================


    rho : float, optional
        Material density


    Returns
    -------
    matlam : MatLamina
        A :class:`.MatLamina` object.

    """
    matlam = MatLamina()

    #laminaProp = (e1, e2, nu12, g12, g13, g23, e3, nu13, nu23)
    if laminaprop == None:
        raise ValueError('laminaprop must be a tuple')
    if len(laminaprop) == 3: #ISOTROPIC legacy
        e = laminaprop[0]
        nu = laminaprop[2]
        g = e/(2*(1+nu))
        laminaprop = (e, e, nu, g, g, g, e, nu, nu)
    if len(laminaprop) == 2: #ISOTROPIC new
        e = laminaprop[0]
        nu = laminaprop[1]
        g = e/(2*(1+nu))
        laminaprop = (e, e, nu, g, g, g, e, nu, nu)
    nu12 = laminaprop[2]
    if len(laminaprop) < 9:
        e2 = laminaprop[1]
        laminaprop = tuple(list(laminaprop)[:6] + [e2, nu12, nu12])
    matlam.e1 = laminaprop[0]
    matlam.e2 = laminaprop[1]
    matlam.e3 = laminaprop[6]
    matlam.nu12 = laminaprop[2]
    matlam.nu13 = laminaprop[7]
    matlam.nu23 = laminaprop[8]
    matlam.nu21 = matlam.nu12 * matlam.e2 / matlam.e1
    matlam.nu31 = matlam.nu13 * matlam.e3 / matlam.e1
    matlam.nu32 = matlam.nu23 * matlam.e3 / matlam.e2
    matlam.g12 = laminaprop[3]
    matlam.g13 = laminaprop[4]
    matlam.g23 = laminaprop[5]
    matlam.rho = rho
    matlam.rebuild()

    return matlam


def laminated_plate(stack, plyt=None, laminaprop=None, rho=0., plyts=None, laminaprops=None,
        rhos=None, offset=0., calc_scf=True):
    """Read a laminate stacking sequence data.

    :class:`.Laminate` object is returned based on the inputs given.

    Parameters
    ----------
    stack : list
        Angles of the stacking sequence in degrees.
    plyt : float, optional
        When all plies have the same thickness, ``plyt`` can be supplied.
    laminaprop : tuple, optional
        When all plies have the same material properties, ``laminaprop``
        can be supplied.
    rho : float, optional
        Uniform material density to be used for all plies.
    plyts : list, optional
        A list of floats with the thickness of each ply.
    laminaprops : list, optional
        A list of tuples with a laminaprop for each ply.
    rhos : list, optional
        A list of floats with the material density of each ply.
    offset : float, optional
        Offset along the normal axis about the mid-surface, which influences
        the laminate properties.
    calc_scf : bool, optional
        If True, use :func:`.Laminate.calc_scf` to compute shear correction
        factors, otherwise the default value of 5/6 is used

    Notes
    -----
    ``plyt`` or ``plyts`` must be supplied
    ``laminaprop`` or ``laminaprops`` must be supplied

    For orthotropic plies, the ``laminaprop`` should be::

        laminaprop = (E11, E22, nu12, G12, G13, G23)

    For isotropic plies, the ``laminaprop`` should be::

        laminaprop = (E, nu)

    """
    lam = Laminate()
    lam.offset = offset
    lam.stack = stack

    if plyts is None:
        if plyt is None:
            raise ValueError('plyt or plyts must be supplied')
        else:
            plyts = [plyt for i in stack]

    if laminaprops is None:
        if laminaprop is None:
            raise ValueError('laminaprop or laminaprops must be supplied')
        else:
            laminaprops = [laminaprop for i in stack]

    if rhos is None:
        rhos = [rho for i in stack]

    plies = []
    for plyt, laminaprop, theta, rho in zip(plyts, laminaprops, stack, rhos):
        laminaprop = laminaprop
        ply = Lamina()
        ply.theta = float(theta)
        ply.h = plyt
        ply.matlamina = read_laminaprop(laminaprop, rho)
        plies.append(ply)
    lam.plies = plies

    lam.rebuild()
    lam.calc_constitutive_matrix()
    if calc_scf:
        lam.calc_scf()

    return lam


def isotropic_plate(thickness, E, nu, offset=0., calc_scf=True):
    """Read data for an isotropic plate

    :class:`.Laminate` object is returned based on the inputs given.

    Parameters
    ----------
    thickness : float
        Plate thickness.
    E : float
        Young modulus.
    nu : float, optional
        Poisson's ratio.
    offset : float, optional
        Offset along the normal axis about the mid-surface, which influences
        the extension-bending coupling (B matrix).
    calc_scf : bool, optional
        If True, use :func:`.Laminate.calc_scf` to compute shear correction
        factors, otherwise the default value of 5/6 is used.

    """
    return laminated_plate(plyt=thickness, stack=[0], laminaprop=(E, nu),
            offset=offset, calc_scf=calc_scf)



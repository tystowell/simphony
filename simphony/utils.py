# Copyright © Simphony Project Contributors
# Licensed under the terms of the MIT License
# (see simphony/__init__.py for details)

"""
This package contains handy functions useful across simphony submodules
and to the average user.
"""

import re
import warnings
from types import SimpleNamespace

from scipy.constants import c as SPEED_OF_LIGHT
from scipy.interpolate import interp1d

try:
    import jax
    import jax.numpy as jnp

    JAX_AVAILABLE = True
except ImportError:
    import numpy as jnp

    def jit(func, *args, **kwargs):
        """Mock "jit" version of a function. Warning is only raised once."""
        warnings.warn("Jax not available, cannot compile using 'jit'!")
        return func

    jax = SimpleNamespace(jit=jit)
    JAX_AVAILABLE = False


MATH_SUFFIXES = {
    "f": "e-15",
    "p": "e-12",
    "n": "e-9",
    "u": "e-6",
    "m": "e-3",
    "c": "e-2",
    "k": "e3",
    "M": "e6",
    "G": "e9",
    "T": "e12",
}


def rect(r, phi) -> jnp.ndarray:
    """
    Convert from polar to rectangular coordinates element-wise.

    Parameters
    ----------
    r : np.ndarray
        The real radii of the complex-valued numbers.
    phi : np.ndarray
        The real phase of the complex-valued numbers.

    Returns
    -------
    np.ndarray
        An array of complex-valued numbers.
    """
    return r * jnp.exp(1j * phi)


def polar(x) -> jnp.ndarray:
    """
    Convert from rectangular to polar coordinates element-wise.

    Parameters
    ----------
    x : np.ndarray
        Array of potentially complex-valued numbers.

    Returns
    -------
    mag, phi
        A tuple of arrays where the first is the element-wise magnitude of the
        argument and the second is the element-wise phase of the argument.
    """
    return jnp.abs(x), jnp.angle(x)


def add_polar(c1, c2):
    """Adds two polar coordinates together.

    Parameters
    ----------
    c1 : (float, float)
        First polar coordinate
    c2 : (float, float)
        Second polar coordinate

    Returns
    -------
    result : (float, float)
        The resulting polar coordinate"""
    r1, phi1 = c1
    r2, phi2 = c2

    # add the vectors in rectangular form
    sum = rect(r1, phi1) + rect(r2, phi2)
    mag = jnp.abs(sum)
    angle = jnp.angle(sum)

    # calculate how many times the original vectors wrapped around
    # then add the biggest amount back to our phase
    # this simulates the steady-state in time-domain
    wrapped1 = (phi1 // (2 * jnp.pi)) * (2 * jnp.pi)
    wrapped2 = (phi2 // (2 * jnp.pi)) * (2 * jnp.pi)
    biggest = max(wrapped1, wrapped2)

    return (mag, angle + biggest)


def mul_polar(c1, c2):
    """Multiplies two polar coordinates together.

    Parameters
    ----------
    c1 : (float, float)
        First polar coordinate
    c2 : (float, float)
        Second polar coordinate

    Returns
    -------
    result : (float, float)
        The resulting polar coordinate"""
    r1, phi1 = c1
    r2, phi2 = c2

    return (r1 * r2, phi1 + phi2)

def mat_mul_polar(array1: jnp.array, array2: jnp.array) -> jnp.array:
    """Multiplies two polar matrixes together
    
    Parameters
    ----------
    array1 : ndarray
    array2 : ndarray
    
    the arrays can be one of the following possiblities:
    #f x n x n x m1 x m2 x 2
    #f x n x n x m1 x m2 x 1
    #f x n x n x m1 x 2 
    #f x n x n x m1 x 1    
    #f x n x n x m2 x 2 
    #f x n x n x m2 x 1
    f x n x n x 2
    f x n x n
    f is the frequency dimension
    n is the number of ports
    m1 is the number of TE modes
    m2 is the number of TM modes 
    The last number of dimensions is 2 if polar and 1 if rectangular.
    Complex rectangular data is of the form a + bj
    Complex polar data is of the form [r, theta]   
    """
    # array1 and 2 should be identical in dimensions
    if jnp.shape(array1) != jnp.shape(array2):
        raise RuntimeError("Arrays must be the same shape to matrix multiply them")    
    
       
    #polar: multiply magnitudes, add angles, or convert to rectangular and call this function
    if jnp.shape(array1)[-1] == 2:
        real1 = array1[..., 0]
        imag1 = array1[..., 1]    
        real2 = array2[..., 0]
        imag2 = array2[..., 1]
        rect1 = rect(real1, imag1)
        rect2 = rect(real2, imag2)
        # return real1*real2+imag1+imag2
        return mat_mul_polar(rect1, rect2)

    #rectangular: simply multiply them
    return array1*array2

def mat_add_polar(array1: jnp.array, array2: jnp.array) -> jnp.array:
    """Adds two polar matrixes together
    
    Parameters
    ----------
    array1 : ndarray
    array2 : ndarray
    
    the arrays can be one of the following possiblities:
    f x n x n x m1 x m2 x 2
    f x n x n x m1 x m2 x 1
    f x n x n x m1 x 2 
    f x n x n x m1 x 1    
    f x n x n x m2 x 2 
    f x n x n x m2 x 1
    f is the frequency dimension
    n is the number of ports
    m1 is the number of TE modes
    m2 is the number of TM modes 
    The last number of dimensions is 2 if polar and 1 if rectangular.
    Complex rectangular data is of the form a + bj
    Complex polar data is of the form [r, theta]   
    """
    # array1 and 2 should be identical in dimensions
    if jnp.shape(array1) != jnp.shape(array2):
        raise RuntimeError("Arrays must be the same shape to matrix multiply them")
    
    #polar: convert to rectangular, then return this function 
    if jnp.shape(array1)[-1] == 2:
        real1 = array1[..., 0]
        imag1 = array1[..., 1]    
        real2 = array2[..., 0]
        imag2 = array2[..., 1]
        rect1 = rect(real1, imag1)
        rect2 = rect(real2, imag2)
        return mat_add_polar(rect1, rect2)
    
    #rectangular: simply add them
    return array1+array2


def str2float(num):
    """Converts a number represented as a string to a float. Can include
    suffixes (such as 'u' for micro, 'k' for kilo, etc.).

    Parameters
    ----------
    num : str
        A string representing a number, optionally with a suffix.

    Returns
    -------
    float
        The string converted back to its floating point representation.

    Raises
    ------
    ValueError
        If the argument is malformed or the suffix is not recognized.

    Examples
    --------
    >>> str2float('14.5c')
    0.145

    Values without suffixes get converted to floats normally.

    >>> str2float('2.53')
    2.53

    If an unrecognized suffix is present, a ``ValueError`` is raised.

    >>> str2float('17.3o')
    ValueError: Suffix 'o' in '17.3o' not recognized.
    ([-+]?[0-9]+[.]?[0-9]*((?:[eE][-+]?[0-9]+)|[a-zA-Z])?)

    Some floats are represented in exponential notation instead of suffixes,
    and we can handle those, too:

    >>> str2float('15.2e-6')
    1.52e-7

    >>> str2float('0.4E6')
    400000.0
    """
    matches = re.findall(
        r"([-+]?[0-9]+(?:[.][0-9]+)?)((?:[eE][-+]?[0-9]+)|(?:[a-zA-Z]))?", num
    )
    if len(matches) > 1:
        raise ValueError("'{}' is malformed".format(num))
    num, suffix = matches[0]
    try:
        if suffix.startswith("e") or suffix.startswith("E"):
            return float(num + suffix)
        else:
            return float(num + (MATH_SUFFIXES[suffix] if suffix != "" else ""))
    except KeyError as e:
        raise ValueError("Suffix {} in '{}' not recognized.".format(str(e), matches[0]))


def freq2wl(freq):
    """Convenience function for converting from frequency to wavelength.

    Parameters
    ----------
    freq : float
        The frequency in SI units (Hz).

    Returns
    -------
    wl : float
        The wavelength in SI units (m).
    """
    return SPEED_OF_LIGHT / freq


def wl2freq(wl):
    """Convenience function for converting from wavelength to frequency.

    Parameters
    ----------
    wl : float
        The wavelength in SI units (m).

    Returns
    -------
    freq : float
        The frequency in SI units (Hz).
    """
    return SPEED_OF_LIGHT / wl


def wlum2freq(wl):
    """Convenience function for converting from wavelength in microns to
    frequency.

    Parameters
    ----------
    wl : float
        The wavelength in microns.

    Returns
    -------
    freq : float
        The frequency in SI units (Hz).
    """
    return wl2freq(wl * 1e-6)


def interpolate(resampled, sampled, s_parameters):
    """Returns the result of a cubic interpolation for a given frequency range.

    Parameters
    ----------
    output_freq : jnp.ndarray
        The desired frequency range for a given input to be interpolated to.
    input_freq : jnp.ndarray
        A frequency array, indexed matching the given s_parameters.
    s_parameters : jnp.array
        S-parameters for each frequency given in input_freq.

    Returns
    -------
    result : jnp.array
        The values of the interpolated function (fitted to the input
        s-parameters) evaluated at the ``output_freq`` frequencies.
    """
    func = interp1d(sampled, s_parameters, kind="cubic", axis=0)
    return func(resampled)

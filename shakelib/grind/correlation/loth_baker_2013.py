import numpy as np
from scipy.interpolate import RectBivariateSpline
import numexpr as ne

Tlist = np.array([0.01, 0.1, 0.2, 0.5, 1, 2, 5, 7.5, 10.0001])

# Table II. Short range coregionalization matrix, B1
B1 = np.array([
    [0.30, 0.24, 0.23, 0.22, 0.16, 0.07, 0.03, 0, 0],
    [0.24, 0.27, 0.19, 0.13, 0.08, 0, 0, 0, 0],
    [0.23, 0.19, 0.26, 0.19, 0.12, 0.04, 0, 0, 0],
    [0.22, 0.13, 0.19, 0.32, 0.23, 0.14, 0.09, 0.06, 0.04],
    [0.16, 0.08, 0.12, 0.23, 0.32, 0.22, 0.13, 0.09, 0.07],
    [0.07, 0, 0.04, 0.14, 0.22, 0.33, 0.23, 0.19, 0.16],
    [0.03, 0, 0, 0.09, 0.13, 0.23, 0.34, 0.29, 0.24],
    [0, 0, 0, 0.06, 0.09, 0.19, 0.29, 0.30, 0.25],
    [0, 0, 0, 0.04, 0.07, 0.16, 0.24, 0.25, 0.24]
    ])

# Table III. Long range coregionalization matrix, B2
B2 = np.array([
    [0.31, 0.26, 0.27, 0.24, 0.17, 0.11, 0.08, 0.06, 0.05],
    [0.26, 0.29, 0.22, 0.15, 0.07, 0, 0, 0, -0.03],
    [0.27, 0.22, 0.29, 0.24, 0.15, 0.09, 0.03, 0.02, 0],
    [0.24, 0.15, 0.24, 0.33, 0.27, 0.23, 0.17, 0.14, 0.14],
    [0.17, 0.07, 0.15, 0.27, 0.38, 0.34, 0.23, 0.19, 0.21],
    [0.11, 0, 0.09, 0.23, 0.34, 0.44, 0.33, 0.29, 0.32],
    [0.08, 0, 0.03, 0.17, 0.23, 0.33, 0.45, 0.42, 0.42],
    [0.06, 0, 0.02, 0.14, 0.19, 0.29, 0.42, 0.47, 0.47],
    [0.05, -0.03, 0, 0.14, 0.21, 0.32, 0.42, 0.47, 0.54]
    ])

# Table IV. Nugget effect coregionalization matrix, B3
B3 = np.array([
    [0.38, 0.36, 0.35, 0.17, 0.04, 0.04, 0, 0.03, 0.08],
    [0.36, 0.43, 0.35, 0.13, 0, 0.02, 0, 0.02, 0.08],
    [0.35, 0.35, 0.45, 0.11, -0.04, -0.02, -0.04, -0.02, 0.03],
    [0.17, 0.13, 0.11, 0.35, 0.2, 0.06, 0.02, 0.04, 0.02],
    [0.04, 0, -0.04, 0.20, 0.30, 0.14, 0.09, 0.12, 0.04],
    [0.04, 0.02, -0.02, 0.06, 0.14, 0.22, 0.12, 0.13, 0.09],
    [0, 0, -0.04, 0.02, 0.09, 0.12, 0.21, 0.17, 0.13],
    [0.03, 0.02, -0.02, 0.04, 0.12, 0.13, 0.17, 0.23, 0.10],
    [0.08, 0.08, 0.03, 0.02, 0.04, 0.09, 0.13, 0.10, 0.22]
    ])

class LothBaker2013(object):
    """
    Created by Christophe Loth, 12/18/2012
    Pythonized and vectorized by C. Bruce Worden, 3/15/2017
    Compute the spatial correlation of epsilons for the NGA ground motion models

    The function is strictly empirical, fitted over the range the range 0.01s <= t1, t2 <= 10s

    Documentation is provided in the following document:
    Loth, C., and Baker, J. W. (2013). “A spatial cross-correlation model of 
    ground motion spectral accelerations at multiple periods.” 
    Earthquake Engineering & Structural Dynamics, 42, 397-417.
    """
    def __init__(self):
        self.rbs1 = RectBivariateSpline(Tlist, Tlist, B1, kx=1, ky=1)
        self.rbs2 = RectBivariateSpline(Tlist, Tlist, B2, kx=1, ky=1)
        self.rbs3 = RectBivariateSpline(Tlist, Tlist, B3, kx=1, ky=1)
        return;


    def getCorrelation(self, t1, t2, h):
        """
        Args:
            t1, t2 (nd arrays):
                The two periods of interest. The periods may be equal,
                and there is no restriction on which one is larger.
            h (nd array):
                The separation distance between two sites (units of km)

            t1, t2, and h should have the same dimensions. If they don't, 
            the results will be unpredictable.

        Returns:
            rho (nd array):
                The predicted correlation coefficient

        """
        # Verify the validity of input arguments
        if np.any(t1 < 0.01) or np.any(t2 < 0.01):
            raise ValueError('The periods must be greater or equal to 0.01s')
        if np.any(t1 > 10) or np.any(t2 > 10):
            raise ValueError('The periods must be less or equal to 10s')
        if np.any(h < 0):
            raise ValueError('The separation distance must be positive')
        if np.shape(t1) != np.shape(t2) or np.shape(t1) != np.shape(h):
            raise ValueError('The input arguments must all have the same dimensions')

        # Linearly interpolate the corresponding value of each coregionalization
        # matrix coefficient
        # This is the slow part

        b1 = self.rbs1.ev(t1, t2)
        b2 = self.rbs2.ev(t1, t2)
        b3 = self.rbs3.ev(t1, t2)

        # Compute the correlation coefficient (Equation 42)
        # This is very fast

        rho = ne.evaluate("b1 * exp(-3 * h / 20) + b2 * exp(-3 * h / 70) + (h == 0) * b3")

        return rho

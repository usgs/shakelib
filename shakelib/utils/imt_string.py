#local imports
import re

#third party imports
import numpy as np

def oq_to_file(oqimt):
    """Convert openquake IMT nomenclature to filename friendly form.
    
    Examples:
    SA(1.0) (Spectral Acceleration at 1 second) -> PSA1p0
    SA(0.3) (Spectral Acceleration at 0.3 second) -> PSA0p3
    SA(15.0) (Spectral Acceleration at 15 seconds) -> PSA15p0
    SA(3) (Spectral Acceleration at 3 seconds) -> PSA3p0
    SA(.5) (Spectral Acceleration at 0.5 seconds) -> PSA0p5

    Args:
        oqimt (str): Openquake IMT nomenclature string.
    Returns:
        str: Filename friendly IMT string.
    """
    if oqimt in ['PGA','PGV','MMI']:
        return oqimt
    float_pattern = r"[-+]?\d*\.\d+|\d+"
    periods = re.findall(float_pattern,oqimt)
    if not len(periods):
        raise ValueError('IMT string "%s" has no corresponding file-name friendly representation.' % oqimt)
    period = periods[0]
    if period.find('.') < 0:
        integer = period
        fraction = '0'
    else:
        integer,fraction = period.split('.')
        if not len(integer):
            integer = '0'
    fileimt = 'PSA%sp%s' % (integer,fraction)
    return fileimt

def file_to_oq(fileimt):
    """Convert filename friendly IMT form to openquake form.
    
    Examples:
    PSA1p0 (Spectral Acceleration at 1 second) -> SA(1.0)
    PSA0p3 (Spectral Acceleration at 0.3 second) -> SA(0.3)
    PSA15p0 (Spectral Acceleration at 15 seconds) -> SA(15.0)

    Args:
        fileimt (str): Filename friendly IMT string.
    Returns:
        str: Openquake IMT nomenclature string.
    """
    if fileimt in ['PGA','PGV','MMI']:
        return fileimt
    integer,fraction = fileimt.replace('PSA','').split('p')
    oqimt = 'SA(%s.%s)' % (integer,fraction)
    return oqimt

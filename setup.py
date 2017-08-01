from distutils.core import setup
import os.path

VERSION = '0.1'

# comment
setup(name='shakelib',
      version=VERSION,
      description='USGS Near-Real-Time Ground Motion Mapping Library',
      author='Bruce Worden, Mike Hearne, Eric Thompson',
      author_email='cbworden@usgs.gov,mhearne@usgs.gov,emthompson@usgs.gov',
      url='http://github.com/usgs/shakelib',
      packages=['shakelib',
                'shakelib.grind',
                'shakelib.grind.conversions',
                'shakelib.grind.conversions.imc',
                'shakelib.grind.conversions.imt',
                'shakelib.grind.correlation',
                'shakelib.grind.directivity',
                'shakelib.grind.gmice',
                'shakelib.grind.gmpe_sets',
                'shakelib.plotting',
                'shakelib.utils',
                ],
      package_data={'shakelib': [os.path.join('test', 'data', '*'),
                                 os.path.join('grind', 'data', 'ps2ff', '*.csv')]},
      scripts=[],
      )

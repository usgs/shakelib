from distutils.core import setup
import os.path
import versioneer


# comment
setup(name='shakelib',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
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
                'shakelib.plotting',
                'shakelib.utils',
                ],
      package_data={'shakelib': [os.path.join('test', 'data', '*'),
                                 os.path.join('grind', 'data', 'ps2ff', '*.csv')]},
      scripts=[],
      )

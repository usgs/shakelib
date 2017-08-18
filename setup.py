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
                'shakelib.conversions',
                'shakelib.conversions.imc',
                'shakelib.conversions.imt',
                'shakelib.correlation',
                'shakelib.directivity',
                'shakelib.gmice',
                'shakelib.rupture',
                'shakelib.plotting',
                'shakelib.utils',
                ],
      package_data={'shakelib': [os.path.join('test', 'data', '*'),
                                 os.path.join('utils', 'data', '*'),
                                 os.path.join('rupture', 'ps2ff', '*.csv')]},
      scripts=[],
      )

#!/bin/bash
echo $PATH

VENV=shakelib2
PYVER=3.5


DEPARRAY=(numpy scipy matplotlib rasterio pandas shapely h5py gdal pytest pytest-cov pytest-mpl jupyter cartopy fiona pycrypto paramiko beautifulsoup4)

# turn off whatever other virtual environment user might be in
source deactivate

#remove any previous virtual environments called shakelib2
CWD=`pwd`
cd $HOME;
conda remove --name $VENV --all -y
cd $CWD

conda create --name $VENV --yes --channel conda-forge python=$PYVER ${DEPARRAY[*]} -y

# activate the new environment
source activate $VENV

# do pip installs of those things that are not available via conda.
#grab the bleeding edge for GEM hazardlib.  They have actual releases
#we can resort to if this becomes a problem.
curl --max-time 60 --retry 3 -L https://github.com/gem/oq-engine/archive/master.zip -o openquake.zip
pip -v install --no-deps openquake.zip
rm openquake.zip

pip -v install https://github.com/usgs/MapIO/archive/master.zip
pip -v install https://github.com/usgs/earthquake-impact-utils/archive/master.zip


# tell the user they have to activate this environment
echo "Type 'source activate $VENV' to use this new virtual environment."

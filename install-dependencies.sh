#!/bin/bash
echo $PATH

VENV=shakelib2
PYVER=3.5

# Is conda installed?
conda=$(which conda)
if [ ! "$conda" ] ; then
    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh;
    bash miniconda.sh -f -b -p $HOME/miniconda
    export PATH="$HOME/miniconda/bin:$PATH"
fi

conda update -q -y conda
conda config --prepend channels conda-forge
conda config --append channels digitalglobe # for rasterio v 1.0a9
conda config --append channels ioos # for rasterio v 1.0a2

unamestr=`uname`
if [[ "$unamestr" == 'Linux' ]]; then
    DEPARRAY=(numpy=1.11 scipy=0.19.1 matplotlib=2.0.2 rasterio=1.0a2 pandas=0.20.3 h5py=2.7.0 gdal=2.1.4 pytest=3.2.0 pytest-cov=2.5.1 cartopy=0.15.1 fiona=1.7.8 numexpr=2.6.2 configobj=5.0.6 decorator=4.1.2 versioneer==0.18)
elif [[ "$unamestr" == 'FreeBSD' ]] || [[ "$unamestr" == 'Darwin' ]]; then
   DEPARRAY=(numpy=1.13.1 scipy=0.19.1 matplotlib=2.0.2 rasterio=1.0a9 pandas=0.20.3 h5py=2.7.0 gdal=2.1.4 pytest=3.2.0 pytest-cov=2.5.1 cartopy=0.15.1 fiona=1.7.8 numexpr=2.6.2 configobj=5.0.6 decorator=4.1.2 versioneer==0.18)
fi

# Additional deps, not not needed for Travis
travis=0
while getopts t FLAG; do
  case $FLAG in
    t)
      travis=1
      ;;
  esac
done
if [ $travis == 0 ] ; then
    DEPARRAY+=(ipython=6.1.0 spyder=3.2.1-py35_0 jupyter=1.0.0 seaborn=0.8.0 sphinx=1.6.3)
fi

echo $DEPARRAY

# Turn off whatever other virtual environment user might be in
source deactivate

# Remove any previous virtual environments called shakelib2
CWD=`pwd`
cd $HOME;
conda remove --name $VENV --all -y
cd $CWD

conda create --name $VENV -y python=$PYVER ${DEPARRAY[*]}

# Activate the new environment
source activate $VENV

# OpenQuake v2.5.0
curl --max-time 60 --retry 3 -L https://github.com/gem/oq-engine/archive/v2.5.0.zip -o openquake.zip
pip -v install --no-deps openquake.zip
rm openquake.zip

pip -v install https://github.com/usgs/MapIO/archive/master.zip
pip -v install https://github.com/usgs/earthquake-impact-utils/archive/master.zip


# Tell the user they have to activate this environment
echo "Type 'source activate $VENV' to use this new virtual environment."

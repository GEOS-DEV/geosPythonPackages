#!/bin/bash
python -m pip install --upgrade ./geos-utils
python -m pip install --upgrade ./geos-geomechanics
python -m pip install --upgrade ./geos-mesh
python -m pip install --upgrade ./geos-posp
python -m pip install --upgrade ./geos-xml-tools
python -m pip install --upgrade ./hdf5-wrapper
python -m pip install --upgrade ./geos-timehistory
python -m pip install --upgrade ./pygeos-tools
python -m pip install --upgrade ./geos-pv
#! trame install requires npm
cd ./geos-trame/vue-components
npm i
npm run build
cd ../../
python -m pip install ./geos-trame
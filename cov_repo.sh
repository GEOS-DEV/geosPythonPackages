#!/bin/bash

python -m pytest --cov=./geos-utils/src/geos/utils geos-utils --cov-report markdown-append:cov.md --cov-config=.coveragerc

python -m pytest --cov=./geos-geomechanics/src/geos/geomechanics geos-geomechanics --cov-report markdown-append:cov.md --cov-config=.coveragerc

python -m pytest --cov=./geos-mesh/src/geos/mesh geos-mesh --cov-report markdown-append:cov.md --cov-config=.coveragerc

python -m pytest --cov=./geos-processing/src/geos/processing geos-processing --cov-report markdown-append:cov.md --cov-config=.coveragerc



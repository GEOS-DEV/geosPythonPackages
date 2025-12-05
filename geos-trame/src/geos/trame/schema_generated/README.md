# Schema Generation

This folder contains auto-generated file based on an xsd file from the GEOS repository.

We should not modify manually these files.

## Context

Input files from GEOS are described as an xml which follow a specific schema. To be able
to parse, serialize and deserialize these files in trame with `trame-simput`, we need to
generate a serializable class for each balise described in the schema used by GEOS.

For that we use a python module named `xsd-pydantic` which allows us to generate a file.
It will contain all class for a given xsd schema file.

When starting the trame application, we can instantiate the expected dataclass when parsing
the input file.

## How to generate a new file

#### 1. Get GEOS validation schema file
First, retrieve the `schema.xsd` corresponding to the GEOS version you want to use.

> [!WARNING]
> We advise to use GEOS version from commit [#1e617be](https://github.com/GEOS-DEV/GEOS/commit/1e617be8614817d92f0a7a159994cbed1661ff98). You may encounter compatibility issues with older versions.


The schema can be generated with the following command line with GEOS:
```bash
geos -s schema.xsd
```

Or it can be found in [GEOS Github repository](https://github.com/GEOS-DEV/GEOS). The schema can be found in `GEOS/src/coreComponents/schema/schema.xsd`.

Copy this file and paste in the `geosPythonPackages`:

```bash
cp schema.xsd geosPythonPackages/geos-trame/src/geos/trame/schema_generated/.
```

#### 2. Create a dedicate venv

```bash
cd geos-trame
python -m venv pydantic-venv
source pydantic-venv/bin/activate
pip install -e .
pip install "xsdata[cli]"
```

#### 3. Generate the new file

The full documentation is [here](https://xsdata-pydantic.readthedocs.io/en/latest/codegen/).


```bash
cd src/geos/trame/schema_generated
python generate_schema.py -v <GEOS-commit>
```

Check the options with `--help` parameters:

```bash
$ python generate_schema.py

usage: generate_schema.py [-h] [-s SCHEMAFILE] [-cf CONFIGFILE] [-v VERSION]

Generate schema from schema.xsd file

options:
  -h, --help            show this help message and exit
  -s SCHEMAFILE, --schemaFile SCHEMAFILE
                        Filepath to GEOS schema file.
  -cf CONFIGFILE, --configFile CONFIGFILE
                        Filepath to xml configuration file for schema generation.
  -v VERSION, --version VERSION
                        GEOS commit sha or version identification.
```
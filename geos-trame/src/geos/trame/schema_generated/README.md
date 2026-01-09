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

First, retrieve the `schema.xsd` corresponding to the GEOS version you want to use.

> [!WARNING]
> We advise to use GEOS version from commit [#1e617be](https://github.com/GEOS-DEV/GEOS/commit/1e617be8614817d92f0a7a159994cbed1661ff98). You may encounter compatibility issues with older versions.

In a sourced virtual environement set for geos_trame,

```bash
(venv) cd geosPythonPackages/geos-trame/src/geos/trame/schema_generated
(venv) python generate_schema.py -g
(venv) mv schema_<GEOS-commit-sha>.xsd schema.xsd
(venv) python generate_schema.py -v <GEOS-commit-sha>
```

This two stage approach is defaulted:

 1. To take the latest commit on GEOS' `develop`. However, if a particular commit on `develop` is of interest,
you can pass it through the option `-c <GEOS-commit-sha>`. It will generate `schema_<GEOS-commit-sha>.xsd`.
 2. To generate the `schema_mod.py` packages, metadata-ing the commit number in the header.

In any other case, `schema.xsd` can be found in [GEOS Github repository](https://github.com/GEOS-DEV/GEOS) under `GEOS/src/coreComponents/schema/schema.xsd`
and the first step can be skipped.

The second stage relies on `xsdata[cli]` interfaced with `pydantic` as driver.
The full documentation can be found [here](https://xsdata-pydantic.readthedocs.io/en/latest/codegen/).

Options to the helper script can be displayed with `--help` parameters:

```bash
$ python generate_schema.py --help

Generate schema from schema.xsd file

optional arguments:
  -h, --help            show this help message and exit
  -g, --get-schema      Get the latest schema files.
  -c COMMIT, --commit COMMIT
                        Force a specific GEOS develop's commit for schema
                        download
  -s SCHEMAFILE, --schemaFile SCHEMAFILE
                        Filepath to GEOS schema file.
  -cf CONFIGFILE, --configFile CONFIGFILE
                        Filepath to xml configuration file for schema
                        generation.
  -v VERSION, --version VERSION
                        GEOS commit sha or version identification.
```
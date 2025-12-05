import argparse
import datetime
import os
import subprocess
import sys


def generateFileFromSchema():
    p = argparse.ArgumentParser(
        description="Generate schema from schema.xsd file"
    )
    p.add_argument(
        "-s",
        "--schemaFile",
        dest="schemaFile",
        type=str,
        default="./schema.xsd",
        help="Filepath to GEOS schema file.",
    )
    p.add_argument(
        "-cf",
        "--configFile",
        dest="configFile",
        type=str,
        default="./config_schema.xml",
        help="Filepath to xml configuration file for schema generation.",
    )
    p.add_argument(
        "-v",
        "--version",
        dest="version",
        type=str,
        default="",
        help="GEOS commit sha or version identification.",
    )

    pp, _ = p.parse_known_args()

    run_process_Xsdata(pp.schemaFile, pp.configFile)
    addHeader(pp.version)
    cleanInit()


def run_process_Xsdata(schemaXSDFile, XmlconfigFile):
    result = subprocess.Popen(
        [
            "xsdata",
            "generate",
            schemaXSDFile,
            "--config",
            XmlconfigFile,
        ],
    )
    if result.wait() != 0:
        raise RunTimeError(
            "Something went wrong with the schema generation. Please check parameters."
        )


def cleanInit():
    root = os.getcwd()

    for dirpath, _, filenames in os.walk(root):
        if "__init__.py" in filenames:
            init_file = os.path.join(dirpath, "__init__.py")
            with open(init_file, "w") as f:
                f.write("")
            print(f"Cleaned {init_file}")


def addHeader(sha: str = "", generatedschemaFile="schema_mod.py"):
    """Manually insert a header containing datetime information and GEOS commit version if provided.

    Args:
        sha(str, optional): commit sha or GEOS version. Default is empty string.
    """
    head = f"""#------------------------------------------------------------------
#
#  Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
#  GEOS version: {sha}
#
#-------------------------------------------------------------------\n"""

    try:
        with open("schema_mod.py", "r") as f:
            schema = f.read()

        with open("schema_mod.py", "w") as g:
            g.write(head)
            g.write(schema)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    generateFileFromSchema()

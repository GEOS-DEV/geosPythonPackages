import argparse
import datetime
import os
import subprocess

import requests


def get_schema( commit_sha: str ) -> None:
    """Fetch a file's raw bytes from a GitHub repository using the REST contents API."""
    #  curl -s -H "Accept: application/vnd.github.raw+json" "https://api.github.com/repos/GEOS-DEV/GEOS/contents/src/coreComponents/schema/schema.xsd?ref={8be64fb}" > schema_.xsd
    owner: str = "GEOS-DEV"
    repo: str = "GEOS"
    path: str = "src/coreComponents/schema/schema.xsd"

    base = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    params = {}
    if commit_sha:
        params[ "ref" ] = commit_sha

    headers = {
        # Ask for raw bytes for files/symlinks
        "Accept": "application/vnd.github.raw+json",
        # Recommended API version header
        "X-GitHub-Api-Version": "2022-11-28",
        # Set a UA; some endpoints prefer one
        "User-Agent": "xsdata-helper-script/1.0",
    }

    # Stream response to avoid loading large files entirely in memory
    with requests.get( base, headers=headers, params=params, stream=True, timeout=60 ) as resp:
        # Common errors: 403/404 when token missing/insufficient or path not found
        if resp.status_code != 200:
            raise RuntimeError( f"GitHub API error {resp.status_code}: {resp.text[:500]}" )
        # Choose output filename
        out_path = f"schema_{commit_sha[:6]}.xsd"
        # Ensure parent directory exists
        os.makedirs( os.path.dirname( out_path ) or ".", exist_ok=True )
        # Write in chunks
        with open( out_path, "wb" ) as f:
            for chunk in resp.iter_content( chunk_size=1024 * 64 ):
                if chunk:
                    f.write( chunk )
    return


def latest_commits( n: int ) -> list:
    """Return the latest `n` commits on `branch` from the given GitHub repo."""
    owner: str = "GEOS-DEV"
    repo: str = "GEOS"
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = { "sha": "develop", "per_page": n }
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "commit-fetch-script/1.0",
    }

    resp = requests.get( url, params=params, headers=headers, timeout=30 )
    resp.raise_for_status()
    commits = resp.json()

    # Return a simplified view: sha, message, author date
    return [ {
        "sha": c[ "sha" ],
        "message": c[ "commit" ][ "message" ].splitlines()[ 0 ],
        "author_date": c[ "commit" ][ "author" ][ "date" ],
        "html_url": c[ "html_url" ],
    } for c in commits ]


def generateFileFromSchema() -> None:
    """Generate pydantic file from xsd file with a parser."""
    p = argparse.ArgumentParser( description="Generate schema from schema.xsd file" )

    p.add_argument(
        "-g",
        "--get-schema",
        action="store_true",
        help="Get the latest schema files.",
    )

    p.add_argument(
        "-c",
        "--commit",
        type=str,
        help="Force a specific GEOS develop's commit for schema download",
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

    if pp.get_schema:
        if pp.commit:
            get_schema( pp.commit )
        else:
            commits = latest_commits( 1 )
            for commit in commits:
                get_schema( commit[ "sha" ] )
    else:
        run_process_Xsdata( pp.schemaFile, pp.configFile )
        addHeader( pp.version )
        cleanInit()


def run_process_Xsdata( schemaXSDFile: str, XmlConfigFile: str ) -> None:
    """Launch the subprocess that run xsdata-pydantic to generate the file from the schema XSD file.

    Args:
        schemaXSDFile(str): Filepath to GEOS XSD file.
        XmlConfigFile(str): Filepath to xsdata configuration file.

    Raises:
        RuntimeError: Error encountered during the subprocess run.
    """
    result = subprocess.Popen( [
        "xsdata",
        "generate",
        schemaXSDFile,
        "--config",
        XmlConfigFile,
    ], )
    if result.wait() != 0:
        raise RuntimeError( "Something went wrong with the schema generation. Please check parameters." )


def cleanInit() -> None:
    """Manually clean the modifications to __init__ files done during xsdata process."""
    root: str = os.getcwd()

    for dirpath, _, filenames in os.walk( root ):
        if "__init__.py" in filenames:
            init_file = os.path.join( dirpath, "__init__.py" )
            with open( init_file, "w" ) as f:
                f.write( "" )
            print( f"Cleaned {init_file}" )


def addHeader( sha: str = "", generatedSchemaFile: str = "schema_mod.py" ) -> None:
    """Manually insert a header containing datetime information and GEOS commit version if provided to the file generated by xsdata previously.

    Args:
        sha(str, optional): commit sha or GEOS version. Default is empty string.
        generatedSchemaFile(str, optional): Name of the file generated.
    """
    head: str = f"""#------------------------------------------------------------------
#
#  Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
#  GEOS version: {sha}
#
#-------------------------------------------------------------------\n\n
# ruff: noqa\n"""

    try:
        with open( generatedSchemaFile, "r" ) as f:
            schema: str = f.read()

        with open( generatedSchemaFile, "w" ) as g:
            g.write( head )
            g.write( schema )

    except Exception as e:
        print( e )


if __name__ == "__main__":
    generateFileFromSchema()

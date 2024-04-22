from dataclasses import dataclass
from pathlib import Path
from git import Repo
import logging
import os
from datetime import datetime
from configparser import ConfigParser


@dataclass
class GitHistory:
    commit: str
    author: str
    email: str


git_history = GitHistory( '', '', '' )
logger = logging.getLogger( 'geos_ats' )


def check_git_history( bin_dir ):
    git_dir = Path( bin_dir ).resolve().parents[ 1 ]
    try:
        r = Repo( git_dir )
        c = r.head.commit
        git_history.commit = c.hexsha
        git_history.author = c.author.name
        git_history.email = c.author.email
    except Exception as e:
        logger.error( repr( e ) )
        logger.error( 'Failed to parse GEOS git history' )


def write_baseline_log( fname ):
    configParser = ConfigParser()
    configParser.add_section( "baseline" )
    configParser.set( "baseline", "commit", git_history.commit )
    configParser.set( "baseline", "author", git_history.author )
    configParser.set( "baseline", "email", git_history.email )
    configParser.set( "baseline", "date", datetime.now().strftime( "%m/%d/%Y" ) )

    os.makedirs( os.path.dirname( fname ), exist_ok=True )
    with open( fname, 'w' ) as f:
        configParser.write( f )

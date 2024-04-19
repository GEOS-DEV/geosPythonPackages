import os
from pathlib import Path
import shutil


def create_assets_folder( target_dir ):
    os.makedirs( target_dir, exist_ok=True )
    mod_path = os.path.dirname( os.path.abspath( Path( __file__ ).resolve() ) )
    for f in [ 'sorttable.js', 'style.css' ]:
        shutil.copyfile( os.path.join( mod_path, f ), os.path.join( target_dir, f ) )

    shutil.unpack_archive( os.path.join( mod_path, 'lightbox.zip' ),
                           os.path.join( target_dir, 'lightbox' ),
                           format='zip' )

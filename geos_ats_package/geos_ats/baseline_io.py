import os
import logging
import tempfile
import shutil
import yaml
import time
from google.cloud import storage

logger = logging.getLogger( 'geos_ats' )


def download_baselines( bucket_name: str,
                        blob_name: str,
                        baseline_path: str,
                        force_redownload: bool = False,
                        ok_delete_old_baselines: bool = False ):
    """
    Download and unpack baselines from GCP to the local machine

    Args:
        bucket_name (str): Name of the GCP bucket
        blob_name (str): Name of the baseline blob
        baseline_path (str): Path to unpack the baselines
        force_redownload (bool): Force re-download baseline files
        ok_delete_old_baselines (bool): Automatically delete old baseline files if present
    """
    # Setup
    baseline_path = os.path.abspath( os.path.expanduser( baseline_path ) )
    status_path = os.path.join( baseline_path, '.blob_name' )

    # Check to see if the baselines are already downloaded
    logger.info( 'Checking for existing baseline files...' )
    if os.path.isdir( baseline_path ):
        logger.info( f'Target baseline directory already exists: {baseline_path}' )
        if os.path.isfile( status_path ):
            last_blob_name = open( status_path, 'r' ).read()
            if ( blob_name == last_blob_name ) and not force_redownload:
                logger.info( f'Target baselines are already downloaded: {blob_name}' )
                logger.info( 'To re-download these files, run with the force_redownload option' )
                return

        if not ok_delete_old_baselines:
            for ii in range( 10 ):
                print( f'Existing baseline files found: {baseline_path}' )
                user_input = input( 'Delete old baselines?  [y/n]' )
                user_input = user_input.strip().lower()
                if user_input in [ "y", "yes" ]:
                    logger.debug( 'User chose to delete old baselines' )
                    break
                elif user_input in [ "n", "no" ]:
                    logger.debug( 'User chose to keep old baselines' )
                    logger.warning( 'Running with out of date baseline files' )
                    return
                else:
                    print( f'Unrecognized option: {user_input}' )
            raise Exception( 'Failed to parse user options for old baselines' )

        logger.info( 'Deleting old baselines...' )
        shutil.rmtree( baseline_path )

    else:
        os.makedirs( os.path.dirname( baseline_path ), exist_ok=True )

    # Download new baselines
    try:
        logger.info( 'Downloading baselines...' )
        tmpdir = tempfile.TemporaryDirectory()
        archive_name = os.path.join( tmpdir.name, 'baselines.tar.gz' )

        # Download from GCP
        client = storage.Client( use_auth_w_custom_endpoint=False )
        bucket = client.bucket( bucket_name )
        blob = bucket.blob( blob_name )
        blob.download_to_filename( archive_name )

        # Unpack new baselines
        logger.info( 'Unpacking baselines...' )
        shutil.unpack_archive( archive_name, baseline_path, format='gztar' )
        logger.info( 'Finished fetching baselines!' )

    except Exception as e:
        logger.error( 'Failed to fetch baseline files' )
        logger.error( str( e ) )


def pack_baselines( archive_name: str, baseline_path: str ):
    """
    Pack and upload baselines to GCP

    Args:
        archive_name (str): Name of the target archive
        baseline_path (str): Path to unpack the baselines
    """
    # Setup
    baseline_path = os.path.abspath( os.path.expanduser( baseline_path ) )
    status_path = os.path.join( baseline_path, '.blob_name' )

    # Check to see if the baselines are already downloaded
    logger.info( 'Checking for existing baseline files...' )
    if not os.path.isdir( baseline_path ):
        logger.error( f'Could not find target baselines: {baseline_path}' )
        raise FileNotFoundError( 'Could not find target baseline files' )

    # Update the blob name
    with open( status_path, 'w' ) as f:
        f.write( os.path.basename( archive_name ) )

    try:
        logger.info( 'Archiving baseline files...' )
        archive_name = os.path.join( tmpdir.name, 'baselines.tar.gz' )
        shutil.make_archive( archive_name, format='gztar', base_dir=baseline_path )
    except Exception as e:
        logger.error( 'Failed to create baseline archive' )
        logger.error( str( e ) )


def upload_baselines( bucket_name: str, archive_name: str ):
    """
    Pack and upload baselines to GCP

    Args:
        bucket_name (str): Name of the GCP bucket
        archive_name (str): Name of the target archive
    """
    # Setup
    if not os.path.isfile( archive_name ):
        logger.error( f'Could not find target archive:{archive_name}' )
        return

    try:
        logger.info( 'Uploading baseline files...' )
        client = storage.Client()
        bucket = client.bucket( bucket_name )
        blob = bucket.blob( os.path.basename( archive_name ) )
        blob.upload_from_filename( archive_name, if_generation_match=0 )
        logger.info( 'Finished uploading baselines!' )

    except Exception as e:
        logger.error( 'Failed to upload baselines!' )
        logger.error( str( e ) )


def manage_baselines( options ):
    """
    Manage the integrated test baselines
    """
    # Check for integrated test yaml file
    test_yaml = ''
    if options.yaml:
        test_yaml = options.yaml
    else:
        test_yaml = os.path.join( options.geos_bin_dir, '..', '..', '.integrated_tests.yaml' )

    if not os.path.isfile( test_yaml ):
        raise Exception( f'Could not find the integrated test yaml file: {test_yaml}' )

    test_options = {}
    with open( test_yaml ) as f:
        test_options = yaml.safe_load( f )

    baseline_options = test_options.get( 'baselines', {} )
    for k in [ 'bucket', 'baseline' ]:
        if k not in baseline_options:
            raise Exception(
                f'Required information (baselines/{k}) missing from integrated test yaml file: {test_yaml}' )

    # Manage baselines
    if options.action in [ 'pack_baselines', 'upload_baselines' ]:
        if os.path.isdir( options.baselineDir ):
            # Check the baseline name and open a temporary directory if required
            tmpdir = tempfile.TemporaryDirectory()
            upload_name = options.baselineArchiveName
            if not upload_name:
                epoch = int( time.time() )
                upload_name = os.path.join( tmpdir.name, f'integrated_test_baseline_{epoch}.tar.gz' )
            else:
                dirname = os.path.dirname( upload_name )
                os.makedirs( dirname, exist_ok=True )

            pack_baselines( upload_name, options.baselineDir )
            if options.action == 'pack_baselines':
                quit()

            upload_baselines( baseline_options[ 'bucket' ], upload_name )

            # Update the test config file
            blob_name = os.path.basename( upload_name )
            baseline_options[ 'baseline' ] = upload_name
            with open( test_yaml, 'w' ) as f:
                yaml.dump( baseline_options, f )
            quit()
        else:
            raise Exception( f'Could not find the requested baselines to upload: {options.baselineDir}' )

    download_baselines( baseline_options[ 'bucket' ],
                        baseline_options[ 'baseline' ],
                        options.baselineDir,
                        force_redownload=options.update_baselines,
                        ok_delete_old_baselines=options.delete_old_baselines )

    # Cleanup
    if not os.path.isdir( options.baselineDir ):
        raise Exception( f'Could not find the specified baseline directory: {options.baselineDir}' )

    if options.action == 'download_baselines':
        quit()
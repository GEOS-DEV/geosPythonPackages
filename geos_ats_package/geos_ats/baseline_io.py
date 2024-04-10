import os
import logging
import tempfile
import shutil
import yaml
import time
import requests
import pathlib
from functools import partial
from tqdm.auto import tqdm
from google.cloud import storage

logger = logging.getLogger( 'geos_ats' )
tmpdir = tempfile.TemporaryDirectory()
baseline_temporary_directory = tmpdir.name


def file_download_progress( headers: dict, url: str, filename: str ):
    """
    Download a file from a url in chunks, showing a progress bar

    Args:
        headers (dict): Request headers
        url (str): Target address
        filename (str): Download filename
    """

    path = pathlib.Path( filename ).expanduser().resolve()
    path.parent.mkdir( parents=True, exist_ok=True )

    r = requests.get( url, stream=True, allow_redirects=True, headers=headers )
    if r.status_code != 200:
        r.raise_for_status()
        raise RuntimeError( f"Request to {url} returned status code {r.status_code}" )

    file_size = int( r.headers.get( 'Content-Length', 0 ) )
    desc = "(Unknown total file size)" if file_size == 0 else ""

    try:
        r.raw.read = partial( r.raw.read, decode_content=True )
        with tqdm.wrapattr( r.raw, "read", total=file_size, desc=desc ) as r_raw:
            with path.open( "wb" ) as f:
                shutil.copyfileobj( r_raw, f )

    except:
        with path.open( "wb" ) as f:
            for chunk in r.iter_content( chunk_size=128 ):
                f.write( chunk )


def collect_baselines( bucket_name: str,
                       blob_name: str,
                       baseline_path: str,
                       force_redownload: bool = False,
                       ok_delete_old_baselines: bool = False,
                       cache_directory: str = '' ):
    """
    Collect and unpack test baselines

    Args:
        bucket_name (str): Name of the GCP bucket
        blob_name (str): Name of the baseline blob
        baseline_path (str): Path to unpack the baselines
        force_redownload (bool): Force re-download baseline files
        ok_delete_old_baselines (bool): Automatically delete old baseline files if present
        cache_directory (str): Search this directory first for files that are already downloaded
    """
    # Setup
    baseline_path = os.path.abspath( os.path.expanduser( baseline_path ) )
    status_path = os.path.join( baseline_path, '.blob_name' )
    cache_directory = os.path.abspath( os.path.expanduser( cache_directory ) )

    # Check to see if the baselines are already downloaded
    logger.info( 'Checking for existing baseline files...' )
    if os.path.isdir( baseline_path ):
        if os.listdir( baseline_path ):
            logger.info( f'Target baseline directory already exists: {baseline_path}' )
            if os.path.isfile( status_path ):
                last_blob_name = open( status_path, 'r' ).read()
                if ( blob_name == last_blob_name ) and not force_redownload:
                    logger.info( f'Target baselines are already downloaded: {blob_name}' )
                    logger.info( 'To re-download these files, run with the force_redownload option' )
                    return
        else:
            ok_delete_old_baselines = True

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

    # Check for old baselines
    archive_name = ''
    blob_tar = f'{blob_name}.tar.gz'
    if cache_directory and not force_redownload:
        logger.info( 'Checking cache directory for existing baseline...' )
        f = os.path.join( cache_directory, blob_tar )
        if os.path.isfile( f ):
            logger.info( 'Baseline found!' )
            archive_name = f

    # Download new baselines
    if not archive_name:
        logger.info( 'Downloading baselines...' )
        if cache_directory:
            archive_name = os.path.join( cache_directory, blob_tar )
        else:
            archive_name = os.path.join( baseline_temporary_directory, blob_tar )

        if 'https://' in bucket_name:
            # Download from URL
            try:
                file_download_progress( {}, f"{bucket_name}/{blob_tar}", archive_name )
            except Exception as e:
                logger.error( f'Failed to download baseline from URL ({bucket_name}/{blob_tar})' )
                logger.error( repr( e ) )
        else:
            # Download from GCP
            try:
                client = storage.Client( use_auth_w_custom_endpoint=False )
                bucket = client.bucket( bucket_name )
                blob = bucket.blob( blob_tar )
                blob.download_to_filename( archive_name )
            except Exception as e:
                logger.error( f'Failed to download baseline from GCP ({bucket_name}/{blob_tar})' )
                logger.error( repr( e ) )

    if os.path.isfile( archive_name ):
        # Unpack new baselines
        logger.info( f'Unpacking baselines: {archive_name}' )
        try:
            shutil.unpack_archive( archive_name, baseline_path, format='gztar' )
            logger.info( 'Finished fetching baselines!' )
        except Exception as e:
            logger.error( repr( e ) )
            raise Exception( f'Failed to unpack baselines: {archive_name}' )

    else:
        raise Exception( f'Could not find baseline files to unpack: expected={archive_name}' )


def pack_baselines( archive_name: str, baseline_path: str, log_path: str = '' ):
    """
    Pack and upload baselines to GCP

    Args:
        archive_name (str): Name of the target archive
        baseline_path (str): Path to unpack the baselines
        log_path (str): Path to log files (optional)
    """
    # Setup
    archive_name = os.path.abspath( archive_name )
    baseline_path = os.path.abspath( os.path.expanduser( baseline_path ) )
    status_path = os.path.join( baseline_path, '.blob_name' )

    # Check to see if the baselines are already downloaded
    logger.info( 'Checking for existing baseline files...' )
    if not os.path.isdir( baseline_path ):
        logger.error( f'Could not find target baselines: {baseline_path}' )
        raise FileNotFoundError( 'Could not find target baseline files' )

    print( 'baseline contents:' )
    print( os.listdir( baseline_path ) )

    # Update the blob name
    logger.info( 'Setting the blob name...' )
    with open( status_path, 'w' ) as f:
        f.write( os.path.basename( archive_name ) )

    # Copy the log directory
    logger.info( 'Copying the logs...' )
    if os.path.isdir( log_path ):
        shutil.rmtree( log_path )

    if log_path:
        log_path = os.path.abspath( os.path.expanduser( log_path ) )
        log_target = os.path.join( baseline_path, 'logs' )

        print( 'log parameters:' )
        print( log_path, log_target )
        shutil.copytree( log_path, log_target )

    try:
        logger.info( 'Archiving baseline files...' )
        shutil.make_archive( archive_name, format='gztar', root_dir=baseline_path )
        logger.info( f'Created {archive_name}.tar.gz' )
    except Exception as e:
        logger.error( 'Failed to create baseline archive' )
        logger.error( repr( e ) )


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
        logger.error( repr( e ) )


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
            upload_name = options.baselineArchiveName
            if upload_name.endswith( '.tar.gz' ):
                upload_name = upload_name[ :-7 ]

            if not upload_name:
                epoch = int( time.time() )
                upload_name = os.path.join( baseline_temporary_directory, f'integrated_test_baseline_{epoch}' )
            else:
                dirname = os.path.dirname( upload_name )
                os.makedirs( dirname, exist_ok=True )

            pack_baselines( upload_name, options.baselineDir, log_path=options.logs )
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

    collect_baselines( baseline_options[ 'bucket' ],
                       baseline_options[ 'baseline' ],
                       options.baselineDir,
                       force_redownload=options.update_baselines,
                       ok_delete_old_baselines=options.delete_old_baselines,
                       cache_directory=options.baselineCacheDirectory )

    # Cleanup
    if not os.path.isdir( options.baselineDir ):
        raise Exception( f'Could not find the specified baseline directory: {options.baselineDir}' )

    if options.action == 'download_baselines':
        quit()

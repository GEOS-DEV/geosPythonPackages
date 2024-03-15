import os
import logging
import tempfile
import shutil
import yaml
import time

logger = logging.getLogger( 'geos_ats' )


def download_baselines( bucket_name, blob_name, baseline_path, force_redownload=False ):
    """
    Download and unpack baselines from GCP to the local machine

    Args:
        bucket_name (str): Name of the GCP bucket
        blob_name (str): Name of the baseline blob
        baseline_path (str): Path to unpack the baselines
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
        from google.cloud import storage
        client = storage.Client()
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


def upload_baselines( bucket_name, blob_name, baseline_path ):
    """
    Pack and upload baselines to GCP

    Args:
        bucket_name (str): Name of the GCP bucket
        blob_name (str): Name of the baseline blob
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

    # Check for old blob name files and over-write if necessary
    last_blob_name = ''
    if os.path.isfile( status_path ):
        last_blob_name = open( status_path, 'r' ).read()
    with open( status_path, 'w' ) as f:
        f.write( blob_name )

    try:
        logger.info( 'Archiving baseline files...' )
        tmpdir = tempfile.TemporaryDirectory()
        archive_name = os.path.join( tmpdir.name, 'baselines.tar.gz' )
        shutil.make_archive( archive_name, format='gztar', base_dir=baseline_path )

        # Upload to gcp
        from google.cloud import storage
        logger.info( 'Uploading baseline files...' )
        client = storage.Client()
        bucket = client.bucket( bucket_name )
        blob = bucket.blob( blob_name )
        blob.upload_from_filename( archive_name, if_generation_match=0 )
        logger.info( 'Finished uploading baselines!' )

    except Exception as e:
        logger.error( 'Failed to upload baselines!' )
        logger.error( str( e ) )

        # Reset the local blob name
        with open( status_path, 'w' ) as f:
            f.write( last_blob_name )


def manage_baselines( options ):
    """
    Manage the integrated test baselines
    """
    # Check for integrated test yaml file
    test_yaml = ''
    if options.testYAML:
        test_yaml = options.testYAML
    else:
        test_yaml = os.path.join( options.geos_bin_dir, '..', '..', '.integrated_tests.yaml' )

    if not os.path.isfile( test_yaml ):
        raise Exception( f'Could not find the integrated test yaml file: {test_yaml}' )

    test_options = yaml.safe_load( open( test_yaml ) )
    baseline_options = test_options.get( 'baselines', {} )
    for k in [ 'bucket', 'latest' ]:
        if k not in baseline_options:
            raise Exception(
                f'Required information (baselines/{k}) missing from integrated test yaml file: {test_yaml}' )

    # Manage baselines
    if options.action == 'upload_baselines':
        if os.path.isdir( options.baselineDir ):
            epoch = int( time.time() )
            upload_name = f'integrated_test_baseline_{epoch}.tar.gz'
            upload_baselines( baseline_options[ 'bucket' ], upload_name, options.baselineDir )

            # Update the test config file
            baseline_options[ 'latest' ] = upload_name
            with open( test_yaml, 'w' ) as f:
                yaml.dump( baseline_options, f )
            quit()
        else:
            raise Exception( f'Could not find the requested baselines to upload: {options.baselineDir}' )

    download_baselines( baseline_options[ 'bucket' ], baseline_options[ 'latest' ], options.baselineDir )

    # Cleanup
    if not os.path.isdir( options.baselineDir ):
        raise Exception( f'Could not find the specified baseline directory: {options.baselineDir}' )

    if options.action == 'download_baselines':
        quit()

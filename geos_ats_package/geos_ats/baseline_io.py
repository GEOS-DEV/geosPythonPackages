import os
import logging
import tempfile
import shutil
import yaml
import time
import requests
import pathlib
import ssl 
from functools import partial
from tqdm.auto import tqdm
from google.cloud import storage
from google.auth.transport.requests import AuthorizedSession
from google.auth import default
                        

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

    certs = ["/usr/local/share/ca-certificates/ADPKI_LLNLROOT.crt.crt",
                "/usr/local/share/ca-certificates/DigiCertGlobalCAG2.crt.crt",
                "/usr/local/share/ca-certificates/cspca.crt.crt",
                "usr/local/share/ca-certificates/ADPKI-11.the-lab.llnl.gov_ADPKI-11.crt.crt",
                "/usr/local/share/ca-certificates/ADPKI-12.the-lab.llnl.gov_ADPKI-12.crt.crt",
                "/usr/local/share/ca-certificates/ADPKI-13.the-lab.llnl.gov_ADPKI-13.crt.crt",
                "/usr/local/share/ca-certificates/ADPKI-14.the-lab.llnl.gov_ADPKI-14.crt.crt", 
                "/usr/local/share/ca-certificates/ADPKI-15.the-lab.llnl.gov_ADPKI-15.crt.crt", 
                "/usr/local/share/ca-certificates/ADPKI-16.the-lab.llnl.gov_ADPKI-16.crt.crt"]

    combined_cert_path = "/usr/local/share/ca-certificates/combined.crt"

    logger.info("file name.")

    with open(combined_cert_path, 'w') as outputfile:
        for cert in certs:
            with open(cert) as infile:
                outputfile.write(infile.read())
                outputfile.write("\n")
    
    
    r = requests.get( url, stream=True, allow_redirects=True, headers=headers, cert=combined_cert_path )
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

def create_anonymous_client_with_custom_cert(cert_path):
    # Create a custom SSL context
    ssl_context = ssl.create_default_context(cafile=cert_path)
    
    # Obtain default credentials
    credentials, project = default()
    
    # Create an authorized session with the custom SSL context
    authed_session = AuthorizedSession(credentials, ssl_context=ssl_context)
    
    # Initialize the storage client with the custom session
    client = storage.Client(credentials=credentials, _http=authed_session)
    
    return client


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
    short_blob_name = os.path.basename( blob_name )

    # Check to see if the baselines are already downloaded
    logger.info( f'Checking for existing baseline files in {baseline_path}' )
    if os.path.isdir( baseline_path ):
        if os.listdir( baseline_path ):
            logger.info( f'Target baseline directory already exists: {baseline_path}' )
            if os.path.isfile( status_path ):
                last_blob_name = open( status_path, 'r' ).read()
                if ( short_blob_name == last_blob_name ) and not force_redownload:
                    logger.info( f'Target baselines are already downloaded: {short_blob_name}' )
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
                    ok_delete_old_baselines = True
                    break
                elif user_input in [ "n", "no" ]:
                    logger.debug( 'User chose to keep old baselines' )
                    logger.warning( 'Running with out of date baseline files' )
                    return
                else:
                    print( f'Unrecognized option: {user_input}' )

            if not ok_delete_old_baselines:
                raise Exception( 'Failed to parse user options for old baselines' )

        logger.info( 'Deleting old baselines...' )
        shutil.rmtree( baseline_path )

    else:
        os.makedirs( os.path.dirname( baseline_path ), exist_ok=True )

    # Check for old baselines
    archive_name = ''
    blob_tar = f'{blob_name}.tar.gz'
    short_blob_tar = f'{short_blob_name}.tar.gz'
    logger.info( f'Checking cache directory ({cache_directory}) for existing baseline named {short_blob_name}' )
    if cache_directory and not force_redownload:
        cache_directory = os.path.abspath( os.path.expanduser( cache_directory ) )
        logger.info( f'Checking cache directory ({cache_directory}) for existing baseline...' )
        f = os.path.join( cache_directory, short_blob_tar )
        if os.path.isfile( f ):
            logger.info( 'Baseline found!' )
            archive_name = f

    # Download new baselines
    if not archive_name:
        logger.info( 'Downloading baselines...' )
        if cache_directory:
            archive_name = os.path.join( cache_directory, short_blob_tar )
        else:
            archive_name = os.path.join( baseline_temporary_directory, short_blob_tar )
        
        logger.info( f'bucket_name {bucket_name}' )
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
                certs = ["/usr/local/share/ca-certificates/ADPKI_LLNLROOT.crt.crt",
                "/usr/local/share/ca-certificates/DigiCertGlobalCAG2.crt.crt",
                "/usr/local/share/ca-certificates/cspca.crt.crt",
                "usr/local/share/ca-certificates/ADPKI-11.the-lab.llnl.gov_ADPKI-11.crt.crt",
                "/usr/local/share/ca-certificates/ADPKI-12.the-lab.llnl.gov_ADPKI-12.crt.crt",
                "/usr/local/share/ca-certificates/ADPKI-13.the-lab.llnl.gov_ADPKI-13.crt.crt",
                "/usr/local/share/ca-certificates/ADPKI-14.the-lab.llnl.gov_ADPKI-14.crt.crt", 
                "/usr/local/share/ca-certificates/ADPKI-15.the-lab.llnl.gov_ADPKI-15.crt.crt", 
                "/usr/local/share/ca-certificates/ADPKI-16.the-lab.llnl.gov_ADPKI-16.crt.crt"]

                combined_cert_path = "/usr/local/share/ca-certificates/combined.crt"

                with open(combined_cert_path, 'w') as outputfile:
                    for cert in certs:
                        with open(cert) as infile:
                           outputfile.write(infile.read())
                           outputfile.write("\n")
             
                os.environ['GRPC_DEFAULT_SSL_ROOTS_FILE_PATH'] = combined_cert_path

                # Obtain default credentials
                credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

                # Print the environment variable
                logger.info(f"GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}")     
                
                client = create_anonymous_client_with_custom_cert(combined_cert_path)

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

    # Update the blob name
    logger.info( 'Setting the blob name...' )
    with open( status_path, 'w' ) as f:
        f.write( os.path.basename( archive_name ) )

    # Copy the log directory
    if log_path:
        logger.info( 'Copying the logs...' )
        log_path = os.path.abspath( os.path.expanduser( log_path ) )
        log_target = os.path.join( baseline_path, 'logs' )
        try:
            if os.path.isdir( log_target ):
                shutil.rmtree( log_target )
            shutil.copytree( log_path, log_target )
        except Exception as e:
            logger.warning( 'Failed to remove old logs' )
            logger.warning( repr( e ) )

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
    if options.action not in [ 'run', 'rerun', 'continue', 'pack_baselines', 'upload_baselines', 'download_baselines' ]:
        return

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

from typing import Optional
from pathlib import Path
import paramiko


# replace by conf-file json
from dataclasses import dataclass
@dataclass( frozen=True )
class SimulationConstant:
    SIMULATION_GEOS_PATH = "/workrd/users/"
    HOST = "p4log01"  # Only run on P4 machine
    REMOTE_HOME_BASE = "/users"
    PORT = 22
    SIMULATIONS_INFORMATION_FOLDER_PATH = "/workrd/users/"
    SIMULATION_DEFAULT_FILE_NAME = "geosDeck.xml"

#If proxyJump are needed
#
# proxy_cmd = "ssh -W {host}:{port} proxyuser@bastion.example.com".format(
#     host=ssh_host, port=ssh_port
# )
# from paramiko import ProxyCommand
# sock = ProxyCommand(proxy_cmd)

# client = paramiko.SSHClient()
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# client.connect(
#     hostname=ssh_host,
#     port=ssh_port,
#     username=username,
#     key_filename=keyfile,
#     sock=sock,   # <— tunnel created by ProxyCommand
# )

class Authentificator:  #namespacing more than anything else

    ssh_client: Optional[ paramiko.SSHClient ] = None

    @staticmethod
    def _sftp_copy_tree( ssh_client, file_tree, remote_root ):
        # Connect to remote server
        sftp = ssh_client.open_sftp()

        Authentificator.dfs_tree( file_tree[ "structure" ], file_tree[ "root" ], sftp=sftp, remote_root=remote_root )

        sftp.close()

    @staticmethod
    def dfs_tree( node, path, sftp, remote_root ):

        lp = Path( path )
        rp = Path( remote_root ) / lp

        if isinstance( node, list ):
            for file in node:
                # sftp.put(lp/Path(file), rp/Path(file))
                with sftp.file( str( rp / Path( file.get( 'name' ) ) ), 'w' ) as f:
                    f.write( file.get( 'content' ) )
                print( f"copying {lp/Path(file.get('name'))} to {rp/Path(file.get('name'))}" )
        elif isinstance( node, dict ):
            if "files" in node:
                for file in node[ "files" ]:
                    # sftp.put( str(lp/Path(file)), str(rp/Path(file)) )
                    with sftp.file( str( rp / Path( file.get( 'name' ) ) ), 'w' ) as f:
                        f.write( file.get( 'content' ) )
                    print( f"copying {lp/Path(file.get('name'))} to {rp/Path(file.get('name'))}" )
            if "subfolders" in node:
                for subfolder, content in node[ "subfolders" ].items():
                    try:
                        sftp.stat( str( rp / Path( subfolder ) ) )
                    except FileNotFoundError:
                        print( f"creating {rp/Path(subfolder)}" )
                        sftp.mkdir( str( rp / Path( subfolder ) ) )
                    Authentificator.dfs_tree( content, lp / Path( subfolder ), sftp, remote_root )

            for folder, content in node.items():
                if folder not in [ "files", "subfolders" ]:
                    try:
                        sftp.stat( str( rp / Path( folder ) ) )
                    except FileNotFoundError:
                        print( f"creating {rp/Path(folder)}" )
                        sftp.mkdir( str( rp / Path( folder ) ) )
                    Authentificator.dfs_tree( content, lp / Path( folder ), sftp, remote_root )

    @staticmethod
    def kill_job( id ):
        if Authentificator.ssh_client:
            Authentificator._execute_remote_command( Authentificator.ssh_client, f"scancel {id}" )
        return None

    @staticmethod
    def get_key( id, pword ):

        try:
            home = os.environ.get( "HOME" )
            PRIVATE_KEY = paramiko.RSAKey.from_private_key_file( f"{home}/.ssh/id_trame" )
            return PRIVATE_KEY
        except paramiko.SSHException as e:
            print( f"Error loading private key: {e}\n" )
        except FileNotFoundError as e:
            print( f"Private key not found: {e}\n Generating key ..." )
            PRIVATE_KEY = Authentificator.gen_key()
            temp_client = paramiko.SSHClient()
            temp_client.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
            temp_client.connect( SimulationConstant.HOST,
                                 SimulationConstant.PORT,
                                 username=id,
                                 password=pword,
                                 timeout=10 )
            Authentificator._transfer_file_sftp( temp_client, f"{home}/.ssh/id_trame.pub",
                                                 f"{SimulationConstant.REMOTE_HOME_BASE}/{id}/.ssh/id_trame.pub" )
            Authentificator._execute_remote_command(
                temp_client,
                f" cat {SimulationConstant.REMOTE_HOME_BASE}/{id}/.ssh/id_trame.pub | tee -a {SimulationConstant.REMOTE_HOME_BASE}/{id}/.ssh/authorized_keys"
            )

            return PRIVATE_KEY

    @staticmethod
    def gen_key():

        home = os.environ.get( "HOME" )
        file_path = f"{home}/.ssh/id_trame"
        key = paramiko.RSAKey.generate( bits=4096 )
        key.write_private_key_file( file_path )

        # Get public key in OpenSSH format
        public_key = f"{key.get_name()} {key.get_base64()}"
        with open( file_path + ".pub", "w" ) as pub_file:
            pub_file.write( public_key )

        print( "SSH key pair generated: id_trame (private), id_trame.pub (public)" )

        return key

    @staticmethod
    def _create_ssh_client( host, port, username, password=None, key=None ) -> paramiko.SSHClient:
        """
        Initializes and returns an SSH client connection.
        Uses context manager for automatic cleanup.
        """
        client = paramiko.SSHClient()
        # Automatically adds the hostname and new host keys to the host files (~/.ssh/known_hosts)
        client.set_missing_host_key_policy( paramiko.AutoAddPolicy() )

        try:
            print( f"Connecting to {host} using key-based authentication..." )
            client.connect( host, port, username, pkey=key, timeout=10 )

            return client
        except paramiko.AuthenticationException:
            print( "Authentication failed. Check your credentials or key." )
            return None
        except paramiko.SSHException as e:
            print( f"Could not establish SSH connection: {e}" )
            return None
        except Exception as e:
            print( f"An unexpected error occurred: {e}" )
            return None

    @staticmethod
    def _execute_remote_command( client, command ):
        """
        Executes a single command on the remote server and prints the output.
        """
        if not client:
            return

        print( f"\n--- Executing Command: '{command}' ---" )
        try:
            # Executes the command. stdin, stdout, and stderr are file-like objects.
            # Ensure command ends with a newline character for some shell environments.
            stdin, stdout, stderr = client.exec_command( command )

            # Wait for the command to finish and read the output
            exit_status = stdout.channel.recv_exit_status()

            # Print standard output
            stdout_data = stdout.read().decode().strip()
            if stdout_data:
                print( "STDOUT:" )
                print( stdout_data )

            # Print standard error (if any)
            stderr_data = stderr.read().decode().strip()
            if stderr_data:
                print( "STDERR:" )
                print( stderr_data )

            print( f"Command exited with status: {exit_status}" )
            return ( exit_status, stdout_data, stderr_data )

        except Exception as e:
            print( f"Error executing command: {e}" )
            return ( -1, "", "" )

    @staticmethod
    def _transfer_file_sftp( client, local_path, remote_path, direction="put" ):
        """
        Transfers a file using SFTP (Secure File Transfer Protocol).
        Direction can be 'put' (upload) or 'get' (download).
        """
        if not client:
            return

        print( f"\n--- Starting SFTP Transfer ({direction.upper()}) ---" )

        try:
            # Establish an SFTP connection session
            sftp = client.open_sftp()

            if direction == "put":
                print( f"Uploading '{local_path}' to '{remote_path}'..." )
                sftp.put( local_path, remote_path )
                print( "Upload complete." )
            elif direction == "get":
                print( f"Downloading '{remote_path}' to '{local_path}'..." )
                sftp.get( remote_path, local_path )
                print( "Download complete." )
            else:
                print( "Invalid transfer direction. Use 'put' or 'get'." )

            sftp.close()
            return True

        except FileNotFoundError:
            print( f"Error: Local file '{local_path}' not found." )
            return False
        except IOError as e:
            print( f"Error accessing remote file or path: {e}" )
            return False
        except Exception as e:
            print( f"An error occurred during SFTP: {e}" )
            return False
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc

from typing import Optional
from pathlib import Path
import paramiko
import os
import json
from dataclasses import dataclass
import trame_server.state as State

@dataclass
class SimulationConstant:
    name: str
    host: str
    partition: str
    partition_tranfert: str
    port: int
    geos_path: str
    geos_module: str
    geos_load_list: list
    remote_home_base: str  # for ssh key
    simulation_default_filename: str
    simulation_remote_path: str
    simulation_dl_default_path: str
    simulation_information_default_path: str
    n_nodes: int
    cores_per_node: int
    mem_per_node: int


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


class Authentificator:

    ssh_client: Optional[ paramiko.SSHClient ] = None

    sim_constants = []
        # SimulationConstant( **item )
        # for item in json.load( open( f'{os.getenv("ASSETS_DIR")}/cluster.json', 'r' ) )  # noqa: SIM115
    # ]

    @staticmethod
    def reload_simconstants():
        Authentificator.sim_constants = [
        SimulationConstant( **item )
        for item in json.load( open( f'{os.getenv("ASSETS_DIR")}/cluster.json', 'r' ) )  # noqa: SIM115
    ]

    @staticmethod
    def get_cluster( name: str ) -> Optional[ SimulationConstant ]:
        """Return the structured meta for cluster selected."""
        match = next( ( item for item in Authentificator.sim_constants if item.name == name ), None )
        return match

    @staticmethod
    def _sftp_copy_tree( ssh_client: paramiko.SSHClient, file_tree: dict, remote_root: str ) -> None:
        """Copy the file tree at remote root using ssh_client."""
        # Connect to remote server
        sftp = ssh_client.open_sftp()

        Authentificator.dfs_tree( file_tree[ "structure" ], file_tree[ "root" ], sftp=sftp, remote_root=remote_root )

        sftp.close()

    @staticmethod
    def dfs_tree( node: list | dict, path: str, sftp: paramiko.SFTPClient, remote_root: str ) -> None:
        """Create the tree represented by node at local path in remote pointed by sftp client at remote_root."""
        if path is None or remote_root is None:
            return  # type:ignore[unreachable]

        lp = Path( path )
        rp = Path( remote_root ) / lp

        if isinstance( node, list ):
            for file in node:
                print( f"copying {lp/Path(file.get('name'))} to {rp/Path(file.get('name'))}" )
                try:
                    with sftp.file( str( rp / Path( file.get( 'name' ) ) ), 'w' ) as f:
                        f.write( file.get( 'content' ) )
                except:
                    print( f"Error copying {lp/Path(file.get('name'))} to {rp/Path(file.get('name'))}")
                    raise
        elif isinstance( node, dict ):
            if "files" in node:
                files = node[ 'files' ]
                for file in files:
                    print( f"copying {lp/Path(file.get('name'))} to {rp/Path(file.get('name'))}" )
                    try:
                        with sftp.file( str( rp / Path( file.get( 'name' ) ) ), 'w' ) as f:
                            f.write( file.get( 'content' ) )
                    except:
                        print( f"Error copying {lp/Path(file.get('name'))} to {rp/Path(file.get('name'))}")
                        raise
            if "subfolders" in node:
                for subfolder, content in node[ "subfolders" ].items():
                    try:
                        sftp.stat( str( rp / Path( subfolder ) ) )
                    except FileNotFoundError:
                        try:
                            print( f"creating {rp/Path(subfolder)}" )
                            sftp.mkdir( str( rp / Path( subfolder ) ) )
                        except:
                            print( f"Error creating {rp/Path(subfolder)} on remote.")
                            raise
                    Authentificator.dfs_tree( content, str( lp / Path( subfolder ) ), sftp, remote_root )

            for folder, content in node.items():
                if folder not in [ "files", "subfolders" ]:
                    try:
                        sftp.stat( str( rp / Path( folder ) ) )
                    except FileNotFoundError:
                        print( f"creating {rp/Path(folder)}" )
                        try:
                            sftp.mkdir( str( rp / Path( folder ) ) )
                        except:
                            print( f"Error creating {rp/Path(subfolder)} on remote.")
                            raise
                    Authentificator.dfs_tree( content, str( lp / Path( folder ) ), sftp, remote_root )

    @staticmethod
    def kill_job( id: int ) -> None:
        """Cancel job identified by id in slurm schedulder."""
        if Authentificator.ssh_client:
            Authentificator._execute_remote_command( Authentificator.ssh_client, f"scancel {id}" )
        return None

    @staticmethod
    def get_key( id: str, pword: str, key_path : str, cluster_name: str) -> paramiko.RSAKey:
        """Return the ssh key if found or create and dispatch one."""
        try:
            import os
            # home = os.environ.get( "HOME" )
            # PRIVATE_KEY = paramiko.RSAKey.from_private_key_file( f"{home}/.ssh/id_trame" )
            PRIVATE_KEY = paramiko.RSAKey.from_private_key_file( key_path )
            return PRIVATE_KEY
        except paramiko.SSHException as e:
            print( f"Error loading private key: {e}\n" )
        except FileNotFoundError as e:
            print( f"Private key not found: {e}\n Generating key at ... {key_path}" )
            PRIVATE_KEY = Authentificator.gen_key(key_path)
            temp_client = paramiko.SSHClient()
            temp_client.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
            temp_client.connect( Authentificator.get_cluster(cluster_name).host,
                                 Authentificator.get_cluster(cluster_name).port,
                                 username=id,
                                 password=pword,
                                 timeout=10 )
            Authentificator._transfer_file_sftp( temp_client, f"{key_path.split('/')[-1]}.pub",
                                                 f"{Authentificator.get_cluster(cluster_name).remote_home_base}/{id}/.ssh/{key_path.split('/')[-1]}.pub" )
            Authentificator._execute_remote_command(
                temp_client,
                f" cat {Authentificator.get_cluster(cluster_name).remote_home_base}/.ssh/{key_path.split('/')[-1]}.pub | tee -a {Authentificator.get_cluster(cluster_name).remote_home_base}/.ssh/authorized_keys"
            )

            return PRIVATE_KEY

    @staticmethod
    def gen_key(key_path : str ) -> paramiko.RSAKey:
        """Generate RSAKey for SSH protocol."""
        import os

        # home = os.environ.get( "HOME" )
        # file_path = f"{home}/.ssh/id_trame"
        key = paramiko.RSAKey.generate( bits=4096 )
        key.write_private_key_file( key_path )

        # Get public key in OpenSSH format
        public_key = f"{key.get_name()} {key.get_base64()}"
        with open( key_path + ".pub", "w" ) as pub_file:
            pub_file.write( public_key )

        suffix = key_path.split('/')[-1]
        print( f"SSH key pair generated: {suffix} (private), {suffix}.pub (public)" )

        return key

    @staticmethod
    def _create_ssh_client( host: str,
                            port: int,
                            username: str,
                            password: str | None = None,
                            key: paramiko.RSAKey = None ) -> paramiko.SSHClient:
        """Initializes and returns an SSH client connection.

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
    def _execute_remote_command( client: paramiko.SSHClient, command: str ) -> tuple[ int, str, str ]:
        """Executes a single command on the remote server and prints the output."""
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
        
        except PermissionError as e:
            print( f"Permission error: {e}" )
            return ( -1, "", "" )
        except IOError as e:
            print( f"Error accessing remote file or path: {e}" )
            return ( -1, "", "" )
        except Exception as e:
            print( f"An error occurred during SFTP: {e}" )
            return ( -1, "", "" )

    @staticmethod
    def _transfer_file_sftp( client: paramiko.SSHClient,
                             local_path: str,
                             remote_path: str,
                             direction: str = "put" ) -> Optional[ bool ]:
        """Transfers a file using SFTP (Secure File Transfer Protocol).

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

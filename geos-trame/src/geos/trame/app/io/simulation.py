# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc

from pathlib import Path
from enum import Enum, unique, auto
from typing import Optional, Any
from trame_server.core import Server

from geos.trame.app.io.ssh_tools import Authentificator
from geos.trame.app.utils.async_file_watcher import AsyncPeriodicRunner

from jinja2 import Environment, FileSystemLoader
import paramiko
import re
import os


@unique
class SimulationStatus( Enum ):
    SCHEDULED = auto()
    RUNNING = auto()
    COMPLETING = auto()
    COPY_BACK = auto()
    DONE = auto()
    NOT_RUN = auto()
    UNKNOWN = auto()


@unique
class SlurmJobStatus( Enum ):
    PENDING = "PEND"
    RUNNING = "R"
    COMPLETING = "CG"
    COMPLETED = "CD"
    SUSPENDED = "S"
    UNKNOWN = "UNKNOWN"


class Simulation:
    """Simulation component.

    Fills the UI with the screenshot as read from the simulation outputs folder and a graph with the time series
    from the simulation.
    Requires a simulation runner providing information on the output path of the simulation to monitor and ways to
    trigger the simulation.
    """

    def __init__( self, server: Server, sim_info_dir: Optional[ Path ] = None ) -> None:
        """Initialize the Simulation object with logging and sim triggers among other callbacks."""
        self._server = server
        controller = server.controller
        self._sim_info_dir = sim_info_dir
        server.state.job_ids = []
        server.state.selected_cluster = None

        server.state.status_colors = {
            "PENDING": "#4CAF50",  #PD
            "RUNNING": "#3F51B5",  #R
            "CANCELLED": "#FFC107",  #CA
            "COMPLETED": "#484B45",  #CD
            "FAILED": "#E53935",  #F
        }
        self._job_status_watcher: Optional[ AsyncPeriodicRunner ] = None
        self._job_status_watcher_period_ms = 2000

        #define triggers
        @controller.trigger( "run_try_login" )
        def run_try_login() -> None:

            # if server.state.key:
            Authentificator.ssh_client = Authentificator._create_ssh_client(
                Authentificator.get_cluster( server.state.selected_cluster_name ).host,  #test
                Authentificator.get_cluster( server.state.selected_cluster_name ).port,
                server.state.login,
                key=Authentificator.get_key( server.state.login, server.state.password ) )

            if Authentificator.ssh_client:
                server.state.access_granted = True

        @controller.trigger( "run_simulation" )
        def run_simulation() -> None:

            # if server.state.access_granted and server.state.sd and server.state.simulation_xml_filename:
            if server.state.access_granted and server.state.simulation_xml_filename:
                if Authentificator.ssh_client:

                    Authentificator._sftp_copy_tree( Authentificator.ssh_client,
                                                     Authentificator.gen_tree( server.state.simulation_xml_filename ),
                                                     server.state.simulation_remote_path )

                    run_id: int = Simulation.render_and_run(
                        'p4_slurm.jinja',
                        'job.slurm',
                        server,
                        job_name=server.state.simulation_job_name,
                        input_file=[
                            item for item in server.state.simulation_xml_filename if item.get( 'type' ) == 'text/xml'
                        ][ 0 ].get( 'name' ),
                        nodes=server.state.sd[ 'nodes' ],
                        ntasks=server.state.sd[ 'total_ranks' ],
                        geos_module=Authentificator.get_cluster( server.state.selected_cluster_name ).geos_module,
                        geos_load_list=" ".join(
                            Authentificator.get_cluster( server.state.selected_cluster_name ).geos_load_list ),
                        geos_path=Authentificator.get_cluster( server.state.selected_cluster_name ).geos_path,
                        mem="0",
                        comment_gr=server.state.slurm_comment,
                        partition='p4_dev',
                        account='myaccount' )

                    Simulation.render_and_run( 'p4_copyback.jinja',
                                               'copyback.slurm',
                                               server,
                                               job_name=server.state.simulation_job_name,
                                               input_file=[
                                                   item for item in server.state.simulation_xml_filename
                                                   if item.get( 'type' ) == 'text/xml'
                                               ][ 0 ].get( 'name' ),
                                               nodes=1,
                                               ntasks=1,
                                               mem="0",
                                               dep_job_id=run_id,
                                               target_dl_path=server.state.simulation_dl_path,
                                               comment_gr=server.state.slurm_comment,
                                               partition='p4_transfer',
                                               account='myaccount' )

                    self._start_result_streams()

                else:
                    raise paramiko.SSHException

        @controller.trigger( "kill_all_simulations" )
        def kill_all_simulations() -> None:
            # exec scancel jobid
            for jobs in server.state.job_ids:
                Authentificator.kill_job( jobs[ 'job_id' ] )

    def __del__( self ) -> None:
        """Clean up running streams on destruction."""
        self._stop_result_streams()

    def set_status_watcher_period_ms( self, period_ms: int ) -> None:
        """Set the watcher period in ms."""
        self._job_status_watcher_period_ms = period_ms
        if self._job_status_watcher:
            self._job_status_watcher.set_period_ms( period_ms )

    def _stop_result_streams( self ) -> None:
        if self._job_status_watcher is not None:
            self._job_status_watcher.stop()

    def _start_result_streams( self ) -> None:
        self._stop_result_streams()
        self._job_status_watcher = AsyncPeriodicRunner( self.check_jobs, period_ms=self._job_status_watcher_period_ms )

    def check_jobs( self ) -> None:
        """Check on running jobs and update their names and progresses."""
        if Authentificator.ssh_client:
            try:
                jid = self._server.state.job_ids
                for index, job in enumerate( jid ):
                    job_id = job[ 'job_id' ]
                    _, sout, _ = Authentificator._execute_remote_command(
                        Authentificator.ssh_client, f'sacct -j {job_id} -o JobID,JobName,State --noheader' )
                    job_line = sout.strip().split( "\n" )[ -1 ]

                    jid[ index ][ 'status' ] = job_line.split()[ 2 ]
                    jid[ index ][ 'name' ] = job_line.split()[ 1 ]

                    if ( jid[ index ][ 'status' ] == 'RUNNING' ):
                        _, sout, _ = Authentificator._execute_remote_command(
                            Authentificator.ssh_client,
                            f"sacct -j {job_id} -o ElapsedRaw,TimelimitRaw --noheader --parsable2 | head -n 1 " )
                        progress_line = sout.strip().split( "|" )
                        jid[ index ][ 'slprogress' ] = str(
                            float( progress_line[ 0 ] ) / float( progress_line[ 1 ] ) / 60 * 100 )

                        # getthe completed status
                        pattern = re.compile( r'\((\d+(?:\.\d+)?)%\s*completed\)' )
                        _, sout, _ = Authentificator._execute_remote_command(
                            Authentificator.ssh_client,
                            f"grep \"completed\" {self._server.state.simulation_remote_path}/job_GEOS_{job_id}.out | tail -1"
                        )
                        m = pattern.search( sout.strip() )
                        if m:
                            jid[ index ][ 'simprogress' ] = str( m.group( 1 ) )

                    print(
                        f"{job_line}-{job_id}\n job id:{jid[index]['job_id']}\n status:{jid[index]['status']}\n name:{jid[index]['name']} \n --- \n"
                    )
                self._server.state.job_ids = jid
                self._server.state.dirty( "job_ids" )
                self._server.state.flush()

            except PermissionError as e:
                print( f"Permission error: {e}" )
            except IOError as e:
                print( f"Error accessing remote file or path: {e}" )
            except Exception as e:
                print( f"An error occurred during SFTP: {e}" )

            return None
        else:
            return None

    @staticmethod
    def render_and_run( template_name: str, dest_name: str, server: Server, **kwargs: Any ) -> str:
        """Render the slurm template and run it. Return it job_id."""
        if server.state.access_granted and server.state.simulation_xml_filename:
            template = Environment(
                loader=FileSystemLoader( f'{os.getenv("TRAME_DIR")}/app/io/jinja_t' ) ).get_template( template_name )
            rendered = template.render( kwargs )

            if Authentificator.ssh_client:
                #write slurm directly on remote
                try:
                    sftp = Authentificator.ssh_client.open_sftp()
                    remote_path = Path( server.state.simulation_remote_path ) / Path( dest_name )
                    with sftp.file( str( remote_path ), 'w' ) as f:
                        f.write( rendered )

                except PermissionError as e:
                    print( f"Permission error: {e}" )
                except IOError as e:
                    print( f"Error accessing remote file or path: {e}" )
                except Exception as e:
                    print( f"An error occurred during SFTP: {e}" )

                _, sout, _ = Authentificator._execute_remote_command(
                    Authentificator.ssh_client, f'cd {server.state.simulation_remote_path} && sbatch {dest_name}' )
                job_lines = sout.strip()
                job_id = re.search( r"Submitted batch job (\d+)", job_lines )
                if job_id:
                    server.state.job_ids.append( { 'job_id': job_id.group( 1 ) } )
                    return job_id.group( 1 )
                else:
                    return "-1"
            else:
                return "-1"
        else:
            return "-1"

    @staticmethod
    def gen_tree( xml_filename: Any ) -> dict:
        """Generate file tree to be copied on remote from files uploaded."""
        import re
        xml_pattern = re.compile( r"\.xml$", re.IGNORECASE )
        mesh_pattern = re.compile( r"\.(vtu|vtm|pvtu|pvtm)$", re.IGNORECASE )
        table_pattern = re.compile( r"\.(txt|dat|csv|geos)$", re.IGNORECASE )
        xml_matches = []
        mesh_matches = []
        table_matches = []

        pattern_file = r"[\w\-.]+\.(?:vtu|pvtu|dat|txt|xml|geos)\b"  # all files
        pattern_xml_path = r"\"(.*/)*([\w\-.]+\.(?:xml))\b"
        pattern_mesh_path = r"\"(.*/)*([\w\-.]+\.(?:vtu|pvtu|vtm|pvtm))\b"
        pattern_table_curly_path = r"((?:[\w\-/]+/)+)*([\w\-.]+\.(?:geos|csv|dat|txt))"

        for file in xml_filename:
            if xml_pattern.search( file.get( "name", "" ) ):
                xml_matches.append( file )
            elif mesh_pattern.search( file.get( "name", "" ) ):
                mesh_matches.append( file )
            elif table_pattern.search( file.get( "name", "" ) ):
                table_matches.append( file )

        #assume the first XML is the main xml
        xml_expected_file_matches = re.findall( pattern_file, xml_matches[ 0 ][ 'content' ].decode( "utf-8" ) )

        #TODO all the needed files
        test_assert = { item.get( "name" ) for item in xml_filename }.intersection( set( xml_expected_file_matches ) )
        assert test_assert

        decoded = re.sub( pattern_xml_path, r'"\2', xml_matches[ 0 ][ 'content' ].decode( "utf-8" ) )
        decoded = re.sub( pattern_mesh_path, r'"mesh/\2', decoded )
        decoded = re.sub( pattern_table_curly_path, r"tables/\2", decoded )

        xml_matches[ 0 ][ 'content' ] = decoded.encode( "utf-8" )

        FILE_TREE = {
            'root': '.',
            "structure": {
                "files": xml_matches,
                "subfolders": {
                    "mesh": mesh_matches,
                    "tables": table_matches
                }
            }
        }
        return FILE_TREE

from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass, field, fields
from enum import Enum, unique, auto
from typing import Callable, Optional, Union
import datetime
from trame_server.core import Server
from trame_server.state import State

from geos.trame.app.io.ssh_tools import Authentificator, SimulationConstant
from geos.trame.app.utils.async_file_watcher import AsyncPeriodicRunner

from jinja2 import Environment, FileSystemLoader
import paramiko
import re
import os


#TODO move outside

# Load template from file
# with open("slurm_job_template.j2") as f:
# template = Template(f.read())

#TODO from private-assets
# template_str = """#!/bin/sh
# #SBATCH --job-name="{{ job_name }}"
# #SBATCH --ntasks={{ ntasks }}
# #SBATCH --partition={{ partition }}
# #SBATCH --comment={{ comment_gr }}
# #SBACTH --account={{ account }}
# #SBATCH --nodes={{ nodes }}
# #SBATCH --time={{ time | default('00:10:00') }}
# #SBATCH --mem={{ mem }}
# #SBATCH --output=job_GEOS_%j.out
# #SBATCH --error=job_GEOS_%j.err

# ulimit -s unlimited
# ulimit -c unlimited

# module purge

# export HDF5_USE_FILE_LOCKING=FALSE
# export OMP_NUM_THREADS=1

# srun --mpi=pmix_v3 --hint=nomultithread \
#     -n {{ ntasks }} geos \
#     -o Outputs_${SLURM_JOBID} \
#     -i {{ input_file | default('geosDeck.xml') }} | tee Outputs_${SLURM_JOBID}/log_${SLURM_JOBID}.out

# """

# template_cb = """#!/bin/sh
# #SBATCH --job-name="{{ job_name }}"
# #SBATCH --ntasks={{ ntasks }}
# #SBATCH --partition={{ partition }} 
# #SBATCH --comment={{ comment_gr }}
# #SBACTH --account={{ account }}
# #SBATCH --nodes={{ nodes }}
# #SBATCH --time={{ time | default('00:10:00') }}
# #SBATCH --mem={{ mem }}
# #SBATCH --output=job_GEOS_%j.out
# #SBATCH --err=job_GEOS_%j.err
# #SBATCH --dependency=afterok:{{ dep_job_id }}

# srun tar cfz {{ dep_job_id }}.tgz Outputs_{{ dep_job_id }}/ && mv -v {{ dep_job_id }}.tgz {{ target_dl_path }}

# """
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

    @classmethod
    def from_string( cls, job_str ) -> "SlurmJobStatus":
        try:
            return cls( job_str )
        except ValueError:
            return cls.UNKNOWN

@dataclass
class LauncherParams:
    simulation_files_path: Optional[ str ] = None
    simulation_cmd_filename: Optional[ str ] = None
    simulation_job_name: Optional[ str ] = None
    simulation_nb_process: int = 1

    @classmethod
    def from_server_state( cls, server_state: State ) -> "LauncherParams":
        state = cls()
        for f in fields( cls ):
            setattr( state, f.name, server_state[ f.name ] )
        return state

    def is_complete( self ) -> bool:
        return None not in [ getattr( self, f.name ) for f in fields( self ) ]

    def assert_is_complete( self ) -> None:
        if not self.is_complete():
            raise RuntimeError( f"Incomplete simulation launch parameters : {self}." )


def get_timestamp() -> str:
    return datetime.utcnow().strftime( "%Y-%m-%d_%H-%M-%S.%f" )[ :-3 ]


def get_simulation_output_file_name( timestamp: str, user_name: str = "user_name" ):
    return f"{user_name}_{timestamp}.json"


# def write_simulation_information_to_repo(info: SimulationInformation, sim_info_path: Path) -> Optional[Path]:
#     return write_file(
#         sim_info_path.as_posix(),
#         get_simulation_output_file_name(info.timestamp, info.user_igg),
#         json.dumps(info.to_dict()),  # type: ignore
#     )

# def get_simulation_screenshot_timestep(filename: str) -> int:
#     """
#     From a given file name returns the time step.
#     Filename is defined as: RenderView0_000000.png with 000000 the time step to parse and return
#     """
#     if not filename:
#         print("Simulation filename is not defined")
#         return -1

#     pattern = re.compile(r"RenderView[0-9]_[0-9]{6}\.png", re.IGNORECASE)
#     if pattern.match(filename) is None:
#         print("Simulation filename does not match the pattern:  RenderView0_000000.png")
#         return -1

#     timestep = os.path.splitext(filename)[0].split("_")[-1]
#     return int(timestep) if timestep else -1

# def get_most_recent_file_from_list(files_list: list[str]) -> Optional[str]:
#     if not files_list:
#         return None
#     return max(files_list, key=get_simulation_screenshot_timestep)

# def get_most_recent_simulation_screenshot(folder_path: Path) -> Optional[str]:
#     return get_most_recent_file_from_list(os.listdir(folder_path)) if folder_path.exists() else None


class ISimRunner( ABC ):
    """
    Abstract interface for sim runner.
    Provides methods to trigger simulation, get simulation output path and knowing if simulation is done or not.
    """
    pass
    # @abstractmethod
    # def launch_simulation(self, launcher_params: LauncherParams) -> tuple[Path, SimulationInformation]:
    #     pass

    # @abstractmethod
    # def get_user_igg(self) -> str:
    #     pass

    # @abstractmethod
    # def get_running_user_jobs(self) -> list[tuple[str, SlurmJobStatus]]:
    #     pass


class SimRunner( ISimRunner ):
    """
    Runs sim on HPC. Wrap paramiko use
    """

    def __init__( self, user ):
        super().__init__()

        # early test
        self.local_upload_file = "test_upload.txt"
        import time
        with open( self.local_upload_file, "w" ) as f:
            f.write( f"This file was uploaded at {time.ctime()}\n" )
        print( f"Created local file: {self.local_upload_file}" )


class Simulation:
    """
    Simulation component.
    Fills the UI with the screenshot as read from the simulation outputs folder and a graph with the time series
    from the simulation.
    Requires a simulation runner providing information on the output path of the simulation to monitor and ways to
    trigger the simulation.
    """

    def __init__( self, sim_runner: ISimRunner, server: Server, sim_info_dir: Optional[ Path ] = None ) -> None:
        self._server = server
        controller = server.controller
        self._sim_runner = sim_runner
        self._sim_info_dir = sim_info_dir or SimulationConstant.SIMULATIONS_INFORMATION_FOLDER_PATH
        server.state.job_ids = []

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
                SimulationConstant.HOST,  #test 
                SimulationConstant.PORT,
                server.state.login,
                key=Authentificator.get_key( server.state.login, server.state.password ) )

            if Authentificator.ssh_client:
                server.state.access_granted = True

        @staticmethod
        def gen_tree( xml_filename ):

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
            test_assert = { item.get( "name" )
                            for item in xml_filename }.intersection( set( xml_expected_file_matches ) )
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



        @controller.trigger( "run_simulation" )
        def run_simulation() -> None:

            # if server.state.access_granted and server.state.sd and server.state.simulation_xml_filename:
            if server.state.access_granted and server.state.simulation_xml_filename:    
                if Authentificator.ssh_client:
                    
                    Authentificator._sftp_copy_tree( Authentificator.ssh_client,
                                                     gen_tree( server.state.simulation_xml_filename ),
                                                     server.state.simulation_remote_path )
                    
                    # sdi = server.state.sd
                    ci = { 'nodes': 1, 'total_ranks': 2 }
                    run_id : int = Simulation.render_and_run('p4_slurm.jinja','job.slurm', server,
                                   job_name=server.state.simulation_job_name,
                                            input_file=[ item for item in server.state.simulation_xml_filename if item.get( 'type' ) == 'text/xml'][ 0 ].get( 'name' ),
                                            nodes=ci[ 'nodes' ],
                                            ntasks=ci[ 'total_ranks' ],
                                            mem=f"0",
                                            comment_gr=server.state.slurm_comment,
                                            partition='p4_dev',
                                            account='myaccount')
                    
                    Simulation.render_and_run('p4_copyback.jinja', 'copyback.slurm', server,
                                    job_name=server.state.simulation_job_name,
                                            input_file=[ item for item in server.state.simulation_xml_filename if item.get( 'type' ) == 'text/xml' ][ 0 ].get( 'name' ),
                                            nodes=ci[ 'nodes' ],
                                            ntasks=ci[ 'total_ranks' ],
                                            mem=f"0",
                                            dep_job_id=run_id,
                                            comment_gr=server.state.slurm_comment,
                                            partition='p4_transfert',
                                            account='myaccount' )

                    self.start_result_streams()

                else:
                    raise paramiko.SSHException

        @controller.trigger( "kill_all_simulations" )
        def kill_all_simulations() -> None:
            # exec scancel jobid
            for jobs in server.state.job_ids:
                Authentificator.kill_job( jobs[ 'job_id' ] )

    def __del__( self ):
        self.stop_result_streams()

    def set_status_watcher_period_ms( self, period_ms ):
        self._job_status_watcher_period_ms = period_ms
        if self._job_status_watcher:
            self._job_status_watcher.set_period_ms( period_ms )

    def _update_job_status( self ) -> None:
        sim_info = self.get_last_user_simulation_info()
        job_status = sim_info.get_simulation_status( self._sim_runner.get_running_user_jobs )
        sim_path = sim_info.get_simulation_dir( job_status )

        self._server.controller.set_simulation_status( job_status )
        self._server.controller.set_simulation_time_stamp( sim_info.timestamp )

        self._update_screenshot_display( sim_info.get_screenshot_path( sim_path ) )
        self._update_plots( sim_info.get_timeseries_path( sim_path ) )

        # Stop results stream if job is done
        if job_status == SimulationStatus.DONE:
            self.stop_result_streams()

    # TODO: might be useful for history
    #
    # def get_last_user_simulation_info(self) -> SimulationInformation:
    #     last_sim_information = self.get_last_information_path()
    #     return SimulationInformation.from_file(last_sim_information)

    # def get_last_information_path(self) -> Optional[Path]:
    #     user_igg = self._sim_runner.get_user_igg()

    #     user_files = list(reversed(sorted(self._sim_info_dir.glob(f"{user_igg}*.json"))))
    #     if not user_files:
    #         return None
    #
    #   return user_files[0]

    def stop_result_streams( self ):
        if self._job_status_watcher is not None:
            self._job_status_watcher.stop()

    def start_result_streams( self ) -> None:
        self.stop_result_streams()

        self._job_status_watcher = AsyncPeriodicRunner( self.check_jobs, period_ms=self._job_status_watcher_period_ms )

    def check_jobs( self ):
        if Authentificator.ssh_client:
            try:
                jid = self._server.state.job_ids
                for index, job in enumerate( jid ):
                    job_id = job[ 'job_id' ]
                    _, sout, _ = Authentificator._execute_remote_command(
                        Authentificator.ssh_client, f'sacct -j {job_id} -o JobID,JobName,State --noheader' )
                    job_line = sout.strip().split( "\n" )[ -1 ]

                    jid[ index ][ 'status' ] = job_line.split()[ 2 ]
                    #  OLD COPY BACK POLICY
                    # if ( jid[ index ][ 'status' ] == 'COMPLETED' ):
                    #     # tar and copy back
                    #     Authentificator._execute_remote_command(
                    #         Authentificator.ssh_client,
                    #         f'cd {self._server.state.simulation_remote_path} && tar cvfz {job_id}.tgz Outputs_{job_id}/'
                    #     )
                    #     Authentificator._transfer_file_sftp(
                    #         Authentificator.ssh_client,
                    #         f'{self._server.state.simulation_dl_path}/{job_id}.tgz',
                    #         f'{self._server.state.simulation_remote_path}/{job_id}.tgz',
                    #         direction='get' )
                    if ( jid[ index ][ 'status' ] == 'RUNNING' ):
                        # getthe completed status
                        pattern = re.compile( r'\((\d+(?:\.\d+)?)%\s*completed\)' )
                        with Authentificator.ssh_client.open_sftp().file(
                                str(
                                    Path( self._server.state.simulation_remote_path ) /
                                    Path( f"job_GEOS_{job_id}.out" ) ), "r" ) as f:
                            for line in f:
                                m = pattern.search( line )
                                if m:
                                    self._server.state.simulation_progress = str( m.group( 1 ) )

                    jid[ index ][ 'name' ] = job_line.split()[ 1 ]
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
        else:
            return None

        @staticmethod
        def render_and_run(template_name: str, dest_name: str , server,  **kwargs) -> int :
            """Render the slurm template and run it. Return it job_id"""

            if server.state.access_granted and server.state.simulation_xml_filename:
                template = Environment(load=FileSystemLoader('jinja_t')).get_template(template)
                rendered = template.render(kwargs)

                if Authentificator.ssh_client:
                    #write slurm directly on remote
                    try:
                        sftp = Authentificator.ssh_client.open_sftp()
                        remote_path = Path( server.state.simulation_remote_path ) / Path( dest_name )
                        with sftp.file( str( remote_path ), 'w' ) as f:
                            f.write( rendered )

                    # except FileExistsError:
                    # print(f"Error: Local file '{remote_path}' not found.")
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
                    server.state.job_ids.append( { 'job_id': job_id[ 1 ] } )

                    return job_id[1]

    # def start_simulation( self ) -> None:
    #     state = self._server.state
    #     script_path = None
    #     try:
    #         launcher_params = LauncherParams.from_server_state( self._server.state )
    #         launcher_params.assert_is_complete()

    #         script_path, sim_info = self._sim_runner.launch_simulation( launcher_params )
    #         self._write_sim_info( launcher_params, sim_info )
    #         self.start_result_streams()
    #         state.simulation_error = ""
    #     except Exception as e:
    #         print( "Error occurred: ", e )
    #         state.simulation_error = str( e )
    #     finally:
    #         state.avoid_rewriting = False
    #         if isinstance( script_path, Path ) and script_path.is_file():
    #             os.remove( script_path )


# def path_to_string( p: Union[ str, Path ] ) -> str:
#     return Path( p ).as_posix()

# def write_file( folder_path: str, filename: str, file_content: str ) -> Optional[ Path ]:
#     try:
#         Path( folder_path ).mkdir( exist_ok=True )
#         file_path = Path( f"{folder_path}/{filename}" )
#         with open( file_path, "w" ) as f:
#             f.write( file_content )
#         return file_path.absolute()
#     except Exception as e:
#         print( "error occurred when copying file to", folder_path, e )
#     return None


from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass, field, fields
from enum import Enum, unique
from geos.trame.app.ui.simulation_status_view import SimulationStatus
from typing import Callable, Optional, Union
import datetime
from trame_server.core import Server
from trame_server.state import State
from geos.trame.app.utils.async_file_watcher import AsyncPeriodicRunner

from jinja2 import Template
import paramiko
import re
import os

#TODO move outside
#TODO use Jinja on real launcher

@dataclass(frozen=True)
class SimulationConstant:
    SIMULATION_GEOS_PATH = "/workrd/users/"
    HOST = "p4log01"  # Only run on P4 machine
    REMOTE_HOME_BASE = "/users"
    PORT = 22
    SIMULATIONS_INFORMATION_FOLDER_PATH= "/workrd/users/"
    SIMULATION_DEFAULT_FILE_NAME = "geosDeck.xml"

    # replace by conf-file json


# Load template from file
# with open("slurm_job_template.j2") as f:
    # template = Template(f.read())

#TODO from private-assets
template_str = """#!/bin/sh
#SBATCH --job-name="{{ job_name }}"
#SBATCH --ntasks={{ ntasks }}
#SBATCH --partition={{ partition }}
#SBATCH --comment={{ comment }}
#SBACTH --account={{ account }}
#SBATCH --nodes={{ nodes }}
#SBATCH --time={{ time | default('24:00:00') }}
#SBATCH --mem={{ mem }}
#SBATCH --output=job_GEOS_%j.out
#SBATCH --error=job_GEOS_%j.err

ulimit -s unlimited
ulimit -c unlimited

module purge
module use /workrd/SCR/GEOS/l1092082/modules
module load geos-develop-d36028cb-hypreUpdate

export HDF5_USE_FILE_LOCKING=FALSE
export OMP_NUM_THREADS=1

srun --mpi=pmix_v3 --hint=nomultithread \
    -n {{ ntasks }} geos \
    -o Outputs_${SLURM_JOBID} \
    -i {{ input_file | default('geosDeck.xml') }} | tee Outputs_${SLURM_JOBID}/log_${SLURM_JOBID}.out

"""



class Authentificator:#namespacing more than anything else

    ssh_client : Optional[paramiko.SSHClient] = None

    @staticmethod
    def _sftp_copy_tree(ssh_client, file_tree,  remote_root):
        # Connect to remote server
        sftp = ssh_client.open_sftp()
        
        Authentificator.dfs_tree(file_tree["structure"], file_tree["root"], sftp=sftp, remote_root=remote_root)

        sftp.close()

    @staticmethod
    def dfs_tree(node, path, sftp, remote_root):

        lp = Path(path)
        rp = Path(remote_root)/lp

        if isinstance(node, list):
            for file in node:
                # sftp.put(lp/Path(file), rp/Path(file))
                with sftp.file( str(rp/Path(file.get('name'))), 'w') as f:
                        f.write(file.get('content'))
                print(f"copying {lp/Path(file.get('name'))} to {rp/Path(file.get('name'))}")
        elif isinstance(node, dict):
            if "files" in node:
                for file in node["files"]:
                    # sftp.put( str(lp/Path(file)), str(rp/Path(file)) )
                    with sftp.file( str(rp/Path(file.get('name'))), 'w') as f:
                        f.write(file.get('content'))
                    print(f"copying {lp/Path(file.get('name'))} to {rp/Path(file.get('name'))}")
            if "subfolders" in node:
                for subfolder, content in node["subfolders"].items():
                    try:
                        sftp.stat( str(rp/Path(subfolder)) )
                    except FileNotFoundError:
                        print(f"creating {rp/Path(subfolder)}")
                        sftp.mkdir( str(rp/Path(subfolder)) ) 
                    Authentificator.dfs_tree(content, lp/Path(subfolder), sftp, remote_root)
            
            for folder, content in node.items():
                if folder not in ["files", "subfolders"]:
                    try:
                        sftp.stat( str(rp/Path(folder)) )
                    except FileNotFoundError:
                        print(f"creating {rp/Path(folder)}")
                        sftp.mkdir( str(rp/Path(folder)) ) 
                    Authentificator.dfs_tree(content, lp/Path(folder), sftp, remote_root)

    @staticmethod
    def kill_job( id ):
        if Authentificator.ssh_client:
            Authentificator._execute_remote_command(Authentificator.ssh_client, f"scancel {id}")
        return None

    @staticmethod
    def get_key( id, pword ):

        try:
            home = os.environ.get("HOME")
            PRIVATE_KEY = paramiko.RSAKey.from_private_key_file(f"{home}/.ssh/id_trame")
            return PRIVATE_KEY
        except paramiko.SSHException as e:
            print(f"Error loading private key: {e}\n")
        except FileNotFoundError as e:
            print(f"Private key not found: {e}\n Generating key ...")
            PRIVATE_KEY = Authentificator.gen_key()
            temp_client = paramiko.SSHClient()
            temp_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            temp_client.connect(SimulationConstant.HOST, SimulationConstant.PORT, username=id, password=pword, timeout=10)
            Authentificator._transfer_file_sftp(temp_client,f"{home}/.ssh/id_trame.pub",f"{SimulationConstant.REMOTE_HOME_BASE}/{id}/.ssh/id_trame.pub")
            Authentificator._execute_remote_command(temp_client,f" cat {SimulationConstant.REMOTE_HOME_BASE}/{id}/.ssh/id_trame.pub | tee -a {SimulationConstant.REMOTE_HOME_BASE}/{id}/.ssh/authorized_keys")

            return PRIVATE_KEY


    @staticmethod
    def gen_key():  

        home = os.environ.get("HOME")
        file_path = f"{home}/.ssh/id_trame"
        key = paramiko.RSAKey.generate(bits=4096)
        key.write_private_key_file(file_path)
        
        # Get public key in OpenSSH format
        public_key = f"{key.get_name()} {key.get_base64()}"
        with open(file_path + ".pub", "w") as pub_file:
            pub_file.write(public_key)

        print("SSH key pair generated: id_trame (private), id_trame.pub (public)")

        return key
    

    @staticmethod
    def _create_ssh_client( host, port, username, password=None, key=None) -> paramiko.SSHClient:
        """
        Initializes and returns an SSH client connection.
        Uses context manager for automatic cleanup.
        """
        client = paramiko.SSHClient()
        # Automatically adds the hostname and new host keys to the host files (~/.ssh/known_hosts)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            print(f"Connecting to {host} using key-based authentication...")
            client.connect(host, port, username, pkey=key, timeout=10)

            return client
        except paramiko.AuthenticationException:
            print("Authentication failed. Check your credentials or key.")
            return None
        except paramiko.SSHException as e:
            print(f"Could not establish SSH connection: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None


    @staticmethod
    def _execute_remote_command(client, command):
        """
        Executes a single command on the remote server and prints the output.
        """
        if not client:
            return

        print(f"\n--- Executing Command: '{command}' ---")
        try:
            # Executes the command. stdin, stdout, and stderr are file-like objects.
            # Ensure command ends with a newline character for some shell environments.
            stdin, stdout, stderr = client.exec_command(command)

            # Wait for the command to finish and read the output
            exit_status = stdout.channel.recv_exit_status()

            # Print standard output
            stdout_data = stdout.read().decode().strip()
            if stdout_data:
                print("STDOUT:")
                print(stdout_data)

            # Print standard error (if any)
            stderr_data = stderr.read().decode().strip()
            if stderr_data:
                print("STDERR:")
                print(stderr_data)

            print(f"Command exited with status: {exit_status}")
            return (exit_status,stdout_data, stderr_data)
        
        except Exception as e:
            print(f"Error executing command: {e}")
            return (-1,"","")

    @staticmethod
    def _transfer_file_sftp(client, local_path, remote_path, direction="put"):
        """
        Transfers a file using SFTP (Secure File Transfer Protocol).
        Direction can be 'put' (upload) or 'get' (download).
        """
        if not client:
            return

        print(f"\n--- Starting SFTP Transfer ({direction.upper()}) ---")
        
        try:
            # Establish an SFTP connection session
            sftp = client.open_sftp()

            if direction == "put":
                print(f"Uploading '{local_path}' to '{remote_path}'...")
                sftp.put(local_path, remote_path)
                print("Upload complete.")
            elif direction == "get":
                print(f"Downloading '{remote_path}' to '{local_path}'...")
                sftp.get(remote_path, local_path)
                print("Download complete.")
            else:
                print("Invalid transfer direction. Use 'put' or 'get'.")

            sftp.close()
            return True
        
        except FileNotFoundError:
            print(f"Error: Local file '{local_path}' not found.")
            return False
        except IOError as e:
            print(f"Error accessing remote file or path: {e}")
            return False
        except Exception as e:
            print(f"An error occurred during SFTP: {e}")
            return False


@unique
class SlurmJobStatus(Enum):
    PENDING = "PEND"
    RUNNING = "R"
    COMPLETING = "CG"
    COMPLETED = "CD"
    SUSPENDED = "S"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_string(cls, job_str) -> "SlurmJobStatus":
        try:
            return cls(job_str)
        except ValueError:
            return cls.UNKNOWN
        
# TODO: dataclass_json
# @dataclass_json
@dataclass
class SimulationInformation:

    def get_simulation_status(
        self,
        get_running_user_jobs_f: Callable[[], list[tuple[str, SlurmJobStatus]]],
    ) -> SimulationStatus:
        """
        Returns the simulation status given the current Jobs running for the current user.
        Only runs the callback if the timeseries file is not already present in the done directory.
        """
        if not self.geos_job_id:
            return SimulationStatus.NOT_RUN

        done_sim_path = self.get_simulation_dir(SimulationStatus.DONE)
        if self.get_timeseries_path(done_sim_path).exists():
            return SimulationStatus.DONE

        user_jobs = get_running_user_jobs_f()
        if (self.geos_job_id, SlurmJobStatus.RUNNING) in user_jobs:
            return SimulationStatus.RUNNING

        if (self.geos_job_id, SlurmJobStatus.COMPLETING) in user_jobs:
            return SimulationStatus.COMPLETING

        if (self.copy_back_job_id, SlurmJobStatus.RUNNING) in user_jobs:
            return SimulationStatus.COPY_BACK

        if (self.copy_job_id, SlurmJobStatus.RUNNING) in user_jobs:
            return SimulationStatus.SCHEDULED

        return SimulationStatus.UNKNOWN
    
@dataclass
class LauncherParams:
    simulation_files_path: Optional[str] = None
    simulation_cmd_filename: Optional[str] = None
    simulation_job_name: Optional[str] = None
    simulation_nb_process: int = 1

    @classmethod
    def from_server_state(cls, server_state: State) -> "LauncherParams":
        state = cls()
        for f in fields(cls):
            setattr(state, f.name, server_state[f.name])
        return state

    def is_complete(self) -> bool:
        return None not in [getattr(self, f.name) for f in fields(self)]

    def assert_is_complete(self) -> None:
        if not self.is_complete():
            raise RuntimeError(f"Incomplete simulation launch parameters : {self}.")


def get_timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def get_simulation_output_file_name(timestamp: str, user_name: str = "user_name"):
    return f"{user_name}_{timestamp}.json"


def parse_launcher_output(output: str) -> SimulationInformation:
    split_output = output.split("\n")

    information = SimulationInformation()
    information_dict = information.to_dict()  # type: ignore

    content_to_parse = [
        ("Working directory: ", "working_directory"),
        ("1. copy job id: ", "copy_job_id"),
        ("2. geos job id: ", "geos_job_id"),
        ("3. copy back job id: ", "copy_back_job_id"),
        ("Run directory: ", "run_directory"),
    ]

    for line in split_output:
        for info_tuple in content_to_parse:
            if info_tuple[0] in line:
                split_line = line.split(info_tuple[0])
                if len(split_line) < 2:
                    continue
                information_dict[info_tuple[1]] = split_line[-1]

    information_dict["timestamp"] = get_timestamp()
    return SimulationInformation.from_dict(information_dict)  # type: ignore


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


class ISimRunner(ABC):
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


class SimRunner(ISimRunner):
    """
    Runs sim on HPC. Wrap paramiko use
    """

    def __init__(self, user):
        super().__init__()

        # early test
        self.local_upload_file = "test_upload.txt"
        import time
        with open(self.local_upload_file, "w") as f:
            f.write(f"This file was uploaded at {time.ctime()}\n")
        print(f"Created local file: {self.local_upload_file}")

  

class Simulation:
    """
    Simulation component.
    Fills the UI with the screenshot as read from the simulation outputs folder and a graph with the time series
    from the simulation.
    Requires a simulation runner providing information on the output path of the simulation to monitor and ways to
    trigger the simulation.
    """




    def __init__(self, sim_runner: ISimRunner, server: Server, sim_info_dir: Optional[Path] = None) -> None:
        self._server = server
        controller = server.controller
        self._sim_runner = sim_runner
        self._sim_info_dir = sim_info_dir or SimulationConstant.SIMULATIONS_INFORMATION_FOLDER_PATH
        server.state.job_ids = []

        server.state.status_colors = {
            "PENDING": "#4CAF50", #PD
            "RUNNING": "#3F51B5", #R
            "CANCELLED": "#FFC107", #CA
            "COMPLETED": "#484B45", #CD
            "FAILED": "#E53935", #F
        }
        self._job_status_watcher: Optional[AsyncPeriodicRunner] = None
        self._job_status_watcher_period_ms = 2000

    
        #define triggers
        @controller.trigger("run_try_login")
        def run_try_login() -> None:

            # if server.state.key:
            Authentificator.ssh_client = Authentificator._create_ssh_client(SimulationConstant.HOST,#test 
                                                     SimulationConstant.PORT, 
                                                     server.state.login, 
                                                     key=Authentificator.get_key(server.state.login, server.state.password))
            
            if Authentificator.ssh_client :
                # id = os.environ.get('USER')
                # Authentificator._execute_remote_command(Authentificator.ssh_client, f"ps aux")
                # Authentificator._execute_remote_command(Authentificator.ssh_client, f"ls -l {SimulationConstant.REMOTE_HOME_BASE}/{id}")
       
                # server.state.update({"access_granted" : True, "key_path" : f"{SimulationConstant.REMOTE_HOME_BASE}/{id}/.ssh/id_trame" })
                # server.state.flush()
                server.state.access_granted = True
                print("login login login")

        @staticmethod
        def gen_tree(xml_filename):

            import re
            xml_pattern = re.compile(r"\.xml$", re.IGNORECASE)
            mesh_pattern = re.compile(r"\.(vtu|vtm|pvtu|pvtm)$", re.IGNORECASE)
            table_pattern = re.compile(r"\.(txt|dat|csv|geos)$", re.IGNORECASE)
            xml_matches = []
            mesh_matches = []
            table_matches = []

            pattern_file = r"[\w\-.]+\.(?:vtu|pvtu|dat|txt|xml|geos)\b" # all files
            pattern_xml_path = r"\"(.*/)([\w\-.]+\.(?:xml))\b"
            pattern_mesh_path = r"\"(.*/)([\w\-.]+\.(?:vtu|pvtu|vtm|pvtm))\b"
            pattern_table_curly_path = r"((?:[\w\-/]+/)+)([\w\-.]+\.(?:geos|csv|dat|txt))"

            for file in xml_filename:
                if xml_pattern.search(file.get("name","")):
                    xml_matches.append(file)
                elif mesh_pattern.search(file.get("name","")):
                    mesh_matches.append(file) 
                elif table_pattern.search(file.get("name","")): 
                    table_matches.append(file) 


            #assume the first XML is the main xml 
            # TODO relocate
            xml_expected_file_matches = re.findall(pattern_file, xml_matches[0]['content'].decode("utf-8"))
            test_assert = {item.get("name") for item in xml_filename}.intersection(set(xml_expected_file_matches))

            decoded = re.sub(pattern_xml_path,r'"\2', xml_matches[0]['content'].decode("utf-8"))
            decoded = re.sub(pattern_mesh_path,r'"mesh/\2', decoded)
            decoded = re.sub(pattern_table_curly_path,r"tables/\2", decoded)

            xml_matches[0]['content'] = decoded.encode("utf-8")


            file_tree = {
            'root' : '.',     
            "structure": {
                "files" : xml_matches,
                "subfolders": {
                   "mesh": mesh_matches,
                   "tables": table_matches
                }
            }
        }
            return file_tree


        @controller.trigger("run_simulation")
        def run_simulation()-> None:
            
            # if server.state.access_granted and server.state.sd and server.state.simulation_xml_filename:
            if server.state.access_granted and server.state.simulation_xml_filename:
                template = Template(template_str)
                # sdi = server.state.sd
                ci ={'nodes': 2 , 'total_ranks': 96 }
                rendered = template.render(job_name=server.state.simulation_job_name,
                                           input_file=server.state.simulation_xml_filename,
                                           nodes= ci['nodes'], ntasks=ci['total_ranks'], mem=f"0",#TODO profile to use the correct amount
                                           commment=server.state.slurm_comment, partition='p4_general', account='myaccount' )

                # with open(Path(server.state.simulation_xml_filename).parent/Path('job.slurm'),'w') as f:
                    # f.write(rendered)
                
                if Authentificator.ssh_client:
                    #write slurm directly on remote
                    try:
                        sftp = Authentificator.ssh_client.open_sftp()
                        remote_path = Path(server.state.simulation_remote_path)/Path('job.slurm')
                        with sftp.file( str(remote_path),'w' ) as f:
                            f.write(rendered)

                    # except FileExistsError:
                        # print(f"Error: Local file '{remote_path}' not found.")
                    except PermissionError as e:
                        print(f"Permission error: {e}")
                    except IOError as e:
                        print(f"Error accessing remote file or path: {e}")
                    except Exception as e:
                        print(f"An error occurred during SFTP: {e}")

                    Authentificator._sftp_copy_tree(Authentificator.ssh_client,
                                    gen_tree(server.state.simulation_xml_filename),
                                    server.state.simulation_remote_path)

                    
                    _,sout, serr = Authentificator._execute_remote_command(Authentificator.ssh_client,
                                                            f'cd {server.state.simulation_remote_path} && sbatch job.slurm')
                    

                    
                    #TODO encapsulate
                    job_lines = sout.strip()
                    job_id = re.search(r"Submitted batch job (\d+)", job_lines)

                    server.state.job_ids.append({'job_id':job_id[1]})
                    

                    

                    # Authentificator._execute_remote_command(Authentificator.ssh_client,
                    #                                         f'squeue -u $USER')
                    self.start_result_streams()
                    

                    Authentificator._transfer_file_sftp(Authentificator.ssh_client,
                                                        remote_path=f'{server.state.simulation_remote_path}/log.out',
                                                        local_path=f'{server.state.simulation_dl_path}/dl.test',
                                                        direction="get")

                else:
                    raise paramiko.SSHException


        @controller.trigger("kill_all_simulations")
        def kill_all_simulations()->None:
            # exec scancel jobid
            for jobs in server.state.job_ids:
                Authentificator.kill_job(jobs['job_id'])

    def __del__(self):
        self.stop_result_streams()

    def set_status_watcher_period_ms(self, period_ms):
        self._job_status_watcher_period_ms = period_ms
        if self._job_status_watcher:
            self._job_status_watcher.set_period_ms(period_ms)

    def _update_job_status(self) -> None:
        sim_info = self.get_last_user_simulation_info()
        job_status = sim_info.get_simulation_status(self._sim_runner.get_running_user_jobs)
        sim_path = sim_info.get_simulation_dir(job_status)

        self._server.controller.set_simulation_status(job_status)
        self._server.controller.set_simulation_time_stamp(sim_info.timestamp)

        self._update_screenshot_display(sim_info.get_screenshot_path(sim_path))
        self._update_plots(sim_info.get_timeseries_path(sim_path))

        # Stop results stream if job is done
        if job_status == SimulationStatus.DONE:
            self.stop_result_streams()

    def get_last_user_simulation_info(self) -> SimulationInformation:
        last_sim_information = self.get_last_information_path()
        return SimulationInformation.from_file(last_sim_information)

    def get_last_information_path(self) -> Optional[Path]:
        user_igg = self._sim_runner.get_user_igg()

        user_files = list(reversed(sorted(self._sim_info_dir.glob(f"{user_igg}*.json"))))
        if not user_files:
            return None

        return user_files[0]

    def stop_result_streams(self):
        if self._job_status_watcher is not None:
            self._job_status_watcher.stop()

    def start_result_streams(self) -> None:
        self.stop_result_streams()

        self._job_status_watcher = AsyncPeriodicRunner(
            self.check_jobs, period_ms=self._job_status_watcher_period_ms
        )

    def check_jobs(self):
        if Authentificator.ssh_client:
            try:
                # _,sout, serr = Authentificator._execute_remote_command(Authentificator.ssh_client, f'date && squeue -u $USER')
                #sacct -j <jobID> --format --format=JobID,State --noheader 
                jid = self._server.state.job_ids
                for index,job in enumerate(jid):
                    job_id = job['job_id']
                    _,sout, serr = Authentificator._execute_remote_command(Authentificator.ssh_client, f'sacct -j {job_id} -o JobID,JobName,State --noheader')
                    job_line = sout.strip().split("\n")[-1]
                    # index = next((i for i, item in enumerate(jid) if item.get("job_id") == job_id), None)
                    # if index is None:
                        # continue
                    # else:
                    jid[index]['status'] = job_line.split()[2]
                    jid[index]['name'] =  job_line.split()[1]
                    print(f"{job_line}-{job_id}\n job id:{jid[index]['job_id']}\n status:{jid[index]['status']}\n name:{jid[index]['name']} \n --- \n")
                self._server.state.job_ids = jid
                self._server.state.dirty("job_ids")
                self._server.state.flush()
                
            except PermissionError as e:
                print(f"Permission error: {e}")
            except IOError as e:
                print(f"Error accessing remote file or path: {e}")
            except Exception as e:
                print(f"An error occurred during SFTP: {e}")
        else:
            return None

            
    def start_simulation(self) -> None:
        state = self._server.state
        script_path = None
        try:
            launcher_params = LauncherParams.from_server_state(self._server.state)
            launcher_params.assert_is_complete()

            script_path, sim_info = self._sim_runner.launch_simulation(launcher_params)
            self._write_sim_info(launcher_params, sim_info)
            self.start_result_streams()
            state.simulation_error = ""
        except Exception as e:
            print("Error occurred: ", e)
            state.simulation_error = str(e)
        finally:
            state.avoid_rewriting = False
            if isinstance(script_path, Path) and script_path.is_file():
                os.remove(script_path)

    def _write_sim_info(self, launcher_params: LauncherParams, sim_info: Optional[SimulationInformation]) -> None:
        if sim_info is None:
            raise RuntimeError("Error parsing simulation launcher output.")

        # Make sure to save the absolute path to the working directory used by the launcher in case parsed information
        # is a relative Path
        if not Path(sim_info.working_directory).is_absolute():
            sim_info.working_directory = path_to_string(
                launcher_params.simulation_files_path + "/" + sim_info.working_directory
            )
        print("simulation information", sim_info)

        sim_info.user_igg = self._sim_runner.get_user_igg()
        write_simulation_information_to_repo(sim_info, self._sim_info_dir)


def path_to_string(p: Union[str, Path]) -> str:
    return Path(p).as_posix()

def write_simulation_information_to_repo(info: SimulationInformation, sim_info_path: Path) -> Optional[Path]:
    return write_file(
        sim_info_path.as_posix(),
        get_simulation_output_file_name(info.timestamp, info.user_igg),
        json.dumps(info.to_dict()),  # type: ignore
    )

def write_file(folder_path: str, filename: str, file_content: str) -> Optional[Path]:
    try:
        Path(folder_path).mkdir(exist_ok=True)
        file_path = Path(f"{folder_path}/{filename}")
        with open(file_path, "w") as f:
            f.write(file_content)
        return file_path.absolute()
    except Exception as e:
        print("error occurred when copying file to", folder_path, e)
    return None

from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass, field, fields
from enum import Enum, unique
from geos.trame.app.ui.simulationStatusView import SimulationStatus
from typing import Callable, Optional
import datetime
from trame_server.core import Server
from trame_server.state import State

#TODO move outside
@dataclass(frozen=True)
class SimulationConstant:
    SIMULATION_GEOS_PATH = "/some/path/"
    SIMULATION_MACHINE_NAME = "p4log01"  # Only run on P4 machine


@unique
class SlurmJobStatus(Enum):
    PENDING = "PD"
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
    pass

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


##TODO yay slurm
def get_launcher_command(launcher_params: LauncherParams) -> str:
    launcher_cmd_args = (
        f"{SimulationConstant.SIMULATION_GEOS_PATH} "
        f"--nprocs {launcher_params.simulation_nb_process} "
        f"--fname {launcher_params.simulation_cmd_filename} "
        f"--job_name {launcher_params.simulation_job_name}"
    )

    # state.simulation_nb_process  is supposed to be an integer, but the UI present a VTextField,
    # so if user changes it, then it can be defined as a str
    if int(launcher_params.simulation_nb_process) > 1:
        launcher_cmd_args += " --partition"
    return launcher_cmd_args


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

    @abstractmethod
    def launch_simulation(self, launcher_params: LauncherParams) -> tuple[Path, SimulationInformation]:
        pass

    @abstractmethod
    def get_user_igg(self) -> str:
        pass

    @abstractmethod
    def get_running_user_jobs(self) -> list[tuple[str, SlurmJobStatus]]:
        pass


class SimRunner(ISimRunner):
    """
    Runs sim on HPC
    """
    pass
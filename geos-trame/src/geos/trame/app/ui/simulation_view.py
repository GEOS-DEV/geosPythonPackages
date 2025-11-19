from trame.widgets import html
from trame.widgets import vuetify3 as vuetify

from geos.trame.app.io.simulation import SimulationConstant 
from geos.trame.app.ui.simulation_status_view import SimulationStatusView


def hint_config():

    return ["P4: 1x12", "P4: 2x6"]


def define_simulation_view(server) -> None:
    with vuetify.VContainer():
        with vuetify.VRow():
            with vuetify.VCol(cols=4):
                vuetify.VTextField(
                    v_model=("login", None,),
                    label="Login",
                    dense=True,
                    hide_details=True,
                    clearable=True,
                    prepend_icon="mdi-login"
                    )
            with vuetify.VCol(cols=4):
                vuetify.VTextField(
                    v_model=("password", None,),
                    label="Password",
                    type="password",
                    dense=True,
                    hide_details=True,
                    clearable=True,
                    prepend_icon="mdi-onepassword"
                    )
        
        #        
            access_granted = False # link to login button callback run_try_logging results
            items = hint_config()
            vuetify.VDivider(vertical=True, thickness=5, classes="mx-4")
            with vuetify.VCol(cols=2):
                vuetify.VSelect(label="Cluster",
                                items=("items",items))

        with vuetify.VRow():
            with vuetify.VCol(cols=8):
                vuetify.VFileInput(
                        v_model=("key_path", None,),
                        label="Path to ssh key",
                        dense=True,
                        hide_details=True,
                        clearable=True,
                        prepend_icon="mdi-key-chain-variant"
                        )
            
                #
            vuetify.VDivider(vertical=True, thickness=5, classes="mx-4")
            with vuetify.VCol(cols=2):
                vuetify.VBtn("Log in", click="trigger('run_try_logging')"),  # type: ignore

                
        vuetify.VDivider(thickness=5, classes="my-4")

        with vuetify.VRow():
            with vuetify.VCol():
                vuetify.VFileInput(
                    v_model=("simulation_cmd_filename", SimulationConstant.SIMULATION_DEFAULT_FILE_NAME),
                    label="Simulation file name",
                    dense=True,
                    hide_details=True,
                    clearable=True,
                    disabled=("!access_granted")
                )
            # with vuetify.VCol(cols=1):
            #     vuetify.VFileInput(
            #         v_model=("cmd_file", None),
            #         prepend_icon="mdi-file-upload-outline",
            #         hide_input=True,
            #         style="padding: 0;",
            #         disabled=("!simulation_files_path",),
            #     )

        with vuetify.VRow(), vuetify.VCol():
            vuetify.VTextField(
                v_model=(
                    "simulation_files_path",
                    None,
                ),
                label="Path where to write files and launch code",
                prepend_icon="mdi-upload",
                dense=True,
                hide_details=True,
                clearable=True,
                disabled=("!access_granted")
            # TODO callback validation of path
            )

        with vuetify.VRow(), vuetify.VCol():
            vuetify.VTextField(
                v_model=("simulation_dl_path",),
                label="Simulation download path",
                dense=True,
                clearable=True,
                prepend_icon="mdi-download",
                disabled=("!access_granted")
            # TODO callback validation of path
            )

        with vuetify.VRow(), vuetify.VCol():
            vuetify.VTextField(
                v_model=("simulation_job_name", "geosJob"),
                label="Job Name",
                dense=True,
                hide_details=True,
                clearable=True,
                disabled=("!access_granted")
            )
        with vuetify.VRow():
            vuetify.VSpacer()
            with vuetify.VCol(cols=1):
                vuetify.VBtn("Run", click="trigger('run_simulation')"),  # type: ignore
            with vuetify.VCol(cols=1):
                vuetify.VBtn("Kill", click="trigger('kill_simulation')"),  # type: ignore
                
        vuetify.VDivider(thickness=5, classes="my-4")

        with vuetify.VRow():
            with vuetify.VCol(cols=2):
                SimulationStatusView(server=server)

        with vuetify.VRow(v_if="simulation_error"):
            html.Div("An error occurred while running simulation : <br>{{simulation_error}}", style="color:red;")

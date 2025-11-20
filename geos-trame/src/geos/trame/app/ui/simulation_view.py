from trame.widgets import html
from trame.widgets import vuetify3 as vuetify

from geos.trame.app.io.simulation import SimulationConstant 
from geos.trame.app.ui.simulation_status_view import SimulationStatusView
import json

def suggest_decomposition(n_unknowns, 
                          memory_per_unknown_bytes, 
                          node_memory_gb, 
                          cores_per_node,
                          min_unknowns_per_rank=10000,
                          strong_scaling=True):
    """
    Suggests node/rank distribution for a cluster computation.
    
    Parameters:
    - n_unknowns: total number of unknowns
    - memory_per_unknown_bytes: estimated memory per unknown
    - node_memory_gb: available memory per node
    - cores_per_node: cores available per node
    - min_unknowns_per_rank: minimum for efficiency
    - strong_scaling: True if problem size is fixed
     
     Note:
        - 10,000-100,000 unknowns per rank is often a sweet spot for many PDE solvers
        - Use power-of-2 decompositions when possible (helps with communication patterns)
        - For 3D problems, try to maintain cubic subdomains (minimizes surface-to-volume ratio, reducing communication)
        - Don't oversubscribe: avoid using more ranks than provide parallel efficiency

    """
    
    # Memory constraint
    node_memory_bytes = node_memory_gb * 1e9
    max_unknowns_per_node = int(0.8 * node_memory_bytes / memory_per_unknown_bytes)
    
    # Compute minimum nodes needed
    min_nodes = max(1, (n_unknowns + max_unknowns_per_node - 1) // max_unknowns_per_node)
    
    # Determine ranks per node
    unknowns_per_node = n_unknowns // min_nodes
    unknowns_per_rank = max(min_unknowns_per_rank, unknowns_per_node // cores_per_node)
    
    # Calculate total ranks needed
    n_ranks = max(1, n_unknowns // unknowns_per_rank)
    
    # Distribute across nodes
    ranks_per_node = min(cores_per_node, (n_ranks + min_nodes - 1) // min_nodes)
    n_nodes = (n_ranks + ranks_per_node - 1) // ranks_per_node
    
    return {
        'nodes': n_nodes,
        'ranks_per_node': ranks_per_node,
        'total_ranks': n_nodes * ranks_per_node,
        'unknowns_per_rank': n_unknowns // (n_nodes * ranks_per_node)
    }

def hint_config(cluster_name, n_unknowns, job_type = 'cpu'):
    
    # return ["P4: 1x22", "P4: 2x11"]
    with open('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/geosPythonPackages/geos-trame/src/geos/trame/assets/cluster.json','r') as file:
            all_cluster = json.load(file)
    selected_cluster = list(filter(lambda d: d.get('name')==cluster_name, all_cluster["clusters"]))[0]

    if job_type == 'cpu': #make it an enum
        sd = suggest_decomposition(n_unknowns,
                              64,
                              selected_cluster['mem_per_node'],
                              selected_cluster['cpu']['per_node']
                              )
    # elif job_type == 'gpu':
        # selected_cluster['n_nodes']*selected_cluster['gpu']['per_node']


    return [ f"{selected_cluster['name']}: {sd['nodes']} x {sd['ranks_per_node']}", f"{selected_cluster['name']}: {sd['nodes'] * 2} x {sd['ranks_per_node'] // 2}" ]



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
            items = hint_config('p4', 12e6)
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
                vuetify.VBtn("Log in", click="trigger('run_try_login')"),  # type: ignore

                
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

        with vuetify.VRow():
            with vuetify.VCol(cols=4):
                vuetify.VTextField(
                    v_model=("simulation_job_name", "geosJob"),
                    label="Job Name",
                    dense=True,
                    hide_details=True,
                    clearable=True,
                    disabled=("!access_granted")
                )
            
            vuetify.VSpacer()
            with vuetify.VCol(cols=1):
                vuetify.VBtn("Run", 
                            click="trigger('run_simulation')",
                            disabled=("!access_granted"),
                            classes="ml-auto"),  # type: ignore


        vuetify.VDivider(thickness=5, classes="my-4")
      
        with vuetify.VRow():
            vuetify.VSpacer()
            with vuetify.VCol(cols=1):
                vuetify.VBtn("Kill", click="trigger('kill_simulation')"),  # type: ignore
                

        with vuetify.VRow():
            with vuetify.VCol(cols=2):
                SimulationStatusView(server=server)

        with vuetify.VRow(v_if="simulation_error"):
            html.Div("An error occurred while running simulation : <br>{{simulation_error}}", style="color:red;")

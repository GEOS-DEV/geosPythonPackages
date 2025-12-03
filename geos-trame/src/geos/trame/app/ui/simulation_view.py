from trame.widgets import html
from trame.widgets import vuetify3 as vuetify

from geos.trame.app.io.simulation import SimulationConstant, Authentificator
from geos.trame.app.ui.simulation_status_view import SimulationStatusView
import json

class SuggestDecomposition:

    def __init__(self, cluster_name, n_unknowns, job_type = 'cpu'):
        
        # return ["P4: 1x22", "P4: 2x11"]
        with open('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/geosPythonPackages/geos-trame/src/geos/trame/assets/cluster.json','r') as file:
                all_cluster = json.load(file)
        self.selected_cluster = list(filter(lambda d: d.get('name')==cluster_name, all_cluster["clusters"]))[0]
        self.n_unknowns = n_unknowns
        self.job_type = job_type

    # @property
    # def selected_cluster(self):
    #     return self.selected_cluster
    
    @staticmethod   
    def compute(   n_unknowns, 
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
    

    def to_list(self):

        if self.job_type == 'cpu': #make it an enum
            sd = SuggestDecomposition.compute(self.n_unknowns,
                                64,
                                self.selected_cluster['mem_per_node'],
                                self.selected_cluster['cpu']['per_node']
                                )
        # elif job_type == 'gpu':
            # selected_cluster['n_nodes']*selected_cluster['gpu']['per_node']


        return [ f"{self.selected_cluster['name']}: {sd['nodes']} x {sd['ranks_per_node']}", f"{self.selected_cluster['name']}: {sd['nodes'] * 2} x {sd['ranks_per_node'] // 2}" ]

  


def define_simulation_view(server) -> None:

    @server.state.change("simulation_xml_temp")
    def on_temp_change(simulation_xml_temp : list, **_):
        current_list = server.state.simulation_xml_filename

        new_list = current_list + simulation_xml_temp 
        server.state.simulation_xml_filename = new_list
        server.state.simulation_xml_temp = []

    @server.state.change("simulation_xml_filename")
    def on_simfiles_change(simulation_xml_filename : list, **_):
        import re
        pattern = re.compile(r"\.xml$", re.IGNORECASE)
        has_xml = any(pattern.search(file if isinstance(file, str) else file.get("name", "")) for file in  simulation_xml_filename)
        server.state.is_valid_jobfiles = has_xml
    
    
    def kill_job(index_to_remove : int) -> None:
        # for now just check there is an xml
        jid = list(server.state.job_ids)
        if 0 <= index_to_remove < len(jid):
                # 1. Supprimer l'élément de la copie de la liste 
            removed_id = jid[index_to_remove]['job_id']
            Authentificator.kill_job(removed_id)
            del jid[index_to_remove]
                
            server.state.job_ids = jid 
            print(f"Job {removed_id} kill. Still running: {len(jid)}") 
        else: 
            print(f"Error: supress index does not exist ({index_to_remove}).")

    
    def run_remove_jobfile(index_to_remove : int) -> None:
        # for now just check there is an xml 
        current_files = list(server.state.simulation_xml_filename) # On prend une copie de la liste 
        if 0 <= index_to_remove < len(current_files):
                # 1. Supprimer l'élément de la copie de la liste 
            del current_files[index_to_remove]
                
                # 2. Remplacer la variable d'état par la nouvelle liste.
                # Ceci est CRITIQUE pour la réactivité, car cela force Vue.js à se mettre à jour. 
            server.state.simulation_xml_filename = current_files 
            print(f"Fichier à l'index {index_to_remove} supprimé. Nouveaux fichiers: {len(current_files)}") 
        else: 
            print(f"Erreur: Index de suppression invalide ({index_to_remove}).")
    

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
            server.state.access_granted = False
            server.state.is_valid_jobfiles = False
            server.state.simulation_xml_filename = [ ]

            sd = SuggestDecomposition('p4', 12)
            items = sd.to_list()
            vuetify.VDivider(vertical=True, thickness=5, classes="mx-4")
            with vuetify.VCol(cols=2):
                vuetify.VSelect(label="Cluster",
                                items=("items",items))

        with vuetify.VRow():
            with vuetify.VCol(cols=8):
                vuetify.VTextField(
                        v_model=("key_path", None,),
                        label="Path to ssh key",
                        dense=True,
                        hide_details=True,
                        clearable=True,
                        prepend_icon="mdi-key-chain-variant"
                        )
            
                #
            vuetify.VDivider(vertical=True, thickness=5, classes="mx-4")
            with vuetify.VCol(cols=1):
                vuetify.VBtn("Log in", 
                             click="trigger('run_try_login')",
                             disabled=("access_granted",)
                             )  # type: ignore
                #
            vuetify.VDivider(vertical=True, thickness=5, classes="mx-4")
            with vuetify.VCol(cols=1):
                vuetify.VTextField(
                        v_model=("slurm_comment", "GEOS,CCS,testTrame",),
                        label="Comment to slurm",
                        dense=True,
                        hide_details=True,
                        clearable=True,
                             )  # type: ignore


                
        vuetify.VDivider(thickness=5, classes="my-4")

        with vuetify.VRow():
            with vuetify.VCol(cols=4):
                vuetify.VFileUpload(
                    v_model=("simulation_xml_temp",[]),
                    title="Simulation file name",
                    density='comfortable',
                    hide_details=True,
                    # clearable=True,
                    multiple=True,
                    filter_by_type='.xml,.vtu,.vtm,.pvtu,.pvtm,.dat,.csv,.txt',
                    # readonly=True,
                    disabled=("!access_granted",)
                )
            with vuetify.VCol(cols=4):
                with vuetify.VList():
                  with vuetify.VListItem( v_for=("(file,i) in simulation_xml_filename"), key="i", value="file",
                                         prepend_icon="mdi-minus-circle-outline",
                                         click=(run_remove_jobfile, "[i]")  ):
                    vuetify.VListItemTitle( "{{ file.name }}" )
                    vuetify.VListItemSubtitle("{{ file.size ? (file.size / 1024).toFixed(1) + ' KB' : 'URL' }}")

        with vuetify.VRow(), vuetify.VCol():
            vuetify.VTextField(
                v_model=("simulation_remote_path", "/workrd/users/l1165478/Example"),
                label="Path where to write files and launch code",
                prepend_icon="mdi-upload",
                dense=True,
                hide_details=True,
                clearable=True,
                disabled=("!access_granted",)
            # TODO callback validation of path
            )

        with vuetify.VRow(), vuetify.VCol():
            vuetify.VTextField(
                v_model=("simulation_dl_path", "/users/l1165478/tmp/Example"),
                label="Simulation download path",
                dense=True,
                clearable=True,
                prepend_icon="mdi-download",
                disabled=("!access_granted",)
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
                    disabled=("!access_granted",)
                )
            
            vuetify.VSpacer()
            with vuetify.VCol(cols=1):
                vuetify.VBtn("Run", 
                            click="trigger('run_simulation')",
                            disabled=("!is_valid_jobfiles",),
                            classes="ml-auto"),  # type: ignore


        vuetify.VDivider(thickness=5, classes="my-4")
      
        with vuetify.VRow():
            vuetify.VSpacer()
            with vuetify.VCol(cols=1):
                vuetify.VBtn("Kill", click="trigger('kill_all_simulations')"),  # type: ignore
        
        color_expression = "status_colors[job_ids[i].status] || '#607D8B'"

        with vuetify.VRow():
            with vuetify.VCol(cols=4):
                # SimulationStatusView(server=server)
                with vuetify.VList():
                    with vuetify.VListItem( v_for=("(jobs,i) in job_ids"), key="i", value="jobs", base_color=(color_expression,)):
                        vuetify.VListItemTitle("{{ jobs.status }} -- {{ jobs.name }} -- {{ jobs.job_id }}")
                        vuetify.VTooltip(text="here is a test for future display")
                        vuetify.VBtn(icon="mdi-delete",click=(kill_job,"[i]"))


        with vuetify.VRow(v_if="simulation_error"):
            html.Div("An error occurred while running simulation : <br>{{simulation_error}}", style="color:red;")
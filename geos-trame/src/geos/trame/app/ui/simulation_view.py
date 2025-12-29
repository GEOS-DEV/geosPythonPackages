from trame.widgets import html
from trame.widgets import vuetify3 as vuetify

from geos.trame.app.io.simulation import Authentificator
from geos.trame.app.io.hpc_tools import SuggestDecomposition

def define_simulation_view( server ) -> None:

    @server.state.change( "selected_cluster_name" )
    def on_cluster_change( selected_cluster_name : str , **_):
        print(selected_cluster_name)
        server.state.decompositions = SuggestDecomposition( Authentificator.get_cluster(selected_cluster_name) , 12 ).to_list()#discard 12 

    @server.state.change( "decomposition" )
    def on_decomposition_selected( decomposition : str, **_):
        ll = SuggestDecomposition( Authentificator.get_cluster(server.state.selected_cluster_name) , 12 ).get_sd()
        if server.state.decomposition:
            server.state.sd = ll[ server.state.decompositions.index(decomposition) ]
            server.state.simulation_remote_path = Authentificator.get_cluster(server.state.selected_cluster_name).simulation_remote_path
            server.state.simulation_dl_path = Authentificator.get_cluster(server.state.selected_cluster_name).simulation_dl_default_path
        else:
            server.state.sd = {'nodes': 0, 'total_ranks': 0}

    @server.state.change( "simulation_xml_temp" )
    def on_temp_change( simulation_xml_temp: list, **_ ):
        current_list = server.state.simulation_xml_filename

        new_list = current_list + simulation_xml_temp
        server.state.simulation_xml_filename = new_list
        server.state.simulation_xml_temp = []

    @server.state.change( "simulation_xml_filename" )
    def on_simfiles_change( simulation_xml_filename: list, **_ ):
        import re
        pattern = re.compile( r"\.xml$", re.IGNORECASE )
        has_xml = any(
            pattern.search( file if isinstance( file, str ) else file.get( "name", "" ) )
            for file in simulation_xml_filename )
        server.state.is_valid_jobfiles = has_xml

    def kill_job( index_to_remove: int ) -> None:
        # for now just check there is an xml
        jid = list( server.state.job_ids )
        if 0 <= index_to_remove < len( jid ):
            # 1. Supprimer l'élément de la copie de la liste
            removed_id = jid[ index_to_remove ][ 'job_id' ]
            Authentificator.kill_job( removed_id )
            del jid[ index_to_remove ]

            server.state.job_ids = jid
            print( f"Job {removed_id} kill. Still running: {len(jid)}" )
        else:
            print( f"Error: supress index does not exist ({index_to_remove})." )

    def run_remove_jobfile( index_to_remove: int ) -> None:
        current_files = list( server.state.simulation_xml_filename )
        if 0 <= index_to_remove < len( current_files ):
            del current_files[ index_to_remove ]

            server.state.simulation_xml_filename = current_files
            print( f"File at {index_to_remove} deleted. New files: {len(current_files)}" )
        else:
            print( f"Erreur: Wrong deletion index ({index_to_remove})." )

    with vuetify.VContainer():
        with vuetify.VRow():
            with vuetify.VCol( cols=4 ):
                vuetify.VTextField( v_model=(
                    "login",
                    None,
                ),
                                    label="Login",
                                    dense=True,
                                    hide_details=True,
                                    clearable=True,
                                    prepend_icon="mdi-login" )
            with vuetify.VCol( cols=4 ):
                vuetify.VTextField( v_model=(
                    "password",
                    None,
                ),
                                    label="Password",
                                    type="password",
                                    dense=True,
                                    hide_details=True,
                                    clearable=True,
                                    prepend_icon="mdi-onepassword" )

        #
            server.state.access_granted = False
            server.state.is_valid_jobfiles = False
            server.state.simulation_xml_filename = []
            server.state.selected_cluster_names = [cluster.name for cluster in Authentificator.sim_constants]
            # server.state.decompositions = []
            server.state.sd = None

            vuetify.VDivider( vertical=True, thickness=5, classes="mx-4" )
            with vuetify.VCol( cols=1 ):
                vuetify.VSelect( label="Cluster", items=( "selected_cluster_names",  ), v_model=("selected_cluster_name", 'local') )
            vuetify.VDivider( vertical=True, thickness=5, classes="mx-4" )
            with vuetify.VCol( cols=1 ):
                vuetify.VSelect( label="Decomposition", items=( "decompositions", []), v_model=("decomposition",'') )

        with vuetify.VRow():
            with vuetify.VCol( cols=8 ):
                vuetify.VTextField( v_model=(
                    "key_path",
                    None,
                ),
                                    label="Path to ssh key",
                                    dense=True,
                                    hide_details=True,
                                    clearable=True,
                                    prepend_icon="mdi-key-chain-variant" )

                #
            vuetify.VDivider( vertical=True, thickness=5, classes="mx-4" )
            with vuetify.VCol( cols=1 ):
                vuetify.VBtn( "Log in", click="trigger('run_try_login')",
                              disabled=( "access_granted", ) )  # type: ignore
                #
            vuetify.VDivider( vertical=True, thickness=5, classes="mx-4" )
            with vuetify.VCol( cols=1 ):
                vuetify.VTextField(
                    v_model=( "slurm_comment", None ),
                    label="Comment to slurm",
                    dense=True,
                    hide_details=True,
                    clearable=True,
                )  # type: ignore

        vuetify.VDivider( thickness=5, classes="my-4" )

        with vuetify.VRow():
            with vuetify.VCol( cols=4 ):
                vuetify.VFileUpload(
                    v_model=( "simulation_xml_temp", [] ),
                    title="Simulation file name",
                    density='comfortable',
                    hide_details=True,
                    # clearable=True,
                    multiple=True,
                    filter_by_type='.xml,.vtu,.vtm,.pvtu,.pvtm,.dat,.csv,.txt',
                    # readonly=True,
                    disabled=( "!access_granted", ) )
            with vuetify.VCol( cols=4 ):
                with vuetify.VList():
                    with vuetify.VListItem( v_for=( "(file,i) in simulation_xml_filename" ),
                                            key="i",
                                            value="file",
                                            prepend_icon="mdi-minus-circle-outline",
                                            click=( run_remove_jobfile, "[i]" ) ):
                        vuetify.VListItemTitle( "{{ file.name }}" )
                        vuetify.VListItemSubtitle( "{{ file.size ? (file.size / 1024).toFixed(1) + ' KB' : 'URL' }}" )

        with vuetify.VRow(), vuetify.VCol():
            vuetify.VTextField( v_model=( "simulation_remote_path", None ),
                                label="Path where to write files and launch code",
                                prepend_icon="mdi-upload",
                                dense=True,
                                hide_details=True,
                                clearable=True,
                                disabled=( "!access_granted", )
                                # TODO callback validation of path
                               )

        with vuetify.VRow(), vuetify.VCol():
            vuetify.VTextField( v_model=( "simulation_dl_path", None ),
                                label="Simulation download path",
                                dense=True,
                                clearable=True,
                                prepend_icon="mdi-download",
                                disabled=( "!access_granted", )
                                # TODO callback validation of path
                               )

        with vuetify.VRow():
            with vuetify.VCol( cols=4 ):
                vuetify.VTextField( v_model=( "simulation_job_name", "geosJob" ),
                                    label="Job Name",
                                    dense=True,
                                    hide_details=True,
                                    clearable=True,
                                    disabled=( "!access_granted", ) )

            vuetify.VSpacer()
            with vuetify.VCol( cols=1 ):
                vuetify.VBtn( "Run",
                              click="trigger('run_simulation')",
                              disabled=( "!is_valid_jobfiles", ),
                              classes="ml-auto" ),  # type: ignore

        vuetify.VDivider( thickness=5, classes="my-4" )

        with vuetify.VRow():
            vuetify.VSpacer()
            with vuetify.VCol( cols=1 ):
                vuetify.VBtn( "Kill All", click="trigger('kill_all_simulations')" ),  # type: ignore

        color_expression = "status_colors[job_ids[i].status] || '#607D8B'"
        with vuetify.VRow():
            with vuetify.VCol( cols=4 ):
                with vuetify.VList():
                    with vuetify.VListItem( v_for=( "(jobs,i) in job_ids" ),
                                            key="i",
                                            value="jobs",
                                            base_color=( color_expression, ),
                                            prepend_icon="mdi-minus-circle-outline",
                                            click=( kill_job, "[i]" ) ):
                        vuetify.VListItemTitle( "{{ jobs.status }} -- {{ jobs.name }} -- {{ jobs.job_id }}" )
                        vuetify.VProgressLinear( v_model=( "simulation_progress", "0" ), )

        with vuetify.VRow( v_if="simulation_error" ):
            html.Div( "An error occurred while running simulation : <br>{{simulation_error}}", style="color:red;" )

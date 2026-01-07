# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
# ignore context collapsing as it is clearer this way
# ruff: noqa: SIM117
from typing import Any

from trame.widgets import html
from trame.widgets import vuetify3 as vuetify
from trame_server import Server

from geos.trame.app.io.simulation import Authentificator
from geos.trame.app.io.hpc_tools import SuggestDecomposition

#rough estimate of n unknowns would be better from GEOS's dry-run
# unknowns (oncell,onpoint)
# for now do not take into account wells as dep on the num of wells (neg vs matrix elmts)
# for now do not take into account frac as dep on the num of frac elmts (prob neg vs matrix elmts)
solvers_to_unknowns = { 
    "CompositionalMultiphaseFVM" : (3, 0),
    "CompositionalMultiphaseHybridFVM" : (4, 0),
    "CompositionalMultiphaseReservoirPoromechanics" : (3,3),
    "CompositionalMultiphaseReservoirPoromechanicsConformingFractures" : (3,6),
    "CompositionalMultiphaseWell" : (3,0),
    "ElasticFirstOrderSEM" : (0,3),
    "ElasticSEM" : (0,3),
    "ImmiscibleMultiphaseFlow": (3,0),
    "LaplaceFEM" : (0,3),
    "MultiphasePoromechanics" : (3,3),
    "MultiphasePoromechanicsReservoir" : (3,3),#??
    "MultiphasePoromechanicsConformingFractures" : (3,6) ,
    "SinglePhaseFVM" : (2,0),
    "SinglePhaseHybridFVM" : (3,0),
    "SinglePhasePoromechanics" : (2,3),
    "SinglePhasePoromechanicsConformingFractures" : (2,3),
    "SinglePhasePoromechanicsConformingFracturesALM" : (2,3),
    "SinglePhaseWell" : (2,0),
    "SolidMechanicsEmbeddedFractures": (0,3),
    "SolidMechanicsAugmentedLagrangianContact": (0,3),
    "SolidMechanicsLagrangeContact": (0,3),
    "SolidMechanicsLagrangeContactBubbleStab": (0,3),
    "SolidMechanicsLagrangianFEM": (0,3)
}

  # helpers
def _what_solver(bcontent) -> int:
        import xml.etree
        sim_xml = xml.etree.ElementTree.fromstring(bcontent['content'])
        nunk = [solvers_to_unknowns.get(elt.tag, 1) for elt in sim_xml.find('Solvers')]
        return max(nunk)


def _how_many_cells( bcontent ) -> tuple[int,int]:
        import vtk
        name = bcontent['name']
        if name.endswith(".vtp"):
            reader = vtk.vtkXMLPolyDataReader()
        elif name.endswith(".vtu"):
            reader = vtk.vtkXMLUnstructuredGridReader()
        elif name.endswith(".vtm"):
            reader = vtk.vtkXMLMultiBlockDataReader()
        else:
            raise ValueError("Unsupported kind (use 'vtp', 'vtu', or 'vtm').")

        reader.SetReadFromInputString(1)
        reader.SetInputString(bcontent['content'])
        reader.Update()
        output = reader.GetOutput()
        return (output.GetNumberOfCells(), output.GetNumberOfPoints())

def _has_internalMesh(bcontent) -> bool:
        import xml.etree
        sim_xml = xml.etree.ElementTree.fromstring(bcontent['content'])
        return (sim_xml.find('Mesh/InternalMesh') is not None)

def _what_internalMesh(bcontent) -> tuple[int,int]:
        import xml.etree
        import re
        sim_xml = xml.etree.ElementTree.fromstring(bcontent['content'])
        nx = sim_xml.find('Mesh/InternalMesh').get('nx')
        nx = sum([int(el) for el in re.findall(r'-?\d+(?:\.\d+)?', nx)])
        ny = sim_xml.find('Mesh/InternalMesh').get('ny')
        ny = sum([int(el) for el in re.findall(r'-?\d+(?:\.\d+)?', ny)])
        nz = sim_xml.find('Mesh/InternalMesh').get('nz')
        nz = sum([int(el) for el in re.findall(r'-?\d+(?:\.\d+)?', nz)])
        return (nx*ny*nz, (nx+1)*(ny+1)*(nz+1))


#TODO a class from it
def define_simulation_view( server: Server ) -> None:
    """Functional definition of UI elements."""

    @server.state.change( "selected_cluster_name" )
    def on_cluster_change( selected_cluster_name: str, **_: Any ) -> None:
        print( f"selecting {selected_cluster_name}" )
        server.state.decompositions = SuggestDecomposition( Authentificator.get_cluster( selected_cluster_name ),
                                                            server.state.nunknowns ).get_sd()
        
        server.state.simulation_remote_path = Authentificator.get_cluster(
                server.state.selected_cluster_name ).simulation_remote_path
        
        server.state.simulation_dl_path = Authentificator.get_cluster(
                server.state.selected_cluster_name ).simulation_dl_default_path

    # @server.state.change( "decomposition" )
    # def on_decomposition_selected( decomposition: str, **_: Any ) -> None:
    #      = SuggestDecomposition( Authentificator.get_cluster( server.state.selected_cluster_name ), server.state.nunknowns ).get_sd()
    #     # if server.state.decomposition:
    #     except:
    #         server.state.sd = { 'nodes': 0, 'total_ranks': 0 }

    @server.state.change( "simulation_xml_temp" )
    def on_temp_change( simulation_xml_temp: list, **_: Any ) -> None:
        current_list = server.state.simulation_xml_filename

        new_list = current_list + simulation_xml_temp
        server.state.simulation_xml_filename = new_list
        server.state.simulation_xml_temp = []

    @server.state.change("nunknowns")
    def on_nunknowns_change( nunknowns : int , **_ : Any) -> None:
        #re-gen list
        if len(server.state.decompositions) > 0:
            server.state.decompositions = SuggestDecomposition( Authentificator.get_cluster( server.state.selected_cluster_name ),
                                                            nunknowns ).get_sd()
        print(f'unknowns changed : {server.state.nunknowns} -> {nunknowns}')
        server.state.nunknowns = nunknowns

    
    @server.state.change( "simulation_xml_filename" )
    def on_simfiles_change( simulation_xml_filename: list, **_: Any ) -> None:
        import re
        has_xml = list([True if file.get( "type", "" ) == 'text/xml' else False
            for file in simulation_xml_filename ])
        
        has_external_mesh = list([True if file.get( "name", "" ).endswith((".vtu",".vtm",".vtp"))  else False
            for file in simulation_xml_filename ])
        
        has_internal_mesh = False
        for i,_ in enumerate(has_xml):
            if has_xml[i]:
                has_internal_mesh = _has_internalMesh(simulation_xml_filename[i])

        if any(has_xml):
            for i,_ in enumerate(has_xml):
                if has_external_mesh[i]:
                    nc, np = _how_many_cells(simulation_xml_filename[i])
                elif has_xml[i]:
                    uc, up = _what_solver(simulation_xml_filename[i]) 
                    if has_internal_mesh:
                        nc,np = _what_internalMesh(simulation_xml_filename[i])
            
            server.state.nunknowns = uc*nc + up*np      
        
        server.state.is_valid_jobfiles = any(has_xml)
        
    def kill_job( index_to_remove: int ) -> None:
        # for now just check there is an xml
        jid = list( server.state.job_ids )
        if 0 <= index_to_remove < len( jid ):
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
            server.state.selected_cluster_names = [ cluster.name for cluster in Authentificator.sim_constants ]
            # server.state.decompositions = []

            vuetify.VDivider( vertical=True, thickness=5, classes="mx-4" )
            with vuetify.VCol( cols=1 ):
                vuetify.VSelect( label="Cluster",
                                 items=( "selected_cluster_names", ),
                                 v_model=( "selected_cluster_name", 'p4' ) )
            vuetify.VDivider( vertical=True, thickness=5, classes="mx-4" )
            with vuetify.VCol( cols=1 ):
                vuetify.VSelect( label="Decomposition",
                                 items=( "decompositions", [] ),
                                 v_model=( "decomposition", None ),
                                item_title="label",
                                item_value="id",
                                return_object=True
                                )

        with vuetify.VRow():
            with vuetify.VCol( cols=8 ):
                vuetify.VTextField( v_model=(
                    "key_path",
                    "/users/$USER/.ssh/id_trame",
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
            with vuetify.VCol( cols=4 ), vuetify.VList():
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
        with vuetify.VRow(), vuetify.VCol( cols=4 ), vuetify.VList():
            with vuetify.VListItem( v_for=( "(jobs,i) in job_ids" ),
                                    key="i",
                                    value="jobs",
                                    base_color=( color_expression, ),
                                    prepend_icon="mdi-minus-circle-outline",
                                    click=( kill_job, "[i]" ) ):
                vuetify.VListItemTitle( "{{ jobs.status }} -- {{ jobs.name }} -- {{ jobs.job_id }}" )
                vuetify.VProgressLinear( v_model=( "jobs.simprogress", "0" ), )
                vuetify.VProgressLinear( v_model=( "jobs.slprogress", "0" ), )

        with vuetify.VRow( v_if="simulation_error" ):
            html.Div( "An error occurred while running simulation : <br>{{simulation_error}}", style="color:red;" )

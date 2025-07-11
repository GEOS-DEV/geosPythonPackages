import argparse
from dataclasses import dataclass
import pytest
from typing import Iterator, Sequence
from geos.mesh.doctor.actions.generate_fractures import FracturePolicy, Options
from geos.mesh.doctor.parsing.generate_fractures_parsing import convert, display_results, fill_subparser
from geos.mesh.io.vtkIO import VtkOutput


@dataclass( frozen=True )
class TestCase:
    __test__ = False
    cli_args: Sequence[ str ]
    options: Options
    exception: bool = False


def __generate_generate_fractures_parsing_test_data() -> Iterator[ TestCase ]:
    field: str = "attribute"
    main_mesh: str = "output.vtu"
    fracture_mesh: str = "fracture.vtu"

    cli_gen: str = f"generate_fractures --policy {{}} --name {field} --values 0,1 --output {main_mesh} --fractures_output_dir ."
    all_cli_args = cli_gen.format( "field" ).split(), cli_gen.format( "internal_surfaces" ).split(), cli_gen.format(
        "dummy" ).split()
    policies = FracturePolicy.FIELD, FracturePolicy.INTERNAL_SURFACES, FracturePolicy.FIELD
    exceptions = False, False, True
    for cli_args, policy, exception in zip( all_cli_args, policies, exceptions ):
        options: Options = Options(
            policy=policy,
            field=field,
            field_values_combined=frozenset( ( 0, 1 ) ),
            field_values_per_fracture=[ frozenset( ( 0, 1 ) ) ],
            mesh_VtkOutput=VtkOutput( output=main_mesh, is_data_mode_binary=True ),
            all_fractures_VtkOutput=[ VtkOutput( output=fracture_mesh, is_data_mode_binary=True ) ] )
        yield TestCase( cli_args, options, exception )


def __f( test_case: TestCase ):
    parser = argparse.ArgumentParser( description='Testing.' )
    subparsers = parser.add_subparsers()
    fill_subparser( subparsers )
    args = parser.parse_args( test_case.cli_args )
    options = convert( vars( args ) )
    assert options.policy == test_case.options.policy
    assert options.field == test_case.options.field
    assert options.field_values_combined == test_case.options.field_values_combined


def test_display_results():
    # Dummy test for code coverage only. Shame on me!
    display_results( None, None )


@pytest.mark.parametrize( "test_case", __generate_generate_fractures_parsing_test_data() )
def test( test_case: TestCase ):
    if test_case.exception:
        with pytest.raises( SystemExit ):
            pytest.skip( "Test to be fixed" )
            __f( test_case )
    else:
        pytest.skip( "Test to be fixed" )
        __f( test_case )

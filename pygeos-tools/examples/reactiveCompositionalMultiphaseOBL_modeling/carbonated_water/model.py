import darts
from darts.models.darts_model import DartsModel
from darts.physics.chemistry.property_container import PropertyContainer
from darts.physics.properties.density import DensityBasic
from darts.physics.properties.basic import ConstFunc
from darts.physics.properties.kinetics import (
    KineticRate,
    LinearReactionSurfaceArea,
)
from darts.physics.properties.phreeqc import Flash as PhreeqcFlash
from darts.physics.properties.reaktoro import Flash as ReaktoroFlash
from darts.physics.chemistry.physics import ElementBasedReactiveFlow
from iapws._iapws import _Viscosity

import numpy as np

try:
    from phreeqpy.iphreeqc.phreeqc_com import IPhreeqc
except ImportError:
    from phreeqpy.iphreeqc.phreeqc_dll import IPhreeqc


# Actual Model class creation here!
class Model( DartsModel ):

    def __init__( self, 
        minerals: list = ['calcite'], 
        kinetic_mechanisms=['acidic', 'neutral', 'carbonate'], 
        n_obl_mult: int = 1,
        perm_poro: str = 'power_8',
        flash: str = 'phreeqc',
        database: str = 'phreeqc'
    ):
        # Call base class constructor
        super().__init__()
        self.minerals = minerals
        self.kinetic_mechanisms = kinetic_mechanisms
        self.n_obl_mult = n_obl_mult
        self.n_solid = len(minerals)
        self.perm_poro = perm_poro
        self.flash = flash
        self.database = database
        self.set_physics()

    def set_physics( self ):
        # some properties
        self.temperature = 323.15  # K
        self.pressure_init = 100  # bar

        self.min_z = 1e-11
        self.obl_min = self.min_z / 10

        # Several parameters here related to components used, OBL limits, and injection composition:
        self.phases = ['gas', 'liq']

        if set(self.minerals) == {'calcite'}:
            # purely for initialization
            self.components = ['H2O', 'H+', 'OH-', 'CO2', 'HCO3-', 'CO3-2', 'CaCO3', 'Ca+2', 'CaOH+', 'CaHCO3+', 'Solid_CaCO3']
            self.elements = ['Solid_CaCO3', 'Ca', 'C', 'O', 'H']
            self.fc_mask = np.array([False, True, True, True, True], dtype=bool)
            Mw = {'Solid_CaCO3': 100.0869, 'Ca': 40.078, 'C': 12.0096, 'O': 15.999, 'H': 1.007} # molar weights in kg/kmol
            self.n_points = list(self.n_obl_mult * np.array([101, 201, 101, 101, 101], dtype=np.intp))
            self.axes_min = [self.pressure_init - 1] + [self.obl_min, self.obl_min, self.obl_min, 0.3]
            self.axes_max = [self.pressure_init + 2] + [1 - self.obl_min, 0.03, 0.03, 0.37]
            # Rate annihilation matrix
            self.E = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                               [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0],
                               [0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0],
                               [1, 0, 1, 2, 3, 3, 3, 0, 1, 3, 0],
                               [2, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0]])
            # Mineral decomposition into elements
            stoich_matrix = np.array([[-1, 1, 1, 3, 0]])
            # Mineral properties
            rock_props = {'Solid_CaCO3': {'density': 2710., 'compressibility': 1.e-6}}
        elif set(self.minerals) == {'calcite', 'dolomite'}:
            # purely for initialization
            self.components = ['H2O', 'H+', 'OH-', 'CO2', 'HCO3-', 'CO3-2',
                               'CaCO3', 'Ca+2', 'CaOH+', 'CaHCO3+', 'Solid_CaCO3',                  # calcite-related
                               'CaMg(CO3)2', 'Mg+2', 'MgOH+', 'MgHCO3+', 'Solid_CaMg(CO3)2']        # dolomite-related
            self.elements = ['Solid_CaCO3', 'Solid_CaMg(CO3)2', 'Ca', 'Mg', 'C', 'O', 'H']
            self.fc_mask = np.array([False, False, True, True, True, True, True], dtype=bool)
            Mw = {'Solid_CaCO3': 100.0869, 'Solid_CaMg(CO3)2': 184.401,
                    'Ca': 40.078, 'Mg': 24.305, 'C': 12.0096, 'O': 15.999, 'H': 1.007} # molar weights in kg/kmol
            self.n_points = list(self.n_obl_mult * np.array([101, 201, 201, 101, 101, 101, 101], dtype=np.intp))
            if self.co2_injection < self.co2_injection_cutoff:
                self.axes_min = [self.pressure_init - 1] + [self.obl_min, self.obl_min, self.obl_min, self.obl_min, self.obl_min, 0.3]
                self.axes_max = [self.pressure_init + 2] + [1 - self.obl_min, 0.4, 0.01, 0.01, 0.02, 0.37]
            else:
                self.axes_min = [self.pressure_init - 1] + [self.obl_min, self.obl_min, self.obl_min, self.obl_min, self.obl_min, 0.25]
                self.axes_max = [self.pressure_init + 2] + [1 - self.obl_min, 0.4, 0.01, 0.01, 0.1, 0.37]
            # Rate annihilation matrix
            self.E = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],    # Solid_CaCO3
                               [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],    # Solid_CaMg(CO3)2
                               [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0],    # Ca
                               [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0],    # Mg
                               [0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 2, 0, 0, 1, 0],    # C
                               [1, 0, 1, 2, 3, 3, 3, 0, 1, 3, 0, 6, 0, 1, 3, 0],    # O
                               [2, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0]])   # H
            # Mineral decomposition into elements
            stoich_matrix = np.array([[-1, 0, 1, 0, 1, 3, 0],
                                      [0, -1, 1, 1, 2, 6, 0]])
            # Mineral properties
            rock_props = {'Solid_CaCO3': {'density': 2710., 'compressibility': 1.e-6},
                          'Solid_CaMg(CO3)2': {'density': 2840., 'compressibility': 1.e-6}}
        elif set(self.minerals) == {'calcite', 'dolomite', 'magnesite'}:
            # purely for initialization
            self.components = ['H2O', 'H+', 'OH-', 'CO2', 'HCO3-', 'CO3-2',
                               'CaCO3', 'Ca+2', 'CaOH+', 'CaHCO3+', 'Solid_CaCO3',                  # calcite-related
                               'CaMg(CO3)2', 'Mg+2', 'MgOH+', 'MgHCO3+', 'Solid_CaMg(CO3)2', 'Solid_MgCO3'] # dolomite-related
            self.elements = ['Solid_CaCO3', 'Solid_CaMg(CO3)2', 'Solid_MgCO3', 'Ca', 'Mg', 'C', 'O', 'H']
            self.fc_mask = np.array([False, False, False, True, True, True, True, True], dtype=bool)
            Mw = {'Solid_CaCO3': 100.0869, 'Solid_CaMg(CO3)2': 184.401, 'Solid_MgCO3': 84.31,
                    'Ca': 40.078, 'Mg': 24.305, 'C': 12.0096, 'O': 15.999, 'H': 1.007} # molar weights in kg/kmol
            self.n_points = list(self.n_obl_mult * np.array([101, 201, 201, 201, 101, 101, 101, 101], dtype=np.intp))
            if self.co2_injection < self.co2_injection_cutoff:
                self.axes_min = [self.pressure_init - 1] + [self.obl_min, self.obl_min, self.obl_min, self.obl_min, self.obl_min, self.obl_min, 0.3]
                self.axes_max = [self.pressure_init + 2] + [1 - self.obl_min, 0.4, 0.2, 0.01, 0.01, 0.02, 0.37]
            else:
                self.axes_min = [self.pressure_init - 1] + [self.obl_min, self.obl_min, self.obl_min, self.obl_min, self.obl_min, self.obl_min, 0.25]
                self.axes_max = [self.pressure_init + 2] + [1 - self.obl_min, 0.4, 0.2, 0.01, 0.01, 0.1, 0.37]

            # Rate annihilation matrix
            self.E = np.array([[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],    # Solid_CaCO3
                               [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],    # Solid_CaMg(CO3)2
                               [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],    # Solid_MgCO3
                               [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0],    # Ca
                               [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0],    # Mg
                               [0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 2, 0, 0, 1, 0, 0],    # C
                               [1, 0, 1, 2, 3, 3, 3, 0, 1, 3, 0, 6, 0, 1, 3, 0, 0],    # O
                               [2, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0]])   # H
            # Mineral decomposition into elements
            stoich_matrix = np.array([[-1, 0, 0, 1, 0, 1, 3, 0],
                                      [0, -1, 0, 1, 1, 2, 6, 0],
                                      [0, 0, -1, 0, 1, 1, 3, 0]])
            # Mineral properties
            rock_props = {'Solid_CaCO3': {'density': 2710., 'compressibility': 1.e-6},
                          'Solid_CaMg(CO3)2': {'density': 2840., 'compressibility': 1.e-6},
                          'Solid_MgCO3': {'density': 2958., 'compressibility': 1.e-6}}

        self.nc = len(self.elements)

        # Create property containers:
        property_container = PropertyContainer(phases_name=self.phases, components_name=self.elements, Mw=Mw,
                                            stoich_matrix=stoich_matrix, min_z=self.obl_min, temperature=self.temperature,
                                            fc_mask=self.fc_mask)
                                            
        # permporo relationship
        type, exp = self.perm_poro.split('_')
        if type == 'power':
            property_container.permporo_mult_ev = PermPoroRelationship(exp=float(exp))
        else:
            print('Other than power law are not supported for permeability-porosity relationship')
        property_container.diffusion_ev = {ph: ConstFunc(np.concatenate([np.zeros(self.n_solid), \
                                         np.ones(self.nc - self.n_solid)]) * 5.2e-10 * 86400) for ph in self.phases}
        property_container.rel_perm_ev = {ph: CustomRelPerm(2) for ph in self.phases}
        property_container.viscosity_ev = { self.phases[0]: GasViscosity(), self.phases[1]: LiquidViscosity() }

        # flash, also here to be able to setup modified PHREEQC/reaktoro flashes
        if self.flash == 'phreeqc':
            # PHREEQC backend expects .dat filenames
            db_filename = f"{self.database}.dat"
            property_container.flash_ev = PhreeqcFlash(
                min_z=property_container.min_z,
                minerals=property_container.minerals,
                components=property_container.components_name[property_container.fc_mask],
                temperature=property_container.temperature,
                database_filename=db_filename,
            )
        elif self.flash == 'reaktoro':
            # Reaktoro expects 'supcrtbl' without .dat; PHREEQC DBs with .dat
            db_filename = 'supcrtbl' if self.database == 'supcrtbl' else f"{self.database}.dat"
            property_container.flash_ev = ReaktoroFlash(
                min_z=property_container.min_z,
                minerals=property_container.minerals,
                components=property_container.components_name[property_container.fc_mask],
                temperature=property_container.temperature,
                database_filename=db_filename,
            )
        else:
            raise ValueError(f'Invalid flash type: {self.flash}')

        # kinetics
        surface_area_ev = LinearReactionSurfaceArea(initial_area_per_mol=0.925)
        property_container.kinetic_rate_ev = {
            m: KineticRate(
                min_z=self.obl_min,
                mineral_name=m.split('_', 1)[1],
                mechanisms=self.kinetic_mechanisms,
                surface_area_ev=surface_area_ev,
            )
            for m in property_container.minerals
        }

        # Mineral properties
        for min, props in rock_props.items():
            property_container.rock_compr_ev[min] = ConstFunc(props['compressibility'])
            property_container.rock_density_ev[min] = DensityBasic(compr=props['compressibility'], dens0=props['density'], p0=1.)

        # Create instance of (own) physics class:
        self.physics = ElementBasedReactiveFlow(timer=self.timer, elements=self.elements, n_points=self.n_points, phases=self.phases,
                                          axes_min=self.axes_min, axes_max=self.axes_max, properties=property_container,
                                          cache=False)

        self.physics.add_property_region(property_container, 0)
        self.engine = self.physics.init_physics( platform='cpu' )
        return

class CustomRelPerm:
    def __init__(self, exp, sr=0):
        self.exp = exp
        self.sr = sr

    def evaluate(self, sat):
        return (sat - self.sr) ** self.exp

class GasViscosity:
    def __init__(self):
        pass
    def evaluate(self, pressure, temperature):
        return 0.0278

class LiquidViscosity:
    def __init__(self):
        pass
    def evaluate(self, density, temperature):
        visc = _Viscosity(rho=density, T=temperature)
        return visc * 1000

class PermPoroRelationship:
    def __init__(self, exp):
        self.exp = exp
    def evaluate(self, poro):
        return poro ** self.exp


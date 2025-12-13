# Automated ParaView Widget Generation

This document explains how to use the automated widget generation system for ParaView plugins based on `CHECK_FEATURES_CONFIG`.

## Overview

The widget generation system automatically creates ParaView property widgets (sliders, input boxes, etc.) for mesh-doctor check parameters based on the `CHECK_FEATURES_CONFIG` dictionary. This eliminates the need to manually write repetitive property setters and decorators.

## How It Works

### 1. Configuration Source

The system reads from `CHECK_FEATURES_CONFIG` in `mesh-doctor/src/geos/mesh_doctor/parsing/allChecksParsing.py`:

```python
CHECK_FEATURES_CONFIG = {
    COLLOCATES_NODES: CheckFeature(
        name=COLLOCATES_NODES,
        optionsCls=cnParser.Options,
        resultCls=cnParser.Result,
        defaultParams={"tolerance": 0.0},  # <-- These are used
        display=cnParser.displayResults
    ),
    ELEMENT_VOLUMES: CheckFeature(
        name=ELEMENT_VOLUMES,
        optionsCls=evParser.Options,
        resultCls=evParser.Result,
        defaultParams={"minVolume": 0.0},  # <-- These are used
        display=evParser.displayResults
    ),
    # ... more checks
}
```

### 2. Widget Generation

The `pvWidgetGenerator.py` module provides:

- **`_get_parameter_metadata()`**: Analyzes parameter names and types to determine appropriate widget types
- **`create_widget_setter()`**: Generates setter methods with ParaView decorators (`@smproperty`, `@smdomain`)
- **`create_widget_group()`**: Groups related parameters with `PropertyGroup` XML
- **`add_widgets_to_class()`**: Dynamically adds all generated methods to the plugin class

### 3. Type Detection

The system automatically detects parameter types and creates appropriate widgets:

| Python Type | ParaView Widget | Domain | Default Min |
|-------------|-----------------|--------|-------------|
| `bool` | Checkbox (intvector) | BooleanDomain | - |
| `int` | Integer input (intvector) | IntRangeDomain | 1 (for size/proc params) |
| `float` | Float input (doublevector) | DoubleRangeDomain | 0.0 (for tolerance/distance/volume) |
| `str` | Text input (stringvector) | - | - |

### 4. Label Generation

Parameter names are automatically converted to user-friendly labels:

- `tolerance` → "Tolerance"
- `minVolume` → "Min Volume"
- `angleTolerance` → "Angle Tolerance"
- `chunk_size` → "Chunk Size"

### 5. Documentation Generation

Documentation is auto-generated based on parameter name patterns:

- Parameters with "tolerance" → "Tolerance value for {check_name} check."
- Parameters with "angle" → "Angle tolerance in degrees for {check_name} check."
- Parameters with "distance" → "Distance threshold for {check_name} check."
- Parameters with "volume" → "Volume threshold for {check_name} check."
- Others → "Parameter {param_name} for {check_name} check."

## Usage

### Basic Usage in PVMeshDoctorChecks

Replace manual widget definitions with automated generation:

```python
from geos.mesh_doctor.parsing.allChecksParsing import CHECK_FEATURES_CONFIG
from geos.pv.utils.pvWidgetGenerator import add_widgets_to_class

@SISOFilter(category=FilterCategory.QC, ...)
class PVMeshDoctorChecks(VTKPythonAlgorithmBase):
    
    def __init__(self):
        self._checksSelection = vtkDataArraySelection()
        self._customParameters = {}  # Important: must exist
        # ... rest of init
    
    # ... your existing methods ...

# Add this at the end of the file (after class definition)
add_widgets_to_class(PVMeshDoctorChecks, CHECK_FEATURES_CONFIG)
```

### What Gets Generated

For each check in `CHECK_FEATURES_CONFIG`, the system generates:

1. **Setter methods** for each parameter, e.g.:
   ```python
   @smproperty.doublevector(name="CollocatedNodes_Tolerance", ...)
   @smdomain.xml("""<DoubleRangeDomain .../>""")
   def SetCollocatedNodesTolerance(self, tolerance: float):
       # Stores value in self._customParameters
   ```

2. **Property group** to organize parameters:
   ```python
   @smproperty.xml("""<PropertyGroup label="Collocated Nodes Parameters">...</PropertyGroup>""")
   def a01GroupCollocatedNodesParams(self):
       pass
   ```

### Accessing Custom Parameters

In your `ApplyFilter` method:

```python
def ApplyFilter(self, inputMesh, outputMesh):
    selectedChecks = getArrayChoices(self._checksSelection)
    
    for checkName in selectedChecks:
        if checkName in self._customParameters:
            params = self._customParameters[checkName]
            # params is a dict like {"tolerance": 0.5, "minVolume": 1e-6}
            # Apply these to your check filter
```

## Benefits

### Before (Manual)

```python
# ~200+ lines of repetitive code per check
@smproperty.doublevector(
    name="CollocatedNodes_Tolerance",
    label="Tolerance",
    default_values=0.0,
    number_of_elements=1,
)
@smdomain.xml("""<DoubleRangeDomain name="range" min="0" />
                  <Documentation>...</Documentation>""")
def SetCollocatedNodesTolerance(self, tolerance: float):
    if not hasattr(self, '_cn_tolerance') or self._cn_tolerance != tolerance:
        self._cn_tolerance = tolerance
        # ... more boilerplate
        
# Repeat for every parameter of every check...
```

### After (Automated)

```python
# Single line at end of file
add_widgets_to_class(PVMeshDoctorChecks, CHECK_FEATURES_CONFIG)
```

## Customization

### Custom Parameter Metadata

If you need custom behavior for specific parameters, modify `_get_parameter_metadata()`:

```python
def _get_parameter_metadata(param_name, param_value, check_name):
    metadata = {
        # ... standard detection ...
    }
    
    # Custom override for specific parameters
    if check_name == "non_conformal" and param_name == "angleTolerance":
        metadata['display_label'] = "Angle Tolerance (degrees)"
        metadata['range_min'] = 0.0
        metadata['range_max'] = 180.0
    
    return metadata
```

### Adding New Checks

Simply add the check to `CHECK_FEATURES_CONFIG` with `defaultParams`:

```python
CHECK_FEATURES_CONFIG = {
    # ... existing checks ...
    MY_NEW_CHECK: CheckFeature(
        name=MY_NEW_CHECK,
        optionsCls=myParser.Options,
        resultCls=myParser.Result,
        defaultParams={"threshold": 1.0, "iterations": 10},  # Auto-generates widgets!
        display=myParser.displayResults
    ),
}
```

The widgets will be automatically generated on next plugin load!

## Comparison: Manual vs Automated

### File Size

- **PVMeshDoctorChecks.py** (manual): ~420 lines
- **PVMeshDoctorChecks_Auto.py** (automated): ~160 lines
- **Reduction**: ~60% less code

### Maintenance

- **Manual**: Add ~40-60 lines per new check parameter
- **Automated**: Just update `defaultParams` in parser module (where it belongs!)

### Consistency

- **Manual**: Easy to have inconsistent naming, documentation, or decorators
- **Automated**: Guaranteed consistent widget generation across all checks

## Testing

To test the automated version:

1. Load `PVMeshDoctorChecks_Auto.py` in ParaView
2. Verify all parameter widgets appear correctly
3. Check that parameter values are stored in `_customParameters`
4. Ensure the PropertyGroup decorators show/hide based on check selection

## Migration Path

1. **Test**: Load `PVMeshDoctorChecks_Auto.py` alongside the manual version
2. **Compare**: Verify widget generation matches manual definitions
3. **Replace**: Rename `PVMeshDoctorChecks_Auto.py` to `PVMeshDoctorChecks.py`
4. **Clean**: Remove old manual widget definitions

## Limitations

- Decorators must be applied at class definition time, so `add_widgets_to_class()` must be called after the class is defined but before it's used
- Complex custom widgets (e.g., file selectors, color pickers) may still need manual definition
- Widget ordering is determined by `ORDERED_CHECK_NAMES` and parameter dictionary order

## Future Enhancements

Potential improvements:

1. Support for enum/choice parameters (dropdown menus)
2. Advanced range constraints (linked parameters)
3. Conditional visibility between parameters
4. Help tooltips from docstrings
5. Unit conversions (e.g., degrees ↔ radians)

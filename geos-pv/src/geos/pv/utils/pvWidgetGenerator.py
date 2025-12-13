# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
"""Utility module for dynamically generating ParaView widget properties from check configurations."""

from typing import Any, Callable
from paraview.util.vtkAlgorithm import smdomain, smproperty


def _get_parameter_metadata(param_name: str, param_value: Any, check_name: str) -> dict[str, Any]:
    """Extract metadata for a parameter to generate appropriate ParaView widgets.
    
    Args:
        param_name: Name of the parameter
        param_value: Default value of the parameter
        check_name: Name of the check this parameter belongs to
        
    Returns:
        Dictionary containing widget metadata
    """
    metadata = {
        'param_name': param_name,
        'default_value': param_value,
        'check_name': check_name,
    }
    
    # Determine the type and widget properties
    if isinstance(param_value, bool):
        metadata['widget_type'] = 'boolean'
        metadata['pv_property'] = 'intvector'
        metadata['domain_type'] = 'BooleanDomain'
        metadata['range_min'] = None
        metadata['range_max'] = None
    elif isinstance(param_value, int):
        metadata['widget_type'] = 'integer'
        metadata['pv_property'] = 'intvector'
        metadata['domain_type'] = 'IntRangeDomain'
        metadata['range_min'] = 1 if 'size' in param_name.lower() or 'proc' in param_name.lower() else None
        metadata['range_max'] = None
    elif isinstance(param_value, float):
        metadata['widget_type'] = 'float'
        metadata['pv_property'] = 'doublevector'
        metadata['domain_type'] = 'DoubleRangeDomain'
        # Set min to 0 for common parameter types
        is_non_negative = any(kw in param_name.lower() for kw in ['tolerance', 'distance', 'volume'])
        metadata['range_min'] = 0.0 if is_non_negative else None
        metadata['range_max'] = None
    else:
        metadata['widget_type'] = 'string'
        metadata['pv_property'] = 'stringvector'
        metadata['domain_type'] = None
        metadata['range_min'] = None
        metadata['range_max'] = None
    
    # Generate nice display label from parameter name
    # Convert camelCase or snake_case to Title Case
    label_parts = []
    if '_' in param_name:
        label_parts = param_name.split('_')
    else:
        # Handle camelCase
        import re
        label_parts = re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', param_name)).split()
    
    metadata['display_label'] = ' '.join(word.capitalize() for word in label_parts)
    
    # Generate documentation
    doc_templates = {
        'tolerance': f"Tolerance value for {check_name} check.",
        'distance': f"Distance threshold for {check_name} check.",
        'volume': f"Volume threshold for {check_name} check.",
        'angle': f"Angle tolerance in degrees for {check_name} check.",
        'size': f"Size parameter for {check_name} check.",
        'proc': "Number of processors for parallel processing.",
    }
    
    metadata['documentation'] = next(
        (doc for key, doc in doc_templates.items() if key in param_name.lower()),
        f"Parameter {param_name} for {check_name} check."
    )
    
    return metadata


def create_widget_setter(param_metadata: dict[str, Any]) -> Callable:
    """Create a setter method with appropriate ParaView decorators.
    
    Args:
        param_metadata: Metadata dictionary for the parameter
        
    Returns:
        Decorated setter method
    """
    param_name = param_metadata['param_name']
    check_name = param_metadata['check_name']
    default_value = param_metadata['default_value']
    display_label = param_metadata['display_label']
    documentation = param_metadata['documentation']
    pv_property = param_metadata['pv_property']
    domain_type = param_metadata['domain_type']
    range_min = param_metadata['range_min']
    
    # Create the internal attribute name
    internal_attr = f'_{check_name.replace("-", "_")}_{param_name}'
    
    # Create method name (PascalCase)
    method_name = f'Set{check_name.title().replace("_", "").replace("-", "")}{param_name[0].upper()}{param_name[1:]}'
    
    # Create the setter function
    def setter(self, value):
        if not hasattr(self, internal_attr) or getattr(self, internal_attr) != value:
            setattr(self, internal_attr, value)
            if check_name not in self._customParameters:
                self._customParameters[check_name] = {}
            self._customParameters[check_name][param_name] = value
            self.Modified()
    
    # Apply property decorator
    if pv_property == 'doublevector':
        setter = smproperty.doublevector(
            name=f'{check_name.title().replace("_", "").replace("-", "")}_{param_name[0].upper()}{param_name[1:]}',
            label=display_label,
            default_values=default_value,
            number_of_elements=1,
        )(setter)
    elif pv_property == 'intvector':
        setter = smproperty.intvector(
            name=f'{check_name.title().replace("_", "").replace("-", "")}_{param_name[0].upper()}{param_name[1:]}',
            label=display_label,
            default_values=default_value,
            number_of_elements=1,
        )(setter)
    
    # Build domain XML
    domain_xml_parts = []
    if domain_type:
        domain_xml_parts.append(f'<{domain_type} name="range"')
        if range_min is not None:
            domain_xml_parts.append(f' min="{range_min}"')
        domain_xml_parts.append(' />')
    domain_xml_parts.append(f'<Documentation>{documentation}</Documentation>')
    domain_xml = '\n'.join(domain_xml_parts)
    
    # Apply domain decorator
    setter = smdomain.xml(domain_xml)(setter)
    
    setter.__name__ = method_name
    setter._param_name = param_name  # Store for later use in grouping
    
    return setter


def create_widget_group(check_name: str, param_names: list[str], group_index: int) -> Callable:
    """Create a property group method for organizing related parameters.
    
    Args:
        check_name: Name of the check
        param_names: List of parameter names in this group
        group_index: Index for ordering groups (used in method name)
        
    Returns:
        Decorated grouping method
    """
    # Create nice display name from check_name
    display_name = check_name.replace('_', ' ').replace('-', ' ').title()
    
    # Build property list for the group
    property_elements = []
    for param_name in param_names:
        prop_name = f'{check_name.title().replace("_", "").replace("-", "")}_{param_name[0].upper()}{param_name[1:]}'
        property_elements.append(f'<Property name="{prop_name}"/>')
    
    # Build the XML
    group_xml = f"""
                    <PropertyGroup label="{display_name} Parameters" panel_widget="Line">
                        {chr(10).join(' ' * 24 + prop for prop in property_elements)}
                        <Hints>
                            <PropertyWidgetDecorator type="ArraySelectionWidgetDecorator"
                            property="ChecksToPerform"
                            array_name="{check_name}" />
                        </Hints>
                    </PropertyGroup>
                    """
    
    def group_method(self):
        """Group {display_name} parameters."""
        pass
    
    # Apply decorator
    group_method = smproperty.xml(group_xml)(group_method)
    
    # Create method name with index for ordering
    group_method.__name__ = f'a{group_index:02d}Group{check_name.title().replace("_", "").replace("-", "")}Params'
    
    return group_method


def generate_widgets_for_check(check_name: str, default_params: dict[str, Any], group_index: int) -> dict[str, Callable]:
    """Generate all widget methods for a specific check.
    
    Args:
        check_name: Name of the check
        default_params: Dictionary of parameter names to default values
        group_index: Index for ordering property groups
        
    Returns:
        Dictionary mapping method names to decorated methods
    """
    methods = {}
    param_names = []
    
    # Create setters for each parameter
    for param_name, param_value in default_params.items():
        metadata = _get_parameter_metadata(param_name, param_value, check_name)
        setter = create_widget_setter(metadata)
        methods[setter.__name__] = setter
        param_names.append(param_name)
    
    # Create the property group
    if param_names:
        group_method = create_widget_group(check_name, param_names, group_index)
        methods[group_method.__name__] = group_method
    
    return methods


def add_widgets_to_class(cls: type, check_features_config: dict) -> type:
    """Add dynamically generated widget methods to a class.
    
    This function can be used as a class decorator or called directly.
    
    Args:
        cls: The class to add methods to
        check_features_config: Dictionary mapping check names to CheckFeature objects
        
    Returns:
        The modified class
    """
    group_index = 1
    
    for check_name, check_feature in check_features_config.items():
        if hasattr(check_feature, 'defaultParams') and check_feature.defaultParams:
            methods = generate_widgets_for_check(
                check_name, 
                check_feature.defaultParams, 
                group_index
            )
            
            # Add methods to class
            for method_name, method in methods.items():
                setattr(cls, method_name, method)
            
            group_index += 1
    
    return cls

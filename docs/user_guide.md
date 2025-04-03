---
Title: GEOS Paraview Plugins User Guide
SubTitle: PV plugins to process GEOS inputs/outputs
Author: Martin LEMAY
Company: TotalEnergies
Date: January 29, 2025
---


<div style="text-align:center" style="line-height:4">

<font size="26"><b>
{{ Title }}
</b></font>

<font size="20"><b>
{{ SubTitle }}
</b></font>

{{ Author }}

*{{ CurrentDate }}*

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

</div>

<div style="page-break-after: always;"></div>

<style>body {text-align: justify}</style>

## Outline 

- [1. Introduction](#1-introduction)
  - [1.1. Paraview at a glance](#11-paraview-at-a-glance)
  - [1.2. Paraview filters for GEOS](#12-paraview-filters-for-geos)
- [2. Pre-processing GEOS inputs](#2-pre-processing-geos-inputs)
- [3. Load and plot GEOS Log Data](#3-load-and-plot-geos-log-data)
  - [3.1. GEOS Log Reader](#31-geos-log-reader)
  - [3.2. Plot data from spreadsheets using Python View Configurator](#32-plot-data-from-spreadsheets-using-python-view-configurator)
- [4. Load and clean GEOS output mesh and properties](#4-load-and-clean-geos-output-mesh-and-properties)
- [5. Geomechanics Post-Processing](#5-geomechanics-post-processing)
  - [5.1. Compute additional geomechanical properties](#51-compute-additional-geomechanical-properties)
  - [5.2. Compute additional surfacic geomechanical properties](#52-compute-additional-surfacic-geomechanical-properties)
  - [5.3. Geomechanics workflows](#53-geomechanics-workflows)
  - [5.4. Plot 2D Mohr's Circles for geomechanics studies](#54-plot-2d-mohrs-circles-for-geomechanics-studies)
- [6. Utilities](#6-utilities)
  - [6.1. Transfer attributes between identical or partial meshes](#61-transfer-attributes-between-identical-or-partial-meshes)
  - [6.2. Transfer properties from Volume mesh to surfaces](#62-transfer-properties-from-volume-mesh-to-surfaces)
  - [6.3. Merge blocks keeping partial attributes](#63-merge-blocks-keeping-partial-attributes)
- [7. Other tools around GEOS](#7-other-tools-around-geos)
  - [7.1. GEOS Python tools](#71-geos-python-tools)
  - [7.2. geos-xml-viewer](#72-geos-xml-viewer)

<div style="page-break-after: always;"></div>

## What you will learn in this documentation

* What are GEOS outputs:
* How to load and plot information from GEOS output log
* How to load and process GEOS output mesh
* How to compute additional geomechanical outputs
* How to plot Mohr's circles
* How to create scatter plots


## Prerequisites

**On GEOS**

* Get the output mesh with properties in pvd format
* Get the simulation log in .txt or .out format

**On Paraview**

* Basic knowledge of Paraview

<div style="page-break-after: always;"></div>

# 1. Introduction

## 1.1. Paraview at a glance

Paraview (PV) is an open source application and architecture for the 2D and 3D visualization and analysis of large scale scientific data sets. It has been developed by the Kitware company since 2000 and is merely funded by DOE programs or by external companies. It is downloaded approximately 100,000 times a year and is recognized as a leader scientific visualization application by many institutions and companies. It has initially been designed for computational fluid dynamics visualizations but its extensible and modular architecture enables it to extend to new areas. It makes ParaView a general purpose tool for a wide range of applications.

For more details, see the following documentation:
* [Paraview website and user guides](https://docs.paraview.org/en/latest/index.html)

<br/>

## 1.2. Paraview filters for GEOS

GEOS is a R&D simulation software, which implies that:

* input data must be cautiously prepared to be compliant with GEOS
* output data must be post-processed to be visualized or to be compliant with other softwares

To this end, several tools have been developed around GEOS to pre-process and post-process GEOS inputs/outputs (see section [Other tools around GEOS](#7-other-tools-around-geos)) and to integrate it in the global geomedeling workflow. 

<br/>

In particular, several Paraview plugins have been developed to enable the users to visualize data -especially unstructured meshes- and to make the tools more user-friendly. These plugins and described in the following.

Filters are organized as following in the `Filters` menu:
* `0- Geos Pre-Processing`: filters to process the mesh before GEOS simulations
* `1- Geos Post-Processing Workflows`: Composite filters that combine individual post-processing filters to apply on GEOS simulation results.
* `2- Geos Output Mesh Pre-Processing`: Individual post-processing filters to apply on GEOS simulation results to clean the mesh.
* `3- Geos Geomechanics`: Individual filters to perform geomechanic analysis of GEOS simulation results.
* `4- Geos Utils`: Individual filters to process and visualize the mesh.

<div style="text-align:center">

![GEOS filters](images/GEOS_filter_organisation.JPG)

<figcaption><i>Figure 1: GEOS filter organization in Paraview.</i></figcaption>
</div>
<br/>

# 2. Pre-processing GEOS inputs

GEOS input data needs to be processed from the geomedeller to make it valid for GEOS. Most of these operations are currently made by [`mesh-doctor`](#71-geos-python-tools) and [`geos-xml-viewer`](#72-geos-xml-viewer), and Paraview plugins are not available yet for these tools. 

The pre-processing `Create Constant attribute Per Region` filter was however developed in Paraview to ease the creation of properties constant per regions, such region being defined using another index property. 
Input mesh can be of any type and composite. The user needs to select the region property, to define the name of output property, and to defined the values of the output property for each region index. If no value is defined for some region indexes, the output property will yield no data value in these regions.

> [!IMPORTANT]
> #### To use this filter
>
> 1. Select the mesh you want to add an attribute
> 2. Apply `Create Constant attribute Per Region` filter
> 3. Define input parameters
> 4. Click on `Apply`

In the example shown in the Figure hereafter, the mesh consists of 3 regions defined using the property named "region" whose values are (0, 1, 2) and can be seen in the 3D viewer on the left hand. A new property named here "Porosity" is created whose values are:

* 0.05 in region index 0
* 0.15 in region index 1
* 0.2 in region index 2

The resulting property is shown in the 3D viewer on the right hand.

<div style="text-align:center">

![GEOS filters](images/CreateConstantAttributePerRegionFilter.JPG)

<figcaption><i>Figure 2: "CreateConstantAttributePerRegion" filter.</i></figcaption>

</div>
<br/>


# 3. Load and plot GEOS Log Data

GEOS dumps data in a log file whose name is usually "job_GEOS_[JOB ID].out". This text file can be read by the user. It contains:
* the list of all the events that happens during the simulation


<div style="text-align:center">

![GEOS log file](images/GEOS_log_start.JPG)

<figcaption><i>Figure 3: GEOS output log file - GEOS events.</i></figcaption>

</div>
<br/>

* if activated, a lot of information on:
  * Flow properties
  * Well properties
  * Aquifer properties
  * Solver properties

<div style="text-align:center">

![GEOS log - time step data](images/GEOS_log_time_step.JPG)

<figcaption><i>Figure 6: GEOS output log file - Time step information.</i></figcaption>

</div>
<br/>

This log file is currently the subject of a lot of work by the GEOS Integration Team to make the information clearer and more easily readible.

The data contained in this file can also be loaded in Paraview as a spreadsheet to be processed and plotted. 

> [!TIP]
> #### How to export simulation data to GEOS log in GEOS xml file?
> 
> Information dumped into the log file is controlled by the field `log_level` from `Statistics` tasks in the xml file.
>
> <div style="text-align:center">
>
> <img src="images/GEOS_XML_flowSolver.JPG" alt="GEOS xml - flow solvers" width="400"/>
> 
> <img src="images/GEOS_XML_Wells.JPG" alt="GEOS xml - wells" width="400"/>
> 
> <figcaption><i>Figure 4: Activation of statistic outputs in the GEOS xml file.</i></figcaption>
> </div>

## 3.1. GEOS Log Reader

A Paraview plugin has been developped to read GEOS log file. To load a log file, the user uses the `Open` command from Paraview, selects the log file, then selects the right reader named `Geos Log Reader`.

<div style="text-align:center">

<img src="images/GEOS_log_Reader0.JPG" alt="GEOS Log Reader" width="400"/>

<figcaption><i>Figure 5: Steps to open GEOS log file using "GEOS Log Reader".</i></figcaption>

</div>
<br/>

The user can now select in the `Properties` panel the information type to load among:

* `Flow` properties statistics
* `Wells` properties statistics
* `Aquifers` properties
* `Convergence` metrics

All the properties read in the file are listed and can be manually selected. In addition, the user can enter the phase names if they are known, and choose working units.

<div style="text-align:center">

![GEOS Log Reader - Properties Panel](images/GEOS_log_Reader1.JPG)

<figcaption><i>Figure 6: "GEOS log Reader" - Properties panel.</i></figcaption>

</div>
<br/>

Loaded data are displayed in a SpreadSheetView.

<div style="text-align:center">

![GEOS Log Data](images/GEOS_log_data_spreadsheet.JPG)

<figcaption><i>Figure 7: Loaded properties as a spreadsheet using "GEOS log Reader".</i></figcaption>

</div>
<br/>

> [!TIP]
> If the user wants to load multiple property types from the log (e.g., both Flow and Wells), the same file must be loaded twice using GEOS Log Reader and selecting in each one the correct type.

> [!CAUTION]
> The reader is compliant until the GEOS commit version #9365098. 
> 
> Use the **csv export** options for more recent versions of GEOS and directly load the csv into Paraview.

> [!TIP]
> #### How to export simulation data to csv file in GEOS xml file?
> 
> Information dumped into the csv file is controlled by the field `writecsv` from `Statistics` tasks in the xml file.
>
> <div style="text-align:center">
>
> <img src="images/GEOS_XML_csv_export.JPG" alt="GEOS xml - csv export" width="400"/>
> 
> <figcaption><i>Figure 8: Activation of csv export in the GEOS xml file.</i></figcaption>
> </div>

## 3.2. Plot data from spreadsheets using Python View Configurator

A common task is to plot the data loaded from GEOS log file or csv files. To do that, a plugin has been developped to create and display plots in Paraview using the `PythonView`.

The user must choose the filter `Filters>4- Geos Utils>Python View Configurator`. In the `Properties` panel, the following parameters must be defined:

* Input sources: input data source to plot
* Curves To Plot: abcissa and ordinate data to plot. Multiple curve can be plotted in the same graph, but a same scale is used for all of them. If some regions are defined, data can be splitted by regions if the checkbox is toggled.
* Curve Convention: Toggle to select from the list the curves to change convention (multiplied by -1). This is usefull for instance to plot Stress and Pressure on a same plot using the right convention.
* Axis Properties: Toggle `Edit Axis Properties` to access to axis properties. Axes can be reversed, use a log scale, display minor ticks, or set limits.
* Title Properties: Toggle `Display Title` to add a title to the figure and edit font properties.
* Legend Properties: Toggle `Display Legend` to add a legend to the figure and edit position and labels.
* Curves Properties: Toggle `Edit Curve Graphics` to edit markers and line properties.

> [!IMPORTANT]
> #### To use this filter
> 1. Select input data to plot
> 2. Apply `Python View Configurator` filter
> 3. Define input parameters
> 4. Click on `Apply`

<div style="text-align:center">

![Pressure vs Time](images/pressure_vs_time.JPG) 

<figcaption><i>Figure 9: Plot Pressure vs. Time using "Python View Configurator" filter from GEOS log outputs.</i></figcaption>

</div>
<br/>

> [!TIP]
> `Python View Configurator` is able to plot data from any spreadsheets, whatever its origin (e.g., data along a line).
> The image hereafter shows an example of pipeline and `Python View Configurator` filter parameters to plot Pressure, total and effective stresses against the depth.
>
> <div style="text-align:center">
> 
> ![Pressure and Stress vs Depth](images/stress_along_well.JPG) 
>
> <figcaption><i>Figure 10: Steps to Plot Pressure and Stress vs. Depth using "Python View Configurator" filter from GEOS output mesh.</i></figcaption>
> 
> </div>

# 4. Load and clean GEOS output mesh and properties

GEOS may result in an output mesh containing simulated properties at multiple time steps. The export format is a `.pvd` xml file referring to the corresponding vtm file for each time step.

<div style="text-align:center">

<img src="images/pvd_file.JPG" alt="GEOS output pvd file" width="500"/>

<figcaption><i>Figure 11: pvd file containing time step value and path to corresponding vtm file.</i></figcaption>

</div>
<br/>

> [!TIP]
> #### How to activate vtk output mesh in GEOS xml file?
> 
> To activate the output mesh, xml file must contains the following sections:
> * `<Outputs>` with the `VTK` field, where `fieldNames` allows to define exported properties, and set `logLevel` key to 2.
> * `<Events>` with `<PeriodicEvents>` pointing to vtk output name.
> 
> <div style="text-align:center">
> 
> ![GEOS output mesh](images/GEOS_XML_vtkOutput.JPG) 
>
> <figcaption><i>Figure 12: Activation of output mesh in GEOS XML file.</i></figcaption>
> 
> </div>

To load GEOS output mesh in Paraview, the user uses the `Open` command from Paraview and selects the `.pvd` file. The file name must appears in the Pipeline Browser. The user may display the properties in the 3D View, and run through the time steps using the `Time Manager` toolbar. 

> [!TIP]
> The `.pvd` file can be copied and manually edited to select desired time steps to save computation time in Paraview.
 
GEOS output mesh is a composite data set containing all the objects used in the simulation including the volume mesh, surfaces (faults), and wells. Each object may contain regions -e.g., one region per layer in the volume mesh, one region per fault, or one region per well- and each region is splitted in ranks because of parallel processing during GEOS simulation. In addition, property names take the name of the region they are computed. Consequently a property may have various prefix although it represents a same property -e.g., "reservoir_Porosity", "overburden_Porosity", "underburden_Porosity". 

<div style="text-align:center">

<img src="images/MultiBlock_inspector.JPG" alt="MultiBlock inspector" width="400"/>

<figcaption><i>Figure 13: Paraview MultiBlock Inspector showing GEOS output mesh architecture.</i></figcaption>

</div>
<br/>

A set of 4 filters located in `Filters>2 Geos Output Mesh Pre-Processing` can be used to clean the mesh depending on mesh content: `Geos Extract And Merge Blocks - Volume Only`, `Geos Extract And Merge Blocks - Volume/Surface`, `Geos Extract And Merge Blocks - Volume/Surface/Well`, `Geos Extract And Merge Blocks - Volume/Well`. These filters result in one, two, or three outputs, `output-0` being the volume mesh, `output-1` being surfaces or wells if 2 outputs are present, `output-3` being wells.
These filters do the following operations:
* merge rank blocks for each regions and create "blockIndex" property to keep memory of ranks
* merge properties whose names contain various prefix and rename some properties like "stress" in "effectiveStress"
* copy some property values from initial time step to the other time steps ("Porosity", "effectiveStress", "Pressure")
* compute surface normal and tangent vectors

> [!IMPORTANT]
> #### To use this filter
> 1. Select GEOS output mesh
> 2. Apply one of `Geos Extract And Merge Blocks` filters according to the data content
> 3. Click on `Apply`

<div style="text-align:center">

![GeosExtractAndMergeBlocks](images/ExtractMergeBlockFilter.JPG) 

<figcaption><i>Figure 14: "Geos Extract And Merge Blocks" filters.</i></figcaption>

</div>
<br/>

# 5. Geomechanics Post-Processing

GEOS computes many outputs including flow and geomechanic properties if coupled flow geomechanics simulations were run. Users however need additional metrics to asses geomechanical stability as part of operational studies. Two filters have been developped to compute these additional metrics: `Geos Geomechanics Analysis` and `Geos Surfacic Geomechanics`. In addition, a third filter allows to plot Mohr's circles on selected cells and time steps.

## 5.1. Compute additional geomechanical properties

`Geos Geomechanics Analysis` filter located in `Filters>3 Geos Geomechanics` computes additional geomechanics properties on input object (volume, surface, polyline mesh). 
This filter has the following input parameters:
* grain bulk modulus to compute Biot coefficient if the property is not in the mesh
* the reference density used to compute specific gravity
* if `Compute Advanced Geomechanical Outputs` is toggled, other metrics are computed. Additional parameters are rock cohesion (in Pa) and friction angle (in °).

> [!IMPORTANT]
> #### To use this filter
> 1. Select output-0 from one of `Geos Extract And Merge Blocks` filters
> 2. Apply `Geos Geomechanics Analysis` filter
> 3. Define input parameters
> 4. Click on `Apply`
 
<div style="text-align:center">

![Geomechanics Analysis filter](images/GeomechanicsAnalysis.JPG)

<figcaption><i>Figure 15: "GEOS Geomechanics Analysis" filter applied on a volume mesh.</i></figcaption>

</div>
<br/>

All properties are computed if they are not already present in the mesh as a GEOS output.

<figcaption><i>Table 1: Geomechanical basic outputs.</i></figcaption>

| <div style="width:200px">Property</div> | <div style="width:200px">Property Name</div> |  <div style="width:250px">Formulae</div> |
| ------------------- | ------------------- | --------------------------- |
| Young modulus       | youngModulus        | $E=\frac{9K.G}{3K+G}$       | 
| Poisson ratio       | poissonRatio        | $\nu=\frac{3K-2G}{2(3K+G)}$ | 
| Bulk modulus        | bulkModulus         | $K=\frac{E}{3(1-2\nu)}$     | 
| Shear modulus       | shearModulus        | $G=\frac{E}{2(1+\nu)}$      | 
| Biot coefficient    | biotCoefficient     | $b=1-\frac{K}{K_{grain}}$   | 
| Specific gravity    | specificGravity     | $SG=\frac{\rho}{\rho_{ref}}$ | 
| Elastic strain      | strainElastic       | $\epsilon=\Delta\sigma_{eff}.C^{-1}$ | 
| Effective stress ratio <br/> in oedometric conditions | stressEffectiveRatio_oed | $r_{eff}^{oed}=\frac{\nu}{1-\nu}$ | 
| Effective stress ratio <br/> in real conditions | stressEffectiveRatio_real | $r_{eff}^{real}=\frac{\sigma_{eff}^h}{\sigma_{eff}^v}$ | |
| Total stress        | stressTotal | $\sigma_{tot}=\sigma_{eff}-bP$ | |
| Total stress deviation | deltaStressTotal | $\Delta\sigma_{tot}=\sigma_{tot}^{@t}-\sigma_{tot}^{@t_0}$ | 
| Total stress ratio <br/> in real conditions | stressTotalRatio_real | $r_{tot}=\frac{\sigma_{tot}^h}{\sigma_{tot}^v}$ | 
| Reservoir Stress Path <br/> in oedometric conditions | RSP_oed | $RSP_{oed}=b\frac{1-2\nu}{1-\nu}$  |
| Reservoir Stress Path <br/> in real conditions | RSP_real | $RSP_{real}=\frac{\Delta\sigma}{\Delta P}$ |  
| Compressibility coefficient <br/> in oedometric conditions | compressibility_oed | $C_{oed}=\frac{1}{\phi}.\frac{3}{3K+4G}$ |  
| Compressibility coefficient <br/> in real conditions | compressibility_real | $C_{real}=\frac{\phi-\phi_0}{\Delta P.\phi_0}$ |  

where $\rho$ is density, $\rho_{ref} is reference density, $K_{grain}$ is grain bulk modulus, $\sigma_{eff}$ is effective stress, *P* is pressure, exponent *h* and *v* stand for horizontal and vertical (e.g., $\sigma_{eff}^v$ is vertical effective stress), *C* is stiffness tensor, $\Delta$ stands for deviation from initial time step (e.g., $\Delta P$  is pressure deviation).

<figcaption><i>Table 2: Geomechanical advanced outputs.</i></figcaption>

| <div style="width:150px">Property</div> | <div style="width:150px">Property Name</div> |  <div style="width:180px">Formulae</div> | <div style="width:250px">Comment</div> |
| ------------------- | ------------------- | --------------------------- | ------- |
| Critical total stress ratio | totalStressRatioCritical_real | $\sigma_{Ĉr}=\frac{P}{\sigma_v}$ | <span style="font-size:0.8em">Corresponds to the fracture index from Lemgruber-Traby et al (2024). Fracturing can occur in areas where K > Total stress ratio. (see [Lemgruber-Traby, A., Cacas, M. C., Bonte, D., Rudkiewicz, J. L., Gout, C., & Cornu, T. (2024). Basin modelling workflow applied to the screening of deep aquifers for potential CO2 storage. Geoenergy, geoenergy2024-010.](https://doi.org/10.1144/geoenergy2024-010))</span> |
| Total stress ratio threshold | totalStressRatioThreshold_real | $\sigma_{Th}=\frac{P}{\sigma_h}$ | <span style="font-size:0.8em">Corresponds to the fracture threshold from Lemgruber-Traby et al (2024). Fracturing can occur in areas where FT > 1. Equals FractureIndex / totalStressRatio. (see [Lemgruber-Traby, A., Cacas, M. C., Bonte, D., Rudkiewicz, J. L., Gout, C., & Cornu, T. (2024). Basin modelling workflow applied to the screening of deep aquifers for potential CO2 storage. Geoenergy, geoenergy2024-010.](https://doi.org/10.1144/geoenergy2024-010))</span> |
| Critical pore pressure | porePressureCritical_real | $P_{Cr}=\frac{c.\cos(\alpha)}{1-\sin(\alpha)} + \frac{3\sigma_3-\sigma_1}{2}$ | <span style="font-size:0.8em">Fracturing can occur in areas where Critical pore pressure is greater than the pressure. (see [Khan, S., Khulief, Y., Juanes, R., Bashmal, S., Usman, M., & Al-Shuhail, A. (2024). Geomechanical Modeling of CO2 Sequestration: A Review Focused on CO2 Injection and Monitoring. Journal of Environmental Chemical Engineering, 112847.](https://doi.org/10.1016/j.jece.2024.112847))</span> |
| Pore pressure threshold | porePressureThreshold_real | $P_{Th}=\frac{P}{P_{Cr}}$ | <span style="font-size:0.8em">Defined as the ratio between pressure and critical pore pressure. Fracturing can occur in areas where critical pore pressure threshold is >1. (see [Khan, S., Khulief, Y., Juanes, R., Bashmal, S., Usman, M., & Al-Shuhail, A. (2024). Geomechanical Modeling of CO2 Sequestration: A Review Focused on CO2 Injection and Monitoring. Journal of Environmental Chemical Engineering, 112847.](https://doi.org/10.1016/j.jece.2024.112847))</span> |

where *c* is rock cohesion and $\alpha$ is friction angle.

> [!CAUTION]
> Elastic moduli properties -i.e., either Shear and Bulk moduli, or Young modulus and Poisson ratio- are necessary to compute additional geomechanical properties. An error message warns the user if these properties are missing.


> #### How to output elastic moduli in GEOS xml file?
> 
> Elastic moduli properties can be manually added to the output mesh in Paraview using for instance the `Calculator` filter. But if these moduli vary in space and/or time, it is better to export the properties in the output mesh. 
> 
> To do that, the `fieldNames` key from `VTK` field in the `<Outputs>` section of GEOS xml file must contains the list of output property names like `rock_bulkModulus`, `rock_shearModulus`, `rock_youngModulus`, `rock_poissonRatio`, etc. (e.g., ![GEOS output mesh]), where `rock` refers to `materialList` key elements from `ElementRegions` field in the xml file.

> [!CAUTION]
> This filter must be applied to output-0 from `Geos Extract And Merge Blocks` filters.

## 5.2. Compute additional surfacic geomechanical properties

`Geos Surfacic Geomechanics` filter located in `Filters>3 Geos Geomechanics` computes additional geomechanics properties and is dedicated to surfaces. This filter computes:
* the displacementJump property in the XYZ axes in addition to normal and tangential axes given by GEOS.
* the shear capacity utilization (SCU) property. This calculation needs rock cohesion (in Pa) and friction angle (in °) to compute failure threshold. SCU formula is: $SCU = \frac{abs(\tau_1)}{\tau_{max}}$, where $\tau_1$ is the maximal principal stress and $\tau_{max}$ is the failure threshold.

> [!IMPORTANT]
> #### To use this filter
> 1. Select output-1 from `Geos Extract And Merge Blocks - Volume/Surface` or `Geos Extract And Merge Blocks - Volume/Surface/Well` filters
> 2. Apply one of `Geos Surfacic Geomechanics` filter
> 3. Define input parameters
> 4. Click on `Apply`

<div style="text-align:center">

![Surface Geomechanics](images/SurfaceGeomechanics.JPG)

<figcaption><i>Figure 16: "GEOS Surface Geomechanics" filter.</i></figcaption>

</div>
<br/>

> [!IMPORTANT]
> This filter must be applied to output-1 from `Geos Extract And Merge Blocks - Volume/Surface` or `Geos Extract And Merge Blocks - Volume/Surface/Well` filters.

## 5.3. Geomechanics workflows

During geomechanical studies, users will most often have to apply one of the `Geos Extract And Merge Blocks` filters, then `Geos Geomechanics Analysis` on output-0 and/or `Geos Surface Geomechanics` on output-1. 

`Geos Geomechanics Workflow` filters located in `Filters>1-Geos Post-Processing Workflows` gather the successive application of these filters in a single one depending on input objects. Results are the same as the combination of the elementary filters.

> [!IMPORTANT]
> #### To use this filter
> 1. Select GEOS output mesh
> 2. Apply one of `Geos Geomechanics Workflow` filters according to the data content
> 3. Define input parameters
> 4. Click on `Apply`
 
<div style="text-align:center">

![Geomechanics Workflows](images/GeomechanicsWorkflows.JPG)

<figcaption><i>Figure 17: "GEOS Geomechanics Workflow - Volume/Surface" filter.</i></figcaption>

</div>
<br/>

## 5.4. Plot 2D Mohr's Circles for geomechanics studies

Geomechanical studies most often rely on Mohr-s circle analysis. Mohr's circle can be plotted from a selection of cells and time steps using `Plot Mohr's Circles` filter located in `Filters>3-Geos Geomechanics`.

Input parameters in the `Properties` panel are:
* Ids of the cell to plot
* Time steps to plot
* Mohr-Coulomb failure envelop parameters -i.e., rock cohesion (in Pa) and friction angle (in °)
* Stress unit used for axes
* Stress convention (default is positive for compression)
* Annotate circle checkbox allows to show/hide normal stress values
* show/hide minor ticks
* Show/Hide title and Legend parameters like font properties and legend location
* Show/Hide user-defined axis limits definition panel
* Show/Hide curve aspect edition panel

> [!IMPORTANT]
> #### To use this filter
> 1. Extract a reduce number of cells from GEOS output mesh (`Find Data>Extract Selection`) ([see Paraview documentatin](https://docs.paraview.org/en/latest/UsersGuide/selectingData.html))
> 2. Apply `MergeBlocks` filter
> 3. Apply `Plot Mohr's Circles` filter
> 4. Select circles to plot
> 5. Select plot parameters
> 6. Click on `Apply`

<div style="text-align:center">

![Mohr's circles plot](images/mohr_circle_plot.JPG)

<figcaption><i>Figure 18: Steps to plot Mohr's circles using "Plot Mohr's Circle" filter from GEOS output mesh.</i></figcaption>

</div>
<br/>

> [!CAUTION]
> `Plot Mohr's Circles` must be applied on a limited number of cells and input mesh must be merged (even if it consists of a single cell)

# 6. Utilities

`Filters>4-Geos Utilities` menu contains generic filters including `Python View Configurator` (see section *[3.2. Plot data from spreadsheets using Python View Configurator](#32-plot-data-from-spreadsheets-using-python-view-configurator))* and `Geos Transfer Attributes From Volume To Surface` filter.

In addition, writers have also been developped and are accessible using `Save Data` command of Paraview by selecting the appropriate output format. Currently, an exporter of a text file for EST containing map properties from GEOS simulation is available.

## 6.1. Transfer attributes between identical or partial meshes 

The filter `Attribute Mapping` allows to transfer properties from a server mesh to a client mesh. The server and client meshes must be either strictly identical or one an extract from the other one. The server mesh must be a single block dataset, whereas the output mesh can be a single or multi block dataset.

> [!IMPORTANT]
> #### To use this filter
> 1. Select the server mesh from which properties will be transferred
> 2. Select the `Attribute Mapping` filter
> 3. In the dialog, check the server mesh then select the client mesh the properties to transfer go to
> 4. In the `Properties` panel, select the properties to transfer
> 5. Click on `Apply`

> In the following example, the property "region" was transferred from GEOS input mesh (to the left) to GEOS output mesh (to the right).

<div style="text-align:center">

![Transfer properties between 2 meshes](images/AttributeMapping.JPG)

<figcaption><i>Figure 19: Application of "Attribute Mapping" filter.</i></figcaption>

</div>
<br/>

## 6.2. Transfer properties from Volume mesh to surfaces

`Geos Transfer Attributes From Volume To Surface` filter allows to transfer attributes initially stored on the volume mesh to a surface mesh. The surface mesh must be conformal to the volume mesh -i.e., surface and volume mesh vertices are collocated and surface faces correspond to volume cell faces. 

Because a surface usually defines a boundary of the model, properties may be discontinuous on both sides of the surface. Two properties are thus created on the surface using the name of input property and a suffix "_minus" and "_plus". Each property corresponds to the property value of cells adjacent to the surface along one side or the other.

> [!IMPORTANT]
> #### To use this filter
> 1. Select the volume mesh the properties to transfer are from
> 2. Apply `Geos Transfer Attributes From Volume To Surface` filter
> 3. In the dialog, select the surface mesh the properties to transfer go to
> 4. In the `Properties` panel, select the properties to transfer
> 5. Click on `Apply`

> In the following example, the property "totalStressThreshold_real" was transferred from volume to surface mesh. Top 3D viewer shows the volume mesh with the property and the surface edges in white.
> Bottom left viewer shows the property on the surface ("totalStressThreshold_real_minus") that was transferred from the volume to right side of the surface, bottom right viewer shows the property on the surface ("totalStressThreshold_real_plus") that was transferred from the volume to the left side of the surface. 

<div style="text-align:center">

![Transfer attributes from volume to surface mesh](images/TransferAttributes.JPG)

<figcaption><i>Figure 20: Application of "Geos Transfer Attributes From Volume To Surface" filter.</i></figcaption>

</div>
<br/>

> [!CAUTION]
> `Transfer Attributes From Volume To Surface` filter must be cautiously applied since the results may be nonsense.

## 6.3. Merge blocks keeping partial attributes

Paraview provides the `Merge Blocks` filter to merge multiblock mesh to a single block mesh. However, if some properties are partial (i.e., present in some blocks of different data type but not all), they are removed in the output mesh. The filter `Merge Blocks Keeping Partial Attributes` extends the `Merge Blocks` filter by transferring in the output mesh partial properties. They take the *nan* value where the attributes were absent. 

> [!IMPORTANT]
> #### To use this filter
> 1. Select the volume mesh to merge
> 2. Apply `Merge Blocks Keeping Partial Attributes` filter
> 3. Click on `Apply`

> In the following example, the mesh to the rigth is a multiBlock dataset containing partial attributes including the pressure defined only in the mid unit. After applying `Merge Blocks Keeping Partial Attributes` filter, all the blocks were merged together and all the attributes are present in the merged dataset.

<div style="text-align:center">

![Merge blocks and keep partial attributes](images/MergeBlocksEnhanced.JPG)

<figcaption><i>Figure 21: Application of "Merge Blocks Keeping Partial Attributes" filter.</i></figcaption>

</div>
<br/>

# 7. Other tools around GEOS

Other tools allow GEOS users to prepare GEOS input data. Except geos2est for which a Paraview plugin exists, these tools do not have a Paraview interface yet.

## 7.1. GEOS Python tools

`GEOS Python tools` allows to process GEOS input and output data (See [documentation](https://geosx-geosx.readthedocs-hosted.com/projects/geosx-geospythonpackages/en/latest/?_sm_au_=iMVrtR60VT6jHPNtQ0WpHK6H8sjL6)). 

Among these tools, [`mesh-doctor`](https://geosx-geosx.readthedocs-hosted.com/projects/geosx-geospythonpackages/en/latest/geos-mesh.html?_sm_au_=iMVrtR60VT6jHPNtQ0WpHK6H8sjL6) processes GEOS input data to make it compliant with GEOS. 

## 7.2. geos-xml-viewer

`geos-xml-viewer` is a Python package dedicated to visualize and process GEOS input xml file (deck). This package provides the following main functionalities:
* create a PartitionedDataSetCollection from vtu file and objects defined in the GEOS deck
* visualize deck objects (mesh, wells, boxes)
* split a deck into multiple files (e.g. one per main node)

<script type="text/javascript" src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>
<script type="text/x-mathjax-config"> MathJax.Hub.Config({ tex2jax: {inlineMath: [['$', '$']]}, messageStyle: "none" });</script>
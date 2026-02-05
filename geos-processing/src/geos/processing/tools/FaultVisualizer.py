import pandas as pd
from matplotlib.lines import Line2D
# ============================================================================
# VISUALIZATION
# ============================================================================
class Visualizer:
    """Visualization utilities"""

    # -------------------------------------------------------------------
    def __init__(self, config):
        self.config = config

    # -------------------------------------------------------------------
    @staticmethod
    def plotMohrCoulombDiagram(surface, time, path, show=True, save=True):
        """Create Mohr-Coulomb diagram with depth coloring"""

        sigmaN = -surface.cell_data["sigmaNEffective"]
        tau = np.abs(surface.cell_data["tauEffective"])
        SCU = np.abs(surface.cell_data["SCU"])
        depth = surface.cell_data['elementCenter'][:, 2]

        cohesion = surface.cell_data["mohrCohesion"][0]
        mu = surface.cell_data["mohrFrictionCoefficient"][0]
        phi = surface.cell_data['mohrFrictionAngle'][0]

        fig, axes = plt.subplots(1, 2, figsize=(16, 8))

        # Plot 1: τ vs σ_n
        ax1 = axes[0]
        sc1 = ax1.scatter(sigmaN, tau, c=depth, cmap='turbo_r', s=20, alpha=0.8)
        sigmaRange = np.linspace(0, np.max(sigmaN), 100)
        tauCritical = cohesion + mu * sigmaRange
        ax1.plot(sigmaRange, tauCritical, 'k--', linewidth=2,
                label=f'M-C (C={cohesion} bar, φ={phi}°)')
        ax1.set_xlabel('Normal Stress [bar]')
        ax1.set_ylabel('Shear Stress [bar]')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_title('Mohr-Coulomb Diagram')

        # Plot 2: SCU vs σ_n
        ax2 = axes[1]
        sc2 = ax2.scatter(sigmaN, SCU, c=depth, cmap='turbo_r', s=20, alpha=0.8)
        ax2.axhline(y=1.0, color='r', linestyle='--', label='Failure (SCU=1)')
        ax2.set_xlabel('Normal Stress [bar]')
        ax2.set_ylabel('SCU [-]')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_title('Shear Capacity Utilization')
        ax2.set_ylim(bottom=0)

        plt.colorbar(sc2, ax=ax2, label='Depth [m]')
        plt.tight_layout()

        if save:
            years = time / (365.25 * 24 * 3600)
            filename = f'mohr_coulomb_phi{phi}_c{cohesion}_{years:.0f}y.png'
            plt.savefig(path / filename, dpi=300, bbox_inches='tight')
            print(f"  📊 Plot saved: {filename}")

        if show:
            plt.show()
        else:
            plt.close()

    # -------------------------------------------------------------------
    @staticmethod
    def loadReferenceData(time, scriptDir=None, profileId=1):
        """
        Load GEOS and analytical reference data for comparison

        Parameters
        ----------
        time : float
            Current simulation time in seconds
        scriptDir : str or Path, optional
            Directory containing reference data files. If None, uses current directory.
        profileId : int, optional
            Profile ID to extract from Excel (default: 1)

        Returns
        -------
        dict
            Dictionary with keys 'geos' and 'analytical', each containing numpy arrays or None
            Format: {'geos': array or None, 'analytical': array or None}

            For GEOS data from Excel, the array has columns:
            [Depth_m, Normal_Stress_bar, Shear_Stress_bar, SCU, X_coordinate_m, Y_coordinate_m]
        """
        if scriptDir is None:
            scriptDir = os.path.dirname(os.path.abspath(__file__))

        result = {'geos': None, 'analytical': None}

        # ===================================================================
        # LOAD GEOS DATA - Try Excel first, then CSV
        # ===================================================================

        geosFileXLSV = 'geos_data_numerical.xlsx'
        geosFileCSV = 'geos_data_numerical.csv'

        # Try Excel format with time-based sheets
        geosXLSVPath = os.path.join(scriptDir, geosFileXLSV)

        if os.path.exists(geosXLSVPath):
            try:
                # Generate sheet name based on current time
                # Format: t_1.00e+02s
                sheetName = f"t_{time:.2e}s"

                print(f"     📂 Loading GEOS data from Excel sheet: '{sheetName}'")

                # Try to read the specific sheet
                try:
                    df = pd.read_excel(geosXLSVPath, sheet_name=sheetName)

                    # Filter by ProfileID if column exists
                    if 'ProfileID' in df.columns:
                        dfProfile = df[df['ProfileID'] == profileId]

                        if len(dfProfile) == 0:
                            print(f"        ⚠️  ProfileID {profileId} not found in sheet '{sheetName}'")
                            print(f"        Available Profile_IDs: {sorted(df['ProfileID'].unique())}")
                            # Take first profile as fallback
                            availableIds = sorted(df['ProfileID'].unique())
                            if len(availableIds) > 0:
                                fallbackId = availableIds[0]
                                print(f"        → Using ProfileID {fallbackId} instead")
                                dfProfile = df[df['ProfileID'] == fallbackId]
                        else:
                            print(f"        ✅ Loaded ProfileID {profileId}: {len(dfProfile)} points")

                        # Extract relevant columns in the expected order
                        # Expected: [Depth, Normal_Stress, Shear_Stress, SCU, ...]
                        columnsToExtract = ['Depth_m', 'Normal_Stress_bar', 'Shear_Stress_bar', 'SCU']

                        # Check which columns exist
                        availableColumns = [col for col in columnsToExtract if col in dfProfile.columns]

                        if len(availableColumns) > 0:
                            result['geos'] = dfProfile[availableColumns].values
                            print(f"        Extracted columns: {availableColumns}")
                        else:
                            print(f"        ⚠️  No expected columns found in DataFrame")
                            print(f"        Available columns: {list(dfProfile.columns)}")
                    else:
                        # No ProfileID column, use all data
                        print(f"        ℹ️  No ProfileID column, using all data")
                        columnsToExtract = ['Depth_m', 'Normal_Stress_bar', 'Shear_Stress_bar', 'SCU']
                        availableColumns = [col for col in columnsToExtract if col in df.columns]

                        if len(availableColumns) > 0:
                            result['geos'] = df[availableColumns].values
                            print(f"        ✅ Loaded {len(result['geos'])} points")

                except ValueError:
                    # Sheet not found, try to find closest time
                    print(f"        ⚠️  Sheet '{sheetName}' not found, searching for closest time...")

                    # Read all sheet names
                    xlFile = pd.ExcelFile(geosXLSVPath)
                    sheetNames = xlFile.sheetNames

                    # Extract times from sheet names
                    sheetTimes = []
                    for sname in sheetNames:
                        if sname.startswith('t_') and sname.endswith('s'):
                            try:
                                # Extract time: t_1.00e+02s -> 100.0
                                timeStr = sname[2:-1]  # Remove 't_' and 's'
                                sheetTime = float(timeStr)
                                sheetTimes.append((sheetTime, sname))
                            except:
                                continue

                    if sheetTimes:
                        # Find closest time
                        sheetTimes.sort(key=lambda x: abs(x[0] - time))
                        closestTime, closestSheet = sheetTimes[0]
                        timeDiff = abs(closestTime - time)

                        print(f"        → Using closest sheet: '{closestSheet}' (Δt={timeDiff:.2e}s)")
                        df = pd.read_excel(geosXLSVPath, sheet_name=closestSheet)

                        # Filter by ProfileID
                        if 'ProfileID' in df.columns:
                            dfProfile = df[df['ProfileID'] == profileId]

                            if len(dfProfile) == 0:
                                # Fallback to first profile
                                availableIds = sorted(df['ProfileID'].unique())
                                if len(availableIds) > 0:
                                    dfProfile = df[df['ProfileID'] == availableIds[0]]
                                    print(f"        → Using ProfileID {availableIds[0]}")

                            columnsToExtract = ['Depth_m', 'Normal_Stress_bar', 'Shear_Stress_bar', 'SCU']   # TODO check
                            availableColumns = [col for col in columnsToExtract if col in dfProfile.columns]

                            if len(availableColumns) > 0:
                                result['geos'] = dfProfile[availableColumns].values
                                print(f"        ✅ Loaded {len(result['geos'])} points")
                        else:
                            # Use all data
                            columnsToExtract = ['Depth_m', 'Normal_Stress_bar', 'Shear_Stress_bar', 'SCU']
                            availableColumns = [col for col in columnsToExtract if col in df.columns]

                            if len(availableColumns) > 0:
                                result['geos'] = df[availableColumns].values
                                print(f"        ✅ Loaded {len(result['geos'])} points")
                    else:
                        print(f"        ⚠️  No valid time sheets found in Excel file")

            except ImportError:
                print(f"        ⚠️  pandas not available, cannot read Excel file")
            except Exception as e:
                print(f"        ⚠️  Error reading Excel: {e}")
                import traceback
                traceback.print_exc()

        # Fallback to CSV if Excel not found or failed
        if result['geos'] is None:
            geosCSVPath = os.path.join(scriptDir, geosFileCSV)
            if os.path.exists(geosCSVPath):
                try:
                    result['geos'] = np.loadtxt(geosCSVPath, delimiter=',', skiprows=1)
                    print(f"     ✅ GEOS data loaded from CSV: {len(result['geos'])} points")
                except Exception as e:
                    print(f"     ⚠️  Error reading CSV: {e}")

        # ===================================================================
        # LOAD ANALYTICAL DATA
        # ===================================================================

        analyticalFile = 'analyticalData.csv'
        analyticalPath = os.path.join(scriptDir, analyticalFile)

        if os.path.exists(analyticalPath):
            try:
                result['analytical'] = np.loadtxt(analyticalPath, delimiter=',', skiprows=1)
                print(f"     ✅ Analytical data loaded: {len(result['analytical'])} points")
            except Exception as e:
                print(f"     ⚠️  Error loading analytical data: {e}")

        return result

    # -------------------------------------------------------------------
    @staticmethod
    def plotDepthProfiles(self, surface, time, path, show=True, save=True,
        profileStartPoints=None,
        maxProfilePoints=1000,
        referenceProfileId=1
        ):

        """
        Plot vertical profiles along the fault showing stress and SCU vs depth
        """

        print("  📊 Creating depth profiles ")

        # Extract data
        centers = surface.cell_data['elementCenter']
        depth = centers[:, 2]
        sigmaN = surface.cell_data['sigmaNEffective']
        tau = surface.cell_data['tauEffective']
        SCU = surface.cell_data['SCU']
        SCU = np.sqrt(SCU**2)
        deltaSCU = surface.cell_data['deltaSCU']

        # Extraire les IDs de faille
        faultIds = None
        if 'FaultMask' in surface.cell_data:
            faultIds = surface.cell_data['FaultMask']
            print(f"  📋 Detected {len(np.unique(faultIds[faultIds > 0]))} distinct faults")
        elif 'attribute' in surface.cell_data:
            faultIds = surface.cell_data['attribute']
            print(f"  📋 Using 'attribute' field for fault identification")
        else:
            print(f"  ⚠️ No fault IDs found - profiles may jump between faults")

        # ===================================================================
        # LOAD REFERENCE DATA (GEOS + Analytical)
        # ===================================================================
        scriptDir = os.path.dirname(os.path.abspath(__file__))
        referenceData = Visualizer.loadReferenceData(
            time,
            scriptDir,
            profileId=referenceProfileId
        )

        geosData = referenceData['geos']
        analyticalData = referenceData['analytical']

        # ===================================================================
        # PROFILE EXTRACTION SETUP
        # ===================================================================

        # Get fault bounds
        xMin, xMax = np.min(centers[:, 0]), np.max(centers[:, 0])
        yMin, yMax = np.min(centers[:, 1]), np.max(centers[:, 1])
        zMin, zMax = np.min(depth), np.max(depth)

        # Auto-compute search radius if not provided
        xRange = xMax - xMin
        yRange = yMax - yMin
        zRange = zMax - zMin

        if self.config.PROFILE_SEARCH_RADIUS is not None:
            searchRadius = self.config.PROFILE_SEARCH_RADIUS
        else:
            searchRadius = min(xRange, yRange) * 0.15


        # Auto-generate profile points if not provided
        if profileStartPoints is None:
            print("  ⚠️  No profileStartPoints provided, auto-generating 5 profiles...")
            nProfiles = 5

            # Determine dominant fault direction
            if xRange > yRange:
                coordName = 'X'
                fixedValue = (yMin + yMax) / 2
                samplePositions = np.linspace(xMin, xMax, nProfiles)
                profileStartPoints = [(x, fixedValue) for x in samplePositions]
            else:
                coordName = 'Y'
                fixedValue = (xMin + xMax) / 2
                samplePositions = np.linspace(yMin, yMax, nProfiles)
                profileStartPoints = [(fixedValue, y) for y in samplePositions]

            print(f"     Auto-generated {nProfiles} profiles along {coordName} direction")

        nProfiles = len(profileStartPoints)

        # ===================================================================
        # CREATE FIGURE
        # ===================================================================

        fig, axes = plt.subplots(1, 4, figsize=(24, 12))
        colors = plt.cm.RdYlGn(np.linspace(0, 1, nProfiles))

        print(f"  📍 Processing {nProfiles} profiles:")
        print(f"     Depth range: [{zMin:.1f}, {zMax:.1f}]m")

        successfulProfiles = 0

        # ===================================================================
        # EXTRACT AND PLOT PROFILES
        # ===================================================================

        for i, (xPos, yPos, zPos) in enumerate(profileStartPoints):
            print(f"     → Profile {i+1}: starting at ({xPos:.1f}, {yPos:.1f}, {zPos:.1f})")

            # depthsSigma, profileSigmaN, PathXSigma, PathYSigma = ProfileExtractor.extractVerticalProfileTopologyBased(
            #         surface, 'sigmaNEffective', xPos, yPos, zPos, verbose=True)

            # depthsTau, profileTau, _, _ = ProfileExtractor.extractVerticalProfileTopologyBased(
            #         surface, 'tauEffective', xPos, yPos, zPos, verbose=False)

            # depthsSCU, profileSCU, _, _ = ProfileExtractor.extractVerticalProfileTopologyBased(
            #         surface, 'SCU', xPos, yPos, zPos, verbose=False)

            # depthsDeltaSCU, profileDeltaSCU, _, _ = ProfileExtractor.extractVerticalProfileTopologyBased(
            #         surface, 'deltaSCU', xPos, yPos, zPos, verbose=False)

            depthsSigma, profileSigmaN, PathXSigma, PathYSigma = ProfileExtractor.extractAdaptiveProfile(
                centers, sigmaN, xPos, yPos, searchRadius)

            depthsTau, profileTau, _, _ = ProfileExtractor.extractAdaptiveProfile(
                centers, tau, xPos, yPos, searchRadius)

            depthsSCU, profileSCU, _, _ = ProfileExtractor.extractAdaptiveProfile(
                centers, SCU, xPos, yPos, searchRadius)

            depthsDeltaSCU, profileDeltaSCU, _, _ = ProfileExtractor.extractAdaptiveProfile(
                centers, SCU, xPos, yPos, searchRadius)

            # Calculate path length
            if len(PathXSigma) > 1:
                pathLength = np.sum(np.sqrt(
                    np.diff(PathXSigma)**2 +
                    np.diff(PathYSigma)**2 +
                    np.diff(depthsSigma)**2
                ))
                print(f"        Path length: {pathLength:.1f}m (horizontal displacement: {np.abs(PathXSigma[-1] - PathXSigma[0]):.1f}m)")

                if self.config.SHOW_PROFILE_EXTRACTOR:
                    ProfileExtractor.plotProfilePath3D(
                        surface=surface,
                        pathX=PathXSigma,
                        pathY=PathYSigma,
                        pathZ=depthsSigma,
                        profileValues=profileSigmaN,
                        scalarName='SCU',
                        savePath=path,
                        show=show
                    )

            # Check if we have enough points
            minPoints = 3
            nPoints = len(depthsSigma)

            if nPoints >= minPoints:
                label = f'Profile {i+1} → ({xPos:.0f}, {yPos:.0f})'

                # Plot 1: Normal stress vs depth
                axes[0].plot(profileSigmaN, depthsSigma,
                            color=colors[i], label=label, linewidth=2.5, alpha=0.8,
                            marker='o', markersize=3, markevery=2)

                # Plot 2: Shear stress vs depth
                axes[1].plot(profileTau, depthsTau,
                            color=colors[i], label=label, linewidth=2.5, alpha=0.8,
                            marker='o', markersize=3, markevery=2)

                # Plot 3: SCU vs depth
                axes[2].plot(profileSCU, depthsSCU,
                            color=colors[i], label=label, linewidth=2.5, alpha=0.8,
                            marker='o', markersize=3, markevery=2)

                # Plot 4: Detla SCU vs depth
                axes[3].plot(profileDeltaSCU, depthsDeltaSCU,
                            color=colors[i], label=label, linewidth=2.5, alpha=0.8,
                            marker='o', markersize=3, markevery=2)

                successfulProfiles += 1
                print(f"        ✅ {nPoints} points found")
            else:
                print(f"        ⚠️  Insufficient points ({nPoints}), skipping")

        if successfulProfiles == 0:
            print("  ❌ No valid profiles found!")
            plt.close()
            return

        # ===================================================================
        # ADD REFERENCE DATA (GEOS + Analytical) - Only once
        # ===================================================================

        if geosData is not None:
            # Colonnes: [Depth_m, Normal_Stress_bar, Shear_Stress_bar, SCU]
            # Index:    [0,       1,                 2,                 3]

            axes[0].plot(geosData[:, 1] *10, geosData[:, 0], 'o',
                        color='blue', markersize=6, label='GEOS Contact Solver',
                        alpha=0.7, mec='k', mew=1, fillstyle='none')

            axes[1].plot(geosData[:, 2] *10, geosData[:, 0], 'o',
                        color='blue', markersize=6, label='GEOS Contact Solver',
                        alpha=0.7, mec='k', mew=1, fillstyle='none')

            if geosData.shape[1] > 3:  # SCU column exists
                axes[2].plot(geosData[:, 3], geosData[:, 0], 'o',
                            color='blue', markersize=6, label='GEOS Contact Solver',
                            alpha=0.7, mec='k', mew=1, fillstyle='none')

        if analyticalData is not None:
            # Format analytique (peut varier)
            axes[0].plot(analyticalData[:, 1] * 10, analyticalData[:, 0], '--',
                        color='darkorange', linewidth=2, label='Analytical', alpha=0.8)
            if analyticalData.shape[1] > 2:
                axes[1].plot(analyticalData[:, 2] * 10, analyticalData[:, 0], '--',
                            color='darkorange', linewidth=2, label='Analytical', alpha=0.8)

        # ===================================================================
        # CONFIGURE PLOTS
        # ===================================================================

        fsize = 14

        # Plot 1: Normal Stress
        axes[0].set_xlabel('Normal Stress σₙ [bar]', fontsize=fsize, weight="bold")
        axes[0].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[0].set_title('Normal Stress Profile', fontsize=fsize+2, weight="bold")
        axes[0].grid(True, alpha=0.3, linestyle='--')
        axes[0].legend(loc='upper left', fontsize=fsize-2)
        axes[0].tick_params(labelsize=fsize-2)

        # Plot 2: Shear Stress
        axes[1].set_xlabel('Shear Stress τ [bar]', fontsize=fsize, weight="bold")
        axes[1].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[1].set_title('Shear Stress Profile', fontsize=fsize+2, weight="bold")
        axes[1].grid(True, alpha=0.3, linestyle='--')
        axes[1].legend(loc='upper left', fontsize=fsize-2)
        axes[1].tick_params(labelsize=fsize-2)

        # Plot 3: SCU
        axes[2].set_xlabel('SCU [-]', fontsize=fsize, weight="bold")
        axes[2].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[2].set_title('Shear Capacity Utilization', fontsize=fsize+2, weight="bold")
        axes[2].axvline(x=0.8, color='forestgreen', linestyle='--', linewidth=2, label='Critical (0.8)')
        axes[2].axvline(x=1.0, color='red', linestyle='--', linewidth=2, label='Failure (1.0)')
        axes[2].grid(True, alpha=0.3, linestyle='--')
        axes[2].legend(loc='upper right', fontsize=fsize-2)
        axes[2].tick_params(labelsize=fsize-2)
        axes[2].set_xlim(left=0)

        # Plot 4: Delta SCU
        axes[3].set_xlabel('Δ SCU [-]', fontsize=fsize, weight="bold")
        axes[3].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[3].set_title('Delta SCU', fontsize=fsize+2, weight="bold")
        axes[3].grid(True, alpha=0.3, linestyle='--')
        axes[3].legend(loc='upper right', fontsize=fsize-2)
        axes[3].tick_params(labelsize=fsize-2)
        axes[3].set_xlim(left=0, right=2)

        # Change verticale scale
        if self.config.MAX_DEPTH_PROFILES != None :
            for i in range(len(axes)):
                axes[i].set_ylim(bottom=self.config.MAX_DEPTH_PROFILES)

        if self.config.MIN_DEPTH_PROFILES != None :
            for i in range(len(axes)):
                axes[i].set_ylim(top=self.config.MIN_DEPTH_PROFILES)

        # Overall title
        years = time / (365.25 * 24 * 3600)
        fig.suptitle(f'Fault Depth Profiles - t={years:.1f} years',
                    fontsize=fsize+2, fontweight='bold', y=0.98)

        plt.tight_layout(rect=[0, 0, 1, 0.96])

        # Save
        if save:
            filename = f'depth_profiles_{years:.0f}y.png'
            plt.savefig(path / filename, dpi=300, bbox_inches='tight')
            print(f"  💾 Depth profiles saved: {filename}")

        # Show
        if show:
            plt.show()
        else:
            plt.close()

    # -------------------------------------------------------------------
    def plotVolumeStressProfiles(self, volumeMesh, faultSurface, time, path,
                                    show=True, save=True,
                                    profileStartPoints=None,
                                    maxProfilePoints=1000):
        """
        Plot stress profiles in volume cells adjacent to the fault
        Extracts profiles through contributing cells on BOTH sides of the fault
        Shows plus side and minus side on the same plots for comparison

        NOTE: Cette fonction utilise extractAdaptiveProfile pour les VOLUMES
        car volumeMesh n'est PAS un maillage surfacique.
        La méthode topologique (extractVerticalProfileTopologyBased)
        est réservée aux maillages SURFACIQUES (faultSurface).
        """

        print("  📊 Creating volume stress profiles (both sides)")

        # ===================================================================
        # CHECK IF REQUIRED DATA EXISTS
        # ===================================================================

        requiredFields = ['sigma1', 'sigma2', 'sigma3', 'side', 'elementCenter']

        for field in requiredFields:
            if field not in volumeMesh.cell_data:
                print(f"  ⚠️  Missing required field: {field}")
                return

        # Check for pressure
        if 'pressure_bar' in volumeMesh.cell_data:
            pressureField = 'pressure_bar'
            pressure = volumeMesh.cell_data[pressureField]
        elif 'pressure' in volumeMesh.cell_data:
            pressureField = 'pressure'
            pressure = volumeMesh.cell_data[pressureField] / 1e5
            print("  ℹ️  Converting pressure from Pa to bar")
        else:
            print("  ⚠️  No pressure field found")
            pressure = None

        # Extract volume data
        centers = volumeMesh.cell_data['elementCenter']
        sigma1 = volumeMesh.cell_data['sigma1']
        sigma2 = volumeMesh.cell_data['sigma2']
        sigma3 = volumeMesh.cell_data['sigma3']
        sideData = volumeMesh.cell_data['side']

        # ===================================================================
        # FILTER CELLS BY SIDE (BOTH PLUS AND MINUS)
        # ===================================================================

        # Plus side (side = 1 or 3)
        maskPlus = (sideData == 1) | (sideData == 3)
        centersPlus = centers[maskPlus]
        sigma1Plus = sigma1[maskPlus]
        sigma2Plus = sigma2[maskPlus]
        sigma3Plus = sigma3[maskPlus]
        if pressure is not None:
            pressurePlus = pressure[maskPlus]

        # Créer subset de cellData pour le côté plus
        cellDataPlus = {}
        for key in volumeMesh.cell_data.keys():
            cellDataPlus[key] = volumeMesh.cell_data[key][maskPlus]

        # Minus side (side = 2 or 3)
        maskMinus = (sideData == 2) | (sideData == 3)
        centersMinus = centers[maskMinus]
        sigma1Minus = sigma1[maskMinus]
        sigma2Minus = sigma2[maskMinus]
        sigma3Minus = sigma3[maskMinus]
        if pressure is not None:
            pressureMinus = pressure[maskMinus]

        # Créer subset de cellData pour le côté minus
        cellDataMinus = {}
        for key in volumeMesh.cell_data.keys():
            cellDataMinus[key] = volumeMesh.cell_data[key][maskMinus]

        print(f"  📍 Plus side: {len(centersPlus):,} cells")
        print(f"  📍 Minus side: {len(centersMinus):,} cells")

        if len(centersPlus) == 0 and len(centersMinus) == 0:
            print("  ⚠️  No contributing cells found!")
            return

        # ===================================================================
        # GET FAULT BOUNDS
        # ===================================================================

        faultCenters = faultSurface.cell_data['elementCenter']

        xMin, xMax = np.min(faultCenters[:, 0]), np.max(faultCenters[:, 0])
        yMin, yMax = np.min(faultCenters[:, 1]), np.max(faultCenters[:, 1])
        zMin, zMax = np.min(faultCenters[:, 2]), np.max(faultCenters[:, 2])

        xRange = xMax - xMin
        yRange = yMax - yMin
        zRange = zMax - zMin

        # Search radius (pour extractAdaptiveProfile sur volumes)
        if self.config.PROFILE_SEARCH_RADIUS is not None:
            searchRadius = self.config.PROFILE_SEARCH_RADIUS
        else:
            searchRadius = min(xRange, yRange) * 0.2

        # ===================================================================
        # AUTO-GENERATE PROFILE POINTS IF NOT PROVIDED
        # ===================================================================

        if profileStartPoints is None:
            print("  ⚠️  No profileStartPoints provided, auto-generating...")
            nProfiles = 3

            if xRange > yRange:
                coordName = 'X'
                fixedValue = (yMin + yMax) / 2
                samplePositions = np.linspace(xMin, xMax, nProfiles)
                profileStartPoints = [(x, fixedValue, zMax) for x in samplePositions]
            else:
                coordName = 'Y'
                fixedValue = (xMin + xMax) / 2
                samplePositions = np.linspace(yMin, yMax, nProfiles)
                profileStartPoints = [(fixedValue, y, zMax) for y in samplePositions]

            print(f"     Auto-generated {nProfiles} profiles along {coordName}")

        nProfiles = len(profileStartPoints)

        # ===================================================================
        # CREATE FIGURE WITH 5 SUBPLOTS
        # ===================================================================

        fig, axes = plt.subplots(1, 5, figsize=(22, 10))

        # Colors: different for plus and minus sides
        colorsPlus = plt.cm.Reds(np.linspace(0.4, 0.9, nProfiles))
        colorsMinus = plt.cm.Blues(np.linspace(0.4, 0.9, nProfiles))

        print(f"  📍 Processing {nProfiles} volume profiles:")
        print(f"     Depth range: [{zMin:.1f}, {zMax:.1f}]m")

        successfulProfiles = 0

        # ===================================================================
        # EXTRACT AND PLOT PROFILES FOR BOTH SIDES
        # ===================================================================

        for i, (xPos, yPos, zPos) in enumerate(profileStartPoints):
            print(f"\n     → Profile {i+1}: starting at ({xPos:.1f}, {yPos:.1f}, {zPos:.1f})")

            # ================================================================
            # PLUS SIDE
            # ================================================================
            if len(centersPlus) > 0:
                print(f"        Processing PLUS side...")

                # Pour VOLUMES, utiliser extractAdaptiveProfile avec cellData
                depthsSigma1Plus, profileSigma1Plus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersPlus, sigma1Plus, xPos, yPos, zPos,
                    searchRadius, verbose=True, cellData=cellDataPlus)

                depthsSigma2Plus, profileSigma2Plus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersPlus, sigma2Plus, xPos, yPos, zPos,
                    searchRadius, verbose=False, cellData=cellDataPlus)

                depthsSigma3Plus, profileSigma3Plus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersPlus, sigma3Plus, xPos, yPos, zPos,
                    searchRadius, verbose=False, cellData=cellDataPlus)

                if pressure is not None:
                    depthsPressurePlus, profilePressurePlus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                        centersPlus, pressurePlus, xPos, yPos, zPos,
                        searchRadius, verbose=False, cellData=cellDataPlus)

                if len(depthsSigma1Plus) >= 3:
                    labelPlus = f'Plus side'

                    # Plot Pressure
                    if pressure is not None:
                        axes[0].plot(profilePressurePlus, depthsPressurePlus,
                                    color=colorsPlus[i], label=labelPlus if i == 0 else '',
                                    linewidth=2.5, alpha=0.8, marker='o', markersize=3, markevery=2)

                    # Plot σ1
                    axes[1].plot(profileSigma1Plus, depthsSigma1Plus,
                                color=colorsPlus[i], label=labelPlus if i == 0 else '',
                                linewidth=2.5, alpha=0.8, marker='o', markersize=3, markevery=2)

                    # Plot σ2
                    axes[2].plot(profileSigma2Plus, depthsSigma2Plus,
                                color=colorsPlus[i], label=labelPlus if i == 0 else '',
                                linewidth=2.5, alpha=0.8, marker='o', markersize=3, markevery=2)

                    # Plot σ3
                    axes[3].plot(profileSigma3Plus, depthsSigma3Plus,
                                color=colorsPlus[i], label=labelPlus if i == 0 else '',
                                linewidth=2.5, alpha=0.8, marker='o', markersize=3, markevery=2)

                    # Plot All stresses
                    axes[4].plot(profileSigma1Plus, depthsSigma1Plus,
                                color=colorsPlus[i], linewidth=2.5, alpha=0.8,
                                linestyle='-', marker="o", markersize=2, markevery=2)
                    axes[4].plot(profileSigma2Plus, depthsSigma2Plus,
                                color=colorsPlus[i], linewidth=2.0, alpha=0.6,
                                linestyle='-', marker="s", markersize=2, markevery=2)
                    axes[4].plot(profileSigma3Plus, depthsSigma3Plus,
                                color=colorsPlus[i], linewidth=2.5, alpha=0.8,
                                linestyle='-', marker="v", markersize=2, markevery=2)

                    print(f"        ✅ PLUS: {len(depthsSigma1Plus)} points")
                    successfulProfiles += 1

            # ================================================================
            # MINUS SIDE
            # ================================================================
            if len(centersMinus) > 0:
                print(f"        Processing MINUS side...")

                # Pour VOLUMES, utiliser extractAdaptiveProfile avec cellData
                depthsSigma1Minus, profileSigma1Minus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersMinus, sigma1Minus, xPos, yPos, zPos,
                    searchRadius, verbose=True, cellData=cellDataMinus)

                depthsSigma2Minus, profileSigma2Minus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersMinus, sigma2Minus, xPos, yPos, zPos,
                    searchRadius, verbose=False, cellData=cellDataMinus)

                depthsSigma3Minus, profileSigma3Minus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersMinus, sigma3Minus, xPos, yPos, zPos,
                    searchRadius, verbose=False, cellData=cellDataMinus)

                if pressure is not None:
                    depthsPressureMinus, profilePressureMinus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                        centersMinus, pressureMinus, xPos, yPos, zPos,
                        searchRadius, verbose=False, cellData=cellDataMinus)

                if len(depthsSigma1Minus) >= 3:
                    labelMinus = f'Minus side'

                    # Plot Pressure
                    if pressure is not None:
                        axes[0].plot(profilePressureMinus, depthsPressureMinus,
                                    color=colorsMinus[i], label=labelMinus if i == 0 else '',
                                    linewidth=2.5, alpha=0.8, marker='s', markersize=3, markevery=2)

                    # Plot σ1
                    axes[1].plot(profileSigma1Minus, depthsSigma1Minus,
                                color=colorsMinus[i], label=labelMinus if i == 0 else '',
                                linewidth=2.5, alpha=0.8, marker='s', markersize=3, markevery=2)

                    # Plot σ2
                    axes[2].plot(profileSigma2Minus, depthsSigma2Minus,
                                color=colorsMinus[i], label=labelMinus if i == 0 else '',
                                linewidth=2.5, alpha=0.8, marker='s', markersize=3, markevery=2)

                    # Plot σ3
                    axes[3].plot(profileSigma3Minus, depthsSigma3Minus,
                                color=colorsMinus[i], label=labelMinus if i == 0 else '',
                                linewidth=2.5, alpha=0.8, marker='s', markersize=3, markevery=2)

                    # Plot All stresses
                    axes[4].plot(profileSigma1Minus, depthsSigma1Minus,
                                color=colorsMinus[i], linewidth=2.5, alpha=0.8,
                                linestyle='-', marker="o", markersize=2, markevery=2)
                    axes[4].plot(profileSigma2Minus, depthsSigma2Minus,
                                color=colorsMinus[i], linewidth=2.0, alpha=0.6,
                                linestyle='-', marker="s", markersize=2, markevery=2)
                    axes[4].plot(profileSigma3Minus, depthsSigma3Minus,
                                color=colorsMinus[i], linewidth=2.5, alpha=0.8,
                                linestyle='-', marker='v', markersize=2, markevery=2)

                    print(f"        ✅ MINUS: {len(depthsSigma1Minus)} points")
                    successfulProfiles += 1

        if successfulProfiles == 0:
            print("  ❌ No valid profiles found!")
            plt.close()
            return

        # ===================================================================
        # CONFIGURE PLOTS
        # ===================================================================

        fsize = 14

        # Plot 0: Pressure
        axes[0].set_xlabel('Pressure [bar]', fontsize=fsize, weight="bold")
        axes[0].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[0].grid(True, alpha=0.3, linestyle='--')
        axes[0].legend(loc='best', fontsize=fsize-2)
        axes[0].tick_params(labelsize=fsize-2)

        if pressure is None:
            axes[0].text(0.5, 0.5, 'No pressure data available',
                        ha='center', va='center', transform=axes[0].transAxes,
                        fontsize=fsize, style='italic', color='gray')

        # Plot 1: σ1 (Maximum principal stress)
        axes[1].set_xlabel('σ₁ (Max Principal) [bar]', fontsize=fsize, weight="bold")
        axes[1].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[1].grid(True, alpha=0.3, linestyle='--')
        axes[1].legend(loc='best', fontsize=fsize-2)
        axes[1].tick_params(labelsize=fsize-2)

        # Plot 2: σ2 (Intermediate principal stress)
        axes[2].set_xlabel('σ₂ (Inter Principal) [bar]', fontsize=fsize, weight="bold")
        axes[2].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[2].grid(True, alpha=0.3, linestyle='--')
        axes[2].legend(loc='best', fontsize=fsize-2)
        axes[2].tick_params(labelsize=fsize-2)

        # Plot 3: σ3 (Min principal stress)
        axes[3].set_xlabel('σ₃ (Min Principal) [bar]', fontsize=fsize, weight="bold")
        axes[3].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[3].grid(True, alpha=0.3, linestyle='--')
        axes[3].legend(loc='best', fontsize=fsize-2)
        axes[3].tick_params(labelsize=fsize-2)

        # Plot 4: All stresses together
        axes[4].set_xlabel('Principal Stresses [bar]', fontsize=fsize, weight="bold")
        axes[4].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[4].grid(True, alpha=0.3, linestyle='--')
        axes[4].tick_params(labelsize=fsize-2)

        # Add legend for line styles
        customLines = [
            Line2D([0], [0], color='red', linewidth=2.5, marker=None, label='Plus side', alpha=0.5),
            Line2D([0], [0], color='blue', linewidth=2.5, marker=None, label='Minus side', alpha=0.5),
            Line2D([0], [0], color='gray', linewidth=2.5, linestyle='-', marker='o', label='σ₁ (max)'),
            Line2D([0], [0], color='gray', linewidth=2.0, linestyle='-', marker='s', label='σ₂ (inter)'),
            Line2D([0], [0], color='gray', linewidth=2.5, linestyle='-', marker='v', label='σ₃ (min)')
        ]
        axes[4].legend(handles=customLines, loc='best', fontsize=fsize-3, ncol=1)

        # Change verticale scale
        if self.config.MAX_DEPTH_PROFILES != None :
            for i in range(len(axes)):
                axes[i].set_ylim(bottom=self.config.MAX_DEPTH_PROFILES)

        if self.config.MIN_DEPTH_PROFILES != None :
            for i in range(len(axes)):
                axes[i].set_ylim(top=self.config.MIN_DEPTH_PROFILES)

        # Overall title
        years = time / (365.25 * 24 * 3600)
        fig.suptitle(f'Volume Stress Profiles - Both Sides Comparison - t={years:.1f} years',
                    fontsize=fsize+2, fontweight='bold', y=0.98)

        plt.tight_layout(rect=[0, 0, 1, 0.96])

        # Save
        if save:
            filename = f'volume_stress_profiles_both_sides_{years:.0f}y.png'
            plt.savefig(path / filename, dpi=300, bbox_inches='tight')
            print(f"  💾 Volume profiles saved: {filename}")

        # Show
        if show:
            plt.show()
        else:
            plt.close()

    # -------------------------------------------------------------------
    def plotAnalyticalVsNumericalComparison(self, volumeMesh, faultSurface, time, path,
                                               show=True, save=True,
                                               profileStartPoints=None,
                                               referenceProfileId=1):
        """
        Plot comparison between analytical fault stresses (Anderson formulas)
        and numerical tensor projection - COMBINED PLOTS ONLY

        Parameters
        ----------
        volumeMesh : pyvista.UnstructuredGrid
            Volume mesh with principal stresses AND analytical stresses
        faultSurface : pyvista.PolyData
            Fault surface mesh with projected stresses
        time : float
            Simulation time
        path : Path
            Output directory
        show : bool
            Show plot interactively
        save : bool
            Save plot to file
        profileStartPoints : list of tuples
            Starting points (x, y, z) for profiles
        referenceProfileId : int
            Which profile ID to load from Excel reference data
        """

        print("\n  📊 Creating Analytical vs Numerical Comparison")

        # ===================================================================
        # CHECK IF ANALYTICAL DATA EXISTS
        # ===================================================================

        requiredAnalytical = ['sigmaNAnalytical', 'tauAnalytical', 'side', 'elementCenter']

        for field in requiredAnalytical:
            if field not in volumeMesh.cell_data:
                print(f"  ⚠️  Missing analytical field: {field}")
                print(f"      Analytical stresses not computed in volume mesh")
                return

        # Check numerical data on fault surface
        if 'sigmaNEffective' not in faultSurface.cell_data:
            print(f"  ⚠️  Missing numerical stress data on fault surface")
            return

        # ===================================================================
        # LOAD REFERENCE DATA (GEOS Contact Solver)
        # ===================================================================

        print("  📂 Loading GEOS Contact Solver reference data...")
        scriptDir = os.path.dirname(os.path.abspath(__file__))
        referenceData = Visualizer.loadReferenceData(
            time,
            scriptDir,
            profileId=referenceProfileId
        )

        geosContactData = referenceData.get('geos', None)

        if geosContactData is not None:
            print(f"     ✅ Loaded {len(geosContactData)} reference points from GEOS Contact Solver")
        else:
            print(f"     ⚠️  No GEOS Contact Solver reference data found")

        # Extraire les IDs de faille
        faultIdsVolume = None
        faultIdsSurface = None

        if 'faultId' in volumeMesh.cell_data:
            faultIdsVolume = volumeMesh.cell_data['faultId']

        if 'FaultMask' in faultSurface.cell_data:
            faultIdsSurface = faultSurface.cell_data['FaultMask']
        elif 'attribute' in faultSurface.cell_data:
            faultIdsSurface = faultSurface.cell_data['attribute']

        # ===================================================================
        # EXTRACT DATA
        # ===================================================================

        # Volume analytical data
        centersVolume = volumeMesh.cell_data['elementCenter']
        sideData = volumeMesh.cell_data['side']
        sigmaNAnalytical = volumeMesh.cell_data['sigmaNAnalytical']
        tauAnalytical = volumeMesh.cell_data['tauAnalytical']

        # Optional: SCU if available
        hasSCUAnalytical = 'SCUAnalytical' in volumeMesh.cell_data
        if hasSCUAnalytical:
            SCUAnalytical = volumeMesh.cell_data['SCUAnalytical']

        # Fault numerical data
        centersFault = faultSurface.cell_data['elementCenter']
        sigmaNNumerical = faultSurface.cell_data['sigmaNEffective']
        tauNumerical = faultSurface.cell_data['tauEffective']

        # Optional: SCU numerical
        hasSCUNumerical = 'SCU' in faultSurface.cell_data
        if hasSCUNumerical:
            SCUNumerical = faultSurface.cell_data['SCU']

        # Filter volume by side
        maskPlus = (sideData == 1) | (sideData == 3)
        maskMinus = (sideData == 2) | (sideData == 3)

        centersPlus = centersVolume[maskPlus]
        sigmaNAnalyticalPlus = sigmaNAnalytical[maskPlus]
        tauAnalyticalPlus = tauAnalytical[maskPlus]
        if hasSCUAnalytical:
            SCUAnalyticalPlus = SCUAnalytical[maskPlus]

        centersMinus = centersVolume[maskMinus]
        sigmaNAnalyticalMinus = sigmaNAnalytical[maskMinus]
        tauAnalyticalMinus = tauAnalytical[maskMinus]
        if hasSCUAnalytical:
            SCUAnalyticalMinus = SCUAnalytical[maskMinus]

        print(f"  📍 Plus side: {len(centersPlus):,} cells with analytical data")
        print(f"  📍 Minus side: {len(centersMinus):,} cells with analytical data")
        print(f"  📍 Fault surface: {len(centersFault):,} cells with numerical data")

        # ===================================================================
        # GET FAULT BOUNDS AND PROFILE SETUP
        # ===================================================================

        xMin, xMax = np.min(centersFault[:, 0]), np.max(centersFault[:, 0])
        yMin, yMax = np.min(centersFault[:, 1]), np.max(centersFault[:, 1])
        zMin, zMax = np.min(centersFault[:, 2]), np.max(centersFault[:, 2])

        xRange = xMax - xMin
        yRange = yMax - yMin

        # Search radius
        if self.config.PROFILE_SEARCH_RADIUS is not None:
            searchRadius = self.config.PROFILE_SEARCH_RADIUS
        else:
            searchRadius = min(xRange, yRange) * 0.2

        # Auto-generate profile points if not provided
        if profileStartPoints is None:
            print("  ⚠️  No profileStartPoints provided, auto-generating...")
            nProfiles = 3

            if xRange > yRange:
                coordName = 'X'
                fixedValue = (yMin + yMax) / 2
                samplePositions = np.linspace(xMin, xMax, nProfiles)
                profileStartPoints = [(x, fixedValue, zMax) for x in samplePositions]
            else:
                coordName = 'Y'
                fixedValue = (xMin + xMax) / 2
                samplePositions = np.linspace(yMin, yMax, nProfiles)
                profileStartPoints = [(fixedValue, y, zMax) for y in samplePositions]

            print(f"     Auto-generated {nProfiles} profiles along {coordName}")

        nProfiles = len(profileStartPoints)

        # ===================================================================
        # CREATE FIGURE: COMBINED PLOTS ONLY
        # 3 columns (σ_n, τ, SCU) x 1 row
        # ===================================================================

        fig, axes = plt.subplots(1, 3, figsize=(18, 10))

        print(f"  📍 Processing {nProfiles} profiles for comparison:")

        successfulProfiles = 0

        # ===================================================================
        # EXTRACT AND PLOT PROFILES
        # ===================================================================

        for i, (xPos, yPos, zPos) in enumerate(profileStartPoints):
            print(f"\n     → Profile {i+1}: starting at ({xPos:.1f}, {yPos:.1f}, {zPos:.1f})")

            # ================================================================
            # PLUS SIDE - ANALYTICAL
            # ================================================================
            if len(centersPlus) > 0:
                depthsSnAnaPlus, profileSnAnaPlus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersPlus, sigmaNAnalyticalPlus, xPos, yPos, zPos,
                    searchRadius, verbose=False)

                depthsTauAnaPlus, profileTauAnaPlus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersPlus, tauAnalyticalPlus, xPos, yPos, zPos,
                    searchRadius, verbose=False)

                if hasSCUAnalytical:
                    depthsSCUAnaPlus, profileSCUAnaPlus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                        centersPlus, SCUAnalyticalPlus, xPos, yPos, zPos,
                        searchRadius, verbose=False, )

                if len(depthsSnAnaPlus) >= 3:
                    # Plot σ_n
                    axes[0].plot(profileSnAnaPlus, depthsSnAnaPlus,
                               color='red', linestyle='-', linewidth=2,
                               alpha=0.3, label='Analytical Side +' if i == 0 else '', marker=None)

                    # Plot τ
                    axes[1].plot(profileTauAnaPlus, depthsTauAnaPlus,
                               color='red', linestyle='-', linewidth=2,
                               alpha=0.3, label='Analytical Side +' if i == 0 else '', marker=None)

                    # Plot SCU if available
                    if hasSCUAnalytical and len(depthsSCUAnaPlus) >= 3:
                        axes[2].plot(profileSCUAnaPlus, depthsSCUAnaPlus,
                                   color='red', linestyle='-', linewidth=2,
                                   alpha=0.3, label='Analytical Side +' if i == 0 else '', marker=None)

            # ================================================================
            # MINUS SIDE - ANALYTICAL
            # ================================================================
            if len(centersMinus) > 0:
                depthsSigmaNAnaMinus, profileSigmaNAnaMinus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersMinus, sigmaNAnalyticalMinus, xPos, yPos, zPos,
                    searchRadius, verbose=False)

                depthsTauAnaMinus, profileTauAnaMinus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersMinus, tauAnalyticalMinus, xPos, yPos, zPos,
                    searchRadius, verbose=False)

                if hasSCUAnalytical:
                    depthsSCUAnaMinus, profileSCUAnaMinus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                        centersMinus, SCUAnalyticalMinus, xPos, yPos, zPos,
                        searchRadius, verbose=False)

                if len(depthsSigmaNAnaMinus) >= 3:
                    # Plot σ_n
                    axes[0].plot(profileSigmaNAnaMinus, depthsSigmaNAnaMinus,
                               color='blue', linestyle='-', linewidth=2,
                               alpha=0.3, label='Analytical Side -' if i == 0 else '', marker=None)

                    # Plot τ
                    axes[1].plot(profileTauAnaMinus, depthsTauAnaMinus,
                               color='blue', linestyle='-', linewidth=2,
                               alpha=0.3, label='Analytical Side -' if i == 0 else '', marker=None)

                    # Plot SCU if available
                    if hasSCUAnalytical and len(depthsSCUAnaMinus) >= 3:
                        axes[2].plot(profileSCUAnaMinus, depthsSCUAnaMinus,
                                   color='blue', linestyle='-', linewidth=2,
                                   alpha=0.3, label='Analytical Side -' if i == 0 else '', marker=None)

            # ================================================================
            # AVERAGES - ANALYTICAL (only for first profile to avoid clutter)
            # ================================================================
            if i == 0 and len(depthsSigmaNAnaMinus) >= 3 and len(depthsSnAnaPlus) >= 3:
                # Arithmetic average
                avgSigmaNArith = (profileSigmaNAnaMinus + profileSnAnaPlus) / 2
                avgTauArith = (profileTauAnaMinus + profileTauAnaPlus) / 2

                axes[0].plot(avgSigmaNArith, depthsSigmaNAnaMinus,
                           color='darkorange', linestyle='-', linewidth=2,
                           alpha=0.6, label='Arithmetic average')

                axes[1].plot(avgTauArith, depthsSigmaNAnaMinus,
                           color='darkorange', linestyle='-', linewidth=2,
                           alpha=0.6, label='Arithmetic average')

                # Geometric average
                avgTauGeom = np.sqrt(profileTauAnaMinus * profileTauAnaPlus)

                axes[1].plot(avgTauGeom, depthsSigmaNAnaMinus,
                           color='purple', linestyle='-', linewidth=2,
                           alpha=0.6, label='Geometric average')

                # Harmonic average
                AvgSigmaNHarm = 2 / (1/profileSigmaNAnaMinus + 1/profileSnAnaPlus)
                AvgTauHarm = 2 / (1/profileTauAnaMinus + 1/profileTauAnaPlus)

                axes[0].plot(AvgSigmaNHarm, depthsSigmaNAnaMinus,
                           color='green', linestyle='-', linewidth=2,
                           alpha=0.6, label='Harmonic average')

                axes[1].plot(AvgTauHarm, depthsSigmaNAnaMinus,
                           color='green', linestyle='-', linewidth=2,
                           alpha=0.6, label='Harmonic average')

            # ================================================================
            # NUMERICAL DATA FROM FAULT SURFACE (Continuum)
            # ================================================================
            print(f"        Extracting numerical data from fault surface...")

            depthsSigmaNNum, profileSigmaNNum, _, _ = ProfileExtractor.extractAdaptiveProfile(
                centersFault, sigmaNNumerical, xPos, yPos, zPos,
                searchRadius, verbose=False)

            depthsTauNum, profileTauNum, _, _ = ProfileExtractor.extractAdaptiveProfile(
                centersFault, tauNumerical, xPos, yPos, zPos,
                searchRadius, verbose=False)

            if hasSCUNumerical:
                depthsSCUNum, profileSCUNum, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersFault, SCUNumerical, xPos, yPos, zPos,
                    searchRadius, verbose=False)

            if len(depthsSigmaNNum) >= 3:
                # Plot numerical with distinct style
                axes[0].plot(profileSigmaNNum, depthsSigmaNNum,
                           color='black', linestyle='-', linewidth=2,
                           alpha=0.7, label='GEOS Continuum' if i == 0 else '',
                           marker='x', markersize=5, markevery=3)

                axes[1].plot(profileTauNum, depthsTauNum,
                           color='black', linestyle='-', linewidth=2,
                           alpha=0.7, label='GEOS Continuum' if i == 0 else '',
                           marker='x', markersize=5, markevery=3)

                if hasSCUNumerical and len(depthsSCUNum) >= 3:
                    axes[2].plot(profileSCUNum, depthsSCUNum,
                               color='black', linestyle='-', linewidth=2,
                               alpha=0.7, label='GEOS Continuum' if i == 0 else '',
                               marker='x', markersize=5, markevery=3)

            successfulProfiles += 1

        if successfulProfiles == 0:
            print("  ❌ No valid profiles found!")
            plt.close()
            return

        # ===================================================================
        # ADD GEOS CONTACT SOLVER REFERENCE DATA (only once)
        # ===================================================================

        if geosContactData is not None:
            # Format: [Depth_m, Normal_Stress_bar, Shear_Stress_bar, SCU]
            # Index:  [0,       1,                 2,                 3]

            print("  📊 Adding GEOS Contact Solver reference data...")

            # Normal stress
            axes[0].plot(geosContactData[:, 1], geosContactData[:, 0],
                        marker='o', color='black', markersize=7,
                        label='GEOS Contact Solver', linestyle='none',
                        alpha=0.8, mec='black', mew=1.5, fillstyle='none')

            # Shear stress
            axes[1].plot(geosContactData[:, 2], geosContactData[:, 0],
                        marker='o', color='black', markersize=7,
                        label='GEOS Contact Solver', linestyle='none',
                        alpha=0.8, mec='black', mew=1.5, fillstyle='none')

            # SCU (if available)
            if geosContactData.shape[1] > 3:
                axes[2].plot(geosContactData[:, 3], geosContactData[:, 0],
                            marker='o', color='black', markersize=7,
                            label='GEOS Contact Solver', linestyle='none',
                            alpha=0.8, mec='black', mew=1.5, fillstyle='none')

        # ===================================================================
        # CONFIGURE PLOTS
        # ===================================================================

        fsize = 14

        # Plot 0: Normal Stress
        axes[0].set_xlabel('Normal Stress σₙ [bar]', fontsize=fsize, weight="bold")
        axes[0].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[0].grid(True, alpha=0.3, linestyle='--')
        axes[0].legend(loc='best', fontsize=fsize-2)
        axes[0].tick_params(labelsize=fsize-1)

        # Plot 1: Shear Stress
        axes[1].set_xlabel('Shear Stress τ [bar]', fontsize=fsize, weight="bold")
        axes[1].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[1].grid(True, alpha=0.3, linestyle='--')
        axes[1].legend(loc='best', fontsize=fsize-2)
        axes[1].tick_params(labelsize=fsize-1)

        # Plot 2: SCU
        axes[2].set_xlabel('SCU [-]', fontsize=fsize, weight="bold")
        axes[2].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[2].axvline(x=0.8, color='forestgreen', linestyle='--', linewidth=2,
                       alpha=0.5, label='Critical (0.8)')
        axes[2].axvline(x=1.0, color='red', linestyle='--', linewidth=2,
                       alpha=0.5, label='Failure (1.0)')
        axes[2].grid(True, alpha=0.3, linestyle='--')
        axes[2].legend(loc='upper right', fontsize=fsize-2, ncol=1)
        axes[2].tick_params(labelsize=fsize-1)
        axes[2].set_xlim(left=0)

        # Overall title
        years = time / (365.25 * 24 * 3600)
        fig.suptitle(f'Analytical (Anderson) vs Numerical (GEOS Continuum & Contact) - t={years:.1f} years',
                    fontsize=fsize+2, fontweight='bold', y=0.995)

        # Change verticale scale
        if self.config.MAX_DEPTH_PROFILES != None :
            for i in range(len(axes)):
                axes[i].set_ylim(bottom=self.config.MAX_DEPTH_PROFILES)

        if self.config.MIN_DEPTH_PROFILES != None :
            for i in range(len(axes)):
                axes[i].set_ylim(top=self.config.MIN_DEPTH_PROFILES)

        plt.tight_layout(rect=[0, 0, 1, 0.99])

        # Save
        if save:
            filename = f'analytical_vs_numerical_comparison_{years:.0f}y.png'
            plt.savefig(path / filename, dpi=300, bbox_inches='tight')
            print(f"\n  💾 Comparison plot saved: {filename}")

        # Show
        if show:
            plt.show()
        else:
            plt.close()


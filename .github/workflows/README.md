# geosPythonPackages CI/CD Documentation

This document explains the Continuous Integration (CI) setup for the geosPythonPackages repository.

## Overview

The CI system consists of two main workflows:

1. **`python-package.yml`** - Tests all Python packages individually
2. **`test_geos_integration.yml`** - Tests integration with the GEOS simulation framework

## Workflow 1: Python Package Testing (`python-package.yml`)

### Purpose
Tests each Python package independently to ensure:
- Code quality (linting with yapf)
- Functionality (unit tests with pytest)
- Python version compatibility (3.10, 3.11, 3.12)
- VTK version compatibility (>= 9.3)

### Tested Packages
- `geos-ats` - Automated Testing System for GEOS
- `geos-geomechanics` - Geomechanics analysis tools
- `geos-mesh` - Mesh conversion and validation tools
- `geos-processing` - Post-processing utilities
- `geos-timehistory` - Time history analysis
- `geos-trame` - Trame-based visualization
- `geos-utils` - Utility functions
- `geos-xml-tools` - XML preprocessing and formatting
- `geos-xml-viewer` - XML viewing tools
- `hdf5-wrapper` - HDF5 file handling wrapper
- `pygeos-tools` - GEOS Python tools

### Jobs

#### 1. Semantic Pull Request Check
```yaml
semantic_pull_request:
  - Validates PR title follows conventional commits format
  - Required format: `type: description` or `type(scope): description`
  - Examples: `feat: add new feature`, `fix(mesh): resolve bug`
```

#### 2. Draft PR Check
```yaml
check_draft:
  - Fails CI if PR is still in draft mode
  - Prevents accidental merging of incomplete work
  - Mark PR as "Ready for review" to proceed
```

#### 3. Build and Test
```yaml
build:
  - Matrix testing across Python 3.10, 3.11, 3.12
  - Installs package dependencies
  - Lints code with yapf
  - Runs pytest tests
```

#### 4. Label Checks
```yaml
check_integration_label:
  - Checks for 'test-geos-integration' label

check_force_integration_label:
  - Checks for 'force-geos-integration' label
```

#### 5. GEOS Integration Required Check
```yaml
check_geos_integration_required:
  - Analyzes changed files
  - Determines if GEOS integration tests are needed
  - See "Smart GEOS Integration Testing" section below
```

#### 6. GEOS CI Dispatch
```yaml
geos_ci_dispatch:
  - Evaluates label + file change requirements
  - Decides whether to run, skip, or fail
  - Provides clear error messages for incorrect label usage
```

#### 7. GEOS Integration Test (Conditional)
```yaml
geos_integration_test:
  - Only runs if dispatch job says to proceed
  - Calls test_geos_integration.yml workflow
```

#### 8. Final Validation
```yaml
final_validation:
  - Summarizes all test results
  - Determines if PR can be merged
```

## Workflow 2: GEOS Integration Testing (`test_geos_integration.yml`)

### Purpose
Tests that geosPythonPackages integrates correctly with GEOS by:
1. Building GEOS with PyGEOSX enabled
2. Installing Python packages into GEOS environment
3. Verifying tools are accessible and functional

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│ 1. Determine GEOS TPL Tag                               │
│    - Extracts TPL version from GEOS devcontainer.json   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Test GEOS Integration                                │
│    ├── Setup: Checkout repos, install dependencies      │
│    ├── Configure: GEOS with PyGEOSX enabled             │
│    ├── Build: Compile GEOS                              │
│    ├── Test 1: Direct setupPythonEnvironment.bash       │
│    ├── Test 2: make geosx_python_tools                  │
│    ├── Test 3: make geosx_python_tools_clean            │
│    ├── Test 4: make geosx_python_tools_test             │
│    └── Test 5: XML formatting                           │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Integration Summary                                  │
│    - Reports pass/fail status                           │
└─────────────────────────────────────────────────────────┘
```

### Test Details

#### Test 1: Direct setupPythonEnvironment.bash
- **Purpose**: Validates the Python setup script works standalone
- **What it does**:
  - Patches script to search `/usr/local/bin/` for pip-installed tools
  - Installs Python packages via the GEOS setup script
  - Creates symlinks to tools in `bin_direct/`
- **Validates**:
  - ✅ Python packages install correctly
  - ✅ Scripts are findable and linkable
  - ✅ All required tools are available

**Key Implementation Detail**: The script is patched because pip installs to `/usr/local/bin/` but the setup script originally only searches:
- `/usr/bin/`
- `$HOME/.local/bin/`
- `$HOME/local/bin/`

#### Test 2: make geosx_python_tools
- **Purpose**: Validates CMake target builds Python tools
- **What it does**:
  - Runs the `geosx_python_tools` CMake target
  - Uses PyGEOSX virtual environment
  - Creates tool symlinks in `bin/`
- **Validates**:
  - ✅ CMake integration works correctly
  - ✅ PyGEOSX virtual environment is created
  - ✅ Tools are accessible via CMake build system

#### Test 3: make geosx_python_tools_clean
- **Purpose**: Validates cleanup target works
- **What it does**:
  - Runs `geosx_python_tools_clean` target
  - Verifies symlinks are removed
  - Rebuilds for next test
- **Validates**:
  - ✅ Clean target removes symlinks
  - ✅ Rebuild works after cleanup

**Note**: This only cleans symlinks, not system-wide packages (by design).

#### Test 4: make geosx_python_tools_test
- **Purpose**: Validates Python tools test suite runs
- **What it does**:
  - Creates required test directory structure
  - Symlinks test script from PyGEOSX environment
  - Runs XML tools unit tests
  - Cleans up test output files
- **Tests Run**:
  - Unit dictionary tests
  - Units conversion tests (25 tests)
  - Parameter regex tests (8 tests)
  - Units regex tests (6 tests)
  - Symbolic regex tests (13 tests)
  - XML processor tests (4 tests)
- **Validates**:
  - ✅ Test infrastructure works
  - ✅ All XML tools function correctly
  - ✅ Cleanup process succeeds

#### Test 5: XML Formatting
- **Purpose**: Validates XML formatting functionality
- **What it does**:
  - Builds `geosx_python_tools` target
  - Runs XML formatting script directly
  - Formats all XML files in GEOS src/ and examples/
- **Validates**:
  - ✅ `format_xml` tool works
  - ✅ Can process GEOS XML files

**Known Issue**: The CMake target `geosx_format_all_xml_files` has a bug (depends on non-existent `geosx_xml_tools` instead of `geosx_python_tools`). We work around this by running the formatting script directly.

### Environment Setup

#### Container Image
```yaml
image: geosx/ubuntu22.04-gcc12:${GEOS_TPL_TAG}
```
- Ubuntu 22.04 with GCC 12
- GEOS dependencies pre-installed
- TPL tag dynamically extracted from GEOS

#### Key Environment Variables
```bash
SETUPTOOLS_USE_DISTUTILS=stdlib     # Avoid setuptools/distutils conflicts
PIP_DISABLE_PIP_VERSION_CHECK=1     # Reduce pip warnings
PYTHONDONTWRITEBYTECODE=1           # Prevent .pyc creation
PATH=/usr/local/bin:$PATH           # Ensure pip scripts are found
```

#### GEOS Build Configuration
```cmake
-DENABLE_PYGEOSX=ON                 # Enable Python integration
-DENABLE_XML_UPDATES=OFF            # Skip XML validation (physics disabled)
-DGEOS_ENABLE_TESTS=OFF            # Disable GEOS tests
-DGEOS_ENABLE_*=OFF                # Disable physics solvers (faster build)
-DGEOS_PYTHON_PACKAGES_BRANCH=...  # Use current PR branch
```

## Smart GEOS Integration Testing

### When Tests Run

GEOS integration tests are **automatically triggered** when changes affect:

#### GEOS-Integrated Packages
- `geos-utils/` - Core utilities used of goesPythonPackages
- `geos-mesh/` - Mesh conversion (`convert_abaqus`, `mesh-doctor`)
- `geos-xml-tools/` - XML preprocessing (`preprocess_xml`, `format_xml`)
- `hdf5-wrapper/` - HDF5 I/O wrapper
- `pygeos-tools/` - Python tools for GEOS
- `geos-ats/` - Automated testing framework

#### Critical Infrastructure Files
- `.github/workflows/python-package.yml` - Main CI workflow
- `.github/workflows/test_geos_integration.yml` - Integration workflow
- `install_packages.sh` - Installation script

### When Tests Are Skipped

Tests are automatically skipped when changes only affect:

#### Documentation
- `docs/` - Documentation files
- `README.md` - Repository README
- `.readthedocs.yml` - ReadTheDocs configuration

#### Non-Integrated Packages
- `geos-geomechanics/` - Standalone geomechanics tools
- `geos-processing/` - Post-processing utilities
- `geos-pv/` - ParaView utilities
- `geos-timehistory/` - Time history analysis
- `geos-trame/` - Trame visualization
- `geos-xml-viewer/` - XML viewing tools

#### Configuration Files
- `.gitignore`, `.gitattributes` - Git configuration
- `.style.yapf`, `.ruff.toml`, `.mypy.ini` - Code style configs
- `.github/workflows/doc-test.yml` - Documentation CI
- `.github/workflows/typing-check.yml` - Type checking CI

### Manual Override Labels

The CI supports two labels for controlling GEOS integration tests:

1. **`test-geos-integration`** - Must be added when changes affect GEOS-integrated packages
   - Required when modifying: `geos-utils`, `geos-mesh`, `geos-xml-tools`, `hdf5-wrapper`, `pygeos-tools`, `geos-ats`
   - CI will fail if this label is missing when required
   - CI will warn if this label is present but not needed (suggest using `force-geos-integration` instead)

2. **`force-geos-integration`** - Forces tests to run regardless of changed files
   - Use this when testing CI changes themselves
   - Use this for docs/config-only PRs where you want to verify GEOS integration still works
   - Overrides all other logic - tests will always run

### Label Decision Logic

The CI uses the following decision matrix:

| GEOS Required<br/>(by file changes) | `test-geos-integration`<br/>label | `force-geos-integration`<br/>label | Result |
|-------------------------------------|-----------------------------------|-------------------------------------|--------|
| - | - | ✅ Yes | ✅ **Run tests** (forced) |
| ✅ Yes | ✅ Yes | ❌ No | ✅ **Run tests** (normal) |
| ✅ Yes | ❌ No | ❌ No | ❌ **ERROR** - Label required |
| ❌ No | ✅ Yes | ❌ No | ⊘ **Skip** - Wrong label (use force instead) |
| ❌ No | ❌ No | ❌ No | ⊘ **Skip tests** (not needed) |

### Example Scenarios

✅ **Tests Will Run (Required + Label)**
```
Changes:
  - geos-mesh/src/mesh_converter.py
  - geos-xml-tools/src/preprocessor.py
Labels: test-geos-integration
Result: GEOS integration will run (changes affect integrated packages)
```

❌ **CI Will Fail (Required but Missing Label)**
```
Changes:
  - geos-utils/src/table_loader.py
  - hdf5-wrapper/src/wrapper.py
Labels: (none)
Result: ERROR - 'test-geos-integration' label required
```

⊘ **Tests Will Skip (Not Required)**
```
Changes:
  - docs/user_guide.md
  - README.md
  - geos-pv/src/visualizer.py
Labels: (none)
Result: GEOS integration not required (skipped)
```

⊘ **Tests Will Skip (Wrong Label)**
```
Changes:
  - docs/installation.md
  - .style.yapf
Labels: test-geos-integration
Result: Warning - Label not needed, use 'force-geos-integration' to force tests (skipped)
```

✅ **Tests Will Run (Forced)**
```
Changes:
  - docs/installation.md
  - .github/workflows/python-package.yml
Labels: force-geos-integration
Result: GEOS integration forced (tests will run regardless of changes)
```

## GEOS Integration: How It Works

### Python Package Installation Flow

```
┌─────────────────────────────────────────────┐
│ 1. GEOS Build System                        │
│    cmake -DENABLE_PYGEOSX=ON                │
│         -DGEOS_PYTHON_PACKAGES_BRANCH=...   │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ 2. CMake calls setupPythonEnvironment.bash  │
│    - Clones geosPythonPackages              │
│    - Creates virtual environment (optional) │
│    - Installs packages via pip              │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ 3. Python Packages Installed                │
│    pip install geos-utils                   │
│    pip install geos-mesh                    │
│    pip install geos-xml-tools               │
│    pip install hdf5-wrapper                 │
│    pip install pygeos-tools                 │
│    pip install geos-ats                     │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ 4. Scripts Available                        │
│    /usr/local/bin/preprocess_xml            │
│    /usr/local/bin/format_xml                │
│    /usr/local/bin/convert_abaqus            │
│    /usr/local/bin/mesh-doctor               │
│    /usr/local/bin/run_geos_ats              │
│    ... and more                             │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ 5. Symlinks Created in GEOS bin/            │
│    build/bin/preprocess_xml -> /usr/...     │
│    build/bin/format_xml -> /usr/...         │
└─────────────────────────────────────────────┘
```

### GEOS Uses These Tools

|       Package      |                        Tools                        |                               Purpose                               |
|--------------------|-----------------------------------------------------|---------------------------------------------------------------------|
| **geos-xml-tools** | `preprocess_xml`;`format_xml`                       | Preprocess XML input files;Format XML for readability               |
| **geos-mesh**      | `convert_abaqus`;`mesh-doctor`                      | Convert Abaqus meshes to VTU/GMSH;Validate and fix mesh quality     |
| **geos-ats**       | `run_geos_ats`;`setup_ats_environment`;`geos_ats_*` | Run automated test suite;Setup test environment;Various test checks |
| **hdf5-wrapper**   | Python API                                          | HDF5 file I/O operations                                            |
| **pygeos-tools**   | Python API                                          | GEOS workflow utilities                                             |
| **geos-utils**     | Python API                                          | Common utility functions                                            |

## Troubleshooting

### Common Issues

#### 1. Scripts Not Found
**Error**: `(could not find where preprocess_xml is installed)`

**Cause**: pip installs to `/usr/local/bin/` but setup script doesn't search there

**Solution**: The CI automatically patches `setupPythonEnvironment.bash` to add `/usr/local/bin/` to search paths

#### 2. Setuptools/Distutils Conflict
**Error**: `AssertionError: /usr/lib/python3.10/distutils/core.py`

**Cause**: Version mismatch between setuptools and distutils

**Solution**: Set `SETUPTOOLS_USE_DISTUTILS=stdlib` environment variable (already done in CI)

#### 3. XML Validation Fails
**Error**: Schema validation errors when physics packages disabled

**Cause**: Schema only includes enabled packages, but XML examples reference all packages

**Solution**: Use `-DENABLE_XML_UPDATES=OFF` to disable validation (already configured)

#### 4. Test 5 Make Target Fails
**Error**: `No rule to make target 'geosx_xml_tools'`

**Cause**: Bug in GEOS CMakeLists.txt - depends on non-existent target

**Solution**: Run formatting script directly (workaround implemented in CI)

## Contributing

When adding new Python packages or modifying existing ones:

1. **Update Package Lists**: If adding a package used by GEOS:
   - Add to `GEOS_INTEGRATED_PACKAGES` in `python-package.yml`
   - Document in this README

2. **Add Tests**: Ensure your package has:
   - Unit tests (pytest)
   - Proper code formatting (yapf)
   - Type hints (mypy compatible)

3. **Update Documentation**:
   - Add package docs to `docs/` directory
   - Update main `README.md` if needed
   - Update this CI README if CI changes

4. **Test Integration**:
   - If package integrates with GEOS, add `test-geos-integration` label to PR
   - Verify all 5 integration tests pass
   - If only testing CI changes on a docs PR, use `force-geos-integration` label

### PR Label Usage Guide

**For PR Authors:**

| Your PR Changes | Required Label | What Happens |
|-----------------|----------------|--------------|
| GEOS-integrated packages<br/>(utils, mesh, xml-tools, etc.) | `test-geos-integration` | ✅ Tests run (required) |
| Docs/config only | (none) | ⊘ Tests skipped |
| Docs + you want to test integration | `force-geos-integration` | ✅ Tests run (forced) |
| CI workflow files | `force-geos-integration` | ✅ Tests run (verify CI works) |

**Common Mistakes:**
- ❌ Modifying `geos-mesh/` without label → CI fails, add `test-geos-integration`
- ❌ Adding `test-geos-integration` to docs-only PR → Warning, remove label or use `force-geos-integration`
- ✅ Modifying `.github/workflows/` with `force-geos-integration` → Tests run to verify CI changes

## References

- [GEOS Repository](https://github.com/GEOS-DEV/GEOS)
- [GEOS Documentation](https://geosx-geosx.readthedocs-hosted.com/)
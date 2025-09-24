======================================
Continuous Integration Developer Guide
======================================

This document explains the geosPythonPackages CI/CD system, how it works, and how developers should use it.

.. contents::
   :local:
   :depth: 3

Overview
========

The geosPythonPackages repository uses a **mandatory two-stage CI system** that ensures all changes are compatible with both the geosPythonPackages ecosystem and the GEOS integration environment.

System Architecture
===================

The CI system consists of multiple workflows that run in a specific sequence:

Workflow Structure
------------------

.. code-block:: text

   Pull Request Created
   ├── Stage 1: Regular CI Tests (Automatic)
   │   ├── semantic_pull_request
   │   ├── build (matrix: Python 3.10, 3.11, 3.12 × 11 packages)
   │   └── check_geos_integration_required
   ├── Stage 2: User Action Required
   │   └── Add "test-geos-integration" label
   └── Stage 3: GEOS Integration Tests
       ├── test_geos_integration (reusable workflow)
       └── final_validation

Workflow Files
--------------

* **python-package.yml**: Main CI orchestrator
* **test_geos_integration.yml**: GEOS integration testing (reusable)
* **doc-test.yml**: Documentation testing
* **typing-check.yml**: Type checking validation

Stage 1: Regular CI Tests
=========================

These tests run automatically on every PR and validate the geosPythonPackages code itself.

Semantic Pull Request Check
---------------------------

**Job**: ``semantic_pull_request``

Validates that PR titles follow conventional commit semantics:

.. code-block:: text

   feat: add new XML validation tool  # Valid
   fix: correct mesh generation bug   # Valid
   docs: update installation guide    # Valid
   Updated some files                 # Invalid

Configuration:
- Uses ``amannn/action-semantic-pull-request@v5.5.3``
- Allows work-in-progress PRs
- Scope is optional

Build Matrix Testing
--------------------

**Job**: ``build``

Tests all packages across multiple Python versions:

**Matrix Dimensions:**
- **Python versions**: 3.10, 3.11, 3.12
- **Packages**: 11 packages (geos-ats, geos-geomechanics, geos-mesh, etc.)
- **Dependencies**: Automatic handling of inter-package dependencies

**Test Steps:**
1. Install package with dependencies
2. Lint with yapf
3. Run pytest (handles packages without tests)

**Key Features:**
- Fail-fast disabled (tests all combinations)
- Max parallel jobs: 3
- Dependency resolution for complex packages

Label Requirement Check
-----------------------

**Job**: ``check_geos_integration_required``

Determines if the mandatory ``test-geos-integration`` label is present.

.. important::
   This job **always runs** and outputs whether GEOS integration testing should proceed.

Stage 2: User Action Required
=============================

After regular CI passes, users **must** add the ``test-geos-integration`` label to proceed.

Why This Step Exists
--------------------

1. **Performance**: GEOS integration tests are resource-intensive
2. **User Control**: Allows validation of regular changes first
3. **Mandatory Validation**: Ensures ALL PRs are tested against GEOS
4. **Clear Workflow**: Explicit user action required for final validation

How to Add the Label
--------------------

**Via GitHub Web Interface:**

1. Navigate to your PR
2. Click "Labels" in the right sidebar
3. Select ``test-geos-integration``

**Via GitHub CLI:**

.. code-block:: bash

   gh pr edit <PR_NUMBER> --add-label "test-geos-integration"

Stage 3: GEOS Integration Tests
===============================

These tests run **only after** the label is added and validate integration with GEOS.

Integration Test Components
---------------------------

**Repository Checkout:**
- Clones geosPythonPackages (current PR branch)
- Clones GEOS (develop branch)

**System Setup:**
- Python 3.10, 3.11, 3.12 environment
- CMake and build tools
- System dependencies

**Integration Validation:**

1. **Python Environment Compatibility**
   
   - Tests ``scripts/setupPythonEnvironment.bash`` from GEOS
   - Validates environment setup procedures

2. **CMake Integration**

   .. code-block:: bash

      cmake .. \
        -DGEOSX_BUILD_SHARED_LIBS=OFF \
        -DENABLE_GEOSX_PYTHON_TOOLS=ON \
        -DGEOS_PYTHON_PACKAGES_SOURCE="${GEOSPYTHONPACKAGES_ROOT}" \
        -DCMAKE_BUILD_TYPE=Release

3. **Build Target Testing**

   - Verifies ``make geosx_python_tools`` target exists
   - Attempts to build Python tools (graceful failure handling)
   - Validates build system integration

4. **Tool Availability Verification**

   - XML processing tools (preprocess_xml.py, format_xml.py)
   - ATS integration (run_geos_ats.py)
   - Package structure validation

5. **Script Integrity Checks**

   - Syntax validation for installation scripts
   - Directory structure verification

Final Validation
----------------

**Job**: ``final_validation``

**Critical Logic:**

.. code-block:: yaml

   if GEOS integration was triggered:
       if GEOS tests passed:
           SUCCESS - PR can be merged
       else:
           FAIL - PR blocked from merging
   else:
       FAIL - Label is mandatory for ALL PRs

Developer Workflow
==================

Complete PR Lifecycle
---------------------

1. **Create Pull Request**

   .. code-block:: bash

      git checkout -b authorname/feature/my-new-feature
      # Make changes
      git commit -m "feat: add new functionality"
      git push origin authorname/feature/my-new-feature
      # Create PR via GitHub

2. **Monitor Regular CI**

   - Wait for ``semantic_pull_request`` and ``build`` jobs to complete
   - Fix any failures in regular testing
   - **Do not add the label until regular CI passes**

3. **Add Integration Label**

   Once regular CI is green:

    1. Navigate to your PR
    2. Click "Labels" in the right sidebar
    3. Select ``test-geos-integration``

   OR

   .. code-block:: bash

      gh pr edit <PR_NUMBER> --add-label "test-geos-integration"

4. **Monitor GEOS Integration**

   - GEOS integration tests will automatically start
   - Monitor progress in the Actions tab

5. **Address Integration Issues**

   If GEOS integration fails:
   - Review the integration test logs
   - Fix compatibility issues
   - Push updates (tests will re-run automatically)

6. **Merge When Ready**

   PR can be merged when ALL status checks are green:
   - semantic_pull_request
   - build (all matrix combinations)
   - Check GEOS Integration Required
   - Test geosPythonPackages Integration with GEOS
   - Final CI Validation
   - Reviews addressed and approved

Troubleshooting
===============

Common Issues and Solutions
---------------------------

**Issue**: "Regular CI failing on build job"

**Solutions**:
- Check package dependencies in matrix configuration
- Verify yapf formatting: ``yapf -r --diff ./package-name --style .style.yapf``
- Run tests locally: ``python -m pytest ./package-name``

**Issue**: "GEOS integration test not starting"

**Solutions**:
- Verify ``test-geos-integration`` label is present
- Ensure regular CI completed successfully first
- Check workflow logs for prerequisite failures

**Issue**: "make geosx_python_tools failing in integration"

**Solutions**:
- Review CMake configuration in integration logs
- Check if new dependencies are needed
- Verify package structure matches GEOS expectations
- Consider if changes require GEOS-side updates

Debug Commands
--------------

**Local Testing Simulation**:

.. code-block:: bash

   # Test yapf formatting
   yapf -r --diff ./geos-xml-tools --style .style.yapf
   
   # Test package installation
   python -m pip install ./geos-xml-tools[test]
   
   # Run package tests
   python -m pytest ./geos-xml-tools
   
   # Test installation script syntax
   bash -n install_packages.sh

**Integration Testing Locally**:

.. code-block:: bash

   # Clone GEOS for local testing
   git clone https://github.com/GEOS-DEV/GEOS.git
   cd GEOS
   
   # Test CMake configuration
   mkdir build && cd build
   cmake .. \
     -DENABLE_GEOSX_PYTHON_TOOLS=ON \
     -DGEOS_PYTHON_PACKAGES_SOURCE="/path/to/geosPythonPackages" \
     -DCMAKE_BUILD_TYPE=Release
   
   # Test build target
   make help | grep geosx_python_tools
   make geosx_python_tools
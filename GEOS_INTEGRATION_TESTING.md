# geosPythonPackages and GEOS Integration Testing

This document explains the new CI requirements for geosPythonPackages contributors to ensure compatibility with GEOS.

## ⚠️ IMPORTANT: New CI Requirements

Starting now, all PRs to geosPythonPackages **MUST** pass GEOS integration testing before they can be merged.

## Quick Start Guide

### For Every PR, you must:

1. ✅ **Ensure standard CI tests pass first** (semantic check, build, lint, test)
2. ✅ **Add the `test-geos-integration` label** to your PR (only after standard tests pass)
3. ✅ **Wait for GEOS integration tests** to pass
4. ✅ **Fix any issues** if GEOS tests fail

## The Complete Workflow Sequence

The CI now follows this **strict sequence**:

### 1️⃣ Standard CI Tests (MUST pass first)
- ✅ Semantic PR title check
- ✅ Build and install all packages
- ✅ Lint with yapf
- ✅ Test with pytest

**⚠️ Until these pass, GEOS integration testing will NOT start**

### 2️⃣ Label Check (after standard tests pass)
- 🏷️ Check for `test-geos-integration` label
- ❌ **FAIL** if label is missing
- ✅ **PROCEED** if label is present

### 3️⃣ GEOS Integration Testing (triggered automatically)
- 🔗 Trigger GEOS CI with your branch
- ⏱️ Wait for GEOS tests to complete (15-30 minutes)
- ✅ **PASS** if GEOS tests succeed
- ❌ **FAIL** if GEOS tests fail

### 4️⃣ Final Validation
- ✅ **VALID** = Standard tests ✅ + Label ✅ + GEOS tests ✅
- ❌ **INVALID** = Any step fails

## Developer Workflow

### Step-by-Step Process:

#### 1. Create Your PR and Iterate
```bash
# Create your branch and make changes
git checkout -b fix/my-awesome-feature
# ... make changes ...
git push origin fix/my-awesome-feature
```

#### 2. Wait for Standard CI to Pass
- **Don't add the label yet!**
- Let the standard CI tests run first
- Fix any issues with:
  - PR title formatting
  - Build errors
  - Lint issues
  - Test failures
- Push fixes and wait for tests to pass

#### 3. Add Label (Only After Standard Tests Pass)
- Go to your PR page
- In the right sidebar, find "Labels"
- Add the label: `test-geos-integration`
- This triggers the GEOS integration sequence

#### 4. Monitor GEOS Integration Results
- The workflow will automatically trigger GEOS CI
- You'll see progress in the "geosPythonPackages CI" workflow
- Wait for results (can take 15-30 minutes)

#### 5. Address Any GEOS Failures
If GEOS integration fails:
- Check the workflow logs for details
- Fix the issues in your branch
- Push the fixes
- The process will restart from step 1

## What Gets Tested in GEOS Integration

The GEOS integration test validates:
- ✅ geosPythonPackages can be installed by GEOS
- ✅ Key tools work: `preprocess_xml`, `format_xml`, `mesh-doctor`
- ✅ Python packages can be imported: `geos_utils`, `geos_mesh`, etc.
- ✅ XML preprocessing functionality works
- ✅ No API breaking changes

## Understanding CI Results

### ✅ VALID (Green) ✅
All requirements met:
- Standard CI tests passed
- `test-geos-integration` label present
- GEOS integration tests passed
- **Ready for review/merge**

### ❌ INVALID (Red) ❌
One or more requirements failed:
- Standard CI tests failed
- Label missing
- GEOS integration tests failed
- **Cannot be merged**

## Common Scenarios

### Scenario 1: Standard Tests Failing
```
❌ Standard CI Tests → ⏸️ Label Check Skipped → ⏸️ GEOS Tests Skipped
```
**Action**: Fix your code first, don't add the label yet

### Scenario 2: Standard Tests Pass, No Label
```
✅ Standard CI Tests → ❌ Label Missing → ⏸️ GEOS Tests Skipped  
```
**Action**: Add the `test-geos-integration` label

### Scenario 3: All Standard Tests Pass, Label Added
```
✅ Standard CI Tests → ✅ Label Present → 🔄 GEOS Tests Running
```
**Action**: Wait for GEOS tests to complete

### Scenario 4: GEOS Tests Fail
```
✅ Standard CI Tests → ✅ Label Present → ❌ GEOS Tests Failed
```
**Action**: Fix the breaking changes, push updates

### Scenario 5: Everything Passes
```
✅ Standard CI Tests → ✅ Label Present → ✅ GEOS Tests Passed → ✅ READY
```
**Action**: Proceed with normal code review

## Benefits of This Approach

1. **🚀 Faster Iteration**: Fix basic issues first without expensive GEOS testing
2. **💰 Cost Efficient**: Only run GEOS CI when standard tests pass
3. **🎯 Clear Sequence**: Developers know exactly when to add the label
4. **🛡️ Protected GEOS**: No breaking changes reach GEOS
5. **📈 Better Feedback**: Clear status at each step

## Tips for Contributors

### DO ✅
- ✅ Let standard CI pass completely before adding the label
- ✅ Fix all basic issues (build, lint, test) first
- ✅ Add the label only when standard tests are green
- ✅ Monitor the GEOS integration progress
- ✅ Fix GEOS-related issues promptly

### DON'T ❌
- ❌ Add the label immediately when creating the PR
- ❌ Add the label while standard tests are still failing
- ❌ Ignore GEOS test failures
- ❌ Remove and re-add the label unnecessarily

## Getting Help

### If you need help:
1. Check the workflow logs for specific error messages
2. Look at the [detailed documentation](https://github.com/GEOS-DEV/GEOS/blob/develop/src/docs/GEOS_PYTHON_INTEGRATION_TESTING.md)
3. Ask in the GEOS-DEV team channels

### Manual Testing:
You can manually trigger GEOS integration testing:
1. Go to [GEOS Actions](https://github.com/GEOS-DEV/GEOS/actions)
2. Find "Test GEOS Integration from geosPythonPackages"
3. Click "Run workflow" and specify your branch

## Summary

| Step | Status | Next Action |
|------|--------|-------------|
| 1. Standard CI | ❌ Failed | Fix code issues |
| 1. Standard CI | ✅ Passed | Add `test-geos-integration` label |
| 2. Label Check | ❌ Missing | Add the label |
| 2. Label Check | ✅ Present | Wait for GEOS tests |
| 3. GEOS Tests | 🔄 Running | Wait (15-30 min) |
| 3. GEOS Tests | ❌ Failed | Fix breaking changes |
| 3. GEOS Tests | ✅ Passed | Ready for review! |

**Remember**: The sequence is strictly enforced - standard tests MUST pass before GEOS integration testing begins!

# Validation tests

This document contains the observations made during the validation tests of the refactoring branch.

## Run 1

- Step: Setup (one-time)
- The command `bash setup_dev_env.sh` creates a venv in the directory `.venv`. If running on MacOS, the venv should be in the directory `venv.nosync`.
- The evdev dependency is not available on MacOS. It should be removed from the dependencies. 
- Tests are stucked at this step.

### Corrections applied (`2589140`)

- **Venv path**: configurable via `SAPHIR_VENV_DIR` env var. On macOS: `SAPHIR_VENV_DIR=./venv.nosync bash setup_dev_env.sh`.
- **Linux-only deps** (`evdev`, `inotify_simple`, `pyudev`): now optional in `setup_dev_env.sh` — installed when available, skipped with a warning otherwise (same pattern as `libvirt-python`).
- `validate_env.sh` also honors `SAPHIR_VENV_DIR`.

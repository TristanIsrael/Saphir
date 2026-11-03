# Validation tests

This document contains the observations made during the validation tests of the refactoring branch.

## Run 1

- Step: Setup (one-time)
- The command `bash setup_dev_env.sh` creates a venv in the directory `.venv`. If running on MacOS, the venv should be in the directory `venv.nosync`.
- The evdev dependency is not available on MacOS. It should be removed from the dependencies. 
- Tests are stucked at this step.

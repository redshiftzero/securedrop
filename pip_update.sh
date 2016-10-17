#!/bin/bash

# Usage: ./pip_update.sh
# Run periodically to keep Python requirements up-to-date

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
requirements_dir="${dir}/securedrop/requirements"
venv="review_env"

# This script should not be run with an active virtualenv. Calling deactivate
# does not work reliably, so instead we warn then quit.
if [[ -n $VIRTUAL_ENV ]]; then
  echo "Please deactivate your virtualenv before running this script."
  exit 1
fi

# Test if pip and virtualenv are available and install them if not
INSTALL='sudo apt-get install -y'
command -v pip >/dev/null 2>&1 || { eval "$INSTALL python-pip"; }
command -v virtualenv >/dev/null 2>&1 || { eval "$INSTALL python-virtualenv"; }

# Create a temporary virtualenv for the SecureDrop Python packages in our
# requirements directory
cd $requirements_dir

trap "rm -rf ${venv}" EXIT

virtualenv -p python2.7 $venv
source "${venv}/bin/activate"

pip install --upgrade pip
pip install pip-tools

# Compile new requirements (.txt) files from our top-level dependency (.in)
# files. See http://nvie.com/posts/better-package-management/
for r in "securedrop" "test"; do
  # Maybe pip-tools will get its act together and standardize their cert-pinning
  # syntax and this line will break. One can only hope.
  pip-compile -U -o "${r}-requirements.txt" "${r}-requirements.in"
done

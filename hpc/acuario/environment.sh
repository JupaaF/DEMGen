#!/bin/bash

set -eu

module purge
module load gcc/10.2.0
module load python/3.12.1
module load git/2.29.2

# Loading boost/1.78.0 attempts to load gcc/6.5.0. Use the paths reported by
# `module show` so the selected GCC 10.2 toolchain remains active.
export BOOST_ROOT=/globalfs/opt/boost/1.78.0
export CPATH="${BOOST_ROOT}/include:${CPATH:-}"
export LIBRARY_PATH="${BOOST_ROOT}/lib:${LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="${BOOST_ROOT}/lib:${LD_LIBRARY_PATH:-}"

export CC=/globalfs/opt/gcc/10.2.0/bin/gcc
export CXX=/globalfs/opt/gcc/10.2.0/bin/g++

# Slurm defines SLURM_SUBMIT_DIR as the directory from which `sbatch` was
# called. Prefer it because some Acuario jobs do not expose BASH_SOURCE while
# this file is being sourced under `set -u`.
if [ -n "${SLURM_SUBMIT_DIR:-}" ]; then
    DEMGEN_ROOT=$(cd "${SLURM_SUBMIT_DIR}" && pwd -P)
elif [ -n "${BASH_SOURCE[0]-}" ]; then
    DEMGEN_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)
elif [ -f "${PWD}/hpc/acuario/environment.sh" ]; then
    DEMGEN_ROOT=$(pwd -P)
else
    echo "Cannot determine DEMGen root. Run from the DEMGen directory." >&2
    return 1 2>/dev/null || exit 1
fi
export DEMGEN_ROOT
export KRATOS_ROOT="${DEMGEN_ROOT}/external/kratos_linux"
export KRATOS_INSTALL="${KRATOS_ROOT}/bin/Release"

if [ -x "${DEMGEN_ROOT}/.venv-acuario/bin/python3" ]; then
    export PATH="${DEMGEN_ROOT}/.venv-acuario/bin:${PATH}"
fi

export PYTHONPATH="${KRATOS_INSTALL}:${DEMGEN_ROOT}/src:${PYTHONPATH:-}"
export LD_LIBRARY_PATH="${KRATOS_INSTALL}/libs:${LD_LIBRARY_PATH}"

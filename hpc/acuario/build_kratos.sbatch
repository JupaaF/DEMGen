#!/bin/bash
#SBATCH --job-name=demgen-build-kratos
#SBATCH --output=hpc/acuario/logs/build-kratos-%j.out
#SBATCH --error=hpc/acuario/logs/build-kratos-%j.err
#SBATCH --partition=R182-open
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=08:00:00

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"
mkdir -p hpc/acuario/logs

source hpc/acuario/environment.sh

CMAKE_VERSION=3.30.1
CMAKE_ARCHIVE="${DEMGEN_ROOT}/hpc/acuario/tools/cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz"
CMAKE_ROOT="${DEMGEN_ROOT}/.tools/cmake-${CMAKE_VERSION}-linux-x86_64"
CMAKE_BIN="${CMAKE_ROOT}/bin/cmake"
CMAKE_SHA256=ac31f077ef3378641fa25a3cb980d21b2f083982d3149a8f2eb9154f2b53696b

if [ ! -x "${CMAKE_BIN}" ]; then
    if [ ! -f "${CMAKE_ARCHIVE}" ]; then
        echo "Offline CMake archive is missing: ${CMAKE_ARCHIVE}" >&2
        echo "Run hpc/acuario/deploy.sh from the local workstation." >&2
        exit 1
    fi

    ACTUAL_CMAKE_SHA256=$(sha256sum "${CMAKE_ARCHIVE}" | awk '{print $1}')
    if [ "${ACTUAL_CMAKE_SHA256}" != "${CMAKE_SHA256}" ]; then
        echo "CMake archive checksum mismatch." >&2
        exit 1
    fi

    mkdir -p "${DEMGEN_ROOT}/.tools"
    tar -xzf "${CMAKE_ARCHIVE}" -C "${DEMGEN_ROOT}/.tools"
fi

if [ ! -x "${CMAKE_BIN}" ]; then
    echo "CMake executable is unavailable after extraction: ${CMAKE_BIN}" >&2
    exit 1
fi

echo "Using CMake at ${CMAKE_BIN}"
"${CMAKE_BIN}" --version

if [ ! -d "${KRATOS_ROOT}/applications/DEMApplication" ]; then
    echo "Kratos source is missing at ${KRATOS_ROOT}. Run deploy.sh first." >&2
    exit 1
fi

if [ ! -x "${DEMGEN_ROOT}/.venv-acuario/bin/python3" ]; then
    /globalfs/opt/python/3.12.1/bin/python3 -m venv \
        "${DEMGEN_ROOT}/.venv-acuario"
fi

source "${DEMGEN_ROOT}/.venv-acuario/bin/activate"

NUMPY_WHEEL="${DEMGEN_ROOT}/hpc/acuario/wheels/numpy-2.2.6-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
if [ ! -f "${NUMPY_WHEEL}" ]; then
    echo "Offline NumPy wheel is missing: ${NUMPY_WHEEL}" >&2
    echo "Run hpc/acuario/deploy.sh from the local workstation." >&2
    exit 1
fi

# Acuario's Python 3.12 module has no SSL support. Install the wheel transferred
# by deploy.sh without consulting PyPI or any other package index.
python3 -m pip install --disable-pip-version-check --no-index "${NUMPY_WHEEL}"

PYTHON_EXECUTABLE=$(command -v python3)
PYTHON_INCLUDE_DIR=$(python3 -c \
    "import sysconfig; print(sysconfig.get_path('include'))")
PYTHON_LIBRARY=$(python3 -c \
    "import os, sysconfig; print(os.path.join(sysconfig.get_config_var('LIBDIR'), sysconfig.get_config_var('LDLIBRARY')))")

export KRATOS_APPLICATIONS="${KRATOS_ROOT}/applications/DEMApplication"

"${CMAKE_BIN}" \
    -H"${KRATOS_ROOT}" \
    -B"${KRATOS_ROOT}/build/Release" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${KRATOS_INSTALL}" \
    -DCMAKE_C_COMPILER="${CC}" \
    -DCMAKE_CXX_COMPILER="${CXX}" \
    -DPYTHON_EXECUTABLE="${PYTHON_EXECUTABLE}" \
    -DPYTHON_INCLUDE_DIR="${PYTHON_INCLUDE_DIR}" \
    -DPYTHON_LIBRARY="${PYTHON_LIBRARY}" \
    -DKRATOS_APPLICATIONS="${KRATOS_APPLICATIONS}" \
    -DKRATOS_BUILD_TESTING=OFF \
    -DKRATOS_BUILD_BENCHMARK=OFF \
    -DUSE_MPI=OFF \
    -DUSE_EIGEN_MKL=OFF \
    -DKRATOS_GENERATE_PYTHON_STUBS=OFF

"${CMAKE_BIN}" --build "${KRATOS_ROOT}/build/Release" \
    --target install -- -j"${SLURM_CPUS_PER_TASK}"

python3 -c 'import KratosMultiphysics; print(KratosMultiphysics.__file__)'
python3 -c 'import KratosMultiphysics.DEMApplication; print("DEMApplication OK")'
python3 -c 'from KratosMultiphysics.restart_utility import RestartUtility; print("RestartUtility OK")'

echo "Kratos build completed successfully."

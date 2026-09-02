#!/bin/bash

set -euo pipefail

LOCAL_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)
REMOTE_HOST=${REMOTE_HOST:-jpfernandez@acuario.cimne.upc.edu}
REMOTE_ROOT=${REMOTE_ROOT:-/home/jpfernandez/DEMGen}
KRATOS_COMMIT=66dbb226f80dc78d5ff3985351effb03798ad2b8
NUMPY_WHEEL="${LOCAL_ROOT}/hpc/acuario/wheels/numpy-2.2.6-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
CMAKE_ARCHIVE="${LOCAL_ROOT}/hpc/acuario/tools/cmake-3.30.1-linux-x86_64.tar.gz"
CMAKE_SHA256=ac31f077ef3378641fa25a3cb980d21b2f083982d3149a8f2eb9154f2b53696b

if [ ! -f "${NUMPY_WHEEL}" ]; then
    echo "Missing offline dependency: ${NUMPY_WHEEL}" >&2
    echo "Download NumPy 2.2.6 for CPython 3.12/manylinux2014 before deploying." >&2
    exit 1
fi

if [ ! -f "${CMAKE_ARCHIVE}" ]; then
    echo "Missing offline dependency: ${CMAKE_ARCHIVE}" >&2
    exit 1
fi

ACTUAL_CMAKE_SHA256=$(sha256sum "${CMAKE_ARCHIVE}" | awk '{print $1}')
if [ "${ACTUAL_CMAKE_SHA256}" != "${CMAKE_SHA256}" ]; then
    echo "CMake archive checksum mismatch: ${CMAKE_ARCHIVE}" >&2
    exit 1
fi

echo "Deploying ${LOCAL_ROOT} to ${REMOTE_HOST}:${REMOTE_ROOT}"

ssh "${REMOTE_HOST}" \
    "mkdir -p '${REMOTE_ROOT}/src' '${REMOTE_ROOT}/tests' '${REMOTE_ROOT}/hpc/acuario/logs' '${REMOTE_ROOT}/simulation_runs/cyclic_stress_10kPa_density_0.64' '${REMOTE_ROOT}/external'"

rsync -az --info=progress2 \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    "${LOCAL_ROOT}/src/" "${REMOTE_HOST}:${REMOTE_ROOT}/src/"

rsync -az --info=progress2 \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    "${LOCAL_ROOT}/tests/" "${REMOTE_HOST}:${REMOTE_ROOT}/tests/"

rsync -az --info=progress2 \
    --exclude='*.txt' \
    --exclude='logs/' \
    "${LOCAL_ROOT}/hpc/acuario/" \
    "${REMOTE_HOST}:${REMOTE_ROOT}/hpc/acuario/"

rsync -az --info=progress2 \
    "${LOCAL_ROOT}/simulation_runs/cyclic_stress_10kPa_density_0.64/ParametersDEMGen.json" \
    "${LOCAL_ROOT}/simulation_runs/cyclic_stress_10kPa_density_0.64/ProjectParametersDEM.json" \
    "${LOCAL_ROOT}/simulation_runs/cyclic_stress_10kPa_density_0.64/MaterialsDEM.json" \
    "${REMOTE_HOST}:${REMOTE_ROOT}/simulation_runs/cyclic_stress_10kPa_density_0.64/"

ssh "${REMOTE_HOST}" bash -s -- "${REMOTE_ROOT}" "${KRATOS_COMMIT}" <<'REMOTE'
set -euo pipefail

remote_root=$1
expected_commit=$2
kratos_root="${remote_root}/external/kratos_linux"

module load git/2.29.2

if [ ! -d "${kratos_root}/.git" ]; then
    git clone --depth 1 --branch fix-stress-calculation \
        https://github.com/KratosMultiphysics/Kratos.git "${kratos_root}"
fi

actual_commit=$(git -C "${kratos_root}" rev-parse HEAD)
if [ "${actual_commit}" != "${expected_commit}" ]; then
    echo "Unexpected Kratos commit: ${actual_commit}; expected ${expected_commit}." >&2
    exit 1
fi

echo "Kratos source is ready at ${actual_commit}."
REMOTE

echo "Deployment completed successfully."
echo "Next: ssh ${REMOTE_HOST} 'cd ${REMOTE_ROOT} && sbatch hpc/acuario/build_kratos.sbatch'"

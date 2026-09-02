#!/bin/bash

set -eu

echo "=== Acuario environment probe ==="
date
hostname
uname -a

echo "=== Operating system ==="
if [ -r /etc/os-release ]; then
    sed -n '1,12p' /etc/os-release
fi

echo "=== Slurm partitions ==="
sinfo -o '%P|%a|%l|%D|%c|%m|%G|%N'

echo "=== Slurm configuration ==="
scontrol show partition

echo "=== Environment modules ==="
if command -v module >/dev/null 2>&1; then
    module --version 2>&1 || true
    module avail 2>&1 || true
    module spider kratos 2>&1 || true
    module spider python 2>&1 || true
    module show kratos/daily 2>&1 || true
    module list 2>&1 || true
else
    echo "The module command is unavailable."
fi

echo "=== Python interpreters ==="
for executable in python3.12 python3 python; do
    if command -v "$executable" >/dev/null 2>&1; then
        command -v "$executable"
        "$executable" --version
    fi
done

echo "=== Kratos import with current environment ==="
python3 - <<'PY' 2>&1 || true
try:
    import KratosMultiphysics
    import KratosMultiphysics.DEMApplication
    from KratosMultiphysics.restart_utility import RestartUtility
except Exception as error:
    print(f"Kratos DEM import failed: {error!r}")
else:
    print(f"Kratos package: {KratosMultiphysics.__file__}")
    print("Kratos DEM and RestartUtility imports succeeded.")
PY

echo "=== Compiler and C library ==="
ldd --version 2>&1 | sed -n '1p' || true
gcc --version 2>&1 | sed -n '1p' || true

echo "=== Container runtimes ==="
for executable in apptainer singularity; do
    if command -v "$executable" >/dev/null 2>&1; then
        command -v "$executable"
        "$executable" --version
    else
        echo "$executable: unavailable"
    fi
done

echo "=== Storage quota ==="
quota -sf /dev/sdb1 2>&1 || quota -s 2>&1 || true

echo "=== Probe complete ==="

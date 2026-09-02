#!/bin/bash

set -eu

echo "=== Acuario Kratos toolchain probe ==="
date
hostname

module purge
module load gcc/10.2.0
module load python/3.12.1
module load boost/1.78.0

echo "=== Loaded modules ==="
module list 2>&1

echo "=== Module definitions ==="
module show gcc/10.2.0 2>&1
module show python/3.12.1 2>&1
module show boost/1.78.0 2>&1
module show cmake/3.13.0 2>&1

echo "=== Compiler ==="
command -v gcc
gcc --version | sed -n '1p'
command -v g++
g++ --version | sed -n '1p'

echo "=== Python ==="
command -v python3
python3 --version
python3 - <<'PY'
import sys
import sysconfig

print(f"executable={sys.executable}")
print(f"include={sysconfig.get_path('include')}")
print(f"libdir={sysconfig.get_config_var('LIBDIR')}")
print(f"ldlibrary={sysconfig.get_config_var('LDLIBRARY')}")
PY
python3 -m pip --version 2>&1 || true

echo "=== Build and transfer commands ==="
for executable in cmake make git curl wget rsync tar; do
    if command -v "$executable" >/dev/null 2>&1; then
        echo "$executable=$(command -v "$executable")"
        "$executable" --version 2>&1 | sed -n '1p' || true
    else
        echo "$executable=unavailable"
    fi
done

echo "=== GitHub connectivity ==="
if command -v timeout >/dev/null 2>&1; then
    timeout 20 git ls-remote \
        https://github.com/KratosMultiphysics/Kratos.git HEAD 2>&1 || true
else
    git ls-remote https://github.com/KratosMultiphysics/Kratos.git HEAD 2>&1 || true
fi

echo "=== User installation paths ==="
python3 -m site --user-base
python3 -m site --user-site

echo "=== Toolchain probe complete ==="

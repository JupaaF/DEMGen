#!/bin/bash
#SBATCH --job-name=demgen-smoke
#SBATCH --output=hpc/acuario/logs/smoke-%j.out
#SBATCH --error=hpc/acuario/logs/smoke-%j.err
#SBATCH --partition=R182-open
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=00:30:00

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"
mkdir -p hpc/acuario/logs
source hpc/acuario/environment.sh

export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export OMP_PROC_BIND=close
export OMP_PLACES=cores

python3 -c 'import KratosMultiphysics.DEMApplication'
python3 -c 'from KratosMultiphysics.restart_utility import RestartUtility'

/usr/bin/time -v python3 hpc/acuario/smoke_test.py


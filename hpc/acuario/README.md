# DEMGen on Acuario

This directory deploys and runs the cyclic stress-controlled case on one
`R182-open` node with OpenMP. The values below come from the Acuario probes run
on 2026-08-21, not from the website's historical partition table.

## 1. Deploy from the local workstation

From the DEMGen repository root:

```bash
./hpc/acuario/deploy.sh
```

The deployment copies the current source and the three input JSON files without
copying local results or the incompatible local Kratos binaries. It then clones
the exact Kratos source commit used by this checkout.

It also transfers the pinned NumPy 2.2.6 wheel from `hpc/acuario/wheels/`.
This is the newest CPython 3.12 wheel compatible with Acuario's glibc 2.17. The
build installs it offline because Acuario's Python module has no SSL support.
The official CMake 3.30.1 Linux archive under `hpc/acuario/tools/` is likewise
transferred and checksum-verified because `/usr/local/bin/cmake` is only
available on the login host, while the shared CMake 3.13 module is too old.
Kratos C++ tests and benchmarks are disabled in this runtime build, preventing
their optional GoogleTest/Google Benchmark downloads from compute nodes.

## 2. Build Kratos on Acuario

```bash
ssh jpfernandez@acuario.cimne.upc.edu
cd /home/jpfernandez/DEMGen
sbatch hpc/acuario/build_kratos.sbatch
```

Monitor it with:

```bash
squeue -u "$USER"
tail -f hpc/acuario/logs/build-kratos-JOB_ID.out
```

The build is successful only when its output ends with:

```text
Kratos build completed successfully.
```

## 3. Run the smoke test

```bash
sbatch hpc/acuario/smoke_test.sbatch
```

After it finishes:

```bash
sacct -j JOB_ID --format=JobID,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
tail -n 80 hpc/acuario/logs/smoke-JOB_ID.out
tail -n 80 hpc/acuario/logs/smoke-JOB_ID.err
```

Do not submit production unless the job state is `COMPLETED`, the exit code is
zero, and the output contains `Acuario smoke test completed successfully.`

## 4. Submit production

```bash
sbatch hpc/acuario/run_cyclic_stress.sbatch
```

Monitor it with:

```bash
squeue -j JOB_ID
tail -f hpc/acuario/logs/cyclic-JOB_ID.out
sstat -j JOB_ID.batch
```

The job requests one node, one Python process, 16 OpenMP threads, 48 GiB, and the
`R182-open` maximum walltime of 10 days. Checkpoint files are written under the
generated case after every stable phase. Resubmitting the production script with
the same input resumes a valid checkpoint automatically.

## Environment evidence

The Acuario probe found:

- Scientific Linux 7.2 and glibc 2.17;
- `R182-open`, 128 CPUs, approximately 512 GB, and a 10-day limit;
- GCC 10.2, Python 3.12.1, CMake 3.30.1, and Boost 1.78 paths;
- no Kratos module and no Apptainer/Singularity runtime;
- GitHub connectivity and `rsync` support.

For that reason the local Ubuntu 24.04 Kratos binary is not transferred. Kratos
is compiled from source on Acuario against its own C library and toolchain.

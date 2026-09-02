# Ejecución de DEMGen/Kratos en el HPC Acuario

## Conclusión operativa

El caso `cyclic_stress_controlled_method` debe ejecutarse como un job **OpenMP de un solo nodo** enviado a Slurm desde el nodo de acceso. El código actual lanza un solo proceso Python y usa `OMP_NUM_THREADS`; no hay en esta ruta evidencia de una ejecución MPI multinodo. Pedir varios nodos no la aceleraría sin modificar y validar primero el programa.

No es posible fijar responsablemente desde la web pública la partición ni el módulo Kratos definitivos. La página de Acuario conserva una tabla de particiones fechada explícitamente en junio de 2018, mientras que una noticia oficial de 2025 anuncia `R630-v4`, `HM`, `R182`, `R182-open`, `R640` y `R6525`. La selección final debe hacerse con `sinfo`, `scontrol` y `module avail` una vez iniciada la sesión ([Getting Started](https://hpc.cimne.upc.edu/getting-started/), [nuevos nodos y particiones, 2025](https://hpc.cimne.upc.edu/2025/02/new-nodes-available/)).

La secuencia segura es:

1. obtener o confirmar la cuenta;
2. entrar por SSH y consultar la configuración viva;
3. comprobar que Kratos y `DEMApplication` importan con el mismo Python que usará el job;
4. transferir DEMGen y el caso;
5. hacer un *smoke test* corto en una partición de desarrollo vigente;
6. medir memoria y escalado OpenMP;
7. enviar el cálculo de producción con tiempo y memoria explícitos.

## Cuenta, acceso y política del nodo de login

- Con cuenta CIMNE, el alta de Acuario se solicita mediante el [sistema de tickets de CIMNE](https://tickets.cimne.upc.edu/) o escribiendo a `cau@cimne.upc.edu`. Sin cuenta CIMNE, la documentación exige un formulario firmado por el responsable CIMNE ([solicitud de cuenta](https://hpc.cimne.upc.edu/getting-started/#h2-request-an-account)).
- El acceso documentado para GNU/Linux es `ssh -X -l USER acuario.cimne.upc.edu`. Para un flujo de consola y batch no se necesita usar aplicaciones gráficas; la parte esencial es el acceso SSH al host publicado ([acceso a Acuario](https://hpc.cimne.upc.edu/getting-started/#h2-access-to-acuario-cluster)).
- SSH es el único método de login publicado. Al entrar se llega a `hpc0`, reservado para editar, compilar, transferir, depurar brevemente y enviar jobs. La administración prohíbe ejecutar allí jobs paralelos o de producción ([Access Information](https://hpc.cimne.upc.edu/access-information/)).
- El usuario debe aceptar la AUP enlazada por CIMNE ([política de acceso](https://hpc.cimne.upc.edu/access-information/#access-policies)).

## Transferencia y almacenamiento

Acuario admite SCP, SFTP y otros métodos sobre el puerto 22; también recomienda FileZilla para transferencia gráfica ([File Transfers](https://hpc.cimne.upc.edu/access-information/#file-transfers)). Una aplicación directa es:

```bash
# Desde la máquina local; sustituir USER y el destino.
scp -r /ruta/a/DEMGen USER@acuario.cimne.upc.edu:/home/USER/
```

Conviene excluir de la transferencia resultados voluminosos que no formen parte del caso y conservar el repositorio/caso en un directorio propio, no en el nodo de login fuera de `/home` o `/shome`.

Los espacios publicados son:

- `/home`: almacenamiento personal con cuota *soft* y *hard*. El límite *soft* puede sobrepasarse hasta el *hard* durante una semana. La cuota se muestra al entrar y puede consultarse con `quota -sf /dev/sdb1`.
- `/shome`: directorios del Acuario antiguo, sin cuota publicada pero más lentos.
- `/tmp` del nodo: recomendado por CIMNE para E/S intermedia frecuente. Es local y se pierde si el nodo falla, de modo que los resultados deben copiarse de vuelta a `$SLURM_SUBMIT_DIR`. La guía ofrece un patrón con `trap` para limpiar incluso tras `scancel` ([Storage y uso de `/tmp`](https://hpc.cimne.upc.edu/getting-started/#h2-storage)).

Para este método, mover el caso entero a `/tmp` requiere cuidado: los checkpoints que deban sobrevivir a una caída deben sincronizarse periódicamente a `/home`. El checkpoint actual al final de una fase estable no protege el progreso de una fase que siga en curso cuando expire el tiempo del job.

## Slurm: comandos y límites confirmados

La guía oficial publica estos comandos:

| Acción | Comando |
|---|---|
| Enviar script | `sbatch run.sh` |
| Ver jobs en cola | `squeue` |
| Ver particiones y nodos | `sinfo` |
| Cancelar | `scancel JOB_ID` |
| Contabilidad final | `sacct` |
| Uso durante el job | `sstat` |
| Vista gráfica o de consola | `sview`, `smap` |

Fuente: [Basic Commands](https://hpc.cimne.upc.edu/getting-started/#h2-understanding-the-resource-manager-slurm).

Dos reservas deben declararse expresamente:

- **Tiempo:** Acuario recomienda dar una estimación porque permite al scheduler aprovechar huecos. Una noticia oficial de febrero de 2025 indica un límite por defecto de 10 días en la mayoría de las particiones, extensiones de hasta 5 días y solicitud especial para tiempos mayores. No asegura que todas las colas tengan ese límite ([política de 2025](https://hpc.cimne.upc.edu/2025/02/new-nodes-available/)).
- **Memoria:** el valor por defecto publicado es 1 GB por core; si el programa consume más, el job puede ser terminado. `--mem` reserva memoria total y `--mem-per-cpu` por CPU; esta última se multiplica por el número de CPUs solicitadas ([Memory resource](https://hpc.cimne.upc.edu/getting-started/#h2-understanding-the-resource-manager-slurm)).

La memoria correcta de DEMGen no está publicada ni debe adivinarse. Debe medirse en el smoke test, por ejemplo con `/usr/bin/time -v`, y reservar margen sobre `Maximum resident set size`.

### Particiones

La tabla histórica de 2018 describe particiones de producción de 10 días y sus equivalentes `*-dev` de una hora y mayor prioridad, pero no es autoridad suficiente para el estado actual. En 2025 se publicaron estas aperturas:

- `R630-v4` en `pez047`;
- `HM` y `HM-dev` en `pez048` y `pez049`;
- `R182` y `R182-open` en `pez051`;
- `R640` en `pez052`;
- `R6525` en `pez053`.

Para `R6525`, Acuario exige `#SBATCH --qos=cpu-limit32` y limita cada job a 32 CPUs; sin esa QoS el job no se ejecutará ([anuncio oficial](https://hpc.cimne.upc.edu/2025/02/new-nodes-available/)). El inventario oficial describe el equipo R6525 con dos AMD EPYC 7702 y 512 GB, pero la disponibilidad y los recursos asignables deben consultarse en vivo ([Computing Resources](https://hpc.cimne.upc.edu/computing-resources/)).

Comandos de preflight imprescindibles:

```bash
sinfo
scontrol show partition
scontrol show partition PARTITION_ELEGIDA
```

Hay que registrar de la salida real: nombre, `MaxTime`, nodos, CPUs, memoria, estado, QoS/cuenta y si la partición está autorizada para el usuario.

## Entorno Python y Kratos

Acuario usa Environment Modules. La guía documenta `module avail`, `module load`, `module list` y `module unload`, y afirma que el entorno cargado se hereda al enviar con `srun`, `sbatch` o `salloc` ([Environment in Acuario](https://hpc.cimne.upc.edu/getting-started/#h2-environment-in-acuario)).

La página muestra `kratos/daily` y `kratos-dependencies`, pero ese ejemplo aparece junto a versiones antiguas de Python, GCC y CMake; una noticia de 2018 anuncia además la retirada de varios de esos módulos. Por tanto, la web no demuestra que el módulo siga disponible ni que incluya `DEMApplication`, la API de restart usada por el método nuevo o una versión de Python compatible ([actualización oficial de módulos](https://hpc.cimne.upc.edu/2018/11/important-modules-updates/)).

Ejecutar al entrar:

```bash
module avail
module spider kratos 2>/dev/null || true
module show kratos/daily
module load kratos/daily
module list

python3 --version
python3 -c 'import KratosMultiphysics; print(KratosMultiphysics.__file__)'
python3 -c 'import KratosMultiphysics.DEMApplication; print("DEMApplication OK")'
python3 -c 'from KratosMultiphysics.restart_utility import RestartUtility; print("RestartUtility OK")'
```

Si `module show` o los imports fallan, no debe lanzarse el caso largo. Debe abrirse un [ticket de soporte CIMNE](https://tickets.cimne.upc.edu/) solicitando un Kratos que incluya `DEMApplication`, o compilar una versión compatible dentro del espacio del usuario.

La documentación oficial de Kratos requiere para compilar el core `Python3-dev`, compilador C++17, CMake y Boost, y recomienda indicar explícitamente `PYTHON_EXECUTABLE` cuando existen varias versiones de Python ([Kratos INSTALL.md](https://github.com/KratosMultiphysics/Kratos/blob/master/INSTALL.md#kratos-dependencies)). Para DEMGen también hay que incluir `DEMApplication` en la configuración de aplicaciones.

### Compatibilidad del binario incluido en este repositorio

La compilación Linux local incluida bajo `external/kratos_linux/bin/Release` no es portable por el mero hecho de copiarla. En este checkout, sus extensiones tienen etiqueta ABI `cpython-312-x86_64-linux-gnu` y fueron compiladas con GCC 13.3 en Ubuntu 24.04; necesitan bibliotecas C/C++ y OpenMP compatibles en el nodo. Esto se obtuvo directamente inspeccionando los binarios del repositorio con `file`, `ldd` y `readelf`, no de la documentación de Acuario.

Antes de intentar reutilizarla en Acuario:

```bash
python3 --version
ldd --version | head -1
gcc --version | head -1
ldd external/kratos_linux/bin/Release/libs/Kratos.cpython-312-x86_64-linux-gnu.so
```

La opción robusta es usar un módulo oficial comprobado o compilar Kratos en Acuario con sus propios módulos. Copiar el binario local sólo es aceptable si todas las comprobaciones ABI y los tres imports anteriores pasan.

## Plantilla de job propuesta

Esta plantilla usa un proceso Python y varios hilos OpenMP. `PARTITION`, `WALLTIME`, `MEMORY` y el bloque de módulos son marcadores que se deben resolver con el preflight; no son valores publicados para este caso.

```bash
#!/bin/bash
#SBATCH --job-name=demgen-cyclic
#SBATCH --output=demgen-cyclic-%j.out
#SBATCH --error=demgen-cyclic-%j.err
#SBATCH --partition=PARTITION
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=MEMORY
#SBATCH --time=WALLTIME

# Añadir solo si PARTITION=R6525:
##SBATCH --qos=cpu-limit32

set -euo pipefail

module purge
module load MODULOS_CONFIRMADOS_EN_ACUARIO

export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export OMP_PROC_BIND=close
export OMP_PLACES=cores

cd "${SLURM_SUBMIT_DIR}"

python3 -c 'import KratosMultiphysics.DEMApplication'
python3 -c 'from KratosMultiphysics.restart_utility import RestartUtility'

python3 src/DEMGen_framework_main.py \
  simulation_runs/cyclic_stress_10kPa_density_0.64/ParametersDEMGen.json
```

La guía OpenMP de Acuario usa `OMP_NUM_THREADS` y exige reservar al menos tantos recursos como hilos. La forma `--ntasks=1` + `--cpus-per-task=8` expresa de manera inequívoca el modelo de este programa; debe confirmarse con la versión de Slurm instalada antes del envío ([ejemplo OpenMP oficial](https://hpc.cimne.upc.edu/getting-started/#h2-understanding-the-resource-manager-slurm), [documentación Slurm enlazada por Acuario](https://slurm.schedmd.com/)).

El `run_omp.sh` actual del repositorio selecciona `R182-open` y `--ntasks-per-node=16`, pero deja `OMP_NUM_THREADS` comentado. Ese archivo demuestra una intención previa, no la disponibilidad actual de la cola ni una reserva correcta para esta ejecución. No debe enviarse sin actualizarlo después del preflight.

## Validación escalonada

### 1. Prueba de imports en el login

Los imports son una actividad corta adecuada para el nodo de acceso. Deben probar `KratosMultiphysics`, `DEMApplication` y `RestartUtility` con el entorno exacto del job.

### 2. Smoke test en partición de desarrollo

Enviar un caso de duración breve a la partición `*-dev` que aparezca en `sinfo`; la documentación histórica indica una hora y prioridad alta para estas colas, pero hay que confirmar el límite actual. El objetivo es verificar arranque, 10 000 partículas, control de esfuerzo, escritura del log y checkpoint.

### 3. Memoria y escalado

Medir el mismo tramo con 4, 8 y, si aporta mejora, 16 hilos. Registrar tiempo de pared y memoria. Kratos/DEMGen no garantiza que duplicar hilos duplique el rendimiento; la elección debe basarse en estas mediciones.

```bash
sacct -j JOB_ID --format=JobID,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
sstat -j JOB_ID.batch
```

### 4. Producción y reanudación

Enviar con tiempo inferior o igual al `MaxTime` real y memoria medida. Comprobar con:

```bash
squeue -j JOB_ID
scontrol show job JOB_ID
tail -f demgen-cyclic-JOB_ID.out
```

Si existe riesgo de alcanzar el walltime, se necesita una de estas dos garantías antes de producción:

- que cada fase estable termine holgadamente antes del límite y deje un checkpoint persistente; o
- checkpoint periódico y una señal previa al walltime que copie/termine limpiamente.

El límite de 10 000 ciclos de DEMGen no equivale a un límite de tiempo de Slurm. Una ejecución puede necesitar varios jobs reanudados aun cuando el algoritmo no haya agotado sus ciclos.

## Información que falta para enviar el job real

Para transformar la plantilla en un script ejecutable hacen falta salidas reales de Acuario, no nuevas suposiciones:

```bash
sinfo -o '%P %a %l %D %c %m %G'
scontrol show partition
module avail
module show kratos/daily
python3 --version
```

También hace falta saber el usuario/directorio asignado y si la cuenta tiene acceso a las particiones abiertas. Con esos datos se podrá fijar la cola, los módulos, el walltime, la memoria y el método de despliegue de Kratos sin inventar configuración.


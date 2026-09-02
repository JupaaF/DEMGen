# Método III: *cyclic stress-controlled method*

## Alcance y fuentes

Esta nota extrae los requisitos reproducibles del método III de Santos et al. y separa explícitamente los parámetros publicados de las decisiones nuevas que necesitará DEMGen. La fuente principal es la [versión final revisada por pares](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full) (Frontiers in Soft Matter, 2024, DOI 10.3389/frsfm.2023.1326756); también se consultaron el [preprint enlazado por el usuario](https://arxiv.org/pdf/2310.16114) y su fuente TeX oficial. La versión final corrige al menos un error importante del preprint, señalado más abajo.

No hay un repositorio de código ni datos enlazado por el artículo o por arXiv. La declaración oficial dice que los datos crudos serán facilitados por los autores bajo petición; el suplemento sólo amplía resultados de otros protocolos y no aporta un algoritmo ejecutable del método III ([Data availability](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#h6)).

## Especificación publicada

| Aspecto | Valor del paper |
|---|---|
| Partículas | `N = 10^4` esferas monodispersas; se generaron 6 realizaciones por combinación de presión, protocolo y fricción |
| Estado inicial | Posiciones aleatorias, fracción volumétrica inicial `phi_init = 0.05`, velocidades traslacionales y rotacionales nulas |
| Geometría | Celda tridimensional periódica; el barostato puede deformarla de forma triclínica |
| Contacto | Resorte-amortiguador-slider Hookeano; `k_n = k_s = 1`, `gamma_n = gamma_s = 0.5 tau^-1`, `tau = sqrt(m/k_n)` |
| Fricción usada en los resultados del método III | Fricción deslizante `mu_s = 0.2` |
| Paso temporal | `Delta t = 0.02 tau`; `0.002 tau` fue ensayado sin cambios estadísticamente apreciables |
| Control de celda del método III | `P_damp = 2.25 tau`, `f_drag = 0` |
| Presión alta | `P_a,0 = 10^-1 k_n/d` |
| Presiones bajas ensayadas | `P_a,f = 10^-2, 10^-3, 10^-4, 10^-5, 10^-6 k_n/d` |
| Ciclos publicados | Se muestran `1`, `10`, `100` y `1000`; la evolución de `phi` se sigue hasta 1000 ciclos |
| Tensor aplicado por defecto | `sigma_xx = sigma_yy = sigma_zz = P_a`; `sigma_xy = sigma_xz = sigma_yz = 0` |

Los datos de inicialización (`N`, monodispersidad, `phi_init`, velocidades y paso temporal) están en la [sección 2.2](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#h4). Los parámetros particulares de los resultados de los métodos III (`mu_s`, `P_damp`, `f_drag` y `P_a,0`) aparecen en el pie de la [Figura 3](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#F3); las cinco presiones bajas están en la [Figura 4](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#F4). El modelo de contacto, las escalas y la celda periódica triclínica están definidos en la [sección 2.1](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#h3).

### Tamaño inicial de la caja

El paper no da una longitud de caja porque trabaja con unidades reducidas. Para esferas monodispersas de diámetro `d`, la fracción volumétrica nominal es

```text
phi = N (pi d^3 / 6) / V_box.
```

Por tanto, para una caja cúbica inicial con `N = 10000` y `phi_init = 0.05`,

```text
L_init = d [N pi / (6 phi_init)]^(1/3)
       = 47.134930674 d
       = 94.269861348 r.
```

Esta es una consecuencia geométrica de los parámetros publicados, no una longitud tabulada por los autores. La caja sólo es cúbica al inicializarla: durante el control de esfuerzo su volumen y sus vectores deben poder evolucionar. En el caso de tensor completo usado por defecto, las tensiones de corte se relajan a cero y los ángulos finales observados fueron `90 ± 0.003 grados`, aunque el mecanismo sigue siendo triclínico ([sección 2.2, restricciones del tensor](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#h4)).

Para partículas no monodispersas, que ya sería una desviación del estudio, la forma general correcta sería `V_box = sum_i(4 pi r_i^3/3) / phi_init`.

## Secuencia exacta de un ciclo

El método III repite el método II. Su secuencia publicada es:

1. Desde el estado diluido `phi_init = 0.05`, aplicar instantáneamente la presión isotrópica alta `P_a,0` y dejar que el sistema alcance un estado atascado (*jammed*).
2. Cambiar instantáneamente la presión aplicada a `P_a,f < P_a,0` y volver a dejar que el sistema alcance un estado atascado.
3. Esto constituye `N_cycle = 1`: los autores aclaran que el primer ciclo del método III equivale al método II con `P_a,0 = 10^-1`.
4. Para cada ciclo adicional, volver a `P_a,0`, esperar de nuevo el atasco, bajar otra vez a `P_a,f` y esperar otro atasco.
5. La configuración que se compara a una densidad objetivo debe tomarse al final de la rama baja, porque allí `P_int = P_a,f`.

La definición está en la [sección 2.2](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#h4), y la equivalencia entre el primer ciclo y método II está en la [sección 3.1](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#h10). No es una onda de presión continua ni una rampa: cada cambio de consigna es instantáneo y cada una de las dos ramas debe atascarse antes de continuar.

## Presión, esfuerzo y unidades físicas

El paper utiliza unidades reducidas:

```text
tau = sqrt(m/k_n)
unidad de presión/esfuerzo = k_n/d
unidad de fuerza = k_n d.
```

En cada estado atascado, el tensor interno satisface `P_int = P_a` dentro de precisión numérica. El tensor de presión interno usado por los autores es

```text
P_int^(alpha,beta) = (1/V) sum_i [p_i^alpha p_i^beta/m + F_i^alpha r_i^beta].
```

La igualdad entre presión interna y aplicada y la definición tensorial están en la [sección 2.1](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#h3). Para replicar su restricción habitual deben controlarse las tres componentes normales de manera independiente al mismo valor y las tres de corte a cero; controlar sólo la media hidrostática es una de las alternativas que estudiaron, no su configuración por defecto.

### Correspondencia con una presión máxima de 200 kPa

La presión alta del paper es `P_a,0* = 0.1`, donde `P* = P/(k_n/d)`. Si DEMGen fija `P_a,0 = 200 kPa` y se desea semejanza adimensional exacta con el paper, necesariamente

```text
k_n/d = 200 kPa / 0.1 = 2 MPa,
k_n = (2 MPa) d.
```

Con esa calibración, las ramas bajas estudiadas equivalen a:

| `P_a,f*` | Presión física |
|---:|---:|
| `10^-2` | `20 kPa` |
| `10^-3` | `2 kPa` |
| `10^-4` | `0.2 kPa = 200 Pa` |
| `10^-5` | `0.02 kPa = 20 Pa` |
| `10^-6` | `0.002 kPa = 2 Pa` |

Si `k_n/d` viene fijado por otro modelo de material, usar 200 kPa no reproduce `P_a,0* = 0.1`; habrá que aceptar esa desviación o recalibrar la rigidez. La versión final advierte además que `p >= 0.1 k_n/d` produce solapes grandes y que el comportamiento Hookeano representa partículas rígidas sobre todo por debajo de ese umbral ([sección 2.1](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#h3)).

En el método publicado no existe un “stress objetivo” independiente de la presión baja: al terminar una rama, el esfuerzo objetivo es precisamente el tensor aplicado a esa rama. Por tanto, si la interfaz pide a la vez `target_stress` y `minimum_cycle_pressure`, debe definirse su diferencia. Para una réplica fiel, ambos representan `P_a,f`; una alternativa no publicada sería que `target_stress` significase una tolerancia de convergencia alrededor de `P_a,f`.

## Atasco y criterio de avance

El paper exige que el sistema se atasque después de aplicar **cada** presión alta y baja. Define `t_jam` mediante el punto de inflexión de la energía cinética para `t > P_damp`; ese punto coincide aproximadamente con la meseta de `phi`. Para recoger una configuración final, las simulaciones se prolongaron al menos hasta `2 t_jam`. Como ejemplo, para `P_a = 10^-4`, `f_drag = 0` y `P_damp = 2.25`, ejecutaron hasta `t/tau = 10^6`, frente a `t_jam ~ 1.5e4 tau`, porque `phi` puede seguir aumentando lentamente después de detenerse la celda ([sección 2.2, criterio de jamming](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#h4)).

Esto **no** constituye un criterio de parada online completamente implementable: el artículo no publica tolerancias de energía cinética, velocidad de la caja, error de presión ni duración de la ventana. La inflexión de energía es más fácil de identificar retrospectivamente. Una implementación deberá definir y validar tolerancias propias, por ejemplo una ventana simultánea para:

- `|P_int,ii - P_applied|` en las tres normales;
- magnitud de las componentes de corte;
- energía cinética y/o su variación;
- variación de `phi` y del volumen de la caja.

El preprint imprime `t_jam proporcional a f_drag/(P_a P_damp)`, aunque también usa `f_drag = 0` con tiempo de atasco finito. La versión final sólo conserva que el tiempo es inversamente proporcional a la presión y aumenta con el drag. Esa fórmula del preprint no debe usarse como estimador operativo sin aclaración de los autores.

## Densidad objetivo y número de ciclos

No hay una única “densidad propuesta” final. `phi_init = 0.05` es la densidad inicial publicada; la densidad final emerge de `P_a,f`, el número de ciclos y los parámetros del material. A presión baja fija, la densidad creció monótonamente con `N_cycle`, pero su asíntota depende de la presión. En la versión final, los packings de baja presión dejaron de compactar aproximadamente después de 30 ciclos, mientras los de presión alta continuaron densificándose ([conclusión](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#h15)).

Los autores ajustan la evolución con la ley KWW:

```text
phi(N) = phi_inf - (phi_inf - phi_0_fit) exp[-(N/alpha)^beta].
```

En principio, si los cuatro parámetros estuvieran calibrados para el mismo material y `P_a,f`, el número continuo estimado para una densidad alcanzable sería

```text
N_est = alpha {-ln[(phi_inf - phi_target)/(phi_inf - phi_0_fit)]}^(1/beta).
```

Sin embargo, el paper no tabula esos parámetros, sólo los representa gráficamente, y recalca que `alpha` y `beta` cambian de comportamiento alrededor de `P_a,f = 10^-4`. Por tanto, la curva KWW sirve para analizar resultados, no para predecir de forma reproducible el número de ciclos de una nueva simulación ([Figura 4 y ecuación 4](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#F4)). La estrategia robusta para DEMGen es comprobar la densidad al final de cada rama baja y seguir ciclando hasta entrar en una tolerancia definida por la aplicación.

Antes de implementar esa parada hay que fijar tres decisiones no resueltas por el paper:

1. **Definición de `phi_target`:** los autores calculan la `phi` reportada eliminando iterativamente los *rattlers*. La versión final define como *rattler* una partícula friccional con `Z_i < 4` y una sin fricción con `Z_i < 6`, y reporta entre `0.1%` y `10%` de *rattlers* ([sección 2.2](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#h4)). Para una réplica cuantitativa hay que usar esa `phi` corregida; para una densidad de ingeniería probablemente se quiera el volumen de todas las partículas, que no es la misma métrica.
2. **Tolerancia y cruce:** `phi(N)` es monotónica a `P_a,f` fija. Si el primer ciclo ya supera el objetivo, o un paso lo cruza, el método no puede reducirla selectivamente. Debe aceptarse una tolerancia/cruce o declarar el objetivo incompatible.
3. **Inalcanzabilidad:** si `phi_target > phi_inf(P_a,f)`, el sistema se estancará. El límite solicitado de `10000` ciclos es una extensión razonable de seguridad, pero no procede del paper, cuyo máximo fue `1000`. Al llegar a 10000 sin satisfacer densidad **y** convergencia de esfuerzo, se debe guardar el estado/diagnóstico y terminar explícitamente como fallo.

## Diferencias y huecos que afectan una réplica fiel

- El preprint arXiv invierte por error los umbrales de *rattlers* (`<6` para friccionales y `<4` para no friccionales). La versión publicada los corrige a `<4` y `<6`, respectivamente; debe usarse la versión final.
- El método requiere fronteras periódicas y una caja deformable en las tres direcciones, incluida la relajación de cortes. Reemplazarla por seis paredes rígidas o por una caja que sólo cambia isotrópicamente no replica exactamente el tensor controlado.
- El contacto del paper es Hookeano lineal con fricción deslizante. Un contacto Hertziano, cohesivo o con fricción de rodadura modifica la escala de presión y la curva `phi(N)`.
- No se publican semilla aleatoria, algoritmo de colocación aleatoria, tolerancias de atasco, ventanas de promedio, ajuste KWW numérico ni archivos LAMMPS. Las seis realizaciones son necesarias para reproducir las incertidumbres del artículo, aunque no para generar un único packing.
- La inicialización a `phi_init = 0.05` puede contener solapes si se colocan centros de forma completamente independiente. El artículo sólo dice “random positions” y no especifica si los evita; imponer una regla adicional podría cambiar el transitorio.
- Las Figuras 3 y 4 se iniciaron con presión y energía cinética iniciales nulas. Conservar esto importa porque el artículo demuestra que presión, energía inicial y drag cambian el packing final ([sección 3.2](https://www.frontiersin.org/journals/soft-matter/articles/10.3389/frsfm.2023.1326756/full#h11)).

### Huecos concretos frente al código Kratos actual

Esta comparación es una lectura del repositorio actual, no una afirmación de los autores:

- `create_particles_inside_of_a_domain.py` recibe tres longitudes de dominio, toma una PSD y añade partículas hasta completar un volumen objetivo (`líneas 42–78` y `162–165`). El nuevo preparador no puede reutilizar ese criterio sin adaptarlo: debe fijar exactamente `N = 10000`, imponer monodispersidad y calcular las tres longitudes desde `phi_init = 0.05`.
- El servo existente sí escribe una consigna isotrópica `[P, P, P]`, pero su convergencia se decide con el **esfuerzo normal medio** y fuerza desbalanceada sobre cinco muestras (`improved_radius_expansion_with_servo_control_method_run.py`, líneas `167–172`, `291–300` y `355–367`). El paper exige además verificar cada componente normal y llevar las tres componentes de corte a cero.
- El volumen actual se trata como el producto de tres longitudes de un *bounding box* ortogonal. No aparece en estos módulos una matriz de celda, factores de *tilt* ni un barostato Parrinello–Rahman. Antes de prometer réplica exacta debe confirmarse si la versión de Kratos incluida soporta una celda periódica triclínica deformable; si sólo mueve seis límites ortogonales, el resultado será una aproximación isotrópica del método III.
- Existe una opción periódica en el generador, incluida en el chequeo de solapes, pero hay que verificar que el movimiento servo de los límites conserva correctamente las imágenes periódicas en cada cambio de presión. La periodicidad en la colocación inicial no demuestra por sí sola periodicidad deformable durante la dinámica.
- La métrica actual de densidad se llama `MeasureTotalPackingDensityOfFinalPacking`; no se observa en este camino el filtrado iterativo de *rattlers*. Debe decidirse si se conserva la densidad nominal de Kratos o se agrega una segunda métrica comparable con las figuras del paper.

## Contrato mínimo recomendado para DEMGen

Para que una primera implementación sea trazable al paper, el caso debería registrar como mínimo:

```text
N_particles = 10000                 # fijo
initial_volume_fraction = 0.05      # paper
particle_distribution = monodisperse
boundary_condition = periodic_3d
high_pressure = 200 kPa             # requisito del usuario
low_pressure = user input           # P_a,f del paper
target_volume_fraction = user input
volume_fraction_definition = with_all_particles | without_rattlers
pressure_tolerance = explicit
volume_fraction_tolerance = explicit
jam_window = explicit
max_cycles = 10000                  # extensión del usuario
```

El estado por ciclo debe incluir, después de cada rama alta y baja, al menos `cycle`, presión aplicada, seis componentes de `P_int`, `phi` nominal, `phi` sin *rattlers*, energía cinética, volumen/vectores de caja, tiempo empleado y resultado del criterio de atasco. Esto permitirá distinguir “densidad inalcanzable” de “barostato no convergente”, algo que el simple mensaje “falló el sistema” no permitiría diagnosticar.

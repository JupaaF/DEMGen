# Packings con fracción sólida y presión/esfuerzo objetivo

## Conclusión ejecutiva

La idea es físicamente razonable y tiene un antecedente casi directo: Santos et al. generan packings DEM de esferas **friccionales y atérmicas** repitiendo compresión a una presión alta y expansión a una presión baja, dejando que el sistema vuelva a atascarse en cada rama. A presión final fija, la fracción sólida aumenta con el número de ciclos y termina saturando. Por tanto, el núcleo útil de la propuesta no necesita temperatura: es un **recocido mecánico cíclico con barostato**.

No obstante, fracción sólida `phi` y presión `p` no son, en general, dos controles independientes. Con tamaños, ley de contacto, fricción y estructura fijados, el control de volumen prescribe `phi` y hace que `p` sea una respuesta; el control de presión prescribe `p` y hace que el volumen, y por tanto `phi`, sea una respuesta. Un par (`phi_target`, `p_target`) sólo es alcanzable si existe una estructura/historia compatible. El ciclo sirve precisamente para cambiar esa estructura —y en términos de jamming, su `phi_J`— mientras el barostato fija la presión terminal.

La recomendación es separar dos bucles:

1. **Bucle interno de presión:** barostato isotrópico (idealmente celda periódica deformable con tensiones de corte llevadas a cero) hasta satisfacer presión, energía cinética y equilibrio de fuerzas.
2. **Bucle externo de estructura/densidad:** variar número de ciclos, amplitud `p_high/p_low`, duración de relajación y, si se justifica, intensidad de agitación. Evaluar `phi` siempre en un estado frío/atérmico y equilibrado a `p_target`.

No conviene que la primera implementación mezcle a la vez temperatura, presión y densidad: primero se debería establecer una línea base puramente mecánica que reproduce Santos et al.; después comparar de forma controlada una variante con agitación.

## Qué significa “calentar” y “enfriar”

Hay tres conceptos distintos que no deben mezclarse:

- **DEM atérmico:** “enfriar” significa disipar energía cinética (damping o minimización) hasta un equilibrio mecánico; “calentar” significaría inyectar velocidades aleatorias, vibración o ruido. No es temperatura termodinámica. Santos et al. excluyen explícitamente las cadenas de termostato de su barostato atérmico y muestran que la energía cinética inicial cambia la fracción sólida final ([artículo, metodología y Fig. 5](https://doi.org/10.3389/frsfm.2023.1326756)). La contribución cinética al tensor de presión debe desaparecer antes de aceptar el packing estático.
- **Sistema térmico de soft spheres/coloides:** hay un termostato real o Monte Carlo a temperatura finita; el recocido térmico permite cruzar barreras y después se hace quench a `T=0`. Schreck et al. combinan quench térmico con compresión/descompresión ([DOI 10.1103/PhysRevE.84.011305](https://doi.org/10.1103/PhysRevE.84.011305)); Ozawa et al. termalizan hard spheres con swap Monte Carlo y luego generan packings jammed sobre una amplia *J-line* ([DOI 10.21468/SciPostPhys.3.4.027](https://doi.org/10.21468/SciPostPhys.3.4.027)). Esto es muy útil conceptualmente, pero no se traslada sin más a granos macroscópicos friccionales.
- **Temperatura física del grano:** calentar cambia radios, rigidez y dimensiones del recipiente mediante expansión térmica. Se ha observado compactación de columnas bajo ciclos térmicos ([Divoux et al., DOI 10.1103/PhysRevLett.101.148303](https://doi.org/10.1103/PhysRevLett.101.148303)), y se ha simulado en DEM mediante expansión del volumen de las partículas ([Yang et al., DOI 10.1016/j.powtec.2021.11.051](https://doi.org/10.1016/j.powtec.2021.11.051)). Es un mecanismo termo-mecánico diferente y no un método publicado para imponer simultáneamente `phi` y `p`.

Para DEMGen, “temperatura granular” debería parametrizarse como energía cinética o intensidad de agitación, no en kelvin, salvo que se implemente expansión térmica y transferencia de calor.

## Interpretación solicitada: temperatura física en kelvin

Esta sección sustituye la interpretación atérmica anterior para la propuesta concreta del usuario: aquí **enfriar y calentar significan cambiar la temperatura física** de partículas y contenedor. El mecanismo no es la agitación molecular `k_B T` —irrelevante para granos macroscópicos— sino convertir una variación `ΔT` en deformación mecánica mediante expansión térmica, contacto y fricción. Es, por tanto, un **ratcheting o shakedown termo-mecánico**.

### Evidencia experimental directa

- [Chen et al., “Packing grains by thermal cycling”, *Nature* 442, 257 (2006), DOI 10.1038/442257a](https://doi.org/10.1038/442257a) usaron esferas de vidrio soda-lime de `d = 0.52 ± 0.06 mm`, `alpha_p = 9e-6 K^-1`, en cilindros de polimetilpenteno con `alpha_c = 1.17e-4 K^-1`, partiendo de `phi = 58.9 ± 0.1%` a `22 ± 1 °C`. Un único ciclo con `ΔT = 10 K` ya produjo compactación irreversible, y ciclos repetidos hasta `41 °C` o `107 °C` siguieron elevando `phi` hacia una saturación. El ajuste de doble relajación dio escalas de `2.72` y `131.79` ciclos a `41 °C`, frente a `1.74` y `57.96` ciclos a `107 °C`: mayor amplitud acelera tanto los reajustes locales como los colectivos ([artículo](https://www.nature.com/articles/442257a), [suplemento](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2F442257a/MediaObjects/41586_2006_BF442257a_MOESM1_ESM.pdf)). Intercambiar materiales —bolas plásticas en vidrio— también compactó, mientras que vidrio en vidrio produjo un efecto menor. Esto apoya como mecanismo dominante la **deformación diferencial entre granos y pared**, no el signo concreto de la diferencia.
- [Divoux, Gayvallet y Géminard, “Creep Motion of a Granular Pile Induced by Thermal Cycling”, *PRL* 101, 148303 (2008), DOI 10.1103/PhysRevLett.101.148303](https://doi.org/10.1103/PhysRevLett.101.148303) observaron una columna de bolas de vidrio de `d = 510 ± 90 µm` en un tubo de vidrio de diámetro interior `13 mm`, con ciclos de `600 s` y `0 < ΔT <= 27.1 K`. Para `ΔT` mayor que aproximadamente `3 K`, la columna se asentó en **cada rama de enfriamiento**; tras 1000 ciclos perdió cerca de `1.5 cm`, alrededor del `1%` de una altura de `140 cm`. Por debajo de `ΔT_c ≈ 3 K`, la compactación pasó a ser intermitente, con colapsos separados por tiempos exponencialmente distribuidos. Como `alpha_p = 9e-6 K^-1` y `alpha_c = 3.6e-6 K^-1` no diferían tanto como en Chen, los autores propusieron otro mecanismo: el gradiente térmico radial genera cizalla cíclica. Estimaron desplazamientos relativos de `0.4–10 nm/K` y una rugosidad de unos `100 nm`, coherente con un umbral finito. El período fue elegido para que la longitud de penetración térmica, unos `6 mm`, fuese comparable al radio del tubo ([preprint primario](https://arxiv.org/abs/0806.1458)).
- [Pan, Gong y Rotta Loria, “Thermal shakedown in granular materials with irregular particle shapes”, *Scientific Reports* 14 (2024), DOI 10.1038/s41598-024-57503-2](https://doi.org/10.1038/s41598-024-57503-2) es especialmente relevante para la combinación de densidad alta y estrés impuesto. Ensayaron arenas secas sueltas (`D_R = 27.5 ± 2.5%`) y densas (`D_R = 80 ± 2.5%`) en un edómetro, aplicando 50 ciclos de `ΔT = 30, 45` o `60 K` a estrés vertical constante de `60, 250` o `500 kPa`. Cada ciclo dejó una contracción irreversible, decreciente con el número de ciclos, tanto en material suelto como denso: un *thermal shakedown* hacia una densidad terminal. Para `ΔT = 60 K`, la contracción tras 50 ciclos fue entre aproximadamente la mitad y el mismo orden que la causada por cargar monotónicamente hasta `1 MPa`. La amplitud, presión, densidad inicial y forma de partícula cambiaron la magnitud. Es evidencia de que la idea puede funcionar incluso desde un packing denso y bajo carga controlada, aunque el control fue uniaxial, no del tensor completo.

### Mecanismos y por qué el orden de las fases importa

Para una partícula isotrópica y una dimensión característica del contenedor,

```text
R_i(T_i) = R_i,ref [1 + alpha_p,i (T_i - T_ref)]
L_c(T_c) = L_c,ref [1 + alpha_c   (T_c - T_ref)]
```

La deformación térmica relativa que realmente moviliza contactos es, en primera aproximación, `(alpha_p - alpha_c) ΔT`, más cualquier deformación debida a gradientes de temperatura. El ciclo sólo cambia permanentemente el packing si esa deformación provoca apertura/cierre de contactos, deslizamiento de Coulomb, rotación, caída gravitatoria o convección. Una expansión y contracción perfectamente homogénea, afín y reversible no compactaría.

Hay dos regímenes de signo opuesto:

1. **Las partículas se expanden más que la celda, o la celda se mantiene fija.** Calentar aumenta solapes y presión, moviliza fricción y puede reordenar; enfriar descarga y abre espacio. En este caso la secuencia propuesta —enfriar, precomprimir en frío, calentar bajo volumen aproximadamente fijo y descomprimir— es sensata.
2. **El contenedor se expande más que las partículas**, como en el experimento principal de Chen y en el DEM de Iliev et al. Calentar abre espacio junto a las paredes y permite asentamiento; enfriar encoge la pared, eleva la presión y produce cizalla. Aquí conviene **calentar primero a baja carga y comprimir durante el enfriamiento**. Empezar siempre por enfriar usaría la rama menos favorable.

Por ello, la regla general no debe ser un orden fijo sino identificar experimentalmente el signo de `d p/dT` a volumen de celda fijo. La rama que eleva el estrés es la rama de carga termo-mecánica; la opuesta es la de descarga y creación de huecos.

Tampoco conviene calentar y descomprimir simultáneamente con un barostato rápido: el cambio de volumen de la celda puede cancelar precisamente la deformación térmica que debía reorganizar los contactos. Es mejor separar la rampa térmica, el *hold* de relajación y la corrección de presión.

### Protocolo cerrado en temperatura y presión

Antes de generar packings debe fijarse una temperatura de aceptación `T_ref`. Un packing no “tiene” una única presión independiente de la temperatura: si se acepta caliente, al enfriarlo cambia el tamaño de grano, el volumen y el estrés. Una iteración robusta sería:

1. Equilibrar el candidato en `(T_ref, p_target)` y registrar `phi_ref`, siempre calculada con los volúmenes de partícula a `T_ref`.
2. Descargar a `p_low` y llevar el sistema al extremo térmico que **abre contactos**; mantener hasta equilibrio térmico y mecánico.
3. Precomprimir a `p_high` en ese extremo térmico y relajar.
4. Recorrer la rama térmica que **carga contactos** con volumen fijo, o con un barostato deliberadamente lento/limitado, hasta que haya deslizamiento y reordenamiento sin superar el estrés de daño `p_safe`.
5. Mantener la temperatura extrema hasta que cesen la conducción transitoria, la energía cinética y la deriva de volumen/contactos.
6. Descargar a `p_low` o directamente cerca de `p_target`; volver a `T_ref` y dejar que se relajen los contactos.
7. Aplicar el barostato isotrópico a `p_target` a `T_ref`; sólo aquí comprobar tolerancias de `phi`, tensor de estrés, energía cinética, coordinación, fabric y fuerzas desbalanceadas.
8. Adaptar `ΔT`, `p_high`, `p_low` y número de ciclos. Detener si `phi_ref` entra en meseta o si la presión máxima, el orden cristalino, la segregación o el daño superan límites.

Para el caso específico `alpha_p > alpha_c`, los pasos 2–6 se leen como **enfriar → comprimir en frío → calentar con celda retenida → relajar → descomprimir → volver a `T_ref`**. Si `alpha_c > alpha_p`, se invierten las ramas caliente/fría. Esta precisión es la principal corrección a la secuencia original.

El trabajo de [Iliev et al., “Behavior of confined granular beds under cyclic thermal loading”, *Granular Matter* 21, 59 (2019), DOI 10.1007/s10035-019-0914-6](https://doi.org/10.1007/s10035-019-0914-6) muestra por qué son necesarios los *holds*: su ciclo DEM fue rampa lineal `T_0 → T_1`, relajación isoterma, rampa `T_1 → T_0` y una segunda relajación. Con `2000` poliedros, `alpha_p = 1e-4`, `alpha_c = 1e-3` y `ΔT = 100` en sus unidades, el calentamiento abrió huecos cerca de las paredes y el enfriamiento construyó cadenas de fuerza laterales. Aparecieron células convectivas toroidales; densidad y picos de presión crecieron al principio y saturaron juntos. Una conicidad de sólo `6°` redujo aproximadamente a la mitad el pico de presión frente al cilindro, mostrando que la geometría de pared no es un detalle menor.

### Magnitudes y grupos adimensionales que conviene barrer

- **Deformación térmica:** `Theta_p = alpha_p ΔT`, `Theta_c = alpha_c ΔT` y `Theta_diff = |alpha_p-alpha_c| ΔT`. En Chen, para `22 → 107 °C`, `Theta_p ≈ 7.7e-4` y `Theta_c ≈ 9.9e-3`: deformaciones pequeñas en términos absolutos pero grandes frente a holguras y solapes de contacto.
- **Desplazamiento de pared respecto al grano:** `G = Theta_diff L/d`, donde `L` es radio o ancho de celda. `G` captura el efecto de tamaño que no aparece mirando sólo `alpha ΔT`.
- **Carga térmica frente al solape elástico:** `Chi = Theta_eff/(delta/d)`. Para Hertz, como orden de magnitud `delta/d ~ (p/E*)^(2/3)`; para resorte lineal, `delta/d ~ p d/k_n`. Si `Chi << 1`, pocos contactos cambian; si `Chi` es del orden de uno, se reconstruye la red; si es demasiado grande, aparecen fuerzas no físicas en soft-sphere DEM o riesgo real de rotura.
- **Desplazamiento frente a rugosidad:** `A = Δu_rel/s`, con `s` la altura de asperidades. El cambio de dinámica alrededor de `ΔT_c ≈ 3 K` de Divoux es coherente con cruzar `A ~ 1`.
- **Cuasiestaticidad mecánica:** usar un número inercial térmico `I_T = |dot(epsilon_T)| d sqrt(rho/p) << 1` y comprobar energía cinética. La rampa no debe convertir el ensayo térmico en un impacto numérico.
- **Homogeneidad térmica:** `Fo = a_eff t_half/L^2`. `Fo >> 1` aproxima temperatura uniforme; `Fo` del orden de uno o menor produce gradientes que pueden ser el mecanismo de cizalla, como en Divoux. A escala de partícula, un `Bi = h d/k_p << 1` justifica asignar una sola temperatura a cada grano.
- **Margen de seguridad:** comparar el pico `p_max` y las fuerzas máximas con rotura, fluencia y deformación admisible del material. La expansión impedida puede multiplicar mucho el estrés aun para decenas de kelvin.

### Implementación DEM termo-mecánica mínima

El precedente numérico más cercano solicitado es [Yang et al., “DEM simulation of cyclic thermal consolidation tests considering the effects of relative density and temperature magnitude”, *Powder Technology* 397, 117007 (2022), DOI 10.1016/j.powtec.2021.11.051](https://doi.org/10.1016/j.powtec.2021.11.051). Usaron PFC2D con contactos lineales y un **método de expansión volumétrica de partícula**, sin resolver transferencia térmica entre partículas. Los ciclos acumularon contracción volumétrica y elevaron el nivel de estrés; cambiaron coordinación y anisotropía de contactos/fuerzas. Para densidades relativas iniciales `D_r = 0.2, 0.4, 0.6, 0.8`, los cocientes de huecos tendieron a converger tras aproximadamente `100` ciclos. Es una demostración útil del ratcheting, pero su temperatura es un campo prescrito y homogéneo: numéricamente modela deformación térmica, no el tiempo físico de calentamiento.

Como validación adicional, [Wu et al., “A simple discrete-element model for numerical studying the dynamic thermal response of granular materials”, *Materials Research Express* 8, 115502 (2021), DOI 10.1088/2053-1591/ac34b8](https://doi.org/10.1088/2053-1591/ac34b8) aplicaron en PFC2D `4000` ciclos entre `-20` y `60 °C`, con carga vertical constante de `1 MPa` y paredes laterales fijas. Obtuvieron acumulación irreversible de deformación volumétrica y evolución de la presión lateral y la red de contactos. Esto se aproxima bastante a un bucle de estrés impuesto en una dirección.

Para una primera versión de DEMGen bastaría:

```text
T(t) prescrito
R_i(T) = R_i,ref [1 + alpha_i (T-T_ref)]
contacto normal + contacto tangencial histórico + Coulomb
pared/celda con alpha_c independiente
barostato activable por fases, con límites p_low/p_high/p_safe
```

Después se puede resolver la temperatura individual de cada grano,

```text
m_i c_p,i dT_i/dt = sum_j H_ij (T_j-T_i) + Q_conv,i + Q_rad,i,
```

y actualizar también `E(T)`, `nu(T)`, `mu(T)`, conductancia de contacto y expansión de la celda. La fricción tangencial debe conservar correctamente su historia cuando cambia el radio. Si todos los radios y una celda periódica escalan exactamente con el mismo `alpha` y `T` uniforme, el movimiento es puramente afín: esa prueba debe dar **cero compactación irreversible** y sirve como test de consistencia.

[Vargas y McCarthy, “Thermal expansion effects and heat conduction in granular materials”, *PRE* 76, 041301 (2007), DOI 10.1103/PhysRevE.76.041301](https://doi.org/10.1103/PhysRevE.76.041301) ya mostraron en DEM 2D que calentar `50` o `100 K` dentro de paredes fijas eleva significativamente las fuerzas medias, mientras una pared móvil cambia la respuesta; el ciclo completo también compacta. Su contraste entre contorno fijo y móvil confirma que el barostato y la ley térmica de la pared forman parte del protocolo físico, no sólo del control numérico.

### Límites y criterio de novedad

- La literatura demuestra compactación termo-cíclica y control de una componente de estrés, pero no encontré un método publicado que garantice un par arbitrario `(phi_target, sigma_target)` mediante feedback simultáneo de `ΔT` y presión. Ahí sí puede estar la novedad.
- La compactación es normalmente direccional y saturante. No sirve para descompactar si se sobrepasa `phi_target`, y un packing inicialmente muy denso puede tener una ventana de cambio pequeña.
- Un barostato isotrópico ideal y rápido puede eliminar el estímulo térmico; un contenedor explícito introduce, en cambio, efectos de pared, gravedad, Janssen y convección. El resultado no se transfiere automáticamente entre ambos.
- `phi` debe compararse siempre a la misma `T_ref`; de otro modo se confunde dilatación reversible del sólido con cambio irreversible de estructura. Del mismo modo, el estrés objetivo se debe aceptar a `T_ref`, no en el extremo caliente.
- `alpha`, módulo elástico, fricción, amortiguamiento y conductividad dependen de `T`; ignorarlo sólo es defendible en una ventana térmica calibrada. Humedad, expansión del fluido intersticial, cohesión, oxidación o cambio de fase añaden mecanismos que estos modelos secos no contienen.
- Los ciclos pueden causar picos de estrés, trituración, desgaste de asperidades, segregación o cristalización. Deben monitorizarse presión máxima, distribución de fuerzas, coordinación, fabric, orden, rotura y no sólo densidad media.

En síntesis: **sí, la versión en kelvin tiene soporte experimental y DEM directo**. La secuencia propuesta es buena cuando la expansión de partícula domina a la de la celda, pero debe invertirse cuando domina la expansión del contenedor. La arquitectura más limpia es un ciclo térmico con ramas de barostato deliberadamente activadas/desactivadas y una aceptación final obligatoria en `(T_ref, p_target)`; `ΔT` actúa como control de estructura y el barostato final como control de estrés.

## Literatura primaria más relevante

| Fuente | Sistema y control | Hallazgo relevante | Relación con la propuesta |
|---|---|---|---|
| [Santos et al., *Frontiers in Soft Matter* 3, 1326756 (2024)](https://doi.org/10.3389/frsfm.2023.1326756) | DEM 3D, esferas monodispersas con fricción deslizante, atérmico; celda periódica triclínica y tensor de estrés controlado | El método III alterna `p_high=10^-1 k_n/d` y `p_low=10^-2...10^-6 k_n/d`, re-atascando en cada rama. A `p_low` fija, `phi` aumenta monótonamente con ciclos y satura; la respuesta depende de presión, fricción, drag y energía inicial. | Es el antecedente casi exacto del ciclo compresión–descompresión. No incluye calentamiento/enfriamiento termostático. También prueba que el mismo estrés puede admitir distintas densidades según el protocolo. |
| [Farhadi, Zhu y Behringer, *PRL* 115, 188001 (2015)](https://doi.org/10.1103/PhysRevLett.115.188001) | Experimento granular cuasi-2D, discos bidispersos o elipses, ciclos de compresión entre estados jammed/unjammed | La presión y la estructura evolucionan entre estados jammed sucesivos; la presión puede relajarse lentamente y aparece una escala de relajación dependiente de `phi`. | Evidencia experimental de que el ciclo reorganiza la red y de que no basta con cruzar una presión: hay que esperar relajación y comprobar memoria/estacionariedad. |
| [Kumar y Luding, *Granular Matter* 18, 58 (2016)](https://doi.org/10.1007/s10035-016-0624-2) | DEM 3D de soft spheres sin fricción sometidas a ciclos de (sobre)compresión isotrópica | Los ciclos elevan lentamente la densidad de jamming efectiva; el trabajo propone `phi_J` como variable interna que almacena la memoria de la deformación. | Es la formulación más directa del ciclo exterior como recocido que mueve `phi_J`, que es el grado adicional necesario para aproximar simultáneamente `phi_target` y `p_target`. |
| [Matsuyama et al., *EPJ E* 44, 133 (2021)](https://doi.org/10.1140/epje/s10189-021-00142-6) | Mezcla 2D de partículas armónicas, entrenamiento por compresión cuasiestática y cizalla oscilatoria | El entrenamiento mecánico modifica la geometría a ambos lados del jamming. | Apoya tratar los ciclos como recocido/entrenamiento mecánico, aunque no busca el par `phi,p` ni usa fricción. |
| [Dagois-Bohy et al., *PRL* 109, 095703 (2012)](https://doi.org/10.1103/PhysRevLett.109.095703) | Soft disks sin fricción, atérmicos; presión y forma de celda variables | Packings creados sólo por compresión en caja fija pueden ser inestables al corte cerca de jamming; relajar la forma de celda produce packings con módulo de corte positivo. | El criterio final no debe limitarse a presión media y densidad: hay que relajar/medir tensiones de corte y estabilidad mecánica. |
| [Smith et al., *PRE* 89, 042203 (2014)](https://doi.org/10.1103/PhysRevE.89.042203) | Granos blandos no esféricos, sin fricción y atérmicos; método de celda variable bajo estrés | Introduce un método basado en entalpía y grados globales de la celda para jamming hidrostático a estrés controlado. | Base formal para el bucle interno de estrés y para una celda periódica deformable. |
| [Zheng, Zhang y Xu, *Chinese Physics B* 27, 066102 (2018)](https://doi.org/10.1088/1674-1056/27/6/066102) | Discos bidispersos sin fricción, `T=0`; minimización FIRE de `H=U+pV` | Obtiene sólidos jammed directamente a la presión deseada; el volumen se optimiza junto con las posiciones. | Es la alternativa limpia a un servo dinámico para potenciales conservativos. No se aplica directamente a fricción de Coulomb dependiente de la historia. |
| [O'Hern et al., *PRE* 68, 011306 (2003)](https://doi.org/10.1103/PhysRevE.68.011306) | Soft spheres/disks sin fricción, `T=0`, estrés aplicado cero; compresión/descompresión con minimización | Cada configuración tiene un umbral `phi_c`; cerca de jamming la presión desaparece con una ley dependiente del potencial. | Explica por qué `phi` y `p` están acopladas dentro de una familia de packings y proporciona el protocolo base de búsqueda por compresión/descompresión. |
| [Goodrich, Liu y Sethna, *PNAS* 113, 9745 (2016)](https://doi.org/10.1073/pnas.1601858113) | Soft spheres sin fricción, `T=0`; ajuste iterativo de `phi` hasta presión objetivo | Generan packings ajustando sistemáticamente la fracción sólida hasta alcanzar `p_target` con 1% de precisión y formalizan el escalado entre exceso de densidad y presión. | Buen patrón numérico para el bucle interno en sistemas sin fricción, pero deja `phi` como resultado de `p_target` y del `phi_J` de la muestra. |
| [Chaudhuri, Berthier y Sastry, *PRL* 104, 165701 (2010)](https://doi.org/10.1103/PhysRevLett.104.165701) | Esferas 3D amorfas sin fricción; varios protocolos de equilibración/compresión | Demuestra una gama continua de densidades de jamming dependiente del protocolo, aun sin cristalización. | Justifica que un bucle externo que cambia historia/recocido pueda mover `phi_J`; también descarta la idea de una densidad jammed universal. |
| [Schreck, O'Hern y Silbert, *PRE* 84, 011305 (2011)](https://doi.org/10.1103/PhysRevE.84.011305) | Discos bidispersos sin fricción; quench térmico a distintas velocidades seguido de compresión/descompresión incremental | Genera más de `10^4` packings sobre un intervalo de `phi_J`; la velocidad de enfriamiento y el estado inicial alteran estructura y densidad. | Es la referencia más cercana a combinar enfriamiento con compresión/descompresión, pero el objetivo es jamming onset y no una presión finita prescrita. |
| [Ozawa, Berthier y Coslovich, *SciPost Physics* 3, 027 (2017)](https://doi.org/10.21468/SciPostPhys.3.4.027) | Hard spheres polidispersas 3D sin fricción; termalización eficiente y posterior jamming | Amplía considerablemente el rango de densidades críticas accesibles; el orden heredado del fluido cambia con el recocido. | Confirma que el recocido térmico es potente para seleccionar `phi_J` en modelos térmicos/frictionless, no necesariamente en DEM granular. |
| [Santos et al., *PRE* 102, 032903 (2020)](https://doi.org/10.1103/PhysRevE.102.032903) | DEM 3D friccional bajo presión controlada; fricción deslizante, rodante y torsional | Con rolling/twisting friction se obtienen estados estables mucho más sueltos (`phi` hasta aproximadamente 0.53) que con sólo sliding friction. | Advierte que la región alcanzable en (`phi,p`) depende fuertemente del modelo de contacto; el controlador no puede compensar una física de contacto incorrecta. |
| [Silbert, *Soft Matter* 6, 2918 (2010)](https://doi.org/10.1039/C001973A) | Soft spheres 3D friccionales; compresión y descompresión hacia jamming para varias fricciones | `phi_J` disminuye desde el límite tipo random-close-packing hacia packings más sueltos al aumentar la fricción, y conserva dependencia del protocolo. | Refuerza que el caso friccional tiene un dominio de densidades y una memoria mucho mayores que el frictionless; una calibración no puede transferirse entre coeficientes/modelos de fricción. |

## Evaluación del ciclo propuesto

### Lo que sí debería funcionar

- La compresión por encima del estado final puede romper/reconstruir contactos; la expansión posterior a `p_target` permite comparar densidades al mismo estrés.
- La agitación controlada durante alguna rama puede ayudar a superar barreras y reordenar, como ocurre en recocido térmico, tapping o entrenamiento mecánico.
- En partículas friccionales hay más historia y más rango de `phi` accesible que en las frictionless; por ello el método parece especialmente prometedor para el modelo DEM de DEMGen.

### Riesgos y límites

- **No hay garantía de alcanzabilidad.** Para soft spheres armónicas cerca de jamming, aproximadamente `p ~ phi - phi_J`; con otras leyes cambia el exponente. Fijar `p_target` y `phi_target` equivale a pedir una `phi_J` efectiva concreta. El protocolo sólo puede recorrer un intervalo finito de `phi_J`.
- **El ciclo puede compactar sólo en una dirección y saturar.** En Santos et al., `phi` crece con el número de ciclos a presión baja fija y alcanza una asíntota. Si se sobrepasa el objetivo, repetir el mismo ciclo no lo corrige.
- **“Calentar” añade presión cinética.** Si se mide el estrés durante la fase agitada, el virial incluye un término cinético y puede producir un falso cumplimiento. La aceptación debe hacerse tras quench y relajación.
- **Fricción implica memoria.** Minimizar `U+pV` es adecuado para contactos conservativos frictionless, pero no representa correctamente el desplazamiento tangencial acumulado y el deslizamiento de Coulomb. Para el modelo friccional hace falta dinámica DEM/barostato y guardar la historia de contactos.
- **Densidad no caracteriza por sí sola el estado.** Dos packings con iguales `phi` y `p` pueden diferir en coordinación, fabric, fracción de contactos movilizados, módulo de corte y anisotropía. Santos et al. muestran incluso packings con igual densidad y aproximadamente un contacto medio por partícula de diferencia.
- **Cristalización/segregación.** Demasiado calentamiento, ciclos lentos o monodispersidad pueden aumentar orden cristalino. Se deben monitorizar al menos coordinación, fabric y un parámetro de orden, además de `phi`.

## Protocolo experimental recomendado para DEMGen

Una prueba mínima, comparable con la literatura, sería:

1. Partir de varias semillas del mismo packing denso y apagar cualquier agitación.
2. Llevar la celda a `p_high` con barostato isotrópico.
3. Mantener hasta cumplir simultáneamente: error de las tres tensiones normales, tensiones de corte, energía cinética, fuerza desbalanceada y deriva de volumen.
4. Bajar a `p_target` —o primero a `p_low` y luego a `p_target`— y volver a equilibrar.
5. Medir `phi`, coordinación, rattlers, fabric, contactos movilizados y orden sólo en el estado frío equilibrado a `p_target`.
6. Repetir si `phi` sigue avanzando hacia el objetivo; detener como inalcanzable si la mejora por ciclo entra en meseta.
7. Después de validar esa línea base, introducir una única amplitud de agitación entre las ramas y hacer una comparación A/B con idénticas semillas.

El controlador externo no debería asumir monotonicidad global. Conviene construir primero mapas empíricos

```text
phi_final = f(p_high, p_low, ciclos, agitacion, friccion, semilla)
```

a `p_target` fijo. Un barrido corto de diseño de experimentos permite estimar el dominio alcanzable antes de diseñar un feedback. Si el comportamiento local sí resulta monótono, se puede ajustar amplitud o número de ciclos por bisección; si hay histéresis o múltiples ramas, es más seguro conservar candidatos y seleccionar el que minimice una función multiobjetivo, por ejemplo error de densidad, error tensorial de estrés, anisotropía y orden cristalino.

## Respuesta corta a la pregunta original

Sí: la parte de comprimir, dejar reordenar y descomprimir iterativamente tiene soporte directo y, para partículas friccionales, Santos et al. (2024) es la referencia central. Añadir enfriamiento/calefacción también tiene precedentes, pero bajo dos significados distintos: quench térmico en modelos frictionless y expansión térmica real en lechos granulares. Para un generador DEM atérmico, empezaría sin “temperatura”, usando disipación completa en los extremos del ciclo; sólo después probaría agitación cinética como un parámetro de recocido y siempre evaluaría `phi` y estrés tras volver a `T_granular≈0`.

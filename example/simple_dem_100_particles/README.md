# Empaquetamiento DEM simple de 100 partículas

Este ejemplo genera 100 discos de radio polidisperso dentro de la caja cuadrada
`[0, 1] x [0, 1]`. Parte de una distribución aleatoria uniforme (sin retícula)
y usa una relajación DEM cuasiestática con crecimiento gradual de radio y
paredes rígidas. La polidispersidad y el muestreo aleatorio evitan una
disposición cristalina, sin crear huecos grandes.

Ejecutar desde la raíz del repositorio:

```bash
python example/simple_dem_100_particles/generate_packing.py
```

El resultado se guarda en `particles_100_square.csv`, con las columnas
`particle_id`, `x`, `y` y `radius`. La fracción de área ocupada es
aproximadamente 0.750, por lo que el empaquetamiento es denso y no tiene
solapes.

Para crear otro packing sin sobrescribir el que usa la presentación, indica
una semilla y un archivo distintos:

```bash
python example/simple_dem_100_particles/generate_packing.py \
  --seed 20260818 \
  --output example/simple_dem_100_particles/particles_100_square_seed_20260818.csv
```

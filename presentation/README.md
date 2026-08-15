# Presentación Académica DEMGen (Manim Slides)

Esta presentación ha sido desarrollada en **Manim Slides** para congresos académicos y seminarios de investigación, basada fielmente en los bocetos de [`Presentacion.pdf`](../Presentacion.pdf).

---

## 🎨 Especificaciones de Diseño y Estilo

- **Fondo**: Negro puro (`#000000`) para alto contraste y elegancia en salas de conferencias.
- **Tipografía**: **Latin Modern Sans / AMS-LaTeX**, la tipografía académica estándar de publicaciones científicas y fórmulas matemáticas.
- **Jerarquía de Color**:
  - **Texto Principal**: Blanco puro (`#FFFFFF`).
  - **Texto Secundario**: Plata pizarra (`#94A3B8`).
  - **Acentos Académicos** (partículas y palabras clave del boceto): Dorado ámbar (`#FBBF24` / `#F59E0B`).
  - **Anotaciones y Flechas de Medición**: Rojo coral académico (`#F87171` / `#EF4444`).
  - **Contenedores DEM**: Estructura alámbrica isométrica con sombreado de suelo sutil.

---

## 📊 Estructura de Diapositivas

1. **Diapositiva 1: Portada (Página 1)**
   - Encabezado: *Mobility to Utrecht:*
   - Título: *How does **DemGen** work?*
   - Ponente: *Fernandez, Juan Pablo*
   - Fechas: *01/08/26 -- 31/08/26*
   - Subtítulo descriptor: *DEMGen · Particle Packing Generator for DEM*

2. **Diapositivas 2 a 6: Outline / Temario (Páginas 2 a 6 - Revelado Progresivo)**
   - Encabezado: *Outline:* con doble subrayado dorado.
   - **①** *What is **DemGen**?*
   - **②** *What **methods** does **DemGen** use?*
   - **③** *Deep dive: **IRESC***
   - **④** *New method: **tapping***
   - **⑤** *Conclusions and future **improvements***

3. **Diapositiva 7: Sección 1 - El Problema (Página 7)**
   - Título: *① What is **DemGen**: the problem*
   - **Visualización 3D Isométrica**: Dos empaquetamientos de partículas esféricas DEM en lechos periódicos tridimensionales.
   - **Variables Microestructurales vs Macroscópicas**:
     - Empaquetamiento Izquierdo: $\mathrm{MCN} = 5$, $\alpha = 0.62$, $\sigma = 60\,\mathrm{kPa}$, $k = ?\,\frac{\mathrm{W}}{\mathrm{m}\cdot\mathrm{K}}$
     - Empaquetamiento Derecho: $\mathrm{MCN} = 5$, $\alpha = 0.62$, $\sigma = 50\,\mathrm{kPa}$, $k = ?\,\frac{\mathrm{W}}{\mathrm{m}\cdot\mathrm{K}}$
   - **Mensaje Central / Conclusión**:
     > *"Two **packings** with similar **microstructure** variables can behave **differently**"*

---

## 🚀 Cómo Ejecutar y Presentar

### Opción 1: Script Automático (Recomendado)

Desde la carpeta `presentation/`:
```bash
./render.sh m    # Calidad media (720p)
# o
./render.sh h    # Alta calidad (1080p)
```

### Opción 2: Modo Interactivo en Vivo con Manim Slides

1. Renderizar la escena de presentación:
   ```bash
   manim -qm presentation.py Presentation
   ```
2. Iniciar el visor interactivo de diapositivas:
   ```bash
   manim-slides present Presentation
   ```

#### Controles del Presentador en Vivo:
- **Espacio / Flecha Derecha**: Avanzar a la siguiente diapositiva / animación.
- **Flecha Izquierda**: Retroceder a la diapositiva anterior.
- **F**: Pantalla completa (Fullscreen).
- **R**: Reiniciar la diapositiva actual.
- **Q / Esc**: Salir de la presentación.

### Opción 3: Presentación HTML en Navegador Web

Ya se encuentra generado el archivo interactivo `presentation_slides.html`. Puedes abrirlo en cualquier navegador:
```bash
xdg-open presentation_slides.html   # en Linux
# o
open presentation_slides.html       # en macOS
```

O regenerarlo cuando desees con:
```bash
manim-slides convert Presentation presentation_slides.html
```

---

## 📁 Archivos Incluidos

- [`presentation.py`](presentation.py): Código fuente completo con todas las escenas y clases modulares (`Presentation`, `TitleSlideScene`, `OutlineSlideScene`, `ProblemSlideScene`).
- [`presentation_slides.html`](presentation_slides.html): Presentación autónoma para navegador.
- [`render.sh`](render.sh): Script ejecutable para compilar y convertir en un solo comando.

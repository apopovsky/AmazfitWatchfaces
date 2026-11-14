# Guía de Desarrollo de Watchfaces para Amazfit T-Rex 3 Pro (Zepp OS)

Guía técnica y compendio de lecciones aprendidas durante el desarrollo de la serie **TR3X** (`wf-tactical-amber`, `wf-minimal-grid`, `wf-dual-lavender`).

---

## 1. Estructura y Manifiesto (`app.json` v3)

* **Target de compilación**: `Amazfit T-Rex 3 Pro (48mm)` (`rocky`, `designWidth: 480`).
* **Flags críticos en `targets.rocky.module.watchface`**:
  ```json
  "watchface": {
    "path": "watchface/index",
    "main": 1,
    "editable": 1,
    "lockscreen": 1
  }
  ```
  * `"editable": 1`: **Imprescindible**. Habilita el soporte de pulsación prolongada en el reloj para acceder al menú de edición.
  * `"lockscreen": 1`: Activa el soporte para la pantalla de bloqueo y modo AOD (Always-On Display).
* **Rutas en Zepp OS v3**:
  * Archivos físicos: `assets/rocky/...`
  * Referencias en código JS o manifiesto: **sin** prefijo `assets/rocky/` (ej: `'bg_amber.png'`).

---

## 2. Editor en Pantalla y Ciclo de Vida

1. **`WATCHFACE_EDIT_GROUP` vs `WATCHFACE_EDIT_MASK`**:
   * `WATCHFACE_EDIT_MASK`: Asignar `show_level: SL.ONLY_EDIT`.
   * `WATCHFACE_EDIT_GROUP`: **NUNCA asignar `show_level: SL.ONLY_EDIT`**. Si se marca `ONLY_EDIT`, el firmware omite su inicialización en modo normal y `getProperty(PROP.CURRENT_TYPE)` devuelve `undefined`.
   * Los IDs de `optional_types` deben ser `>= 100000`.
2. **Detección del retorno del editor (`WIDGET_DELEGATE`)**:
   * Al guardar cambios y salir del editor, **`build()` no vuelve a ejecutarse**.
   * Debe usarse `W.WIDGET_DELEGATE` para recibir `resume_call` y aplicar la paleta/estilo inmediatamente:
     ```javascript
     ui.createWidget(W.WIDGET_DELEGATE, {
       resume_call: refreshAll,
     })
     ```
   * En el listener de `timeSensor.onPerMinute`, reevaluar las opciones seleccionadas como salvaguarda secundaria.

---

## 3. Sensores, Datos y UI

1. **Excepción de RHR (Resting Heart Rate)**:
   * No existe `data_type` del sistema para RHR en widgets `TEXT_IMG`.
   * Debe leerse con `new sensor.HeartRate().getResting()`, escuchar `heartSensor.onRestingChange()` y pintarse mediante un widget `TEXT`.
2. **Atajos Táctiles a Apps Nativas (`IMG_CLICK`)**:
   * Colocar un `IMG_CLICK` transparente (`src: ''`) sobre el área deseada con `type: resolveDataType('HEART')` o `WEATHER` para abrir la app correspondiente al tocar la pantalla.
3. **Centrado Óptico Dinámico (12h / 24h)**:
   * Los dígitos `0..9` tienen anchos variables (especialmente el `1` ~60px frente a ~80px de los demás).
   * Al usar formato 12h, si la hora tiene un solo dígito (`chars[0] === null`), ocultar el primer widget (`widget.setProperty(PROP.VISIBLE, false)`) y centrar las 3 cifras restantes (`9:45`) para evitar asimetrías.
4. **Arcos de Progreso (`ARC_PROGRESS`)**:
   * El firmware utiliza ángulos horarios donde **`0° = 12 en punto`**, `90° = 3`, `180° = 6`, `270° = 9`.
   * Al actualizar con `setProperty(PROP.MORE, ...)`, pasar siempre el objeto de configuración completo.
5. **Sparkline de Frecuencia Cardíaca (`GRADKIENT_POLYLINE`)**:
   * Alimentar desde `heartSensor.getToday()`, filtrando valores `25 < v < 240` en una ventana móvil (últimas 3 horas) y promediando en buckets.
   * Los puntos `{ x, y }` deben ser relativos a la caja `(x, y, w, h)` del widget.
   * Llamar a `sparklineWidget.clear()` antes de cada actualización.
6. **Colorimetría AMOLED (RGB565)**:
   * Para evitar que los tonos grises o pistas de arcos se vean azulados tras la cuantización del firmware, usar valores estrictamente neutros (`R === G === B`), como `RGB(24,24,24)` o `0x2A2A2A`.
7. **Limpieza en `onDestroy`**:
   * Desuscribir siempre los callbacks de sensores (`offChange`, `offRestingChange`, `offLastChange`) para evitar fugas de memoria y consumo de batería.

---

## 4. Compilación y Despliegue con `zeus`

```bash
# Regenerar recursos (PNG recortados, paletas y glyphs.js)
python scripts/generate_assets.py

# Compilación sin prompts interactivos
zeus build --target "Amazfit T-Rex 3 Pro (48mm)"

# Generar código QR de instalación (caduca a los 7 días)
zeus preview --target "Amazfit T-Rex 3 Pro (48mm)"
```

* **Instalación**: Escanear desde *App Zepp → Perfil → Amazfit T-Rex 3 Pro → Modo desarrollador → Escanear*.  
  *(Para habilitar el modo desarrollador en Zepp: Perfil → Ajustes → Acerca de → 7 toques sobre el logo de Zepp).*

---
name: zepp-os-watchface
description: >-
  Desarrolla, compila, depura y despliega watchfaces personalizados para relojes Amazfit con Zepp OS (especialmente Amazfit T-Rex 3 / T-Rex 3 Pro 48mm) usando JavaScript (@zos/ui, @zos/sensor), generación de recursos con Python/Pillow y @zeppos/zeus-cli. Úsala siempre que el usuario pida crear, modificar, centrar, cambiar colores/estilos o generar un QR de instalación para una esfera de reloj Amazfit.
---

# Desarrollo de Watchfaces en Zepp OS (Amazfit T-Rex 3 Pro 48mm)

## 1. Repositorio de Referencia del Proyecto
- **Repositorio local**: `c:\Projects\AmazfitWatchfaces` (GitHub: `apopovsky/AmazfitWatchfaces`)
  - `wf-tactical-amber/`: TR3X Tactical (bisel de 60 marcas, batería de 10 segmentos, cajas biseladas para biometría, sparkline HR en vivo).
  - `wf-dual-styles/`: TR3X Dash v1.2.0 (doble estilo alternable A/B, arcos laterales de pasos/calorías o arco superior unificado).
  - `wf-minimal-grid/`: TR3X Minimal (cápsula redondeada de batería, cuadrícula abierta 2x2 para biometría).
  - `wf-dual-lavender/`: TR3X Lavender (arcos laterales delgados, fecha y dos pastillas bicolores personalizables).
  - Cada proyecto contiene:
    - `app.json`: Manifiesto Zepp OS `configVersion: "v3"`.
    - `scripts/generate_assets.py`: Generador de glifos antialiased con supersampling (Pillow), fondos pre-renderizados, iconos, `watchface/glyphs.js` y previews.
    - `watchface/index.js`: Código fuente JavaScript legible (`@zos/ui`, `@zos/sensor`).
    - `watchface/glyphs.js`: Métricas exactas de glifos (`GLYPH_METRICS`) y paleta de colores (`PALETTE`) generadas automáticamente.

## 2. Manifiesto (`app.json` v3) y Rutas de Recursos
- **Configuración del Target T-Rex 3 Pro (48mm)**:
  - Clave en `targets`: `"rocky"` (`designWidth: 480`).
  - `platforms`: `Rocky` (`10551552`), `RockyWN` (`10551553`), `RockyW` (`10551555`).
  - `runtime.apiVersion`: `{ "compatible": "3.6.0", "target": "3.6.0", "minVersion": "3.6" }`, `"type": 2`.
  - `permissions`:
    ```json
    "permissions": [
      "data:user.hd.pai",
      "data:user.hd.heart_rate",
      "data:user.hd.calorie",
      "data:user.hd.step"
    ]
    ```
- **Flags OBLIGATORIOS en `module.watchface`**:
  ```json
  "targets": {
    "rocky": {
      "module": {
        "watchface": {
          "path": "watchface/index",
          "main": 1,
          "editable": 1,
          "lockscreen": 1
        }
      },
      ...
    }
  }
  ```
  - `"editable": 1`: **Imprescindible**. Sin este flag, el firmware ignora la pulsación prolongada en el reloj y no permite abrir el editor de la esfera.
  - `"lockscreen": 1`: Habilita la ejecución y renderizado del modo AOD (Always-On Display / pantalla de bloqueo).
- **Regla de carpetas en `configVersion: "v3"`**:
  - Archivos físicos: Guardar en `assets/<targetKey>/` (ej. `assets/rocky/icon.png`, `assets/rocky/bg_amber.png`).
  - En código (`app.json` e `index.js`): Referenciar **sin** el prefijo `assets/rocky/` (ej. `'bg_amber.png'`, `'clock/cream/0.png'`).

## 3. Comandos No Interactivos de `zeus` CLI y Flujo de Despliegue
1. **Actualizar catálogo de dispositivos** (si falta el target):
   ```powershell
   zeus cache update
   ```
2. **Compilar y generar QR de previsualización**:
   - Pasar siempre el nombre completo del dispositivo en `--target` (no `"rocky"`), para evitar prompts interactivos que bloquean la terminal:
     ```powershell
     cd "c:\Projects\AmazfitWatchfaces\wf-tactical-amber"
     python scripts\generate_assets.py
     zeus build --target "Amazfit T-Rex 3 Pro (48mm)"
     zeus preview --target "Amazfit T-Rex 3 Pro (48mm)"
     ```
3. **Autenticación OAuth no interactiva**:
   - Si `zeus status` muestra `login status: no login`, lanzar `zeus login` en background, detectar el puerto local del callback en escucha (`node.exe`) y generar la URL OAuth para el navegador:
     `https://user.zepp.com/universalLogin/index.html#/login?project_name=zeppos_zeus_cli&platform_app=com.huami.webapp&project_redirect_uri=http%3A%2F%2Flocalhost%3A<PORT>%2Flogin%2Fcallback`
4. **Renderizado de QR y Caducidad**:
   - Convertir los bloques ASCII de `zeus preview` (`█`, `▀`, `▄`, ` `) a un archivo PNG nítido (con Pillow) y guardarlo en `docs/<nombre>_qr.png`.
   - **Caducidad**: Los QRs de `zeus preview` expiran a los **7 días** de ser generados.
5. **Modo Desarrollador en la app Zepp**:
   - Para desbloquear el menú de desarrollador por primera vez: *App Zepp → Perfil → Ajustes → Acerca de → pulsar el logo de Zepp 7 veces*.
   - Luego escanear desde: *Perfil → Amazfit T-Rex 3 Pro → Modo desarrollador → Escanear*.

## 4. Reglas Críticas de Firmware, Sensores y UI

### 4.1. Edición en el Reloj y Ciclo de Vida (`WATCHFACE_EDIT_GROUP` + `WIDGET_DELEGATE`)
- **Regla del `show_level`**:
  - `WATCHFACE_EDIT_MASK`: Asignar `show_level: SL.ONLY_EDIT`.
  - `WATCHFACE_EDIT_GROUP`: **NUNCA asignar `show_level: SL.ONLY_EDIT`**. Debe quedar sin `show_level` (o con `ONLY_NORMAL`). Si se marca `ONLY_EDIT`, el firmware omite su inicialización en modo normal y `getProperty(PROP.CURRENT_TYPE)` devuelve `undefined`, imposibilitando leer la opción guardada.
  - Todos los IDs `type` en `optional_types` deben ser `>= 100000`.
- **Detección del retorno del editor (`WIDGET_DELEGATE`)**:
  - Al salir del editor en el reloj, **`build()` NO vuelve a ejecutarse**.
  - Para aplicar los cambios inmediatamente al salir del editor, registrar un delegado de reanudación:
    ```javascript
    ui.createWidget(W.WIDGET_DELEGATE, {
      resume_call: refreshAll,
    })
    ```
  - Como salvaguarda adicional, volver a evaluar las opciones en el callback por minuto de `timeSensor.onPerMinute`.

### 4.2. Sensores, Tipos de Datos y la Excepción de RHR
- **Helper para resolución de tipos de datos**:
  ```javascript
  function resolveDataType(key) {
    if (ui.data_type && ui.data_type[key] !== undefined) return ui.data_type[key]
    if (typeof hmUI !== 'undefined' && hmUI.data_type && hmUI.data_type[key] !== undefined) return hmUI.data_type[key]
    return undefined
  }
  ```
  Tipos nativos soportados para `TEXT_IMG`: `WEATHER`, `WEATHER_CURRENT`, `HRV`, `BIO_CHARGE`, `PAI_WEEKLY`, `HEART`, `STEP`, `CALORIE`.
- **La Excepción de RHR (Frecuencia Cardíaca en Reposo)**:
  - **No existe un `data_type` del sistema para RHR en `TEXT_IMG`**.
  - RHR debe leerse directamente a través del sensor de ritmo cardíaco:
    ```javascript
    const heartSensor = new sensor.HeartRate()
    const rhr = heartSensor.getResting()
    rhrValueWidget.setProperty(PROP.TEXT, rhr && rhr > 0 ? String(rhr) : '--')
    heartSensor.onRestingChange(updateResting)
    ```
- **Limpieza de listeners en `onDestroy`**:
  - Todo callback suscrito (`batterySensor.onChange`, `heartSensor.onRestingChange`, `heartSensor.onLastChange`, `stepSensor.onChange`, etc.) debe desuscribirse con su respectivo `off*` en `onDestroy` para evitar fugas de memoria y consumo fantasma de batería en el firmware.

### 4.3. Atajos Táctiles a Apps del Sistema (`IMG_CLICK`)
- Para que el usuario pueda pulsar sobre métricas (como ritmo cardíaco o clima) y abrir la aplicación nativa del reloj:
  ```javascript
  const hrDt = resolveDataType('HEART')
  if (hrDt !== undefined) {
    ui.createWidget(W.IMG_CLICK, {
      x: 170, y: 362, w: 140, h: 48,
      src: '', // Transparente
      type: hrDt,
      show_level: showNormal,
    })
  }
  ```

### 4.4. Centrado Óptico Dinámico de la Hora (12h / 24h)
- Nunca usar `IMG_TIME` con anchos fijos si se busca estética profesional.
- **Glifos recortados a medida**:
  - Dígitos normales `0..9`: Ancho individual recortado (~`80–86 px`), altura ~`104–112 px`.
  - Dígito `1`: Con pie horizontal ("slab base") y nariz inclinada (~`60 px`).
  - Separador `:`: Dos bloques cuadrados redondeados (~`18 px`).
- **Soporte de formato 12h vs 24h**:
  ```javascript
  const hourFmt = timeSensor.getHourFormat() // 0 = 12h, 1 = 24h
  const rawHour = timeSensor.getFormatHour()
  const minStr = String(timeSensor.getMinutes()).padStart(2, '0')
  const hourStr = hourFmt === 0 ? String(rawHour) : String(rawHour).padStart(2, '0')

  const chars = [
    hourStr.length === 2 ? hourStr[0] : null,
    hourStr.length === 2 ? hourStr[1] : hourStr[0],
    ':',
    minStr[0],
    minStr[1],
  ]
  ```
  - Si `chars[0] === null` (hora de 1 dígito en modo 12h), ocultar el widget (`widget.setProperty(PROP.VISIBLE, false)`) y calcular `curX = Math.round((480 - totalW) / 2)` **sin** el ancho del primer dígito para mantener el centrado perfecto.
- **AOD (Always-On Display)**: Usar dígitos **sólidos atenuados** (~70% brillo / gris) del mismo tamaño, evitando contornos huecos que penalizan la legibilidad.

### 4.5. Arcos de Progreso (`ARC_PROGRESS`) y Arcos Segmentados
- **Ángulos horarios en T-Rex 3 Pro**: En Zepp OS, los arcos usan ángulos donde **`0° = 12 en punto`**, `90° = 3`, `180° = 6`, `270° = 9`:
  - Arco lateral izquierdo: `start_angle: 222, end_angle: 318`
  - Arco lateral derecho (abajo hacia arriba): `start_angle: 138, end_angle: 42`
  - Arco superior: `start_angle: -54, end_angle: 54`
- **Actualización con `setProperty(PROP.MORE, ...)`**: Pasar siempre el objeto de configuración completo (`center_x, center_y, radius, line_width, start_angle, end_angle, color, level`), nunca `{ level }` en solitario.
- **Arcos segmentados pre-renderizados**: Para estéticas tácticas con bloques curvos (ej. 10 segmentos de batería), es preferible pre-renderizar con Python/Pillow (`arc_seg/<color>/0..10.png`) y alternar el `src` de un `W.IMG`, ahorrando cómputo en el reloj.

### 4.6. Sparkline de Tendencia Cardíaca (`GRADKIENT_POLYLINE`)
- **Procesamiento de datos**:
  - `heartSensor.getToday()` devuelve hasta 1440 lecturas diarias por minuto.
  - Filtrar valores fisiológicos válidos (`v > 25 && v < 240`) en una ventana reciente (últimas 3 horas / 180 min) y calcular promedios en ~26 buckets equidistantes.
- **Coordenadas**: Los puntos `{ x, y }` pasados a `sparklineWidget.addLine({ data: pts, count: pts.length })` deben ser **relativos a la caja `(x, y, w, h)` del widget** (`0..w`, `0..h`).
- Llamar siempre a `sparklineWidget.clear()` antes de redibujar y usar un `CIRCLE` con coordenadas absolutas (`box.x + last.x`, `box.y + last.y`) como punto terminal.

### 4.7. Colorimetría AMOLED y Rendimiento
- **Grises 100% neutros (`R === G === B`)**: Para evitar el tinte azulado tras la conversión interna del firmware a RGB565, fondos (`RGB(24,24,24)`), pistas de arcos (`0x2A2A2A`) y divisores (`0x6E6E6E`) deben tener canales rojo, verde y azul idénticos.
- **Fondos estáticos pre-renderizados**: Pre-renderizar biseles, cuadrículas y marcos en imágenes de fondo completas (`bg_<color>.png`) en lugar de crearlos con decenas de widgets `FILL_RECT` / `LINE`.
- **Área reservada del sistema**: Dejar libre `x = 240, y = 18..44` para el icono de notificaciones del sistema.

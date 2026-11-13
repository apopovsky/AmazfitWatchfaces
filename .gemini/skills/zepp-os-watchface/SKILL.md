---
name: zepp-os-watchface
description: >-
  Develop, build, debug, and deploy custom Amazfit watchfaces for Zepp OS devices such as the Amazfit T-Rex 3 / T-Rex 3 Pro 48mm using JavaScript (@zos/ui, @zos/sensor), generate assets, compile for the target hardware, preview the result on the device, and apply practical rules for firmware, sensors, and UI behavior.
---

# Zepp OS Watchface Development (Amazfit T-Rex 3 Pro 48mm)

## 1. Project Reference Repository
- Local repository: `c:\Projects\AmazfitWatchfaces` (GitHub: `apopovsky/AmazfitWatchfaces`)
  - `wf-tactical-amber/`: TR3X Tactical (60-mark bezel, 10-segment battery, chamfered biometric boxes, live HR sparkline)
  - `wf-dual-styles/`: TR3X Dash v1.2.0 (two switchable styles, A/B, with lateral step/calorie arcs or a unified upper arc)
  - `wf-minimal-grid/`: TR3X Minimal (rounded battery capsule, open 2x2 biometric grid)
  - `wf-dual-lavender/`: TR3X Lavender (thin lateral arcs, date, and two customizable bicolor pills)
  - Each project contains:
    - `app.json`: Zepp OS manifest with `configVersion: "v3"`.
    - `scripts/generate_assets.py`: Generator for antialiased glyphs with supersampling (Pillow), pre-rendered backgrounds, icons, `watchface/glyphs.js`, and previews.
    - `watchface/index.js`: Human-readable JavaScript source using `@zos/ui` and `@zos/sensor`.
    - `watchface/glyphs.js`: Exact glyph metrics (`GLYPH_METRICS`) and generated palette (`PALETTE`).

## 2. Manifest (`app.json` v3) and Resource Paths
- Target configuration for the T-Rex 3 Pro (48mm):
  - Target key in `targets`: `"rocky"` (`designWidth: 480`)
  - `platforms`: `Rocky` (`10551552`), `RockyWN` (`10551553`), `RockyW` (`10551555`)
  - `runtime.apiVersion`: `{ "compatible": "3.6.0", "target": "3.6.0", "minVersion": "3.6" }`, `"type": 2`
  - `permissions`:
    ```json
    "permissions": [
      "data:user.hd.pai",
      "data:user.hd.heart_rate",
      "data:user.hd.calorie",
      "data:user.hd.step"
    ]
    ```
- Required flags in `module.watchface`:
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
  - `"editable": 1`: Essential. Without this flag, the firmware ignores long-press on the watch and the watchface editor cannot be opened.
  - `"lockscreen": 1`: Enables execution and rendering in AOD (Always-On Display / lock screen mode).
- Folder rule for `configVersion: "v3"`:
  - Physical files must be stored in `assets/<targetKey>/` (for example: `assets/rocky/icon.png`, `assets/rocky/bg_amber.png`).
  - In code (`app.json` and `index.js`), reference them without the `assets/rocky/` prefix (for example: `'bg_amber.png'`, `'clock/cream/0.png'`).

## 3. Non-Interactive `zeus` CLI Commands and Deployment Flow
1. Update the device catalog if the target is missing:
   ```powershell
   zeus cache update
   ```
2. Build and generate a preview QR:
   - Always pass the full device name to `--target` instead of `"rocky"` to avoid interactive prompts that can block the terminal:
     ```powershell
     cd "c:\Projects\AmazfitWatchfaces\wf-tactical-amber"
     python scripts\generate_assets.py
     zeus build --target "Amazfit T-Rex 3 Pro (48mm)"
     zeus preview --target "Amazfit T-Rex 3 Pro (48mm)"
     ```
3. Non-interactive OAuth login:
   - If `zeus status` reports `login status: no login`, start `zeus login` in the background, detect the local callback port used by `node.exe`, and open the browser with the generated OAuth URL:
     `https://user.zepp.com/universalLogin/index.html#/login?project_name=zeppos_zeus_cli&platform_app=com.huami.webapp&project_redirect_uri=http%3A%2F%2Flocalhost%3A<PORT>%2Flogin%2Fcallback`
4. QR rendering and expiration:
   - Convert the ASCII QR blocks from `zeus preview` (`█`, `▀`, `▄`, ` `) into a crisp PNG using Pillow and save it to `docs/<name>_qr.png`.
   - `zeus preview` QR codes expire after 7 days.
5. Developer mode in the Zepp app:
   - To unlock the developer menu for the first time: Zepp App → Profile → Settings → About → tap the Zepp logo 7 times.
   - Then scan from: Profile → Amazfit T-Rex 3 Pro → Developer mode → Scan.

## 4. Critical Firmware, Sensor, and UI Rules

### 4.1. Editing on the Watch and Lifecycle (`WATCHFACE_EDIT_GROUP` + `WIDGET_DELEGATE`)
- Rule for `show_level`:
  - `WATCHFACE_EDIT_MASK`: set `show_level: SL.ONLY_EDIT`
  - `WATCHFACE_EDIT_GROUP`: never assign `show_level: SL.ONLY_EDIT`; leave it without `show_level` (or use `ONLY_NORMAL`). If `ONLY_EDIT` is assigned, the firmware skips initialization in normal mode and the watchface can break.
  - All `type` IDs in `optional_types` must be `>= 100000`.
- Detecting when the editor exits (`WIDGET_DELEGATE`):
  - When leaving the editor on the watch, `build()` is not called again.
  - To apply changes immediately after exiting the editor, register a resume delegate:
    ```javascript
    ui.createWidget(W.WIDGET_DELEGATE, {
      resume_call: refreshAll,
    })
    ```
  - As an additional safeguard, re-evaluate the options in the `timeSensor.onPerMinute` callback.

### 4.2. Sensors, Data Types, and the RHR Exception
- Helper to resolve data types:
  ```javascript
  function resolveDataType(key) {
    if (ui.data_type && ui.data_type[key] !== undefined) return ui.data_type[key]
    if (typeof hmUI !== 'undefined' && hmUI.data_type && hmUI.data_type[key] !== undefined) return hmUI.data_type[key]
    return undefined
  }
  ```
  Native data types supported for `TEXT_IMG`: `WEATHER`, `WEATHER_CURRENT`, `HRV`, `BIO_CHARGE`, `PAI_WEEKLY`, `HEART`, `STEP`, `CALORIE`.
- The RHR exception (Resting Heart Rate):
  - There is no system `data_type` for RHR in `TEXT_IMG`.
  - RHR must be read directly from the heart-rate sensor:
    ```javascript
    const heartSensor = new sensor.HeartRate()
    const rhr = heartSensor.getResting()
    rhrValueWidget.setProperty(PROP.TEXT, rhr && rhr > 0 ? String(rhr) : '--')
    heartSensor.onRestingChange(updateResting)
    ```
- Clean up listeners in `onDestroy`:
  - Every subscribed callback (`batterySensor.onChange`, `heartSensor.onRestingChange`, `heartSensor.onLastChange`, `stepSensor.onChange`, etc.) must be unsubscribed with the corresponding `off*` method inside `onDestroy`.

### 4.3. Touch Shortcuts to System Apps (`IMG_CLICK`)
- This allows the user to tap metrics such as heart rate or weather and open the native watch app:
  ```javascript
  const hrDt = resolveDataType('HEART')
  if (hrDt !== undefined) {
    ui.createWidget(W.IMG_CLICK, {
      x: 170, y: 362, w: 140, h: 48,
      src: '', // Transparent
      type: hrDt,
      show_level: showNormal,
    })
  }
  ```

### 4.4. Dynamic Optical Centering of the Time (12h / 24h)
- Never use `IMG_TIME` with fixed widths if you want a professional aesthetic.
- Custom-cropped glyphs:
  - Normal digits `0..9`: individual width trimmed to roughly `80–86 px`, height around `104–112 px`
  - Digit `1`: includes a horizontal slab base and slanted nose (~`60 px`)
  - Separator `:`: two rounded square blocks (~`18 px`)
- Support for 12h and 24h formats:
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
  - If `chars[0] === null` (single-digit hour in 12h mode), hide the widget (`widget.setProperty(PROP.VISIBLE, false)`) and compute `curX = Math.round((480 - totalW) / 2)` without including the width of the first digit.
- AOD (Always-On Display): use muted solid digits at roughly 70% brightness (gray) with the same sizing, avoiding hollow outlines that reduce readability.

### 4.5. Progress Arcs (`ARC_PROGRESS`) and Segmented Arcs
- Hourly arc angles on the T-Rex 3 Pro: In Zepp OS, arc angles follow this convention: `0° = 12 o'clock`, `90° = 3`, `180° = 6`, `270° = 9`
  - Left-side arc: `start_angle: 222, end_angle: 318`
  - Right-side arc (bottom to top): `start_angle: 138, end_angle: 42`
  - Top arc: `start_angle: -54, end_angle: 54`
- Updating via `setProperty(PROP.MORE, ...)`: always pass the full configuration object (`center_x, center_y, radius, line_width, start_angle, end_angle, color, level`), never a partial object such as `{ level: ... }`.
- Pre-rendered segmented arcs: for tactical aesthetics with curved blocks (for example, a 10-segment battery), it is preferable to pre-render them with Python/Pillow (`arc_seg/<color>/0..10.png`) and compose them in the UI rather than drawing them widget by widget.

### 4.6. Heart Rate Trend Sparkline (`GRADKIENT_POLYLINE`)
- Data processing:
  - `heartSensor.getToday()` returns up to 1440 readings per day, one per minute.
  - Filter only valid physiological values (`v > 25 && v < 240`) in a recent window (last 3 hours / 180 minutes) and compute averages across roughly 26 evenly spaced buckets.
- Coordinates: the points `{ x, y }` passed to `sparklineWidget.addLine({ data: pts, count: pts.length })` must be relative to the widget box `(x, y, w, h)` (`0..w`, `0..h`).
- Always call `sparklineWidget.clear()` before redrawing and use a `CIRCLE` with absolute coordinates (`box.x + last.x`, `box.y + last.y`) as the terminal point.

### 4.7. AMOLED Colorimetry and Performance
- Neutral grays at 100% (`R === G === B`): to avoid the blue tint that can appear after the firmware converts the image to RGB565, use neutral backgrounds such as `RGB(24,24,24)`, arc tracks like `0x2A2A2A`, and separators like `0x6E6E6E`.
- Pre-rendered static backgrounds: render bezels, grids, and frames as full background images (`bg_<color>.png`) instead of creating them with dozens of `FILL_RECT` / `LINE` widgets.
- Reserved system area: leave free `x = 240, y = 18..44` for the system notification icon.

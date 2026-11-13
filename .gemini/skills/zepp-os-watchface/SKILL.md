---
name: zepp-os-watchface
description: >-
  Develop, design, compile, debug, and package custom watchfaces for Amazfit smartwatches powered by Zepp OS (Zepp OS 1.0, 2.x, 3.x, and 3.6+ / 4.x) using JavaScript (@zos/ui, @zos/sensor, @zos/app, hmUI, hmSensor), asset generation pipelines, and @zeppos/zeus-cli. Use whenever creating or modifying watchfaces, designing layouts, handling Always-On Display (AOD), editable complications/styles, biometrics, or previewing on devices.
---

# Zepp OS Watchface Development Guide

A comprehensive, production-grade guide for developing, configuring, optimizing, and deploying custom watchfaces across Amazfit smartwatches powered by Zepp OS.

---

## 1. Zepp OS Architecture & Compatibility

Zepp OS powers Amazfit wearable devices through a lightweight JavaScript runtime.

### 1.1 Device Form Factors & Target Resolutions
| Form Factor | Typical Resolutions | Common Target Devices |
| :--- | :--- | :--- |
| **Round (Flagship / Outdoor)** | `480x480` | Amazfit T-Rex 3, T-Rex 3 Pro (48mm), Balance, Cheetah Pro |
| **Round (Standard)** | `454x454` | Amazfit GTR 4, GTR 3, GTR 3 Pro, T-Rex 2, T-Rex Ultra, Falcon |
| **Round (Compact)** | `390x390`, `416x416` | Amazfit GTR Mini, Cheetah (Round) |
| **Square / Rectangular** | `390x450`, `336x384` | Amazfit GTS 4, GTS 3, Active, Active Edge, Bip series |

### 1.2 API Levels & Dual-Import Compatibility Wrapper
* **Zepp OS 1.0 (Legacy)**: Global namespaces `hmUI`, `hmSensor`, `hmApp`, `hmSetting`.
* **Zepp OS 2.x / 3.x / 4.x (Modern)**: Modular ES packages `@zos/ui`, `@zos/sensor`, `@zos/app`, `@zos/display`, `@zos/router`.
* **Universal Compatibility Pattern**:
  ```javascript
  // Polyfill / Universal import pattern for multi-version resilience
  let ui = typeof hmUI !== 'undefined' ? hmUI : {}
  let sensor = typeof hmSensor !== 'undefined' ? hmSensor : {}

  try {
    const zosUi = require('@zos/ui')
    if (zosUi) ui = zosUi
  } catch (e) {}

  try {
    const zosSensor = require('@zos/sensor')
    if (zosSensor) sensor = zosSensor
  } catch (e) {}

  export const W = ui.widget || (typeof hmUI !== 'undefined' ? hmUI.widget : {})
  export const PROP = ui.prop || (typeof hmUI !== 'undefined' ? hmUI.prop : {})
  export const SL = ui.show_level || (typeof hmUI !== 'undefined' ? hmUI.show_level : {})
  ```

---

## 2. Project Directory Structure & Manifest (`app.json`)

### 2.1 Standard Project Layout (Config Version `v3`)
```text
my-watchface/
├── app.json                 # Manifest: targets, permissions, metadata
├── app.js                   # Application lifecycle entry
├── watchface/
│   ├── index.js             # Core watchface UI & sensor logic
│   └── glyphs.js            # Exported font metrics & color constants
├── assets/
│   └── <targetKey>/         # Target-specific assets (e.g., assets/rocky/ or assets/balance/)
│       ├── icon.png         # App/watchface icon (typically 100x100)
│       ├── bg.png           # Full pre-rendered background
│       ├── clock/           # Digit slices for dynamic optical kerning
│       └── preview/         # Complication/style selection thumbnails
├── scripts/
│   └── generate_assets.py   # Optional Pillow script for font & asset generation
└── package.json             # Optional dependencies & scripts
```

### 2.2 Manifest Specification (`app.json`)
```json
{
  "configVersion": "v3",
  "app": {
    "appId": 1000101,
    "appName": "My Custom Face",
    "appType": "watchface",
    "version": {
      "code": 1,
      "name": "1.0.0"
    },
    "icon": "icon.png",
    "vender": "DeveloperName",
    "description": "High performance custom watchface for Zepp OS"
  },
  "permissions": [
    "data:user.hd.heart_rate",
    "data:user.hd.step",
    "data:user.hd.calorie",
    "data:user.hd.pai",
    "device:os.bg_service"
  ],
  "runtime": {
    "apiVersion": {
      "compatible": "3.0.0",
      "target": "3.6.0",
      "minVersion": "3.0.0"
    },
    "type": 2
  },
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
      "platforms": [
        { "name": "Rocky", "deviceSource": 10551552 },
        { "name": "RockyWN", "deviceSource": 10551553 },
        { "name": "RockyW", "deviceSource": 10551555 }
      ],
      "designWidth": 480
    }
  },
  "i18n": {
    "en-US": { "appName": "My Custom Face" },
    "es-ES": { "appName": "Mi Esfera Personalizada" }
  }
}
```

### 2.3 Critical Manifest Rules
1. **`"editable": 1` (Mandatory for customization)**: If omitted or set to `0`, the firmware will ignore long-press gestures on the watch screen and disable the interactive complication/style editor.
2. **`"lockscreen": 1` (Mandatory for AOD)**: Enables execution and rendering of the Always-On Display (screen-off / ambient mode).
3. **Asset Path Resolution (`configVersion: "v3"`)**:
   * Physical filesystem storage: `assets/<targetKey>/<path-to-file>`.
   * References in code (`index.js` or `app.json`): **Do NOT include** `assets/<targetKey>/`. Use the relative path directly (e.g., `'bg.png'`, `'clock/0.png'`).

---

## 3. Watchface Lifecycle & Display States

### 3.1 Watchface Entrypoint (`watchface/index.js`)
```javascript
import { createWidget, widget, prop, show_level } from '@zos/ui'
import { Time } from '@zos/sensor'

WatchFace({
  onInit() {
    // 1. Initialize data structures, configuration state, and sensor instances
  },

  build() {
    // 2. Instantiate background, widgets, text, arcs, and complication groups
    // 3. Register WIDGET_DELEGATE for resume/pause events
    // 4. Attach sensor event listeners
  },

  onDestroy() {
    // 5. CRITICAL: Unregister all sensor callbacks to prevent memory leaks and battery drain
  }
})
```

### 3.2 Display Levels (`show_level`)
The display mode defines when widgets are visible to minimize CPU and power consumption:
* `show_level.ONLY_NORMAL`: Rendered only during active watchface mode.
* `show_level.ONAL_AOD` (or `show_level.ONLY_AOD`): Rendered only in Always-On Display (ambient rest-screen mode).
* `show_level.ONLY_EDIT`: Rendered only while the user is actively customizing the watchface on the device.
* Combine levels with bitwise OR: `show_level.ONLY_NORMAL | show_level.ONAL_AOD`.

### 3.3 The `WIDGET_DELEGATE` Pattern (Post-Edit Lifecycle)
> [!IMPORTANT]
> When a user exits the on-watch edit screen after changing a style or complication, **`build()` is NOT re-executed**.
> To detect when the user exits the editor or wakes the watchface, use a virtual `WIDGET_DELEGATE`:

```javascript
createWidget(widget.WIDGET_DELEGATE, {
  resume_call: () => {
    // Fired on watchface launch and immediately upon returning from the on-watch editor
    refreshComplicationsAndStyles()
  },
  pause_call: () => {
    // Fired when user swipes away to cards, notification center, or opens an app
  }
})
```

---

## 4. Editable Complications & Custom Styles

Zepp OS provides native support for user-customizable slots (complications) and visual styles via `WATCHFACE_EDIT_GROUP`.

### 4.1 The Golden Rules of `WATCHFACE_EDIT_GROUP`
1. **Never set `show_level: ONLY_EDIT` on `WATCHFACE_EDIT_GROUP`**:
   The group must be instantiated in normal mode so that the firmware preserves user selections. If marked `ONLY_EDIT`, `getProperty(prop.CURRENT_TYPE)` will return `undefined` during normal display mode!
2. **Set `show_level: ONLY_EDIT` on `WATCHFACE_EDIT_MASK`**:
   The mask represents the selection border/focus indicator and must only appear during customization.
3. **Custom Type ID Range**:
   Official system types are low integers. For custom types (e.g., custom colors, custom biometric layouts), IDs **must be $\ge 100000$ (`0x186a0` to `UINT32_MAX`)**:

```javascript
const EDIT_TYPES = {
  STYLE_TACTICAL: 100001,
  STYLE_MINIMAL: 100002,
  STYLE_ANALOG: 100003
}

const optionalTypes = [
  {
    type: EDIT_TYPES.STYLE_TACTICAL,
    preview: 'preview/tactical.png',
    title_en: 'Tactical',
    title_sc: '战术',
    title_es: 'Táctico'
  },
  {
    type: EDIT_TYPES.STYLE_MINIMAL,
    preview: 'preview/minimal.png',
    title_en: 'Minimal',
    title_sc: '极简',
    title_es: 'Minimalista'
  }
]

const editGroup = createWidget(widget.WATCHFACE_EDIT_GROUP, {
  edit_id: 101,
  x: 140,
  y: 200,
  w: 200,
  h: 80,
  select_margin: 0,
  select_radius: 12,
  default_type: EDIT_TYPES.STYLE_TACTICAL,
  optional_types: optionalTypes,
  count: optionalTypes.length,
  // Leave show_level unset (or ONLY_NORMAL) so it initializes properly!
})

// Reading the user's saved choice:
const currentType = editGroup.getProperty(prop.CURRENT_TYPE)
```

---

## 5. UI Widgets Reference (`@zos/ui`)

### 5.1 Digital Time: `IMG_TIME` vs Custom Dynamic Kerning
* **Standard `IMG_TIME`**: Easy to implement for basic layouts, but can produce asymmetric gaps in 12-hour mode or when digits have varying widths (such as a narrow digit `'1'`).
* **Custom Dynamic Optical Kerning (Recommended for Premium Faces)**:
  Slice individual digit PNGs (e.g., `0.png` through `9.png` and `: .png`) with exact bounding widths. Assemble them dynamically in `onPerMinute`:

```javascript
function updateClockDisplay(timeSensor, digitWidgets, glyphMetrics, screenWidth = 480) {
  const is12Hour = timeSensor.getHourFormat() === 0 // 0 = 12h, 1 = 24h
  const rawHour = timeSensor.getFormatHour()
  const minStr = String(timeSensor.getMinutes()).padStart(2, '0')
  const hourStr = is12Hour ? String(rawHour) : String(rawHour).padStart(2, '0')

  const chars = [
    hourStr.length === 2 ? hourStr[0] : null,
    hourStr.length === 2 ? hourStr[1] : hourStr[0],
    ':',
    minStr[0],
    minStr[1]
  ]

  // Calculate exact total width using character metrics
  let totalWidth = 0
  for (const c of chars) {
    if (c !== null) totalWidth += glyphMetrics[c]?.width || 0
  }

  let currentX = Math.round((screenWidth - totalWidth) / 2)

  for (let i = 0; i < digitWidgets.length; i++) {
    const char = chars[i]
    const w = digitWidgets[i]
    if (char === null) {
      w.setProperty(prop.VISIBLE, false)
    } else {
      const metric = glyphMetrics[char]
      w.setProperty(prop.MORE, {
        x: currentX,
        y: metric.y,
        w: metric.width,
        h: metric.height,
        src: metric.src,
        visible: true
      })
      currentX += metric.width
    }
  }
}
```

### 5.2 Analog Clock Hands: `TIME_POINTER`
Used for rotational watch hands where the system rotates images automatically based on time:
```javascript
createWidget(widget.TIME_POINTER, {
  hour_centerX: 240,       // Rotation center on watchface screen (X)
  hour_centerY: 240,       // Rotation center on watchface screen (Y)
  hour_posX: 16,           // Pivot coordinate inside the hand image (X)
  hour_posY: 180,          // Pivot coordinate inside the hand image (Y)
  hour_path: 'hands/hour.png',
  hour_cover_path: 'hands/cap.png', // Center hub cap overlay
  hour_cover_x: 224,
  hour_cover_y: 224,
  minute_centerX: 240,
  minute_centerY: 240,
  minute_posX: 12,
  minute_posY: 220,
  minute_path: 'hands/minute.png',
  second_centerX: 240,
  second_centerY: 240,
  second_posX: 8,
  second_posY: 240,
  second_path: 'hands/second.png'
})
```

### 5.3 Progress Arcs: `ARC_PROGRESS`
Zepp OS uses standard clock angle orientations where:
$$\text{0}^\circ = \text{12 o'clock}, \quad \text{90}^\circ = \text{3 o'clock}, \quad \text{180}^\circ = \text{6 o'clock}, \quad \text{270}^\circ = \text{9 o'clock}$$

```javascript
const arc = createWidget(widget.ARC_PROGRESS, {
  center_x: 240,
  center_y: 240,
  radius: 228,
  start_angle: 220, // Left lateral arc starting at bottom-left
  end_angle: 320,   // ending at top-left
  color: 0xFF9E0B,
  line_width: 8,
  level: 65         // 0 to 100 percentage
})

// Updating ARC_PROGRESS:
// ALWAYS pass the full geometry object. Passing only { level } can reset coordinates on certain firmware builds!
function updateArc(widgetInstance, currentVal, maxVal, color) {
  const level = Math.min(100, Math.max(0, Math.round((currentVal / maxVal) * 100)))
  widgetInstance.setProperty(prop.MORE, {
    center_x: 240,
    center_y: 240,
    radius: 228,
    start_angle: 220,
    end_angle: 320,
    line_width: 8,
    color: color,
    level: level
  })
}
```

### 5.4 Sparkline Trends: `GRADIENT_POLYLINE`
Used for historical trendlines (e.g., 24-hour heart rate or barometric pressure):
```javascript
const polyline = createWidget(widget.GRADIENT_POLYLINE, {
  x: 160,
  y: 340,
  w: 160,
  h: 50,
  type: 0 // Solid or gradient mode
})

// Coordinates in addLine MUST be relative to widget box (0..w, 0..h):
function drawSparkline(polylineWidget, readings, boxWidth, boxHeight) {
  polylineWidget.clear()
  if (!readings || readings.length < 2) return

  const min = Math.min(...readings)
  const max = Math.max(...readings)
  const range = max - min || 1

  const points = readings.map((val, idx) => ({
    x: Math.round((idx / (readings.length - 1)) * boxWidth),
    y: Math.round(boxHeight - ((val - min) / range) * boxHeight)
  }))

  polylineWidget.addLine({
    data: points,
    count: points.length
  })
}
```

### 5.5 Interactive Touch Areas: `IMG_CLICK`
To enable users to tap on biometrics (e.g., heart rate, steps, weather) and launch the corresponding native watch app:
```javascript
const dataType = ui.data_type || (typeof hmUI !== 'undefined' ? hmUI.data_type : {})

createWidget(widget.IMG_CLICK, {
  x: 160,
  y: 330,
  w: 160,
  h: 60,
  src: '', // Fully transparent overlay
  type: dataType.HEART || 1, // Opens native Heart Rate app
  show_level: show_level.ONLY_NORMAL
})
```

---

## 6. Biometrics & Hardware Sensors (`@zos/sensor`)

### 6.1 Available Sensors & Usage Matrix
| Sensor | Class Name (`@zos/sensor`) | Key Methods | Relevant Permissions |
| :--- | :--- | :--- | :--- |
| **Time** | `Time` | `getHours()`, `getMinutes()`, `getSeconds()`, `getFormatHour()`, `getHourFormat()`, `onPerMinute()` | None |
| **Heart Rate** | `HeartRate` | `getCurrent()`, `getLast()`, `getResting()`, `getToday()`, `onCurrentChange()`, `onRestingChange()` | `data:user.hd.heart_rate` |
| **Step** | `Step` | `getCurrent()`, `getTarget()`, `onChange()` | `data:user.hd.step` |
| **Calorie** | `Calorie` | `getCurrent()`, `getTarget()`, `onChange()` | `data:user.hd.calorie` |
| **Battery** | `Battery` | `getCurrent()`, `onChange()` | None |
| **Weather** | `Weather` | `getForecast()`, `check()` | None |
| **Distance** | `Distance` | `getCurrent()`, `onChange()` | `data:user.hd.step` |
| **PAI** | `Pai` | `getTotal()`, `getDaily()`, `onChange()` | `data:user.hd.pai` |
| **Blood Oxygen** | `BloodOxygen` | `getCurrent()`, `onChange()` | `data:user.hd.spo2` |
| **Barometer** | `Barometer` | `getAirPressure()`, `getAltitude()`, `onChange()` | None |

### 6.2 The Resting Heart Rate (RHR) Exception
> [!WARNING]
> There is **no system `data_type`** for Resting Heart Rate in `TEXT_IMG`.
> RHR must be fetched directly from `HeartRate.getResting()` and rendered using a `TEXT` or custom slice widget:

```javascript
import { HeartRate } from '@zos/sensor'

const hr = new HeartRate()
const restingBpm = hr.getResting() // Returns resting HR integer or 0 if uncalculated

const onRestingChange = () => {
  const val = hr.getResting()
  rhrWidget.setProperty(prop.TEXT, val > 0 ? String(val) : '--')
}

hr.onRestingChange(onRestingChange)
```

### 6.3 Sensor Listener Cleanup (`onDestroy`)
To prevent memory leaks and aggressive battery consumption, every subscribed callback must be paired with its `off*` cleanup:
```javascript
WatchFace({
  build() {
    this.timeSensor = new Time()
    this.stepSensor = new Step()
    this.batterySensor = new Battery()

    this.onMinuteCallback = () => this.updateTime()
    this.onStepCallback = () => this.updateSteps()
    this.onBatteryCallback = () => this.updateBattery()

    this.timeSensor.onPerMinute(this.onMinuteCallback)
    this.stepSensor.onChange(this.onStepCallback)
    this.batterySensor.onChange(this.onBatteryCallback)
  },

  onDestroy() {
    if (this.timeSensor && this.onMinuteCallback) {
      this.timeSensor.offPerMinute(this.onMinuteCallback)
    }
    if (this.stepSensor && this.onStepCallback) {
      this.stepSensor.offChange(this.onStepCallback)
    }
    if (this.batterySensor && this.onBatteryCallback) {
      this.batterySensor.offChange(this.onBatteryCallback)
    }
  }
})
```

---

## 7. AMOLED Colorimetría & Power Optimization

1. **RGB565 Neutral Grays**:
   The watch hardware converts 24-bit RGB888 color into 16-bit RGB565. Grays with slight variations between channels can develop an unwanted green or blue tint. Ensure $R = G = B$ for all neutral tones:
   * Dark Slate Background: `0x181818` (R: 24, G: 24, B: 24)
   * Track / Slot Border: `0x2A2A2A` (R: 42, G: 42, B: 42)
   * Divider Line: `0x6E6E6E` (R: 110, G: 110, B: 110)
2. **Pre-rendered Static Backgrounds**:
   Instead of dynamically drawing dozens of tick marks, bezels, corner chamfers, and borders using individual `FILL_RECT`, `LINE`, or `CIRCLE` widgets, bake them into a single PNG background (`bg.png`). This eliminates render overhead and maintains 60 FPS transitions.
3. **Always-On Display (AOD / Screen-off)**:
   * Keep the On-Pixel Ratio (OPR) below **15–20%**.
   * Replace vibrant accent colors with muted grays or 50% luminance tones.
   * Hide non-essential complication cards, sparklines, and progress arcs.
   * Display solid, dimmed numerals for clock digits instead of thin hollow outlines (hollow outlines often suffer from sub-pixel aliasing and poor legibility under direct sunlight).
4. **System Reserved Space**:
   On round displays (such as 480x480), reserve the upper area at coordinates `x: 240, y: 18..44` to avoid overlapping system notification indicators and status icons.

---

## 8. Development & Deployment Toolchain (`@zeppos/zeus-cli`)

### 8.1 Setup & Installation
```bash
# Install Zeus CLI globally
npm install -g @zeppos/zeus-cli

# Verify version and update target device cache
zeus --version
zeus cache update
```

### 8.2 Build Commands (Non-Interactive Terminal Friendly)
Always supply the full device name via `--target` to avoid interactive terminal selection prompts:
```bash
# Build for specific hardware target
zeus build --target "Amazfit T-Rex 3 Pro (48mm)"
# or for Amazfit Balance
zeus build --target "Amazfit Balance"
# or for Amazfit GTR 4
zeus build --target "Amazfit GTR 4"
```

### 8.3 Device Preview & Installation QR Code
```bash
# Generate the on-device installation QR code
zeus preview --target "Amazfit T-Rex 3 Pro (48mm)"
```
* **QR Expiration**: QR codes generated via `zeus preview` are valid for **7 days**.
* **Converting ASCII QR to Image**: The CLI prints an ASCII block QR code in the terminal. You can capture or pipe this to a Pillow script to save a clean PNG image for documentation or easy scanning.

### 8.4 Enabling Developer Mode on the Zepp App
1. Open the **Zepp App** on your smartphone.
2. Navigate to: **Profile → Settings → About**.
3. Tap the **Zepp Logo 7 times** until the toast notification confirms developer mode is enabled.
4. Return to: **Profile → [Your Connected Watch] → Developer Mode**.
5. Tap **Scan** and point the camera at the QR code generated by `zeus preview`.

---

## 9. Comprehensive Troubleshooting & Sanity Checklist

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Watch ignores long press to edit** | Missing `"editable": 1` in `app.json` | Add `"editable": 1` under `targets.<targetKey>.module.watchface`. |
| **AOD does not appear on lock screen** | Missing `"lockscreen": 1` in `app.json` | Add `"lockscreen": 1` under `targets.<targetKey>.module.watchface`. |
| **`getProperty(prop.CURRENT_TYPE)` is `undefined`** | `WATCHFACE_EDIT_GROUP` configured with `show_level: ONLY_EDIT` | Remove `show_level` from `WATCHFACE_EDIT_GROUP`. Only the `WATCHFACE_EDIT_MASK` should have `ONLY_EDIT`. |
| **Edit option does not update on screen exit** | Firmware does not re-call `build()` upon exiting editor | Register a `WIDGET_DELEGATE` and refresh layout inside `resume_call`. |
| **Arc progress jumps or changes radius** | Updated with incomplete property payload `{ level }` | Pass the complete object (`center_x, center_y, radius, line_width, start_angle, end_angle, color, level`) in `setProperty(prop.MORE, ...)`. |
| **Excessive battery drain** | Sensor listeners not cleared | Explicitly call `.offChange()`, `.offPerMinute()`, `.offRestingChange()` in `onDestroy()`. |
| **Asymmetric clock spacing in 12h mode** | Unhandled 1-digit hour in fixed-width `IMG_TIME` | Use custom dynamic optical kerning to measure exact widths and center `9:45` dynamically. |
| **Gray elements appear bluish or greenish** | RGB888 color quantization to RGB565 | Ensure channels are identical: $R = G = B$ (e.g., `0x2A2A2A`). |
| **Zeus build interactive prompt freezes agent** | Incomplete target identifier | Use exact full device string: `zeus build --target "Amazfit T-Rex 3 Pro (48mm)"`. |
| **Missing custom complication preview** | Custom type ID $< 100000$ | Ensure custom `type` values in `optional_types` are $\ge 100000$. |

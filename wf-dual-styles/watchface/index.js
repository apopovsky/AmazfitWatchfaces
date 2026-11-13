import * as ui from '@zos/ui'
import * as sensor from '@zos/sensor'
import { GLYPH_METRICS, PALETTE } from './glyphs'

const W = ui.widget || (typeof hmUI !== 'undefined' && hmUI.widget)
const PROP = ui.prop || (typeof hmUI !== 'undefined' && hmUI.prop)
const ALIGN = ui.align || (typeof hmUI !== 'undefined' && hmUI.align)
const SL = ui.show_level || (typeof hmUI !== 'undefined' && hmUI.show_level)

const EDIT_LAYOUT_ID = 101
const EDIT_PRIMARY_ID = 102
const EDIT_SECONDARY_ID = 103

const LAYOUT_STYLE_A = 100001
const LAYOUT_STYLE_B = 100002

const PRIMARY_TYPE_BASE = 100100
const SECONDARY_TYPE_BASE = 100200

const DAYS_ES = ['', 'LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']
const MONTHS_ES = ['', 'ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']

const DATA_FONT_WHITE = Array.from({ length: 10 }, (_, i) => `data/white/${i}.png`)
const DATA_FONT_TOP = Array.from({ length: 10 }, (_, i) => `data/top/${i}.png`)
const WEATHER_IMAGES = Array.from({ length: 29 }, (_, i) => `icons/weather/${i}.png`)

const HEART_COLOR = 0xFF435A
// Pure neutral gray track & divider colors (R === G === B) so AMOLED never tints them blue
const TRACK_COLOR = 0x2A2A2A
const DIVIDER_COLOR = 0x6E6E6E

const SPARK_BOX = { x: 152, y: 420, w: 176, h: 24 }
const FALLBACK_SPARK_REL = [
  { x: 0, y: 18 },
  { x: 14, y: 11 },
  { x: 28, y: 16 },
  { x: 42, y: 6 },
  { x: 56, y: 14 },
  { x: 70, y: 10 },
  { x: 84, y: 17 },
  { x: 98, y: 15 },
  { x: 112, y: 8 },
  { x: 126, y: 16 },
  { x: 140, y: 12 },
  { x: 152, y: 7 },
  { x: 164, y: 13 },
  { x: 176, y: 14 },
]

function resolveDataType(key) {
  if (ui.data_type && ui.data_type[key] !== undefined) {
    return ui.data_type[key]
  }
  if (typeof hmUI !== 'undefined' && hmUI.data_type && hmUI.data_type[key] !== undefined) {
    return hmUI.data_type[key]
  }
  return undefined
}

function buildSparklinePoints(todayData, currentMinOfDay) {
  if (!Array.isArray(todayData) || todayData.length === 0) {
    return FALLBACK_SPARK_REL
  }
  const endIdx = Math.min(todayData.length - 1, Math.max(0, currentMinOfDay))
  const windowMins = 180
  const startIdx = Math.max(0, endIdx - windowMins + 1)

  const buckets = 26
  const sliceLen = Math.max(1, endIdx - startIdx + 1)
  const step = sliceLen / buckets
  const averaged = []

  for (let b = 0; b < buckets; b++) {
    const bStart = Math.floor(startIdx + b * step)
    const bEnd = Math.min(endIdx, Math.floor(startIdx + (b + 1) * step))
    let sum = 0
    let cnt = 0
    for (let i = bStart; i <= bEnd; i++) {
      const v = todayData[i]
      if (typeof v === 'number' && v > 25 && v < 240) {
        sum += v
        cnt++
      }
    }
    if (cnt > 0) {
      averaged.push({ idx: b, val: sum / cnt })
    }
  }

  if (averaged.length < 2) {
    return FALLBACK_SPARK_REL
  }

  let minV = Infinity
  let maxV = -Infinity
  for (let i = 0; i < averaged.length; i++) {
    if (averaged[i].val < minV) minV = averaged[i].val
    if (averaged[i].val > maxV) maxV = averaged[i].val
  }

  const span = Math.max(18, maxV - minV)
  const mid = (minV + maxV) / 2
  const low = mid - span / 2
  const high = mid + span / 2

  const padY = 3
  const usableH = SPARK_BOX.h - padY * 2

  return averaged.map((pt, i) => {
    const nx = Math.round((i / (averaged.length - 1)) * SPARK_BOX.w)
    const norm = Math.max(0, Math.min(1, (pt.val - low) / (high - low)))
    const ny = Math.round(padY + (1 - norm) * usableH)
    return { x: nx, y: ny }
  })
}

WatchFace({
  onInit() {
    this._cleanups = []
  },

  onResume() {
    if (this._refresh) {
      this._refresh()
    }
  },

  build() {
    const showNormal = SL.ONLY_NORMAL
    const showAod = SL.ONLY_AOD
    const showEdit = SL.ONLY_EDIT

    // 1. Edit mask & editable groups (Style, Primary Color, Secondary Color)
    ui.createWidget(W.WATCHFACE_EDIT_MASK, {
      x: 0,
      y: 0,
      w: 480,
      h: 480,
      src: 'editor/mask.png',
      show_level: showEdit,
    })

    const layoutGroup = ui.createWidget(W.WATCHFACE_EDIT_GROUP, {
      edit_id: EDIT_LAYOUT_ID,
      x: 170,
      y: 52,
      w: 140,
      h: 110,
      select_image: 'editor/select.png',
      un_select_image: 'editor/unselect.png',
      default_type: LAYOUT_STYLE_A,
      optional_types: [
        { type: LAYOUT_STYLE_A, preview: 'editor/style_a.png', title_en: 'Arcs + 4', title_sc: 'Arcs + 4', title_tc: 'Arcs + 4' },
        { type: LAYOUT_STYLE_B, preview: 'editor/style_b.png', title_en: 'Batt + Pill', title_sc: 'Batt + Pill', title_tc: 'Batt + Pill' },
      ],
      count: 2,
      tips_BG: 'editor/tips.png',
      tips_x: 0,
      tips_y: -30,
      tips_width: 140,
      tips_margin: 4,
      show_level: showEdit,
    })

    const primaryGroup = ui.createWidget(W.WATCHFACE_EDIT_GROUP, {
      edit_id: EDIT_PRIMARY_ID,
      x: 56,
      y: 185,
      w: 140,
      h: 110,
      select_image: 'editor/select.png',
      un_select_image: 'editor/unselect.png',
      default_type: PRIMARY_TYPE_BASE + 1, // Blue default
      optional_types: PALETTE.map((c, idx) => ({
        type: PRIMARY_TYPE_BASE + idx,
        preview: `editor/color_${c.key}.png`,
        title_en: c.name,
        title_sc: c.name,
        title_tc: c.name,
      })),
      count: PALETTE.length,
      tips_BG: 'editor/tips.png',
      tips_x: 0,
      tips_y: -30,
      tips_width: 140,
      tips_margin: 4,
      show_level: showEdit,
    })

    const secondaryGroup = ui.createWidget(W.WATCHFACE_EDIT_GROUP, {
      edit_id: EDIT_SECONDARY_ID,
      x: 284,
      y: 185,
      w: 140,
      h: 110,
      select_image: 'editor/select.png',
      un_select_image: 'editor/unselect.png',
      default_type: SECONDARY_TYPE_BASE + 2, // Orange default
      optional_types: PALETTE.map((c, idx) => ({
        type: SECONDARY_TYPE_BASE + idx,
        preview: `editor/color_${c.key}.png`,
        title_en: c.name,
        title_sc: c.name,
        title_tc: c.name,
      })),
      count: PALETTE.length,
      tips_BG: 'editor/tips.png',
      tips_x: 0,
      tips_y: -30,
      tips_width: 140,
      tips_margin: 4,
      show_level: showEdit,
    })

    // Mutable state driven by edit options
    let style = 'a'
    let primary = PALETTE[1]
    let secondary = PALETTE[2]

    const syncEditOptions = () => {
      try {
        const curLayout = layoutGroup.getProperty(PROP.CURRENT_TYPE)
        style = curLayout === LAYOUT_STYLE_B ? 'b' : 'a'

        const pType = primaryGroup.getProperty(PROP.CURRENT_TYPE) || (PRIMARY_TYPE_BASE + 1)
        const sType = secondaryGroup.getProperty(PROP.CURRENT_TYPE) || (SECONDARY_TYPE_BASE + 2)
        const pIdx = Math.max(0, Math.min(PALETTE.length - 1, pType - PRIMARY_TYPE_BASE))
        const sIdx = Math.max(0, Math.min(PALETTE.length - 1, sType - SECONDARY_TYPE_BASE))
        primary = PALETTE[pIdx]
        secondary = PALETTE[sIdx]
      } catch (_e) {}
    }

    syncEditOptions()

    // 2. Backgrounds (Normal dynamic background & Pure Black AOD)
    const bgWidget = ui.createWidget(W.IMG, {
      x: 0,
      y: 0,
      w: 480,
      h: 480,
      src: `bg_${style}.png`,
      show_level: showNormal,
    })

    ui.createWidget(W.FILL_RECT, {
      x: 0,
      y: 0,
      w: 480,
      h: 480,
      color: 0x000000,
      show_level: showAod,
    })

    // 3. Outer Progress Arcs (Both sets are created, toggled via VISIBLE property)
    const stepsArcSpec = {
      center_x: 240,
      center_y: 240,
      radius: 226,
      line_width: 12,
      start_angle: 222,
      end_angle: 318,
      color: primary.normalHex,
    }
    const calArcSpec = {
      center_x: 240,
      center_y: 240,
      radius: 226,
      line_width: 12,
      start_angle: 138,
      end_angle: 42,
      color: secondary.normalHex,
    }
    const battArcSpec = {
      center_x: 240,
      center_y: 240,
      radius: 224,
      line_width: 16,
      start_angle: -54,
      end_angle: 54,
      color: primary.normalHex,
    }

    const stepsTrack = ui.createWidget(W.ARC_PROGRESS, {
      ...stepsArcSpec,
      color: TRACK_COLOR,
      level: 100,
      show_level: showNormal,
    })
    const stepsArc = ui.createWidget(W.ARC_PROGRESS, {
      ...stepsArcSpec,
      level: 0,
      show_level: showNormal,
    })

    const calTrack = ui.createWidget(W.ARC_PROGRESS, {
      ...calArcSpec,
      color: TRACK_COLOR,
      level: 100,
      show_level: showNormal,
    })
    const calArc = ui.createWidget(W.ARC_PROGRESS, {
      ...calArcSpec,
      level: 0,
      show_level: showNormal,
    })

    const battTrack = ui.createWidget(W.ARC_PROGRESS, {
      ...battArcSpec,
      color: TRACK_COLOR,
      level: 100,
      show_level: showNormal,
    })
    const battArc = ui.createWidget(W.ARC_PROGRESS, {
      ...battArcSpec,
      level: 0,
      show_level: showNormal,
    })

    // 4. Top Battery Icon + % (dynamically centered around x=240)
    const battIconWidget = ui.createWidget(W.IMG, {
      x: 172,
      y: 48,
      w: 48,
      h: 26,
      src: 'icons/battery/white/2.png',
      show_level: showNormal,
    })
    const battTextWidget = ui.createWidget(W.TEXT, {
      x: 228,
      y: 42,
      w: 92,
      h: 38,
      text: '--%',
      color: 0xFFFFFF,
      text_size: 30,
      align_h: ALIGN.LEFT,
      align_v: ALIGN.CENTER_V,
      show_level: showNormal,
    })

    // 5. Weather Icon + Temperature | Spanish Date (centered around x=240)
    const weatherDt = resolveDataType('WEATHER')
    if (weatherDt !== undefined) {
      ui.createWidget(W.IMG_LEVEL, {
        x: 96,
        y: 94,
        w: 34,
        h: 32,
        image_array: WEATHER_IMAGES,
        image_length: WEATHER_IMAGES.length,
        type: weatherDt,
        show_level: showNormal,
      })
    }
    const weatherCurDt = resolveDataType('WEATHER_CURRENT')
    if (weatherCurDt !== undefined) {
      ui.createWidget(W.TEXT_IMG, {
        x: 134,
        y: 94,
        w: 62,
        h: 34,
        font_array: DATA_FONT_TOP,
        negative_image: 'data/top/minus.png',
        unit_en: 'data/top/degree.png',
        unit_sc: 'data/top/degree.png',
        unit_tc: 'data/top/degree.png',
        invalid_image: 'data/top/invalid.png',
        align_h: ALIGN.CENTER_H,
        h_space: 1,
        type: weatherCurDt,
        show_level: showNormal,
      })
    }

    ui.createWidget(W.FILL_RECT, {
      x: 202,
      y: 96,
      w: 2,
      h: 28,
      color: DIVIDER_COLOR,
      show_level: showNormal,
    })

    // Style A: Single continuous date string
    const dateWidgetSingle = ui.createWidget(W.TEXT, {
      x: 216,
      y: 91,
      w: 190,
      h: 38,
      text: 'DOM 08 NOV',
      color: 0xFFFFFF,
      text_size: 27,
      align_h: ALIGN.LEFT,
      align_v: ALIGN.CENTER_V,
      show_level: showNormal,
    })

    // Style B: 3-part date with highlighted accent day number
    const dateWidgetDayName = ui.createWidget(W.TEXT, {
      x: 216,
      y: 91,
      w: 66,
      h: 38,
      text: 'DOM',
      color: 0xFFFFFF,
      text_size: 27,
      align_h: ALIGN.LEFT,
      align_v: ALIGN.CENTER_V,
      show_level: showNormal,
    })
    const dateWidgetDayNum = ui.createWidget(W.TEXT, {
      x: 282,
      y: 91,
      w: 42,
      h: 38,
      text: '08',
      color: primary.normalHex,
      text_size: 27,
      align_h: ALIGN.CENTER_H,
      align_v: ALIGN.CENTER_V,
      show_level: showNormal,
    })
    const dateWidgetMonth = ui.createWidget(W.TEXT, {
      x: 326,
      y: 91,
      w: 76,
      h: 38,
      text: 'NOV',
      color: 0xFFFFFF,
      text_size: 27,
      align_h: ALIGN.LEFT,
      align_v: ALIGN.CENTER_V,
      show_level: showNormal,
    })

    const aodDateWidget = ui.createWidget(W.TEXT, {
      x: 90,
      y: 280,
      w: 300,
      h: 36,
      text: 'DOM 08 NOV',
      color: 0x9E9E9E,
      text_size: 26,
      align_h: ALIGN.CENTER_H,
      align_v: ALIGN.CENTER_V,
      show_level: showAod,
    })

    // 6. Optically Centered Digital Clock (Normal + Solid Full-Size AOD)
    const normalClockDigits = Array.from({ length: 5 }, () =>
      ui.createWidget(W.IMG, {
        x: 0,
        y: 148,
        src: 'clock_a/white/0.png',
        show_level: showNormal,
      }),
    )

    const aodClockDigits = Array.from({ length: 5 }, () =>
      ui.createWidget(W.IMG, {
        x: 0,
        y: 154,
        src: 'clock_aod/white/0.png',
        show_level: showAod,
      }),
    )

    // 7. Biometric Cards / Pill (HRV | RHR | BIO | PAI)
    const cardDefs = [
      { label: 'HRV', dataKey: 'HRV' },
      { label: 'RHR', dataKey: 'RHR' },
      { label: 'BIO', dataKey: 'BIO_CHARGE' },
      { label: 'PAI', dataKey: 'PAI_WEEKLY' },
    ]

    const cardLabelWidgets = []
    const cardValueWidgets = []
    let rhrValueWidget = null

    cardDefs.forEach((spec) => {
      const boxW = 80
      const boxX = 0

      const lbl = ui.createWidget(W.TEXT, {
        x: boxX,
        y: 285,
        w: boxW,
        h: 24,
        text: spec.label,
        color: primary.normalHex,
        text_size: 20,
        align_h: ALIGN.CENTER_H,
        align_v: ALIGN.CENTER_V,
        show_level: showNormal,
      })
      cardLabelWidgets.push(lbl)

      let valWidget = null
      if (spec.dataKey === 'RHR') {
        rhrValueWidget = ui.createWidget(W.TEXT, {
          x: boxX,
          y: 309,
          w: boxW,
          h: 38,
          text: '--',
          color: 0xFFFFFF,
          text_size: 33,
          align_h: ALIGN.CENTER_H,
          align_v: ALIGN.CENTER_V,
          show_level: showNormal,
        })
        valWidget = rhrValueWidget
      } else {
        const dt = resolveDataType(spec.dataKey)
        if (dt !== undefined) {
          valWidget = ui.createWidget(W.TEXT_IMG, {
            x: boxX,
            y: 312,
            w: boxW,
            h: 36,
            font_array: DATA_FONT_WHITE,
            invalid_image: 'data/white/invalid.png',
            align_h: ALIGN.CENTER_H,
            h_space: 1,
            type: dt,
            show_level: showNormal,
          })
        } else {
          valWidget = ui.createWidget(W.TEXT, {
            x: boxX,
            y: 309,
            w: boxW,
            h: 38,
            text: '--',
            color: 0x8E8E8E,
            text_size: 32,
            align_h: ALIGN.CENTER_H,
            align_v: ALIGN.CENTER_V,
            show_level: showNormal,
          })
        }
      }
      cardValueWidgets.push(valWidget)
    })

    // 8. Bottom Heart Rate + Sparkline
    ui.createWidget(W.IMG, {
      x: 192,
      y: 374,
      w: 34,
      h: 32,
      src: 'icons/heart.png',
      show_level: showNormal,
    })

    const hrDt = resolveDataType('HEART')
    if (hrDt !== undefined) {
      ui.createWidget(W.TEXT_IMG, {
        x: 234,
        y: 372,
        w: 88,
        h: 36,
        font_array: DATA_FONT_WHITE,
        invalid_image: 'data/white/invalid.png',
        align_h: ALIGN.LEFT,
        h_space: 1,
        type: hrDt,
        show_level: showNormal,
      })
    }

    const sparklineWidget = ui.createWidget(W.GRADKIENT_POLYLINE, {
      x: SPARK_BOX.x,
      y: SPARK_BOX.y,
      w: SPARK_BOX.w,
      h: SPARK_BOX.h,
      line_color: HEART_COLOR,
      line_width: 3,
      show_level: showNormal,
    })

    const sparkDotWidget = ui.createWidget(W.CIRCLE, {
      center_x: -20,
      center_y: -20,
      radius: 4,
      color: HEART_COLOR,
      show_level: showNormal,
    })

    // 9. Touch Shortcuts
    const heartClickDt = resolveDataType('HEART')
    if (heartClickDt !== undefined) {
      ui.createWidget(W.IMG_CLICK, {
        x: 170,
        y: 366,
        w: 140,
        h: 52,
        src: '',
        type: heartClickDt,
        show_level: showNormal,
      })
    }
    if (weatherCurDt !== undefined) {
      ui.createWidget(W.IMG_CLICK, {
        x: 92,
        y: 90,
        w: 106,
        h: 40,
        src: '',
        type: weatherCurDt,
        show_level: showNormal,
      })
    }

    // 10. Sensors
    const timeSensor = new sensor.Time()
    const batterySensor = new sensor.Battery()
    const heartSensor = new sensor.HeartRate()
    const stepSensor = new sensor.Step()
    const calorieSensor = new sensor.Calorie()

    // 11. Dynamic Layout and Appearance Logic
    const applyLayoutAndColors = () => {
      const isStyleA = style === 'a'

      // Background
      bgWidget.setProperty(PROP.SRC, `bg_${style}.png`)

      // Arcs visibility & colors
      stepsTrack.setProperty(PROP.VISIBLE, isStyleA)
      stepsArc.setProperty(PROP.VISIBLE, isStyleA)
      calTrack.setProperty(PROP.VISIBLE, isStyleA)
      calArc.setProperty(PROP.VISIBLE, isStyleA)

      battTrack.setProperty(PROP.VISIBLE, !isStyleA)
      battArc.setProperty(PROP.VISIBLE, !isStyleA)

      if (isStyleA) {
        stepsArc.setProperty(PROP.COLOR, primary.normalHex)
        stepsArc.setProperty(PROP.MORE, {
          ...stepsArcSpec,
          color: primary.normalHex,
        })
        calArc.setProperty(PROP.COLOR, secondary.normalHex)
        calArc.setProperty(PROP.MORE, {
          ...calArcSpec,
          color: secondary.normalHex,
        })
      } else {
        battArc.setProperty(PROP.COLOR, primary.normalHex)
        battArc.setProperty(PROP.MORE, {
          ...battArcSpec,
          color: primary.normalHex,
        })
      }

      // Date widgets
      dateWidgetSingle.setProperty(PROP.VISIBLE, isStyleA)
      dateWidgetDayName.setProperty(PROP.VISIBLE, !isStyleA)
      dateWidgetDayNum.setProperty(PROP.VISIBLE, !isStyleA)
      dateWidgetDayNum.setProperty(PROP.COLOR, primary.normalHex)
      dateWidgetMonth.setProperty(PROP.VISIBLE, !isStyleA)

      // Biometric columns layout & colors
      const colCenters = isStyleA ? [104, 195, 286, 377] : [100, 194, 286, 380]
      const rightColColor = isStyleA ? secondary.normalHex : primary.normalHex
      const cardColors = [
        primary.normalHex,
        primary.normalHex,
        rightColColor,
        rightColColor,
      ]

      for (let idx = 0; idx < 4; idx++) {
        const cx = colCenters[idx]
        const boxW = 80
        const boxX = cx - boxW / 2
        if (cardLabelWidgets[idx]) {
          cardLabelWidgets[idx].setProperty(PROP.X, boxX)
          cardLabelWidgets[idx].setProperty(PROP.COLOR, cardColors[idx])
        }
        if (cardValueWidgets[idx]) {
          cardValueWidgets[idx].setProperty(PROP.X, boxX)
        }
      }

      // Clock baseline Y
      const clockY = isStyleA ? 148 : 146
      for (let i = 0; i < 5; i++) {
        normalClockDigits[i].setProperty(PROP.Y, clockY)
      }
    }

    const layoutGlyphRow = (widgets, chars, folderPrefix, accentKey, metricSet, gapDigit, gapColon) => {
      let totalW = 0
      const widths = []
      for (let i = 0; i < 5; i++) {
        const ch = chars[i]
        const w = ch === null ? 0 : (metricSet[ch]?.w || 0)
        widths.push(w)
        if (ch !== null) {
          totalW += w
          if (i < 4) {
            totalW += i === 1 || i === 2 ? gapColon : gapDigit
          }
        }
      }
      let curX = Math.round((480 - totalW) / 2)
      for (let i = 0; i < 5; i++) {
        const ch = chars[i]
        const widget = widgets[i]
        if (ch === null) {
          widget.setProperty(PROP.VISIBLE, false)
          continue
        }
        const colorFolder = i >= 3 ? accentKey : 'white'
        const fname = ch === ':' ? 'colon.png' : `${ch}.png`
        widget.setProperty(PROP.VISIBLE, true)
        widget.setProperty(PROP.X, curX)
        widget.setProperty(PROP.SRC, `${folderPrefix}/${colorFolder}/${fname}`)
        curX += widths[i] + (i === 1 || i === 2 ? gapColon : gapDigit)
      }
    }

    const updateTime = () => {
      const hourFmt = timeSensor.getHourFormat()
      const rawHour = timeSensor.getFormatHour()
      const min = timeSensor.getMinutes()
      const hourStr = hourFmt === 0 ? String(rawHour) : String(rawHour).padStart(2, '0')
      const minStr = String(min).padStart(2, '0')

      const chars = [
        hourStr.length === 2 ? hourStr[0] : null,
        hourStr.length === 2 ? hourStr[1] : hourStr[0],
        ':',
        minStr[0],
        minStr[1],
      ]

      layoutGlyphRow(normalClockDigits, chars, `clock_${style}`, primary.key, GLYPH_METRICS[style], 8, 12)
      layoutGlyphRow(aodClockDigits, chars, 'clock_aod', primary.key, GLYPH_METRICS.aod, 8, 12)
    }

    const updateDate = () => {
      const wd = DAYS_ES[timeSensor.getDay()] || 'LUN'
      const dd = String(timeSensor.getDate()).padStart(2, '0')
      const mm = MONTHS_ES[timeSensor.getMonth()] || 'ENE'
      if (dateWidgetSingle) {
        dateWidgetSingle.setProperty(PROP.TEXT, `${wd} ${dd} ${mm}`)
      }
      if (dateWidgetDayName) {
        dateWidgetDayName.setProperty(PROP.TEXT, wd)
        dateWidgetDayNum.setProperty(PROP.TEXT, dd)
        dateWidgetMonth.setProperty(PROP.TEXT, mm)
      }
      aodDateWidget.setProperty(PROP.TEXT, `${wd} ${dd} ${mm}`)
    }

    const updateBattery = () => {
      const battIconColor = style === 'b' ? primary.key : 'white'
      const pct = Math.max(0, Math.min(100, batterySensor.getCurrent() || 0))
      const lvlIdx = pct <= 15 ? 0 : pct <= 35 ? 1 : pct <= 60 ? 2 : pct <= 85 ? 3 : 4
      const txt = `${pct}%`
      const textW = txt.length * 17 + 4
      const totalW = 48 + 8 + textW
      const startX = Math.round((480 - totalW) / 2)
      battIconWidget.setProperty(PROP.X, startX)
      battIconWidget.setProperty(PROP.SRC, `icons/battery/${battIconColor}/${lvlIdx}.png`)
      battTextWidget.setProperty(PROP.X, startX + 56)
      battTextWidget.setProperty(PROP.TEXT, txt)

      if (style === 'b' && battArc) {
        battArc.setProperty(PROP.MORE, {
          ...battArcSpec,
          color: primary.normalHex,
          level: pct,
        })
      }
    }

    const updateProgressArcs = () => {
      if (style !== 'a') return

      if (stepsArc && stepSensor) {
        const cur = stepSensor.getCurrent() || 0
        const tgt = Math.max(1, stepSensor.getTarget() || 8000)
        const raw = Math.round((cur * 100) / tgt)
        const lvl = cur > 0 ? Math.max(4, Math.min(100, raw)) : 0
        stepsArc.setProperty(PROP.MORE, {
          ...stepsArcSpec,
          color: primary.normalHex,
          level: lvl,
        })
      }
      if (calArc && calorieSensor) {
        const cur = calorieSensor.getCurrent() || 0
        const tgt = Math.max(1, calorieSensor.getTarget() || 500)
        const raw = Math.round((cur * 100) / tgt)
        const lvl = cur > 0 ? Math.max(4, Math.min(100, raw)) : 0
        calArc.setProperty(PROP.MORE, {
          ...calArcSpec,
          color: secondary.normalHex,
          level: lvl,
        })
      }
    }

    const updateResting = () => {
      if (!rhrValueWidget) return
      const rhr = heartSensor.getResting()
      rhrValueWidget.setProperty(PROP.TEXT, rhr && rhr > 0 ? String(rhr) : '--')
    }

    const updateSparkline = () => {
      try {
        const today = heartSensor.getToday()
        const curMin = timeSensor.getHours() * 60 + timeSensor.getMinutes()
        const pts = buildSparklinePoints(today, curMin)
        sparklineWidget.clear()
        if (pts.length >= 2) {
          sparklineWidget.addLine({ data: pts, count: pts.length })
          const last = pts[pts.length - 1]
          sparkDotWidget.setProperty(PROP.CENTER_X, SPARK_BOX.x + last.x)
          sparkDotWidget.setProperty(PROP.CENTER_Y, SPARK_BOX.y + last.y)
        } else {
          sparkDotWidget.setProperty(PROP.CENTER_X, -20)
          sparkDotWidget.setProperty(PROP.CENTER_Y, -20)
        }
      } catch (_e) {}
    }

    const refreshAll = () => {
      syncEditOptions()
      applyLayoutAndColors()
      updateTime()
      updateDate()
      updateBattery()
      updateProgressArcs()
      updateResting()
      updateSparkline()
    }

    // Attach instance refresh callback for onResume
    this._refresh = refreshAll

    // Initial render
    refreshAll()

    // Sensor event bindings
    timeSensor.onPerMinute(() => {
      // Re-check edit options and refresh
      syncEditOptions()
      applyLayoutAndColors()
      updateTime()
    })
    timeSensor.onPerDay(updateDate)
    batterySensor.onChange(updateBattery)
    heartSensor.onRestingChange(updateResting)
    heartSensor.onLastChange(updateSparkline)
    stepSensor.onChange(updateProgressArcs)
    calorieSensor.onChange(updateProgressArcs)

    // WIDGET_DELEGATE triggers resume_call whenever returning from edit screen
    ui.createWidget(W.WIDGET_DELEGATE, {
      resume_call: refreshAll,
    })

    this._cleanups.push(() => {
      try {
        batterySensor.offChange(updateBattery)
        heartSensor.offRestingChange(updateResting)
        heartSensor.offLastChange(updateSparkline)
        stepSensor.offChange(updateProgressArcs)
        calorieSensor.offChange(updateProgressArcs)
      } catch (_e) {}
    })
  },

  onDestroy() {
    if (this._cleanups) {
      this._cleanups.forEach((fn) => fn())
      this._cleanups = []
    }
  },
})

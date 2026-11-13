import * as ui from '@zos/ui'
import * as sensor from '@zos/sensor'
import { GLYPH_METRICS, PALETTE } from './glyphs'

const W = ui.widget || (typeof hmUI !== 'undefined' && hmUI.widget)
const PROP = ui.prop || (typeof hmUI !== 'undefined' && hmUI.prop)
const ALIGN = ui.align || (typeof hmUI !== 'undefined' && hmUI.align)
const SL = ui.show_level || (typeof hmUI !== 'undefined' && hmUI.show_level)

const EDIT_PRIMARY_ID = 101
const EDIT_SECONDARY_ID = 102

const PRIMARY_TYPE_BASE = 100100
const SECONDARY_TYPE_BASE = 100200

const DAYS_ES = ['', 'LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']
const MONTHS_ES = ['', 'ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']

const DATA_FONT_WHITE = Array.from({ length: 10 }, (_, i) => `data/white/${i}.png`)
const DATA_FONT_TOP = Array.from({ length: 10 }, (_, i) => `data/top/${i}.png`)
const WEATHER_IMAGES = Array.from({ length: 29 }, (_, i) => `icons/weather/${i}.png`)

const HEART_COLOR = 0xFF435A
const TRACK_COLOR = 0x2A2A2A
const DIVIDER_COLOR = 0x6E6E6E

const SPARK_BOX = { x: 160, y: 418, w: 160, h: 20 }
const FALLBACK_SPARK_REL = [
  { x: 0, y: 14 },
  { x: 12, y: 8 },
  { x: 24, y: 13 },
  { x: 36, y: 5 },
  { x: 48, y: 11 },
  { x: 60, y: 8 },
  { x: 72, y: 15 },
  { x: 84, y: 13 },
  { x: 96, y: 6 },
  { x: 108, y: 14 },
  { x: 120, y: 10 },
  { x: 132, y: 5 },
  { x: 144, y: 11 },
  { x: 160, y: 12 },
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

  const padY = 2
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

  build() {
    const showNormal = SL.ONLY_NORMAL
    const showAod = SL.ONLY_AOD
    const showEdit = SL.ONLY_EDIT

    // 1. Editable Color Selectors (Arcs/Pills Accent + Minute Digit Color)
    // IMPORTANT: Do NOT set show_level: showEdit on WATCHFACE_EDIT_GROUP!
    ui.createWidget(W.WATCHFACE_EDIT_MASK, {
      x: 0,
      y: 0,
      w: 480,
      h: 480,
      src: 'editor/mask.png',
      show_level: showEdit,
    })

    const primaryGroup = ui.createWidget(W.WATCHFACE_EDIT_GROUP, {
      edit_id: EDIT_PRIMARY_ID,
      x: 72,
      y: 162,
      w: 156,
      h: 136,
      select_image: 'editor/select.png',
      un_select_image: 'editor/unselect.png',
      default_type: PRIMARY_TYPE_BASE + 0, // Lavender default
      optional_types: PALETTE.map((c, idx) => ({
        type: PRIMARY_TYPE_BASE + idx,
        preview: `editor/primary_${c.key}.png`,
        title_en: `Tema: ${c.name}`,
        title_sc: `Tema: ${c.name}`,
        title_tc: `Tema: ${c.name}`,
      })),
      count: PALETTE.length,
      tips_BG: 'editor/tips.png',
      tips_x: 18,
      tips_y: 142,
      tips_width: 120,
      tips_margin: 4,
    })

    const secondaryGroup = ui.createWidget(W.WATCHFACE_EDIT_GROUP, {
      edit_id: EDIT_SECONDARY_ID,
      x: 252,
      y: 162,
      w: 156,
      h: 136,
      select_image: 'editor/select.png',
      un_select_image: 'editor/unselect.png',
      default_type: SECONDARY_TYPE_BASE + 1, // White default
      optional_types: PALETTE.map((c, idx) => ({
        type: SECONDARY_TYPE_BASE + idx,
        preview: `editor/secondary_${c.key}.png`,
        title_en: `Min: ${c.name}`,
        title_sc: `Min: ${c.name}`,
        title_tc: `Min: ${c.name}`,
      })),
      count: PALETTE.length,
      tips_BG: 'editor/tips.png',
      tips_x: 18,
      tips_y: 142,
      tips_width: 120,
      tips_margin: 4,
    })

    const readTheme = () => {
      const pRaw = primaryGroup.getProperty(PROP.CURRENT_TYPE)
      const sRaw = secondaryGroup.getProperty(PROP.CURRENT_TYPE)
      const pI = Math.max(0, Math.min(PALETTE.length - 1, (typeof pRaw === 'number' && pRaw >= PRIMARY_TYPE_BASE ? pRaw : PRIMARY_TYPE_BASE + 0) - PRIMARY_TYPE_BASE))
      const sI = Math.max(0, Math.min(PALETTE.length - 1, (typeof sRaw === 'number' && sRaw >= SECONDARY_TYPE_BASE ? sRaw : SECONDARY_TYPE_BASE + 1) - SECONDARY_TYPE_BASE))
      return { primary: PALETTE[pI], secondary: PALETTE[sI] }
    }

    let { primary, secondary } = readTheme()

    // 2. Background (Top Battery Capsule + Left Biometric Pill in primary, Right Biometric Pill in secondary)
    const bgWidget = ui.createWidget(W.IMG, {
      x: 0,
      y: 0,
      w: 480,
      h: 480,
      src: `bg_${primary.key}.png`,
      show_level: showNormal,
    })

    const rightPillWidget = ui.createWidget(W.IMG, {
      x: 244,
      y: 294,
      w: 168,
      h: 70,
      src: `pills/pill_${secondary.key}.png`,
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

    // 3. Slim Left & Right Perimeter Progress Arcs
    const stepsArcSpec = {
      center_x: 240,
      center_y: 240,
      radius: 228,
      line_width: 7,
      start_angle: 222,
      end_angle: 318,
      color: primary.normalHex,
    }
    const calArcSpec = {
      center_x: 240,
      center_y: 240,
      radius: 228,
      line_width: 7,
      start_angle: 138,
      end_angle: 42,
      color: primary.normalHex,
    }

    ui.createWidget(W.ARC_PROGRESS, {
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

    ui.createWidget(W.ARC_PROGRESS, {
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

    // 4. Top Battery Inside Capsule
    const battIconWidget = ui.createWidget(W.IMG, {
      x: 182,
      y: 48,
      w: 44,
      h: 22,
      src: 'icons/battery/white/2.png',
      show_level: showNormal,
    })
    const battTextWidget = ui.createWidget(W.TEXT, {
      x: 234,
      y: 40,
      w: 76,
      h: 36,
      text: '--%',
      color: 0xFFFFFF,
      text_size: 28,
      align_h: ALIGN.LEFT,
      align_v: ALIGN.CENTER_V,
      show_level: showNormal,
    })

    // 5. Weather Icon + Temperature | Spanish Date (DOM & NOV in accent, 08 in white)
    const weatherDt = resolveDataType('WEATHER')
    if (weatherDt !== undefined) {
      ui.createWidget(W.IMG_LEVEL, {
        x: 96,
        y: 110,
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
        y: 110,
        w: 60,
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
      x: 198,
      y: 110,
      w: 2,
      h: 28,
      color: DIVIDER_COLOR,
      show_level: showNormal,
    })

    const dateWidgetDayName = ui.createWidget(W.TEXT, {
      x: 214,
      y: 106,
      w: 70,
      h: 38,
      text: 'DOM',
      color: primary.normalHex,
      text_size: 27,
      align_h: ALIGN.LEFT,
      align_v: ALIGN.CENTER_V,
      show_level: showNormal,
    })
    const dateWidgetDayNum = ui.createWidget(W.TEXT, {
      x: 286,
      y: 106,
      w: 44,
      h: 38,
      text: '08',
      color: 0xFFFFFF,
      text_size: 27,
      align_h: ALIGN.CENTER_H,
      align_v: ALIGN.CENTER_V,
      show_level: showNormal,
    })
    const dateWidgetMonth = ui.createWidget(W.TEXT, {
      x: 332,
      y: 106,
      w: 76,
      h: 38,
      text: 'NOV',
      color: primary.normalHex,
      text_size: 27,
      align_h: ALIGN.LEFT,
      align_v: ALIGN.CENTER_V,
      show_level: showNormal,
    })

    const aodDateWidget = ui.createWidget(W.TEXT, {
      x: 90,
      y: 282,
      w: 300,
      h: 36,
      text: 'DOM 08 NOV',
      color: 0x9E9E9E,
      text_size: 26,
      align_h: ALIGN.CENTER_H,
      align_v: ALIGN.CENTER_V,
      show_level: showAod,
    })

    // 6. Optically Centered Digital Clock with Triple-Dot Colon (⋮)
    const normalClockDigits = Array.from({ length: 5 }, () =>
      ui.createWidget(W.IMG, {
        x: 0,
        y: 170,
        src: 'clock/white/0.png',
        show_level: showNormal,
      }),
    )

    const aodClockDigits = Array.from({ length: 5 }, () =>
      ui.createWidget(W.IMG, {
        x: 0,
        y: 156,
        src: 'clock_aod/white/0.png',
        show_level: showAod,
      }),
    )

    // 7. Dual Rounded Biometric Pills (HRV | RHR and BIO | PAI)
    const colCenters = [111, 193, 287, 369]
    const cardSpecs = [
      { label: 'HRV', dataKey: 'HRV' },
      { label: 'RHR', dataKey: 'RHR' },
      { label: 'BIO', dataKey: 'BIO_CHARGE' },
      { label: 'PAI', dataKey: 'PAI_WEEKLY' },
    ]

    let rhrValueWidget = null
    const labelWidgets = []

    cardSpecs.forEach((spec, idx) => {
      const cx = colCenters[idx]
      const boxW = 78
      const boxX = cx - boxW / 2
      const isRightPill = idx >= 2

      labelWidgets.push(
        ui.createWidget(W.TEXT, {
          x: boxX,
          y: 299,
          w: boxW,
          h: 22,
          text: spec.label,
          color: isRightPill ? secondary.normalHex : primary.normalHex,
          text_size: 19,
          align_h: ALIGN.CENTER_H,
          align_v: ALIGN.CENTER_V,
          show_level: showNormal,
        }),
      )

      if (spec.dataKey === 'RHR') {
        rhrValueWidget = ui.createWidget(W.TEXT, {
          x: boxX,
          y: 318,
          w: boxW,
          h: 36,
          text: '--',
          color: 0xFFFFFF,
          text_size: 32,
          align_h: ALIGN.CENTER_H,
          align_v: ALIGN.CENTER_V,
          show_level: showNormal,
        })
      } else {
        const dt = resolveDataType(spec.dataKey)
        if (dt !== undefined) {
          ui.createWidget(W.TEXT_IMG, {
            x: boxX,
            y: 321,
            w: boxW,
            h: 34,
            font_array: DATA_FONT_WHITE,
            invalid_image: 'data/white/invalid.png',
            align_h: ALIGN.CENTER_H,
            h_space: 1,
            type: dt,
            show_level: showNormal,
          })
        } else {
          ui.createWidget(W.TEXT, {
            x: boxX,
            y: 318,
            w: boxW,
            h: 36,
            text: '--',
            color: 0xFFFFFF,
            text_size: 32,
            align_h: ALIGN.CENTER_H,
            align_v: ALIGN.CENTER_V,
            show_level: showNormal,
          })
        }
      }
    })

    // 8. Bottom Heart Rate + Sparkline
    ui.createWidget(W.IMG, {
      x: 194,
      y: 380,
      w: 34,
      h: 32,
      src: 'icons/heart.png',
      show_level: showNormal,
    })

    const hrDt = resolveDataType('HEART')
    if (hrDt !== undefined) {
      ui.createWidget(W.TEXT_IMG, {
        x: 236,
        y: 378,
        w: 88,
        h: 34,
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
      radius: 3,
      color: HEART_COLOR,
      show_level: showNormal,
    })

    // 9. Touch Shortcuts
    if (hrDt !== undefined) {
      ui.createWidget(W.IMG_CLICK, {
        x: 170,
        y: 374,
        w: 140,
        h: 48,
        src: '',
        type: hrDt,
        show_level: showNormal,
      })
    }
    if (weatherCurDt !== undefined) {
      ui.createWidget(W.IMG_CLICK, {
        x: 92,
        y: 106,
        w: 104,
        h: 40,
        src: '',
        type: weatherCurDt,
        show_level: showNormal,
      })
    }

    // 10. Sensors & Dynamic Updates
    const timeSensor = new sensor.Time()
    const batterySensor = new sensor.Battery()
    const heartSensor = new sensor.HeartRate()
    const stepSensor = new sensor.Step()
    const calorieSensor = new sensor.Calorie()

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

      layoutGlyphRow(normalClockDigits, chars, 'clock', secondary.key, GLYPH_METRICS.normal, 8, 12)
      layoutGlyphRow(aodClockDigits, chars, 'clock_aod', secondary.key, GLYPH_METRICS.aod, 8, 12)
    }

    const updateDate = () => {
      const wd = DAYS_ES[timeSensor.getDay()] || 'LUN'
      const dd = String(timeSensor.getDate()).padStart(2, '0')
      const mm = MONTHS_ES[timeSensor.getMonth()] || 'ENE'
      dateWidgetDayName.setProperty(PROP.TEXT, wd)
      dateWidgetDayNum.setProperty(PROP.TEXT, dd)
      dateWidgetMonth.setProperty(PROP.TEXT, mm)
      aodDateWidget.setProperty(PROP.TEXT, `${wd} ${dd} ${mm}`)
    }

    const updateBattery = () => {
      const pct = Math.max(0, Math.min(100, batterySensor.getCurrent() || 0))
      const lvlIdx = pct <= 15 ? 0 : pct <= 35 ? 1 : pct <= 60 ? 2 : pct <= 85 ? 3 : 4
      const txt = `${pct}%`
      const textW = txt.length * 16 + 4
      const totalW = 44 + 8 + textW
      const startX = Math.round((480 - totalW) / 2)
      battIconWidget.setProperty(PROP.X, startX)
      battIconWidget.setProperty(PROP.SRC, `icons/battery/white/${lvlIdx}.png`)
      battTextWidget.setProperty(PROP.X, startX + 52)
      battTextWidget.setProperty(PROP.TEXT, txt)
    }

    const updateProgressArcs = () => {
      const curSteps = stepSensor.getCurrent() || 0
      const tgtSteps = Math.max(1, stepSensor.getTarget() || 8000)
      const rawSteps = Math.round((curSteps * 100) / tgtSteps)
      const lvlSteps = curSteps > 0 ? Math.max(4, Math.min(100, rawSteps)) : 0
      stepsArc.setProperty(PROP.MORE, {
        ...stepsArcSpec,
        level: lvlSteps,
      })

      const curCal = calorieSensor.getCurrent() || 0
      const tgtCal = Math.max(1, calorieSensor.getTarget() || 500)
      const rawCal = Math.round((curCal * 100) / tgtCal)
      const lvlCal = curCal > 0 ? Math.max(4, Math.min(100, rawCal)) : 0
      calArc.setProperty(PROP.MORE, {
        ...calArcSpec,
        level: lvlCal,
      })
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
      const nextTheme = readTheme()
      if (nextTheme.primary.key !== primary.key || nextTheme.secondary.key !== secondary.key) {
        primary = nextTheme.primary
        secondary = nextTheme.secondary
        stepsArcSpec.color = primary.normalHex
        calArcSpec.color = primary.normalHex
        bgWidget.setProperty(PROP.SRC, `bg_${primary.key}.png`)
        rightPillWidget.setProperty(PROP.SRC, `pills/pill_${secondary.key}.png`)
        dateWidgetDayName.setProperty(PROP.COLOR, primary.normalHex)
        dateWidgetMonth.setProperty(PROP.COLOR, primary.normalHex)
        labelWidgets.forEach((lw, idx) => lw.setProperty(PROP.COLOR, idx >= 2 ? secondary.normalHex : primary.normalHex))
      }
      updateTime()
      updateDate()
      updateBattery()
      updateProgressArcs()
      updateResting()
      updateSparkline()
    }

    refreshAll()

    timeSensor.onPerMinute(updateTime)
    timeSensor.onPerDay(updateDate)
    batterySensor.onChange(updateBattery)
    heartSensor.onRestingChange(updateResting)
    heartSensor.onLastChange(updateSparkline)
    stepSensor.onChange(updateProgressArcs)
    calorieSensor.onChange(updateProgressArcs)

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

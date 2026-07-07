import { useEffect, useRef, useState } from 'react'

/**
 * Categorical slots 1 (blue) and 2 (orange) from the validated dataviz
 * palette: CVD-separated and ≥3:1 against both surfaces. s1/s2 double as
 * the cool/warm poles when a visual needs polarity fills.
 */
export const SERIES = {
  light: { s1: '#2a78d6', s2: '#eb6834', grid: 'rgba(0,0,0,0.12)' },
  dark: { s1: '#3987e5', s2: '#d95926', grid: 'rgba(255,255,255,0.16)' },
}

export type SeriesColors = (typeof SERIES)['light']

/** Is the surrounding theme dark? Judged from the inherited text color. */
function isDarkInk(el: HTMLElement): boolean {
  const m = getComputedStyle(el).color.match(/\d+/g)
  if (!m) return false
  const [r, g, b] = m.map(Number)
  return 0.299 * r + 0.587 * g + 0.114 * b > 128
}

/**
 * Shared plumbing for lesson visuals: a measured container that tracks
 * its width and the effective theme, exposing the validated series colors.
 */
export function useChartContainer() {
  const ref = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(640)
  const [dark, setDark] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const observer = new ResizeObserver(([entry]) => {
      setWidth(entry.contentRect.width)
    })
    observer.observe(el)
    setDark(isDarkInk(el))
    const scheme = window.matchMedia('(prefers-color-scheme: dark)')
    const onScheme = () => setDark(isDarkInk(el))
    scheme.addEventListener('change', onScheme)
    return () => {
      observer.disconnect()
      scheme.removeEventListener('change', onScheme)
    }
  }, [])

  return { ref, width, dark, colors: SERIES[dark ? 'dark' : 'light'] }
}

/** Size a canvas for the device pixel ratio; returns a scaled 2D context. */
export function setupCanvas(
  canvas: HTMLCanvasElement,
  width: number,
  height: number,
): CanvasRenderingContext2D | null {
  const dpr = window.devicePixelRatio || 1
  canvas.width = width * dpr
  canvas.height = height * dpr
  const ctx = canvas.getContext('2d')
  ctx?.scale(dpr, dpr)
  return ctx
}

/** Trace v(t) for t in [0,1] across the canvas width as a 2px line. */
export function traceWave(
  ctx: CanvasRenderingContext2D,
  width: number,
  midY: number,
  amp: number,
  v: (t: number) => number,
  color: string,
  dash: number[] = [],
): void {
  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.setLineDash(dash)
  ctx.beginPath()
  for (let px = 0; px <= width; px++) {
    const t = px / width
    const y = midY - v(t) * amp
    if (px === 0) ctx.moveTo(px, y)
    else ctx.lineTo(px, y)
  }
  ctx.stroke()
  ctx.setLineDash([])
}

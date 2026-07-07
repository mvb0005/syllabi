import { useEffect, useRef, useState } from 'react'
import { setupCanvas, traceWave, useChartContainer } from './chart'

const SIGNAL_F = 4 // Hz — the fixed tone being probed

/**
 * Inner-product demo: slide a template tone against a fixed 4 Hz signal
 * and watch the product's area accumulate (matched) or cancel
 * (orthogonal). This is one bin of the student's dft(), made visible.
 */
export function InnerProductProbe() {
  const { ref, width, colors } = useChartContainer()
  const wavesRef = useRef<HTMLCanvasElement>(null)
  const productRef = useRef<HTMLCanvasElement>(null)
  const [f2, setF2] = useState(7)
  const [phi, setPhi] = useState(0)

  const phiRad = (phi * Math.PI) / 180
  const signal = (t: number) => Math.cos(2 * Math.PI * SIGNAL_F * t)
  const template = (t: number) => Math.cos(2 * Math.PI * f2 * t + phiRad)

  // Normalized inner product (2/T)∫x·y dt: 1.0 for a matched template.
  let inner = 0
  const STEPS = 1000
  for (let i = 0; i < STEPS; i++) {
    const t = (i + 0.5) / STEPS
    inner += signal(t) * template(t)
  }
  inner *= 2 / STEPS

  useEffect(() => {
    const waves = wavesRef.current
    const product = productRef.current
    const container = ref.current
    if (!waves || !product || !container || width === 0) return
    const ink = getComputedStyle(container).color
    const h = 110

    const wCtx = setupCanvas(waves, width, h)
    if (wCtx) {
      wCtx.strokeStyle = colors.grid
      wCtx.beginPath()
      wCtx.moveTo(0, h / 2)
      wCtx.lineTo(width, h / 2)
      wCtx.stroke()
      traceWave(wCtx, width, h / 2, h * 0.4, signal, colors.s1)
      traceWave(wCtx, width, h / 2, h * 0.4, template, colors.s2, [6, 4])
    }

    const pCtx = setupCanvas(product, width, h)
    if (pCtx) {
      const midY = h / 2
      const amp = h * 0.4
      // Polarity fills: cool for positive area, warm for negative — the
      // inner product is the (signed) sum of exactly these regions.
      for (let px = 0; px <= width; px++) {
        const t = px / width
        const v = signal(t) * template(t)
        pCtx.fillStyle = v >= 0 ? colors.s1 : colors.s2
        pCtx.globalAlpha = 0.3
        pCtx.fillRect(px, Math.min(midY, midY - v * amp), 1, Math.abs(v) * amp)
      }
      pCtx.globalAlpha = 1
      pCtx.strokeStyle = colors.grid
      pCtx.beginPath()
      pCtx.moveTo(0, midY)
      pCtx.lineTo(width, midY)
      pCtx.stroke()
      pCtx.globalAlpha = 0.8
      traceWave(pCtx, width, midY, amp, (t) => signal(t) * template(t), ink)
      pCtx.globalAlpha = 1
    }
    // signal/template are stable closures over f2/phi; deps cover them.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [f2, phi, width, colors, ref])

  const verdict =
    Math.abs(inner) > 0.9
      ? 'matched — every lobe adds'
      : Math.abs(inner) < 0.05
        ? 'orthogonal — the areas cancel exactly'
        : 'partial overlap'

  return (
    <div ref={ref} className="my-4">
      <div className="mb-2 flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <label className="flex items-center gap-2">
          template frequency = {f2.toFixed(1)} Hz
          <input
            type="range"
            min={1}
            max={10}
            step={0.5}
            value={f2}
            onChange={(e) => setF2(Number(e.target.value))}
          />
        </label>
        <label className="flex items-center gap-2">
          template phase φ = {phi}°
          <input
            type="range"
            min={0}
            max={180}
            step={5}
            value={phi}
            onChange={(e) => setPhi(Number(e.target.value))}
          />
        </label>
      </div>
      <p className="mb-0.5 flex flex-wrap gap-x-5 text-sm text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-4" style={{ background: colors.s1 }} />
          the signal we received ({SIGNAL_F} Hz)
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block w-4 border-b-2 border-dashed"
            style={{ borderColor: colors.s2 }}
          />
          the template — the wave we&rsquo;re testing for
        </span>
      </p>
      <canvas ref={wavesRef} style={{ width: '100%', height: 110 }} />
      <p className="mb-0.5 mt-2 text-sm text-muted-foreground">
        the two curves multiplied together, point by point — blue area counts
        as +, orange as −
      </p>
      <canvas ref={productRef} style={{ width: '100%', height: 110 }} />
      <p className="mt-1 text-sm text-muted-foreground">
        net area (the &ldquo;similarity score&rdquo; ⟨x, y⟩) = {inner.toFixed(2)} ·{' '}
        {verdict}
      </p>
    </div>
  )
}

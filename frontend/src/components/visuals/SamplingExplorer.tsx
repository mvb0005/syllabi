import { useEffect, useRef, useState } from 'react'
import { setupCanvas, traceWave, useChartContainer } from './chart'

/**
 * Interactive sampling/aliasing explorer: a tone at f Hz sampled at fs Hz.
 * The reconstruction follows the samples — and lies about the frequency the
 * moment fs drops below 2f. Reference implementation in TS; the v1 plan
 * swaps the spectrum math for the student's compiled dft().
 */
export function SamplingExplorer() {
  const { ref, width, colors } = useChartContainer()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [f, setF] = useState(3)
  const [fs, setFs] = useState(14)

  const nyquist = fs / 2
  const alias = Math.abs(f - fs * Math.round(f / fs))
  const aliased = f > nyquist + 1e-9

  useEffect(() => {
    const canvas = canvasRef.current
    const container = ref.current
    if (!canvas || !container || width === 0) return
    const ink = getComputedStyle(container).color
    const height = 240
    const ctx = setupCanvas(canvas, width, height)
    if (!ctx) return

    const midY = height / 2
    const amp = height * 0.38

    // Recessive grid: midline only.
    ctx.strokeStyle = colors.grid
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(0, midY)
    ctx.lineTo(width, midY)
    ctx.stroke()

    traceWave(ctx, width, midY, amp, (t) => Math.cos(2 * Math.PI * f * t), colors.s1)
    traceWave(ctx, width, midY, amp, (t) => Math.cos(2 * Math.PI * alias * t), colors.s2, [6, 4])

    // Samples: 8px ink dots with a 2px surface ring (the ADC's keepers).
    for (let k = 0; k <= fs; k++) {
      const t = k / fs
      if (t > 1) break
      const x = t * width
      const y = midY - Math.cos(2 * Math.PI * f * t) * amp
      ctx.beginPath()
      ctx.arc(x, y, 5, 0, 2 * Math.PI)
      ctx.strokeStyle = colors.grid
      ctx.lineWidth = 2
      ctx.stroke()
      ctx.fillStyle = ink
      ctx.beginPath()
      ctx.arc(x, y, 4, 0, 2 * Math.PI)
      ctx.fill()
    }
  }, [f, fs, alias, width, colors, ref])

  return (
    <div ref={ref} className="my-4">
      <div className="mb-2 flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <label className="flex items-center gap-2">
          signal f = {f.toFixed(1)} Hz
          <input
            type="range"
            min={1}
            max={12}
            step={0.1}
            value={f}
            onChange={(e) => setF(Number(e.target.value))}
          />
        </label>
        <label className="flex items-center gap-2">
          sample rate f<sub>s</sub> = {fs.toFixed(1)} Hz
          <input
            type="range"
            min={2}
            max={24}
            step={0.5}
            value={fs}
            onChange={(e) => setFs(Number(e.target.value))}
          />
        </label>
      </div>
      <div className="mb-1 flex gap-5 text-sm text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-4" style={{ background: colors.s1 }} />
          true signal
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block w-4 border-b-2 border-dashed"
            style={{ borderColor: colors.s2 }}
          />
          reconstruction
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-current" />
          samples
        </span>
      </div>
      <canvas ref={canvasRef} style={{ width: '100%', height: 240 }} />
      <p className="mt-1 text-sm text-muted-foreground">
        highest frequency these samples can represent (the Nyquist limit,
        f<sub>s</sub>/2) = {nyquist.toFixed(1)} Hz ·{' '}
        {aliased
          ? `⚠ signal is above it — the samples are indistinguishable from a ${alias.toFixed(1)} Hz tone, and no later processing can tell the difference`
          : 'signal is below it — the reconstruction matches the signal exactly'}
      </p>
    </div>
  )
}

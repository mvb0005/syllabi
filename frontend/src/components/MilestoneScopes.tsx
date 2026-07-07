import { useEffect, useRef, useState } from 'react'
import type { VizKind } from './vizHarness'
import { setupCanvas, useChartContainer } from './visuals/chart'

/**
 * Scopes drawn by the student's own compiled code. The harness appended by
 * vizHarness.ts exposes the student's functions; after a run, the same WASM
 * artifact that ran the self-tests is re-instantiated (without running main)
 * and the scope calls the student's functions through it.
 */

interface WasmInstance {
  HEAPF32: Float32Array
  _viz_alloc?: (nFloats: number) => number
  _viz_dft?: (ptr: number, n: number) => number
  _viz_pattern?: (nElem: number, steerDeg: number, points: number) => number
}

/** Instantiate the compiled module without running main (no test output). */
async function loadInstance(js: string): Promise<WasmInstance> {
  const url = URL.createObjectURL(new Blob([js], { type: 'text/javascript' }))
  try {
    const { default: createModule } = (await import(/* @vite-ignore */ url)) as {
      default: (opts: object) => Promise<WasmInstance>
    }
    return await createModule({ noInitialRun: true, print: () => {}, printErr: () => {} })
  } finally {
    URL.revokeObjectURL(url)
  }
}

export function UserCodeScope({ kind, js }: { kind: VizKind; js: string }) {
  // The instance is tagged with the source it was built from; a result for
  // stale js is simply not rendered, so no state reset is needed when js
  // changes (and no setState runs synchronously inside the effect).
  const [loaded, setLoaded] = useState<{
    js: string
    instance: WasmInstance | null
  } | null>(null)

  useEffect(() => {
    let cancelled = false
    loadInstance(js)
      .then((instance) => !cancelled && setLoaded({ js, instance }))
      .catch(() => !cancelled && setLoaded({ js, instance: null }))
    return () => {
      cancelled = true
    }
  }, [js])

  const current = loaded?.js === js ? loaded : null
  if (!current)
    return <p className="mt-2 text-sm text-muted-foreground">loading scope…</p>
  if (!current.instance)
    return (
      <p className="mt-2 text-sm text-muted-foreground">
        ⚠ could not load your compiled module for the scope
      </p>
    )
  return kind === 'spectrum' ? (
    <SpectrumScope instance={current.instance} />
  ) : (
    <ArrayPatternScope instance={current.instance} />
  )
}

const N_FFT = 64

/** Magnitude spectrum of a complex tone, computed by the student's dft(). */
function SpectrumScope({ instance }: { instance: WasmInstance }) {
  const { ref, width, colors } = useChartContainer()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [freq, setFreq] = useState(5)

  useEffect(() => {
    const canvas = canvasRef.current
    const container = ref.current
    if (!canvas || !container || width === 0) return
    if (!instance._viz_alloc || !instance._viz_dft) return
    const ink = getComputedStyle(container).color

    const iq = new Float32Array(2 * N_FFT)
    for (let n = 0; n < N_FFT; n++) {
      iq[2 * n] = Math.cos((2 * Math.PI * freq * n) / N_FFT)
      iq[2 * n + 1] = Math.sin((2 * Math.PI * freq * n) / N_FFT)
    }
    const inPtr = instance._viz_alloc(2 * N_FFT)
    instance.HEAPF32.set(iq, inPtr / 4)
    const outPtr = instance._viz_dft(inPtr, N_FFT)
    const flat = instance.HEAPF32.subarray(outPtr / 4, outPtr / 4 + 2 * N_FFT)
    const mags = Array.from({ length: N_FFT }, (_, k) =>
      Math.hypot(flat[2 * k], flat[2 * k + 1]),
    )

    const h = 190
    const ctx = setupCanvas(canvas, width, h)
    if (!ctx) return
    const plotH = h - 22
    const barW = width / N_FFT
    ctx.strokeStyle = colors.grid
    ctx.beginPath()
    ctx.moveTo(0, plotH + 0.5)
    ctx.lineTo(width, plotH + 0.5)
    ctx.stroke()
    ctx.fillStyle = colors.s1
    for (let k = 0; k < N_FFT; k++) {
      const bh = (Math.min(mags[k], N_FFT) / N_FFT) * (plotH - 8)
      ctx.fillRect(k * barW + 1, plotH - bh, Math.max(barW - 2, 1), bh)
    }
    ctx.fillStyle = ink
    ctx.font = '11px sans-serif'
    for (const k of [0, 16, 32, 48, 63]) {
      ctx.fillText(String(k), k * barW + 2, h - 8)
    }
  }, [freq, width, colors, instance, ref])

  return (
    <div ref={ref} className="my-3">
      <p className="mb-1 text-sm font-bold">
        Spectrum scope — drawn by <em>your</em> <code>dft()</code>
      </p>
      <label className="mb-1 flex items-center gap-2 text-sm">
        tone frequency = {freq.toFixed(2)} cycles per {N_FFT}-sample window
        <input
          type="range"
          min={0}
          max={N_FFT - 1}
          step={0.25}
          value={freq}
          onChange={(e) => setFreq(Number(e.target.value))}
        />
      </label>
      <canvas ref={canvasRef} style={{ width: '100%', height: 190 }} />
      <p className="mt-1 text-sm text-muted-foreground">
        each bar is one output bin |X[k]| — the tone's energy should sit in
        bin k = {Math.round(freq) % N_FFT}
        {Number.isInteger(freq * 4) && !Number.isInteger(freq)
          ? '; a between-bin frequency smears across neighbors (spectral leakage)'
          : ''}
        {freq > N_FFT / 2
          ? ` — past bin ${N_FFT / 2} you are seeing the aliasing fold: bin ${Math.round(freq) % N_FFT || 0} is the "negative" frequency ${Math.round(freq) - N_FFT}`
          : ''}
      </p>
    </div>
  )
}

/** Array response vs. arrival angle, swept through the student's functions. */
function ArrayPatternScope({ instance }: { instance: WasmInstance }) {
  const { ref, width, colors } = useChartContainer()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [steer, setSteer] = useState(20)
  const [nElem, setNElem] = useState(8)
  const POINTS = 361

  useEffect(() => {
    const canvas = canvasRef.current
    const container = ref.current
    if (!canvas || !container || width === 0) return
    if (!instance._viz_pattern) return
    const ink = getComputedStyle(container).color

    const outPtr = instance._viz_pattern(nElem, steer, POINTS)
    const gains = instance.HEAPF32.subarray(outPtr / 4, outPtr / 4 + POINTS)

    const h = 190
    const ctx = setupCanvas(canvas, width, h)
    if (!ctx) return
    const plotH = h - 22
    const xOf = (i: number) => (i / (POINTS - 1)) * width
    ctx.strokeStyle = colors.grid
    ctx.beginPath()
    ctx.moveTo(0, plotH + 0.5)
    ctx.lineTo(width, plotH + 0.5)
    ctx.stroke()
    // steering marker
    ctx.setLineDash([4, 4])
    ctx.beginPath()
    const steerX = ((steer + 90) / 180) * width
    ctx.moveTo(steerX, 4)
    ctx.lineTo(steerX, plotH)
    ctx.stroke()
    ctx.setLineDash([])
    ctx.strokeStyle = colors.s1
    ctx.lineWidth = 2
    ctx.beginPath()
    for (let i = 0; i < POINTS; i++) {
      const y = plotH - (Math.min(gains[i], nElem) / nElem) * (plotH - 8)
      if (i === 0) ctx.moveTo(xOf(i), y)
      else ctx.lineTo(xOf(i), y)
    }
    ctx.stroke()
    ctx.fillStyle = ink
    ctx.font = '11px sans-serif'
    for (const deg of [-90, -45, 0, 45, 90]) {
      const x = ((deg + 90) / 180) * width
      ctx.fillText(`${deg}°`, Math.min(x + 2, width - 26), h - 8)
    }
  }, [steer, nElem, width, colors, instance, ref])

  return (
    <div ref={ref} className="my-3">
      <p className="mb-1 text-sm font-bold">
        Beam pattern scope — drawn by <em>your</em>{' '}
        <code>steering_vector()</code> and <code>beamform()</code>
      </p>
      <div className="mb-1 flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <label className="flex items-center gap-2">
          steering angle = {steer}°
          <input
            type="range"
            min={-60}
            max={60}
            step={1}
            value={steer}
            onChange={(e) => setSteer(Number(e.target.value))}
          />
        </label>
        <label className="flex items-center gap-2">
          antennas N = {nElem}
          <input
            type="range"
            min={2}
            max={16}
            step={1}
            value={nElem}
            onChange={(e) => setNElem(Number(e.target.value))}
          />
        </label>
      </div>
      <canvas ref={canvasRef} style={{ width: '100%', height: 190 }} />
      <p className="mt-1 text-sm text-muted-foreground">
        array response |y| vs. a test wave's arrival angle (dashed line =
        where you steered; the curve peaks there at the full gain N = {nElem},
        and the smaller humps beside it are sidelobes — directions the array
        can't help hearing a little)
      </p>
    </div>
  )
}
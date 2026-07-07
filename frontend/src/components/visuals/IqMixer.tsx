import { useEffect, useRef, useState } from 'react'
import { setupCanvas, traceWave, useChartContainer } from './chart'

/**
 * Complex downconversion demo: a carrier at f0 mixed with a tunable LO.
 * When the LO matches the carrier, I/Q collapse to DC — the carrier is
 * gone and only the (here, constant) complex envelope remains. Mistuned,
 * I/Q rotate at the offset: the spinning that carrier sync must kill.
 */
export function IqMixer() {
  const { ref, width, colors } = useChartContainer()
  const rfRef = useRef<HTMLCanvasElement>(null)
  const iqRef = useRef<HTMLCanvasElement>(null)
  const [f0, setF0] = useState(8)
  const [flo, setFlo] = useState(6)
  const [phi, setPhi] = useState(45)

  const df = f0 - flo
  const locked = Math.abs(df) < 1e-9

  useEffect(() => {
    const rf = rfRef.current
    const iq = iqRef.current
    const container = ref.current
    if (!rf || !iq || !container || width === 0) return
    const ink = getComputedStyle(container).color
    const phiRad = (phi * Math.PI) / 180
    const h = 110

    const rfCtx = setupCanvas(rf, width, h)
    if (rfCtx) {
      rfCtx.strokeStyle = colors.grid
      rfCtx.beginPath()
      rfCtx.moveTo(0, h / 2)
      rfCtx.lineTo(width, h / 2)
      rfCtx.stroke()
      rfCtx.globalAlpha = 0.65
      traceWave(rfCtx, width, h / 2, h * 0.4, (t) => Math.cos(2 * Math.PI * f0 * t + phiRad), ink)
      rfCtx.globalAlpha = 1
    }

    const iqCtx = setupCanvas(iq, width, h)
    if (iqCtx) {
      iqCtx.strokeStyle = colors.grid
      iqCtx.beginPath()
      iqCtx.moveTo(0, h / 2)
      iqCtx.lineTo(width, h / 2)
      iqCtx.stroke()
      traceWave(iqCtx, width, h / 2, h * 0.4, (t) => Math.cos(2 * Math.PI * df * t + phiRad), colors.s1)
      traceWave(iqCtx, width, h / 2, h * 0.4, (t) => Math.sin(2 * Math.PI * df * t + phiRad), colors.s2, [6, 4])
    }
  }, [f0, df, phi, width, colors, ref])

  return (
    <div ref={ref} className="my-4">
      <div className="mb-2 flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <label className="flex items-center gap-2">
          transmitter's carrier frequency f₀ = {f0.toFixed(1)} Hz
          <input
            type="range"
            min={4}
            max={16}
            step={0.5}
            value={f0}
            onChange={(e) => setF0(Number(e.target.value))}
          />
        </label>
        <label className="flex items-center gap-2">
          receiver's local oscillator (its own tuning knob) = {flo.toFixed(1)} Hz
          <input
            type="range"
            min={4}
            max={16}
            step={0.5}
            value={flo}
            onChange={(e) => setFlo(Number(e.target.value))}
          />
        </label>
        <label className="flex items-center gap-2">
          transmitted phase φ = {phi}° (the message riding the carrier)
          <input
            type="range"
            min={0}
            max={360}
            step={5}
            value={phi}
            onChange={(e) => setPhi(Number(e.target.value))}
          />
        </label>
      </div>
      <p className="mb-0.5 text-sm text-muted-foreground">
        what the antenna sees — a wave oscillating too fast to store directly
      </p>
      <canvas ref={rfRef} style={{ width: '100%', height: 110 }} />
      <p className="mb-0.5 mt-2 flex flex-wrap gap-x-5 text-sm text-muted-foreground">
        <span>what the receiver keeps — two slow measurements per instant:</span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-4" style={{ background: colors.s1 }} />
          I, &ldquo;in-phase&rdquo; (how much cosine)
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block w-4 border-b-2 border-dashed"
            style={{ borderColor: colors.s2 }}
          />
          Q, &ldquo;quadrature&rdquo; (how much sine)
        </span>
      </p>
      <canvas ref={iqRef} style={{ width: '100%', height: 110 }} />
      <p className="mt-1 text-sm text-muted-foreground">
        {locked
          ? 'tuned exactly to the carrier: I and Q go flat — two constant numbers now carry everything the wave was saying'
          : `mistuned by ${Math.abs(df).toFixed(1)} Hz: I and Q wobble at the difference frequency instead of holding still (fixing this automatically is Phase IV)`}
      </p>
    </div>
  )
}

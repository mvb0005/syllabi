import { useEffect, useRef } from 'react'
import type { TestViz } from './testviz'
import { setupCanvas, useChartContainer } from './visuals/chart'

/**
 * Test-case graphs. Each parsed TESTVIZ record renders as a small overlay
 * chart: your output as bars, the reference as a dashed line through the
 * same points, plus an explicit pass/fail verdict.
 */

function TestGraph({ viz }: { viz: TestViz }) {
  const { ref, width, colors } = useChartContainer()
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const container = ref.current
    if (!canvas || !container || width === 0) return
    const ink = getComputedStyle(container).color
    const h = 130
    const ctx = setupCanvas(canvas, width, h)
    if (!ctx) return

    const n = Math.max(viz.expected.length, viz.actual.length)
    if (n === 0) return
    const peak = Math.max(...viz.expected, ...viz.actual, 1e-6)
    const yOf = (v: number) => h - 4 - (Math.max(v, 0) / peak) * (h - 12)
    const xOf = (i: number) => (i / n) * width

    ctx.strokeStyle = colors.grid
    ctx.beginPath()
    ctx.moveTo(0, h - 4.5)
    ctx.lineTo(width, h - 4.5)
    ctx.stroke()

    // Your output: bars.
    ctx.fillStyle = colors.s1
    const barW = Math.max(width / n - 1, 1)
    for (let i = 0; i < viz.actual.length; i++) {
      const y = yOf(viz.actual[i])
      ctx.fillRect(xOf(i), y, barW, h - 4 - y)
    }

    // Reference: dashed ink line through the same points.
    ctx.strokeStyle = ink
    ctx.lineWidth = 1.5
    ctx.setLineDash([5, 3])
    ctx.beginPath()
    for (let i = 0; i < viz.expected.length; i++) {
      const x = xOf(i) + barW / 2
      const y = yOf(viz.expected[i])
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.stroke()
    ctx.setLineDash([])
  }, [viz, width, colors, ref])

  return (
    <div ref={ref} className="min-w-[16rem] flex-1">
      <p className="mb-0.5 text-sm">
        <span className="font-bold">{viz.pass ? '✓' : '✗'}</span> {viz.name}{' '}
        <span className="text-muted-foreground">
          — {viz.pass ? 'pass' : 'fail'}
        </span>
      </p>
      <canvas ref={canvasRef} style={{ width: '100%', height: 130 }} />
      <p className="mt-0.5 text-xs text-muted-foreground">
        {viz.xlabel} · bars = your output, dashed = expected
      </p>
    </div>
  )
}

export function TestGraphs({ graphs }: { graphs: TestViz[] }) {
  if (graphs.length === 0) return null
  return <div className="mt-3 flex flex-wrap gap-x-6 gap-y-4">{graphs.map((g) => (
    <TestGraph key={g.name} viz={g} />
  ))}</div>
}

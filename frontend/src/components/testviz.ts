/**
 * TESTVIZ protocol: the fixed harness prints one "TESTVIZ {json}" line per
 * test case with the reference (expected) and student (actual) series.
 * Parsing lives here, outside the component files, so Fast Refresh keeps
 * working (component modules must export only components).
 */

export interface TestViz {
  name: string
  pass: boolean
  xlabel: string
  expected: number[]
  actual: number[]
}

/** Split worker output into test graphs and the remaining printable lines. */
export function parseTestViz(lines: string[]): {
  graphs: TestViz[]
  rest: string[]
} {
  const graphs: TestViz[] = []
  const rest: string[] = []
  for (const line of lines) {
    if (line.startsWith('TESTVIZ ')) {
      try {
        graphs.push(JSON.parse(line.slice('TESTVIZ '.length)) as TestViz)
        continue
      } catch {
        // malformed — fall through so the raw line stays visible
      }
    }
    rest.push(line)
  }
  return { graphs, rest }
}

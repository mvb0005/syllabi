import { cpp } from '@codemirror/lang-cpp'
import CodeMirror from '@uiw/react-codemirror'
import { useEffect, useRef, useState } from 'react'
import { compileCpp } from '@/api/client'
import { UserCodeScope } from '@/components/MilestoneScopes'
import { TestGraphs } from '@/components/TestGraphs'
import { parseTestViz, type TestViz } from '@/components/testviz'
import { VIZ_HARNESS, detectVizKind } from '@/components/vizHarness'

const RUN_TIMEOUT_MS = 15_000

type RunState =
  | { phase: 'idle' }
  | { phase: 'compiling' }
  | { phase: 'running' }
  | { phase: 'done'; passed: boolean; output: string; graphs: TestViz[] }
  | { phase: 'compile-error'; diagnostics: string }
  | { phase: 'error'; message: string }

/**
 * Worker source: imports the compiled ES6/WASM module from a blob URL and
 * relays its stdout/stderr. Runs off the main thread so a student's
 * infinite loop can't freeze the page — the host terminates it on timeout.
 */
const WORKER_SOURCE = `
  self.onmessage = async (e) => {
    const lines = [];
    try {
      const { default: createModule } = await import(e.data);
      await createModule({
        print: (t) => lines.push(t),
        printErr: (t) => lines.push(t),
      });
      self.postMessage({ ok: true, lines });
    } catch (err) {
      self.postMessage({ ok: false, lines, error: String(err) });
    }
  };
`

interface CodeMilestoneProps {
  starterCode: string
  /** Appends this assignment's fixed (server-side) test harness on compile. */
  assignmentId: string
}

/**
 * In-browser code milestone: edit the exercise, compile it (plus the
 * assignment's fixed test harness, appended server-side) to WASM, and run
 * the tests right here. The harness prints one TESTVIZ line per case —
 * rendered as expected-vs-actual graphs — and "all tests passed" when
 * everything holds.
 */
export function CodeMilestone({ starterCode, assignmentId }: CodeMilestoneProps) {
  const [code, setCode] = useState(starterCode)
  const [state, setState] = useState<RunState>({ phase: 'idle' })
  const [scopeJs, setScopeJs] = useState<string | null>(null)
  const cleanupRef = useRef<(() => void) | null>(null)
  const vizKind = detectVizKind(starterCode)

  useEffect(() => () => cleanupRef.current?.(), [])

  const run = async () => {
    cleanupRef.current?.()
    setState({ phase: 'compiling' })
    setScopeJs(null)
    let result
    try {
      // The viz harness adds the extern "C" entry points the scope calls;
      // the backend appends the assignment's fixed test harness after it.
      result = await compileCpp(
        code + (vizKind ? VIZ_HARNESS[vizKind] : ''),
        assignmentId,
      )
    } catch (err) {
      setState({ phase: 'error', message: String(err) })
      return
    }
    if (!result.ok) {
      setState({ phase: 'compile-error', diagnostics: result.diagnostics })
      return
    }
    if (vizKind) setScopeJs(result.js)

    setState({ phase: 'running' })
    const moduleUrl = URL.createObjectURL(
      new Blob([result.js], { type: 'text/javascript' }),
    )
    const workerUrl = URL.createObjectURL(
      new Blob([WORKER_SOURCE], { type: 'text/javascript' }),
    )
    const worker = new Worker(workerUrl, { type: 'module' })
    const cleanup = () => {
      worker.terminate()
      URL.revokeObjectURL(moduleUrl)
      URL.revokeObjectURL(workerUrl)
      cleanupRef.current = null
    }
    cleanupRef.current = cleanup
    const timeout = setTimeout(() => {
      cleanup()
      setState({
        phase: 'error',
        message: `program did not finish within ${RUN_TIMEOUT_MS / 1000}s — check for an infinite loop`,
      })
    }, RUN_TIMEOUT_MS)

    worker.onmessage = (e: MessageEvent) => {
      clearTimeout(timeout)
      const { ok, lines, error } = e.data as {
        ok: boolean
        lines: string[]
        error?: string
      }
      cleanup()
      const { graphs, rest } = parseTestViz(lines)
      const output = [...rest, ...(error && !ok ? [error] : [])].join('\n')
      const passed = ok && lines.some((l) => l.includes('all tests passed'))
      setState({ phase: 'done', passed, output, graphs })
    }
    worker.onerror = (e) => {
      clearTimeout(timeout)
      cleanup()
      setState({ phase: 'error', message: e.message || 'worker failed' })
    }
    worker.postMessage(moduleUrl)
  }

  const busy = state.phase === 'compiling' || state.phase === 'running'

  return (
    <div className="my-3">
      <div className="border border-foreground/25 text-[0.85rem]">
        <CodeMirror
          value={code}
          onChange={setCode}
          extensions={[cpp()]}
          basicSetup={{ foldGutter: false, searchKeymap: false }}
          maxHeight="30rem"
        />
      </div>
      <div className="mt-2 flex items-center gap-4">
        <button
          type="button"
          onClick={run}
          disabled={busy}
          className="border border-foreground/60 px-4 py-1 text-sm font-bold uppercase tracking-widest disabled:opacity-40"
        >
          {state.phase === 'compiling'
            ? 'Compiling…'
            : state.phase === 'running'
              ? 'Running…'
              : 'Compile & run tests'}
        </button>
        {state.phase === 'done' && (
          <span className="text-sm font-bold">
            {state.passed ? '✓ all tests passed' : '✗ tests failed'}
          </span>
        )}
      </div>
      {state.phase === 'compile-error' && (
        <pre className="mt-2 max-h-64 overflow-auto border-l-2 border-foreground/60 bg-transparent p-2 text-xs whitespace-pre-wrap">
          {state.diagnostics}
        </pre>
      )}
      {state.phase === 'done' && <TestGraphs graphs={state.graphs} />}
      {state.phase === 'done' && state.output && (
        <pre className="mt-2 max-h-64 overflow-auto border-l-2 border-foreground/60 bg-transparent p-2 text-xs whitespace-pre-wrap">
          {state.output}
        </pre>
      )}
      {state.phase === 'error' && (
        <p className="mt-2 text-sm text-muted-foreground">⚠ {state.message}</p>
      )}
      {vizKind && scopeJs && state.phase === 'done' && (
        <UserCodeScope kind={vizKind} js={scopeJs} />
      )}
    </div>
  )
}

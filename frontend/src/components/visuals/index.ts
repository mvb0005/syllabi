import type { ComponentType } from 'react'
import { InnerProductProbe } from './InnerProductProbe'
import { IqMixer } from './IqMixer'
import { SamplingExplorer } from './SamplingExplorer'

/**
 * Registry of interactive lesson visuals, addressable from module markdown
 * via a fenced block:
 *
 * ```visual
 * {"name": "sampling-explorer"}
 * ```
 *
 * v0 visuals run reference implementations; the v1 pipeline (PLAN.md
 * Phase 5) swaps in the student's compiled WASM per exercise.
 */
export const VISUALS: Record<string, ComponentType> = {
  'sampling-explorer': SamplingExplorer,
  'iq-mixer': IqMixer,
  'inner-product-probe': InnerProductProbe,
}

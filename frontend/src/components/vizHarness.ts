/**
 * The extern "C" harnesses appended to a milestone's source before
 * compilation so the scopes can call the student's functions
 * (EMSCRIPTEN_KEEPALIVE exports them without flag plumbing). Kept out of
 * the component files so Fast Refresh keeps working (component modules
 * must export only components).
 */

export type VizKind = 'spectrum' | 'pattern'

/** Which scope an exercise gets, keyed on its starter code's contract. */
export function detectVizKind(starterCode: string): VizKind | null {
  if (starterCode.includes('std::vector<cf> dft(')) return 'spectrum'
  if (starterCode.includes('steering_vector(')) return 'pattern'
  return null
}

export const VIZ_HARNESS: Record<VizKind, string> = {
  spectrum: `

// ---- platform harness: powers the spectrum scope (not part of the exercise) ----
#include <emscripten.h>
extern "C" {
EMSCRIPTEN_KEEPALIVE float* viz_alloc(int n_floats) {
    static std::vector<float> buf; buf.resize(n_floats); return buf.data();
}
EMSCRIPTEN_KEEPALIVE float* viz_dft(float* iq, int n) {
    std::vector<cf> x(n);
    for (int i = 0; i < n; ++i) x[i] = cf{iq[2*i], iq[2*i+1]};
    auto X = dft(x);
    static std::vector<float> out; out.resize(2*n);
    for (int i = 0; i < n; ++i) { out[2*i] = X[i].real(); out[2*i+1] = X[i].imag(); }
    return out.data();
}
}
`,
  pattern: `

// ---- platform harness: powers the beam pattern scope (not part of the exercise) ----
#include <emscripten.h>
extern "C" {
EMSCRIPTEN_KEEPALIVE float* viz_pattern(int n_elem, float steer_deg, int points) {
    static std::vector<float> out; out.resize(points);
    const float d2r = std::numbers::pi_v<float> / 180.f;
    VectorXcf w = steering_vector(n_elem, steer_deg * d2r);
    for (int i = 0; i < points; ++i) {
        float th = (-90.f + 180.f * i / (points - 1)) * d2r;
        out[i] = std::abs(beamform(w, steering_vector(n_elem, th)));
    }
    return out.data();
}
}
`,
}

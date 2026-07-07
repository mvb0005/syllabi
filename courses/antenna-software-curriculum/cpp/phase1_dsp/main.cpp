// Phase I — DSP Foundations
// Exercise: implement dft() and fir_filter() so the self-tests below pass.
// Then: replace dft() with a radix-2 FFT, benchmark, and compare with FFTW3
// (linked automatically if found; guard with #ifdef HAVE_FFTW).

#include <cassert>
#include <cmath>
#include <complex>
#include <cstdio>
#include <numbers>
#include <vector>

using cf = std::complex<float>;

// TODO(Phase I, ex. 1): naive O(N^2) DFT.  X[k] = sum_n x[n] e^{-j 2π k n / N}
//
// The story: bin X[k] scores "how much of frequency k is in x". For each
// candidate frequency k (in cycles per N-sample window):
//   - build the comparison tone's value at sample n — a unit phasor
//     spinning k times per window, spun BACKWARDS (negative phase) so that
//     a matching tone in x gets un-spun to a standstill;
//   - multiply x[n] by it and add the product into X[k].
// If x contains frequency k, all N products point the same way and the sum
// is big (magnitude ~N). Any other frequency keeps rotating and cancels
// itself out over the window. This is the lesson's inner-product probe run
// once per frequency — nothing more.
std::vector<cf> dft(const std::vector<cf>& x) {
    std::vector<cf> X(x.size(), cf{0.f, 0.f});
    // ... your code here ...
    return X;
}

// TODO(Phase I, ex. 2): FIR filter  y[n] = sum_k h[k] x[n-k]  (zero-padded edges)
//
// The story: each output sample is a weighted blend of the most recent
// inputs — h holds the blend weights: x[n] gets h[0], x[n-1] gets h[1], ...
// Treat samples before the start as zero (skip any weight that would reach
// past the beginning), so y keeps x's length and y[0] == h[0] * x[0].
// Try h = {0.5f, 0.5f}: every output averages the current and previous
// sample — noise smooths out, slow trends pass through: a low-pass filter.
// "Finite impulse response" means the output forgets: only the last
// h.size() inputs ever matter.
//
// Same operation as the DFT, by the way: multiply a signal against a
// pattern and sum. The DFT holds the signal still and tries different
// frequency patterns; the FIR holds one pattern and slides it along in time.
std::vector<cf> fir_filter(const std::vector<cf>& x, [[maybe_unused]] const std::vector<float>& h) {
    std::vector<cf> y(x.size(), cf{0.f, 0.f});
    // ... your code here ...
    return y;
}

int main() {
    // Test 1: DFT of a pure tone concentrates energy in one bin.
    constexpr int N = 64, k0 = 5;
    std::vector<cf> tone(N);
    for (int n = 0; n < N; ++n) {
        float ph = 2.f * std::numbers::pi_v<float> * k0 * n / N;
        tone[n] = {std::cos(ph), std::sin(ph)};
    }
    auto X = dft(tone);
    assert(std::abs(X[k0]) > 0.9f * N && "DFT: tone should land in bin k0");

    // Test 2: identity FIR (h = {1}) must pass the signal through unchanged.
    std::vector<float> identity{1.f};
    auto y = fir_filter(tone, identity);
    for (int n = 0; n < N; ++n) {
        assert(std::abs(y[n] - tone[n]) < 1e-5f && "FIR: identity filter must be transparent");
    }

    std::puts("phase1_dsp: all tests passed");
    return 0;
}

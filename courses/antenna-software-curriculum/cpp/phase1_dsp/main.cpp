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

// TODO(Phase I, ex. 1): naive O(N^2) DFT of x.  X[k] = sum_n x[n] e^{-j 2π k n / N}
std::vector<cf> dft(const std::vector<cf>& x) {
    std::vector<cf> X(x.size(), cf{0.f, 0.f});
    // ... your code here ...
    return X;
}

// TODO(Phase I, ex. 2): FIR filter y[n] = sum_k h[k] x[n-k]  (zero-padded edges)
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
    auto y = fir_filter(tone, {1.0f});
    assert(std::abs(y[10] - tone[10]) < 1e-5f && "FIR: identity filter failed");

    std::puts("phase1_dsp: all tests passed");
    return 0;
}

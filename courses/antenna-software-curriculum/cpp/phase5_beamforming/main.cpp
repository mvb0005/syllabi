// Phase V — Phased Arrays & Beamforming
// Exercise: implement steering_vector() and beamform() with Eigen so an
// 8-element λ/2 array steered at the source achieves the full N-fold gain.
// Extensions: null steering, MVDR weights, MUSIC DoA spectrum, 8×8 planar.

#include <Eigen/Dense>
#include <cassert>
#include <cmath>
#include <complex>
#include <cstdio>
#include <numbers>

using Eigen::VectorXcf;
using cf = std::complex<float>;

// TODO(Phase V, ex. 1): steering vector a_n(θ) = e^{ j k d n sinθ },
// n = 0..N-1, with d = λ/2 so kd = π.  theta in radians.
VectorXcf steering_vector(int N, [[maybe_unused]] float theta) {
    VectorXcf a = VectorXcf::Zero(N);
    // ... your code here ...
    return a;
}

// TODO(Phase V, ex. 2): conventional beamformer output  y = wᴴ x
cf beamform([[maybe_unused]] const VectorXcf& w, [[maybe_unused]] const VectorXcf& x) {
    // ... your code here ...
    return {0.f, 0.f};
}

int main() {
    constexpr int N = 8;
    const float theta0 = 20.f * std::numbers::pi_v<float> / 180.f;

    VectorXcf x = steering_vector(N, theta0);   // unit-amplitude plane wave
    VectorXcf w = steering_vector(N, theta0);   // matched (steered) weights

    float gain = std::abs(beamform(w, x));
    assert(std::abs(gain - float(N)) < 1e-3f && "beamformer: expected coherent gain N");

    // Off-steer check: pointing 40° away must lose ≥ 10 dB.
    VectorXcf w_off = steering_vector(N, theta0 + 40.f * std::numbers::pi_v<float> / 180.f);
    float leak = std::abs(beamform(w_off, x));
    assert(leak < gain * 0.316f && "beamformer: off-axis rejection too weak");

    std::puts("phase5_beamforming: all tests passed");
    return 0;
}

// Phase II — Digital Modulation
// Exercise: implement a Gray-coded QPSK mapper and hard-decision slicer so the
// round-trip test passes.  Extensions: 16-QAM, RRC pulse shaping, AWGN + BER
// sweep reproducing Figure 1 of the curriculum site.

#include <cassert>
#include <complex>
#include <cstdint>
#include <cstdio>
#include <random>
#include <vector>

using cf = std::complex<float>;

// TODO(Phase II, ex. 1): map bit pairs to Gray-coded QPSK, unit average energy.
//   00 -> (+1+j)/√2   01 -> (-1+j)/√2   11 -> (-1-j)/√2   10 -> (+1-j)/√2
std::vector<cf> qpsk_mod([[maybe_unused]] const std::vector<uint8_t>& bits) {
    std::vector<cf> syms(bits.size() / 2);
    // ... your code here ...
    return syms;
}

// TODO(Phase II, ex. 2): hard-decision demapper (nearest constellation point).
std::vector<uint8_t> qpsk_demod([[maybe_unused]] const std::vector<cf>& syms) {
    std::vector<uint8_t> bits(syms.size() * 2, 0);
    // ... your code here ...
    return bits;
}

int main() {
    std::mt19937 rng(42);
    std::vector<uint8_t> bits(2000);
    for (auto& b : bits) b = rng() & 1;

    auto rx = qpsk_demod(qpsk_mod(bits));
    assert(rx == bits && "QPSK: noiseless round trip must be error-free");

    std::puts("phase2_modulation: all tests passed");
    return 0;
}

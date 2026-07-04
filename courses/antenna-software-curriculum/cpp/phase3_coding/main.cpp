// Phase III — Channel Coding
// Exercise: implement a rate-1/2, constraint-length-3 convolutional encoder
// (generators g0 = 111, g1 = 101 — the classic K=3 code) and a hard-decision
// Viterbi decoder.  The test encodes, flips two bits, and expects perfect
// recovery.  Extension: soft decisions, then LDPC via aff3ct.

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <vector>

// TODO(Phase III, ex. 1): convolutional encoder, zero-terminated (append K-1 zeros).
std::vector<uint8_t> conv_encode([[maybe_unused]] const std::vector<uint8_t>& bits) {
    std::vector<uint8_t> out;
    // ... your code here ...
    return out;
}

// TODO(Phase III, ex. 2): Viterbi decoder — 4 states, Hamming branch metrics,
// traceback from the zero state.
std::vector<uint8_t> viterbi_decode([[maybe_unused]] const std::vector<uint8_t>& coded, size_t n_info) {
    std::vector<uint8_t> out(n_info, 0);
    // ... your code here ...
    return out;
}

int main() {
    std::vector<uint8_t> info = {1,0,1,1,0,0,1,0,1,1,1,0,0,1,0,1};
    auto coded = conv_encode(info);
    assert(coded.size() == 2 * (info.size() + 2) && "encoder: wrong output length");

    coded[5] ^= 1;                      // inject two channel errors
    coded[20] ^= 1;

    auto decoded = viterbi_decode(coded, info.size());
    assert(decoded == info && "Viterbi: failed to correct 2 errors");

    std::puts("phase3_coding: all tests passed");
    return 0;
}

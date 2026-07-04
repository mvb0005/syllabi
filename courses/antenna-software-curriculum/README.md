# A Practitioner's Curriculum in Algorithms for Applied Antenna Software Systems

A six-phase, project-driven C++ curriculum: raw IQ samples → software modem →
digital beamformer. The curriculum itself is published as a scholarly,
paper-styled website (LaTeX math via KaTeX, figures computed in-browser), and
every milestone has a stubbed C++ exercise with a self-test.

## Layout

```
docs/   The website (single self-contained page, GitHub Pages ready)
cpp/    CMake workspace — one target per phase, TODO stubs + failing tests
```

## Build the exercises

```sh
git clone https://github.com/<your-username>/antenna-curriculum.git
cd antenna-curriculum/cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build          # tests fail until you implement the TODOs
```

Optional dependencies (targets are skipped gracefully if missing):

```sh
sudo apt install libeigen3-dev libfftw3-dev   # Debian/Ubuntu
brew install eigen fftw                        # macOS
```

## Publish the site

```sh
git init && git add -A && git commit -m "curriculum v1"
gh repo create antenna-curriculum --public --source . --push
```

Then in the repository settings: **Pages → Deploy from branch → `main` /
`docs`**. The page will be served at
`https://<your-username>.github.io/antenna-curriculum/`.

To preview locally: `python3 -m http.server -d docs` and open
<http://localhost:8000>. (KaTeX loads from a CDN, so an internet connection is
required for math rendering.)

## Curriculum summary

| Phase | Topic | Milestone |
|---|---|---|
| I | DSP foundations | FFT + FIR by hand; IQ spectrum analyzer |
| II | Digital modulation | QAM modem, BER validated against theory |
| III | Channel coding | Viterbi decoder; LDPC coding gain via aff3ct |
| IV | Synchronization | Carrier/timing recovery, Doppler correction |
| V | Phased arrays | 8×8 Eigen beamformer: steer, null, sweep |
| VI | Systems integration | GNU Radio blocks, RTL-SDR, real-time discipline |

**Capstone:** a multithreaded end-to-end link simulator — bits → LDPC → OFDM →
AWGN + Doppler → sync → demod → decode → bits — benchmarked in samples/sec.

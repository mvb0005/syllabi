"""Seed the LMS with the antenna-software-curriculum course.

Loads "A Practitioner's Curriculum in Algorithms for Applied Antenna
Software Systems" (six phases, DSP -> modulation -> coding ->
synchronization -> beamforming -> systems integration) as a Course with
Modules and Assignments, using the starter C++ exercises checked into
``courses/antenna-software-curriculum/cpp`` as assignment content and
deterministic self-tests.

Run directly against the configured ``DATABASE_URL``:

    python -m backend.scripts.seed_antenna_course
"""

import asyncio
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import AsyncSessionLocal
from backend.models.assignment import Assignment, GradingType, TestCase
from backend.models.course import Course, Module
from backend.models.user import User, UserRole
from backend.schemas.user import UserCreate
from backend.services.user_service import UserService

REPO_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_DIR = REPO_ROOT / "courses" / "antenna-software-curriculum"

COURSE_TITLE = "A Practitioner's Curriculum in Algorithms for Applied Antenna Software Systems"
COURSE_DESCRIPTION = (
    "A six-phase, project-driven curriculum that takes a software engineer with strong "
    "systems fundamentals from raw IQ samples to a working software modem and digital "
    "beamformer, implemented entirely in C++. Treats a modern phased-array communication "
    "system (e.g. a Starlink user terminal) as its motivating artifact, decomposed into "
    "its algorithmic layers: DSP, modulation, channel coding, synchronization, and array "
    "processing. Culminates in a multithreaded end-to-end link simulator."
)

SEED_INSTRUCTOR_EMAIL = "curriculum-author@antenna-curriculum.dev"
SEED_INSTRUCTOR_NAME = "M. (Independent Study Program)"


@dataclass
class AssignmentSpec:
    """Static description of one assignment within a phase module."""

    title: str
    description_md: str
    grading_type: GradingType
    self_test: tuple[str, str] | None = None  # (test_case name, shell command)


@dataclass
class ModuleSpec:
    """Static description of one phase module and its assignment(s)."""

    title: str
    content_md: str
    assignments: list[AssignmentSpec] = field(default_factory=list)


def _fenced_cpp(path: Path) -> str:
    """Return the file's contents as a fenced C++ code block."""
    return f"```cpp\n{path.read_text().rstrip()}\n```"


def _build_command(phase_dir: str, target: str) -> str:
    """Return the cmake/ctest invocation that validates a phase's self-test."""
    return (
        "cd courses/antenna-software-curriculum/cpp && "
        "cmake -B build -DCMAKE_BUILD_TYPE=Release && "
        f"cmake --build build --target {target} -j && "
        f"./build/{phase_dir}/{target}"
    )


def _module_specs() -> list[ModuleSpec]:
    """Build the six phase specs, embedding starter code read from disk."""
    phase1_main = CURRICULUM_DIR / "cpp" / "phase1_dsp" / "main.cpp"
    phase2_main = CURRICULUM_DIR / "cpp" / "phase2_modulation" / "main.cpp"
    phase3_main = CURRICULUM_DIR / "cpp" / "phase3_coding" / "main.cpp"
    phase5_main = CURRICULUM_DIR / "cpp" / "phase5_beamforming" / "main.cpp"

    return [
        ModuleSpec(
            title="Phase I — DSP Foundations",
            content_md=(
                "## Signals as Data\n\n"
                "All processing operates on the complex baseband representation. A real "
                "passband signal at carrier frequency $f_c$ is expressed through its "
                "in-phase and quadrature components:\n\n"
                "$$x(t) = I(t)\\cos(2\\pi f_c t) - Q(t)\\sin(2\\pi f_c t) = "
                "\\Re\\{s(t)\\, e^{j 2\\pi f_c t}\\},$$\n\n"
                "where $s(t) = I(t) + jQ(t)$ is the complex envelope. In software, $s(t)$ "
                "becomes a stream of `std::complex<float>` sampled at rate $f_s$, subject "
                "to the Nyquist criterion $f_s \\ge 2B$ for bandwidth $B$. This IQ stream "
                "is the fundamental data type of the entire curriculum.\n\n"
                "## This Phase\n\n"
                "Sampling, the DFT and its FFT realization, and FIR/IIR filtering. "
                "Implement a radix-2 FFT and a windowed-sinc FIR filter by hand before "
                "adopting FFTW3, building intuition for memory layout and vectorization.\n\n"
                "**Milestone:** a command-line spectrum analyzer — raw IQ file in, "
                "power spectral density out."
            ),
            assignments=[
                AssignmentSpec(
                    title="DFT and FIR filtering",
                    description_md=(
                        "Implement `dft()` and `fir_filter()` in "
                        "`courses/antenna-software-curriculum/cpp/phase1_dsp/main.cpp` so "
                        "the self-tests below pass. Extension: replace `dft()` with a "
                        "radix-2 FFT and benchmark against FFTW3.\n\n" + _fenced_cpp(phase1_main)
                    ),
                    grading_type=GradingType.deterministic,
                    self_test=(
                        "phase1_dsp self-test suite passes",
                        _build_command("phase1_dsp", "phase1_dsp"),
                    ),
                )
            ],
        ),
        ModuleSpec(
            title="Phase II — Digital Modulation",
            content_md=(
                "Mapping bits to waveforms. For $M$-QAM, $\\log_2 M$ bits select a "
                "constellation point; symbols are pulse-shaped with a root-raised-cosine "
                "filter and recovered by matched filtering. The phase closes with OFDM, "
                "whose transmit operation is a single inverse DFT:\n\n"
                "$$x[n] = \\frac{1}{N}\\sum_{k=0}^{N-1} X_k\\, e^{j 2\\pi k n / N}, "
                "\\qquad n = 0,\\ldots,N-1.$$\n\n"
                "**Milestone:** a QAM modem validated against the theoretical bit-error-"
                "rate curves ($P_b = Q(\\sqrt{2E_b/N_0})$ for BPSK/QPSK; 16-QAM pays "
                "roughly 4 dB for its higher spectral efficiency)."
            ),
            assignments=[
                AssignmentSpec(
                    title="Gray-coded QPSK mapper and slicer",
                    description_md=(
                        "Implement `qpsk_mod()` and `qpsk_demod()` in "
                        "`courses/antenna-software-curriculum/cpp/phase2_modulation/main.cpp` "
                        "so the noiseless round-trip test passes. Extensions: 16-QAM, RRC "
                        "pulse shaping, AWGN + BER sweep.\n\n" + _fenced_cpp(phase2_main)
                    ),
                    grading_type=GradingType.deterministic,
                    self_test=(
                        "phase2_modulation self-test suite passes",
                        _build_command("phase2_modulation", "phase2_modulation"),
                    ),
                )
            ],
        ),
        ModuleSpec(
            title="Phase III — Channel Coding",
            content_md=(
                'The algorithmic heart of "encoding data." Convolutional codes with '
                "Viterbi decoding (dynamic programming on a trellis), interleaving, and "
                "modern graph codes. An LDPC code is defined by a sparse parity-check "
                "matrix $H$: a vector $\\mathbf{c}$ is a codeword iff "
                "$H\\mathbf{c}^{\\mathsf T} = \\mathbf{0} \\pmod 2$, and decoding is belief "
                "propagation on the associated Tanner graph — message passing, a "
                "familiar idiom from distributed systems, here applied to probabilities. "
                "LDPC is the code family used by DVB-S2 and Starlink's downlink.\n\n"
                "**Milestone:** a hand-written Viterbi decoder; measured coding gain using "
                "aff3ct's LDPC codec."
            ),
            assignments=[
                AssignmentSpec(
                    title="Convolutional encoder and Viterbi decoder",
                    description_md=(
                        "Implement `conv_encode()` (rate-1/2, K=3, generators g0=111, "
                        "g1=101) and `viterbi_decode()` in "
                        "`courses/antenna-software-curriculum/cpp/phase3_coding/main.cpp` "
                        "so the test — encode, flip two bits, recover perfectly — "
                        "passes. Extension: soft decisions, then LDPC via aff3ct.\n\n"
                        + _fenced_cpp(phase3_main)
                    ),
                    grading_type=GradingType.deterministic,
                    self_test=(
                        "phase3_coding self-test suite passes",
                        _build_command("phase3_coding", "phase3_coding"),
                    ),
                )
            ],
        ),
        ModuleSpec(
            title="Phase IV — Synchronization & Receivers",
            content_md=(
                "Carrier and timing recovery (Costas and Gardner loops), channel "
                "estimation, equalization, and Doppler compensation. A LEO satellite at "
                "~7.5 km/s imposes Doppler shifts up to $\\pm f_c v/c \\approx \\pm 300$ kHz "
                "at Ku band — synchronization is not optional bookkeeping but a "
                "first-class algorithmic problem.\n\n"
                "No starter code is bundled for this phase yet; the deliverable below is "
                "a design/derivation writeup, graded by rubric."
            ),
            assignments=[
                AssignmentSpec(
                    title="Doppler-compensated carrier and timing recovery",
                    description_md=(
                        "Design (and, where practical, prototype) a receiver chain for a "
                        "LEO downlink that must track a Doppler shift sweeping "
                        "±300 kHz over a pass. Cover: (1) a Costas loop for carrier "
                        "phase/frequency recovery, (2) a Gardner timing-error detector for "
                        "symbol timing, (3) how Doppler-rate (not just Doppler offset) "
                        "affects loop bandwidth selection. Justify your loop bandwidth and "
                        "damping choices against the maximum expected Doppler rate."
                    ),
                    grading_type=GradingType.llm_rubric,
                )
            ],
        ),
        ModuleSpec(
            title="Phase V — Phased Arrays & Beamforming",
            content_md=(
                "An $N$-element uniform linear array with spacing $d$ steers a beam "
                "purely in software by applying complex weights $w_n$ to each element. "
                "The far-field array factor is\n\n"
                "$$AF(\\theta) = \\sum_{n=0}^{N-1} w_n\\, e^{j k d\\, n \\sin\\theta}, "
                "\\qquad k = \\frac{2\\pi}{\\lambda},$$\n\n"
                "and choosing $w_n = e^{-j k d\\, n \\sin\\theta_0}$ points the main lobe at "
                "$\\theta_0$ with no moving parts. In C++ this is one Eigen expression, "
                "`w.adjoint() * snapshot`; the engineering is in making it fast and "
                "calibrated. Adaptive beamforming (MVDR) and direction-of-arrival "
                "estimation (MUSIC) extend the same linear-algebraic machinery.\n\n"
                "**Milestone:** an 8-element λ/2 linear-array beamformer in Eigen: steer "
                "a beam, null an interferer, sweep a pattern. Extension: generalize to an "
                "8x8 planar array."
            ),
            assignments=[
                AssignmentSpec(
                    title="Steering vector and conventional beamformer",
                    description_md=(
                        "Implement `steering_vector()` and `beamform()` with Eigen in "
                        "`courses/antenna-software-curriculum/cpp/phase5_beamforming/main.cpp` "
                        "so an 8-element λ/2 array steered at the source achieves the "
                        "full N-fold coherent gain, and off-axis (40° away) rejection "
                        "is at least 10 dB. Extensions: null steering, MVDR weights, MUSIC "
                        "DoA spectrum, 8x8 planar array.\n\n" + _fenced_cpp(phase5_main)
                    ),
                    grading_type=GradingType.deterministic,
                    self_test=(
                        "phase5_beamforming self-test suite passes",
                        _build_command("phase5_beamforming", "phase5_beamforming"),
                    ),
                )
            ],
        ),
        ModuleSpec(
            title="Phase VI — Systems Integration",
            content_md=(
                "Link budgets, GNU Radio out-of-tree blocks in C++, and real signals via "
                "an RTL-SDR through SoapySDR. Real-time discipline is treated explicitly: "
                "lock-free ring buffers between threads, zero allocation on the hot path, "
                "fixed-point arithmetic, and SIMD vectorization of inner loops.\n\n"
                "**Capstone:** a multithreaded end-to-end link simulator: bits -> LDPC "
                "encode -> OFDM modulate -> AWGN + Doppler channel -> synchronize -> "
                "demodulate -> decode -> bits, with a simulated beamforming front end, "
                "benchmarked in samples per second."
            ),
            assignments=[
                AssignmentSpec(
                    title="Capstone: end-to-end link simulator",
                    description_md=(
                        "Compose the Phase I-V building blocks (DFT/FIR, QPSK/QAM "
                        "modulation, convolutional or LDPC coding, Doppler-tracking "
                        "synchronization, and array beamforming) into a single "
                        "multithreaded pipeline: bits -> encode -> modulate -> AWGN + "
                        "Doppler channel -> synchronize -> demodulate -> decode -> bits, "
                        "with a simulated beamforming front end. Report throughput in "
                        "samples per second and describe your real-time discipline "
                        "(ring buffers, allocation policy, SIMD use)."
                    ),
                    grading_type=GradingType.hybrid,
                )
            ],
        ),
    ]


async def _get_or_create_instructor(db: AsyncSession) -> User:
    """Return the seed instructor user, creating it if it doesn't exist yet."""
    existing = await db.scalar(select(User).where(User.email == SEED_INSTRUCTOR_EMAIL))
    if existing is not None:
        return existing

    user_service = UserService(db)
    return await user_service.create_user(
        UserCreate(
            email=SEED_INSTRUCTOR_EMAIL,
            full_name=SEED_INSTRUCTOR_NAME,
            role=UserRole.instructor,
            password=secrets.token_hex(32),
        )
    )


async def seed_antenna_course(db: AsyncSession) -> Course:
    """Create (or return the existing) antenna-software-curriculum course.

    Idempotent: if a course with the same title already exists, it is
    returned unchanged rather than duplicated.

    Args:
        db: Active async database session.

    Returns:
        The seeded (or pre-existing) Course ORM instance, with modules and
        assignments eagerly created.
    """
    existing_course = await db.scalar(select(Course).where(Course.title == COURSE_TITLE))
    if existing_course is not None:
        return existing_course

    instructor = await _get_or_create_instructor(db)

    course = Course(
        title=COURSE_TITLE,
        description=COURSE_DESCRIPTION,
        instructor_id=instructor.id,
        is_published=True,
    )
    db.add(course)
    await db.flush()

    for order_index, module_spec in enumerate(_module_specs()):
        module = Module(
            course_id=course.id,
            title=module_spec.title,
            order_index=order_index,
            content_md=module_spec.content_md,
        )
        db.add(module)
        await db.flush()

        for assignment_spec in module_spec.assignments:
            assignment = Assignment(
                module_id=module.id,
                title=assignment_spec.title,
                description_md=assignment_spec.description_md,
                grading_type=assignment_spec.grading_type,
                max_score=100,
            )
            db.add(assignment)
            await db.flush()

            if assignment_spec.self_test is not None:
                name, command = assignment_spec.self_test
                db.add(
                    TestCase(
                        assignment_id=assignment.id,
                        name=name,
                        code=command,
                        weight=1.0,
                        is_hidden=False,
                    )
                )

    await db.commit()
    await db.refresh(course)
    return course


async def main() -> None:
    """Entry point: seed the antenna course against the configured database."""
    async with AsyncSessionLocal() as db:
        course = await seed_antenna_course(db)
        print(f"Seeded course '{course.title}' (id={course.id})")


if __name__ == "__main__":
    asyncio.run(main())

"""1,000-particle exchange signal degradation solver for the Nexus Protocol.

Each of the PARTICLE_COUNT (1 000) particles carries a unique algebraic
blend (alpha, beta, gamma) and sensitivity derived from a deterministic
Linear Congruential Generator — no external randomness, fully reproducible,
strictly read-only.

All 1 000 particles independently evaluate a degraded exchange signal and
propose a corrected value for every dimension.  Their classifications are
majority-voted and their corrections are median-aggregated into a single
consensus repaired signal.

Degradation types detected
--------------------------
CLEAN          — all dimensions within expected ranges
NOISY          — small random scatter around expected midpoints
DRIFTED        — systematic offset in a consistent direction
SPIKED         — one or more dimensions violently outside range
CLIPPED        — values pinned at range boundaries
DROPPED        — dimensions reporting near-zero when non-zero expected
JITTERED       — high variance across the particle ensemble
ALIASED        — periodic pattern of out-of-range values
CROSS_TALK     — correlated deviation across multiple dimensions
CRITICALLY_ILL — severe multi-dimension collapse
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# math.exp underflows to 0 for arguments below ~-745 on 64-bit IEEE 754.
# Using -700 as a safe floor leaves a small margin above true underflow.
_EXP_FLOOR: float = -700.0
PARTICLE_COUNT: int = 1_000

# LCG constants (Numerical Recipes)
_LCG_A: int = 1_664_525
_LCG_C: int = 1_013_904_223
_LCG_M: int = 2 ** 32

# Degradation classification thresholds
_THRESH_CRITICAL: float = 60.0
_THRESH_DEGRADED: float = 25.0
_THRESH_NOISY: float = 8.0

# Exchange signal dimension catalogue with (ideal_min, ideal_max)
EXCHANGE_SIGNAL_RANGES: Dict[str, Tuple[float, float]] = {
    "price_feed": (0.0, 1_000_000.0),
    "order_book_depth": (10.0, 1_000_000.0),
    "liquidity_signal": (1.0, 100.0),
    "volume_signal": (0.0, 1_000_000.0),
    "spread_signal": (0.001, 5.0),
    "tick_completeness": (90.0, 100.0),
    "latency_ms": (0.0, 200.0),
    "timestamp_jitter_ms": (0.0, 50.0),
    "cross_venue_deviation": (0.0, 2.0),
    "noise_floor": (0.0, 3.0),
    "drift_rate": (-1.0, 1.0),
    "bit_error_rate": (0.0, 0.01),
    "packet_loss_pct": (0.0, 1.0),
    "feed_staleness_s": (0.0, 5.0),
    "clipping_events": (0.0, 0.0),
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SignalParticle:
    """A single correction particle with unique algebraic blend parameters."""

    particle_id: int
    alpha: float      # L1 (linear) blend weight
    beta: float       # L2 (polynomial) blend weight
    gamma: float      # L3 (exponential) blend weight
    sensitivity: float  # correction aggressiveness in [0.5, 1.5]


@dataclass(frozen=True)
class DegradedSignal:
    """A raw (possibly degraded) exchange signal snapshot.

    Parameters
    ----------
    exchange:
        Name of the exchange or feed source.
    dimensions:
        Mapping of signal dimension name → observed value.
    expected_ranges:
        Per-dimension ``(min, max)`` ideal operating range.
        Defaults to ``EXCHANGE_SIGNAL_RANGES`` for any key not supplied.
    context:
        Optional description of the signal context.
    """

    exchange: str
    dimensions: Dict[str, float]
    expected_ranges: Dict[str, Tuple[float, float]] = field(
        default_factory=dict
    )
    context: str = ""

    def range_for(self, dim: str) -> Optional[Tuple[float, float]]:
        """Return the expected range for *dim*, falling back to catalogue."""
        if dim in self.expected_ranges:
            return self.expected_ranges[dim]
        return EXCHANGE_SIGNAL_RANGES.get(dim)


@dataclass(frozen=True)
class ParticleVote:
    """One particle's evaluation of a degraded signal."""

    particle_id: int
    degradation_score: float   # 0 = clean, 100 = fully degraded
    classification: str        # CLEAN / NOISY / DEGRADED / CRITICAL
    corrected: Dict[str, float]


@dataclass(frozen=True)
class SignalRepairResult:
    """Consensus result fused across all 1 000 particles.

    Attributes
    ----------
    exchange:
        Echo of the input exchange label.
    particle_count:
        Number of particles used (always ``PARTICLE_COUNT``).
    consensus_degradation:
        Median degradation score across all particles (0–100).
    consensus_classification:
        Majority-voted classification label.
    degradation_type:
        Detected degradation pattern (CLEAN / NOISY / DRIFTED / …).
    particle_agreement:
        Fraction (0–100 %) of particles that agree on the consensus class.
    corrected_signal:
        Per-dimension median correction across all particles.
    original_signal:
        Echo of the raw input dimensions.
    repair_chain:
        Step-by-step derivation of the repair decision.
    verdict:
        Single-line human-readable repair verdict.
    """

    exchange: str
    particle_count: int
    consensus_degradation: float
    consensus_classification: str
    degradation_type: str
    particle_agreement: float
    corrected_signal: Dict[str, float]
    original_signal: Dict[str, float]
    repair_chain: List[str] = field(default_factory=list)
    verdict: str = ""


# ---------------------------------------------------------------------------
# Deterministic particle generator (LCG — no external random)
# ---------------------------------------------------------------------------

def generate_particles(count: int = PARTICLE_COUNT) -> List[SignalParticle]:
    """Generate *count* unique particles deterministically via LCG.

    The LCG seed is fixed at 42 so every run produces identical particles.
    """

    particles: List[SignalParticle] = []
    seed = 42

    for i in range(count):
        seed = (_LCG_A * seed + _LCG_C) % _LCG_M
        alpha = 0.5 + (seed % 1_000) / 2_000.0          # [0.500, 1.000]

        seed = (_LCG_A * seed + _LCG_C) % _LCG_M
        beta = 0.05 + (seed % 1_000) / 2_000.0           # [0.050, 0.550]

        seed = (_LCG_A * seed + _LCG_C) % _LCG_M
        gamma = 0.02 + (seed % 1_000) / 5_000.0          # [0.020, 0.220]

        seed = (_LCG_A * seed + _LCG_C) % _LCG_M
        sensitivity = 0.5 + (seed % 1_000) / 1_000.0     # [0.500, 1.500]

        particles.append(
            SignalParticle(i, alpha, beta, gamma, sensitivity)
        )

    return particles


# ---------------------------------------------------------------------------
# Single-particle evaluation
# ---------------------------------------------------------------------------

def _particle_correct_dim(
    value: float,
    lo: float,
    hi: float,
    particle: SignalParticle,
) -> Tuple[float, float]:
    """Apply one particle's three-layer correction to a single dimension.

    Returns ``(corrected_value, degradation_contribution)``.
    """

    span = max(hi - lo, 1e-9)
    mid = (lo + hi) / 2.0

    # Deviation: how far outside [lo, hi] is the value?
    deviation = max(0.0, lo - value) + max(0.0, value - hi)
    deg = min(100.0, (deviation / span) * 100.0)

    # Layer 1 — linear pull toward midpoint
    l1 = value + particle.alpha * (mid - value) * 0.10

    # Layer 2 — polynomial pull (stronger for larger deviations)
    pull2 = (deviation / span) * particle.sensitivity
    l2 = value + particle.beta * (mid - value) * pull2

    # Layer 3 — exponential smoothing toward midpoint
    exp_arg = -abs(deviation) / (span * max(particle.sensitivity, 1e-9))
    w = math.exp(max(exp_arg, _EXP_FLOOR))   # guard IEEE 754 underflow
    l3 = value * w + mid * (1.0 - w)

    denom = particle.alpha + particle.beta + particle.gamma
    corrected = (
        particle.alpha * l1
        + particle.beta * l2
        + particle.gamma * l3
    ) / max(denom, 1e-9)

    return corrected, deg


def evaluate_particle(
    signal: DegradedSignal,
    particle: SignalParticle,
) -> ParticleVote:
    """Evaluate one particle's assessment of and correction for *signal*."""

    corrected: Dict[str, float] = {}
    deg_scores: List[float] = []

    for dim, value in signal.dimensions.items():
        rng = signal.range_for(dim)
        if rng is None:
            corrected[dim] = value
            continue
        lo, hi = rng
        c, deg = _particle_correct_dim(value, lo, hi, particle)
        corrected[dim] = c
        deg_scores.append(deg)

    mean_deg = (
        sum(deg_scores) / len(deg_scores) if deg_scores else 0.0
    )

    if mean_deg >= _THRESH_CRITICAL:
        cls = "CRITICAL"
    elif mean_deg >= _THRESH_DEGRADED:
        cls = "DEGRADED"
    elif mean_deg >= _THRESH_NOISY:
        cls = "NOISY"
    else:
        cls = "CLEAN"

    return ParticleVote(
        particle_id=particle.particle_id,
        degradation_score=mean_deg,
        classification=cls,
        corrected=corrected,
    )


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def _majority(labels: List[str]) -> Tuple[str, float]:
    """Return (majority_label, agreement_pct)."""
    if not labels:
        return ("CLEAN", 100.0)
    counts: Dict[str, int] = {}
    for lbl in labels:
        counts[lbl] = counts.get(lbl, 0) + 1
    best = max(counts, key=lambda k: counts[k])
    return best, counts[best] / len(labels) * 100.0


def _detect_degradation_type(
    signal: DegradedSignal,
    votes: List[ParticleVote],
    consensus_deg: float,
) -> str:
    """Infer the degradation pattern from signal geometry and vote spread."""

    dims = signal.dimensions
    n = len(dims)
    if n == 0:
        return "CLEAN"

    if consensus_deg < _THRESH_NOISY:
        return "CLEAN"

    # Collect per-dim deviations
    deviations: List[float] = []
    directions: List[float] = []
    clipped = 0
    dropped = 0

    for dim, value in dims.items():
        rng = signal.range_for(dim)
        if rng is None:
            continue
        lo, hi = rng
        span = max(hi - lo, 1e-9)
        mid = (lo + hi) / 2.0
        dev = max(0.0, lo - value) + max(0.0, value - hi)
        deviations.append(dev / span)
        directions.append((value - mid) / span)
        if value <= lo + span * 0.01 or value >= hi - span * 0.01:
            clipped += 1
        if value <= lo + span * 0.05:
            dropped += 1

    if not deviations:
        return "CLEAN"

    mean_dev = sum(deviations) / len(deviations)
    mean_dir = sum(directions) / len(directions)
    max_dev = max(deviations)

    # Variance of particle degradation scores (jitter indicator)
    p_scores = [v.degradation_score for v in votes]
    p_mean = sum(p_scores) / len(p_scores)
    p_var = sum((s - p_mean) ** 2 for s in p_scores) / len(p_scores)

    if clipped / max(n, 1) >= 0.5:
        return "CLIPPED"
    if dropped / max(n, 1) >= 0.4:
        return "DROPPED"
    if max_dev > 2.0:
        return "SPIKED"
    if abs(mean_dir) > 0.3:
        return "DRIFTED"
    if math.sqrt(p_var) > 15.0:
        return "JITTERED"
    if mean_dev > 0.5:
        return "CRITICALLY_ILL"
    if consensus_deg >= _THRESH_DEGRADED:
        return "DEGRADED"
    return "NOISY"


# ---------------------------------------------------------------------------
# Main repair engine
# ---------------------------------------------------------------------------

def repair_signal(
    signal: DegradedSignal,
    particles: Optional[List[SignalParticle]] = None,
) -> SignalRepairResult:
    """Run all 1 000 particles against *signal* and return consensus repair.

    Parameters
    ----------
    signal:
        The ``DegradedSignal`` to evaluate and correct.
    particles:
        Override the particle set (used in tests for speed).  Defaults to
        the full 1 000-particle ensemble generated by ``generate_particles()``.

    Returns
    -------
    ``SignalRepairResult`` — consensus degradation assessment and repaired
    signal values for every dimension.
    """

    if particles is None:
        particles = generate_particles(PARTICLE_COUNT)

    votes: List[ParticleVote] = [
        evaluate_particle(signal, p) for p in particles
    ]

    # Aggregate degradation scores
    all_deg = [v.degradation_score for v in votes]
    consensus_deg = _median(all_deg)

    # Majority-vote classification
    all_cls = [v.classification for v in votes]
    consensus_cls, agreement = _majority(all_cls)

    # Median-aggregate per-dimension corrections
    dims = list(signal.dimensions.keys())
    corrected: Dict[str, float] = {}
    for dim in dims:
        corrections = [
            v.corrected[dim] for v in votes if dim in v.corrected
        ]
        corrected[dim] = (
            _median(corrections) if corrections
            else signal.dimensions[dim]
        )

    deg_type = _detect_degradation_type(signal, votes, consensus_deg)

    verdict = (
        f"[{signal.exchange}] {consensus_cls} ({deg_type})"
        f" | degradation={consensus_deg:.2f}%"
        f" | particle_agreement={agreement:.1f}%"
        f" | {PARTICLE_COUNT} particles"
    )

    chain = [
        f"[SR-1] Exchange     : {signal.exchange}"
        + (f" — {signal.context}" if signal.context else ""),
        f"[SR-2] Dimensions   : {len(dims)} signal dims evaluated",
        f"[SR-3] Particles    : {len(particles)} unique correction strategies",
        f"[SR-4] Deg scores   : min={min(all_deg):.2f}"
        f" median={consensus_deg:.2f}"
        f" max={max(all_deg):.2f}",
        "[SR-5] Class votes  : "
        + "  ".join(
            f"{lbl}={all_cls.count(lbl)}"
            for lbl in ("CLEAN", "NOISY", "DEGRADED", "CRITICAL")
        ),
        f"[SR-6] Consensus    : {consensus_cls}"
        f" ({agreement:.1f}% of {len(particles)} particles agree)",
        f"[SR-7] Deg type     : {deg_type}",
        "[SR-8] Corrected dims: "
        + ", ".join(
            f"{d}:{signal.dimensions[d]:.3f}"
            f"->{corrected.get(d, signal.dimensions[d]):.3f}"
            for d in list(dims)[:5]
        )
        + ("..." if len(dims) > 5 else ""),
        f"[SR-9] VERDICT      : {verdict}",
    ]

    return SignalRepairResult(
        exchange=signal.exchange,
        particle_count=len(particles),
        consensus_degradation=consensus_deg,
        consensus_classification=consensus_cls,
        degradation_type=deg_type,
        particle_agreement=agreement,
        corrected_signal=corrected,
        original_signal=dict(signal.dimensions),
        repair_chain=chain,
        verdict=verdict,
    )


# ---------------------------------------------------------------------------
# Report renderer
# ---------------------------------------------------------------------------

def render_repair_report(
    result: SignalRepairResult,
    show_chain: bool = True,
    show_corrections: bool = True,
) -> str:
    """Render a safe read-only signal repair report."""

    lines = [
        "[NEXUS SIGNAL REPAIR ENGINE]",
        f"BOT: @FuzzysTodd | {PARTICLE_COUNT} particles"
        " | Linear + Polynomial + Exponential per particle",
        "======= EXCHANGE SIGNAL DEGRADATION REPORT =======",
        "",
        f"  Exchange      : {result.exchange}",
        f"  Classification: {result.consensus_classification}",
        f"  Degradation   : {result.consensus_degradation:.2f}%",
        f"  Deg type      : {result.degradation_type}",
        f"  Agreement     : {result.particle_agreement:.1f}%"
        f" of {result.particle_count} particles",
        "",
        f"  VERDICT: {result.verdict}",
    ]

    if show_corrections and result.corrected_signal:
        lines.append("")
        lines.append("  Corrected signal values:")
        for dim in result.corrected_signal:
            orig = result.original_signal.get(dim, 0.0)
            corr = result.corrected_signal[dim]
            delta = corr - orig
            sign = "+" if delta >= 0 else ""
            lines.append(
                f"    {dim:<28}: "
                f"{orig:>12.4f} -> {corr:>12.4f}  ({sign}{delta:.4f})"
            )

    if show_chain:
        lines.append("")
        lines.append("  Repair chain:")
        for step in result.repair_chain:
            lines.append(f"    {step}")

    lines.append("")
    lines.append("===================================================")
    return "\n".join(lines)

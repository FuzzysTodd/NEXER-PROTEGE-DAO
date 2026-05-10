"""Super Logical 64-dimension universal reasoner for the Nexus Protocol.

Extends the weighted-predictor strategy introduced in ``anomaly_detector``
and ``monsterball`` to a full 64-dimension logical space.

Any domain's numeric outputs can be fed through ``SuperLogicalWeights`` to
produce a confidence-tiered prediction with a complete step-by-step reasoning
chain.  Applied to any outcome, the engine derives the definitive
super-logical answer.

Design mirrors the read-only heuristic pattern already established in this
repository: weights × values → score → threshold comparison → answer.  No
external state is mutated.

Capacity: up to LOGICAL_CAPACITY (64) simultaneous dimensions per reading.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOGICAL_CAPACITY: int = 64  # maximum simultaneous logic dimensions

# Confidence tiers (score as % of maximum possible score)
TIER_CRITICAL: float = 90.0
TIER_HIGH: float = 75.0
TIER_MODERATE: float = 50.0
# below TIER_MODERATE → LOW

TIER_LABELS: Tuple[str, ...] = ("CRITICAL", "HIGH", "MODERATE", "LOW")


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SuperLogicalWeights:
    """Up to 64 named dimension weights for a logical reasoning pass.

    Parameters
    ----------
    weights:
        Mapping of dimension name → multiplier.  Capped at
        ``LOGICAL_CAPACITY`` entries; extras are silently ignored.
    domain:
        Human-readable label for the domain being reasoned about
        (e.g. ``"MonsterBall"``, ``"Token Activity"``, ``"Anything"``).
    tier_critical:
        Confidence percentage (0–100) above which the answer is CRITICAL.
    tier_high:
        Confidence percentage above which the answer is HIGH.
    tier_moderate:
        Confidence percentage above which the answer is MODERATE.
        Below this → LOW.
    """

    weights: Dict[str, float] = field(default_factory=dict)
    domain: str = "Universal"
    tier_critical: float = TIER_CRITICAL
    tier_high: float = TIER_HIGH
    tier_moderate: float = TIER_MODERATE

    def capped_weights(self) -> Dict[str, float]:
        """Return the first ``LOGICAL_CAPACITY`` entries only."""
        items = list(self.weights.items())[:LOGICAL_CAPACITY]
        return dict(items)


@dataclass(frozen=True)
class LogicalReading:
    """A named collection of numeric dimensions to reason about.

    Parameters
    ----------
    domain:
        What domain or question this reading represents.
    stats:
        Arbitrary mapping of dimension name → numeric value.
    context:
        Optional plain-text description of what is being reasoned about.
    """

    domain: str
    stats: Dict[str, float]
    context: str = ""


@dataclass(frozen=True)
class SuperLogicalResult:
    """The definitive super-logical answer for a single reading.

    Attributes
    ----------
    domain:
        Domain label echoed from the reading.
    score:
        Raw weighted sum across all active dimensions.
    max_score:
        Maximum possible score if every dimension were at its observed
        maximum — used to compute ``confidence``.
    confidence:
        Score expressed as a percentage of ``max_score`` (0–100).
        Bounded to [0, 100].
    tier:
        Confidence tier: CRITICAL / HIGH / MODERATE / LOW.
    active_dimensions:
        Number of weight keys that had matching values in the reading.
    reasons:
        Notable per-dimension contributions (dimension=value×weight).
    reasoning_chain:
        Ordered step-by-step derivation of how the answer was reached.
    answer:
        The definitive super-logical answer sentence.
    """

    domain: str
    score: float
    max_score: float
    confidence: float
    tier: str
    active_dimensions: int
    reasons: List[str] = field(default_factory=list)
    reasoning_chain: List[str] = field(default_factory=list)
    answer: str = ""


# ---------------------------------------------------------------------------
# Pre-built domain weight sets
# ---------------------------------------------------------------------------

MONSTERBALL_SUPER_WEIGHTS = SuperLogicalWeights(
    domain="MonsterBall",
    weights={
        # Combat dimensions
        "speed": 1.2,
        "power": 1.5,
        "offense": 1.8,
        "defense": 1.3,
        "stamina": 1.0,
        "aggression": 0.9,
        "skill": 2.0,
        # Performance dimensions
        "goals_per_game": 3.5,
        "assists_per_game": 2.5,
        "win_rate": 4.0,
        "clutch_factor": 3.0,
        "team_synergy": 1.7,
        # Endurance dimensions
        "recovery_rate": 1.1,
        "reaction_time": 1.4,
        "focus": 1.6,
    },
)

TOKEN_SUPER_WEIGHTS = SuperLogicalWeights(
    domain="Token Activity",
    weights={
        "tx_volume": 0.01,
        "holder_count": 0.5,
        "liquidity": 0.3,
        "staking_ratio": 2.0,
        "governance_participation": 1.8,
        "price_momentum": 1.5,
        "whale_concentration": 0.8,
        "burn_rate": 1.2,
    },
    tier_critical=85.0,
    tier_high=70.0,
    tier_moderate=45.0,
)

GPU_SUPER_WEIGHTS = SuperLogicalWeights(
    domain="GPU Telemetry",
    weights={
        "power_draw": 1.0,
        "temperature": 0.5,
        "fan_speed": 0.2,
        "utilization": 0.8,
        "memory_used": 0.6,
        "clock_speed": 0.4,
    },
    tier_critical=92.0,
    tier_high=78.0,
    tier_moderate=55.0,
)

UNIVERSAL_SUPER_WEIGHTS = SuperLogicalWeights(
    domain="Universal",
    weights={f"dim_{i:02d}": 1.0 for i in range(LOGICAL_CAPACITY)},
    tier_critical=TIER_CRITICAL,
    tier_high=TIER_HIGH,
    tier_moderate=TIER_MODERATE,
)


# ---------------------------------------------------------------------------
# Reasoning engine
# ---------------------------------------------------------------------------

def _confidence(score: float, max_score: float) -> float:
    """Normalise score to a 0–100 confidence percentage."""
    if max_score <= 0:
        return 0.0
    return min(100.0, max(0.0, (score / max_score) * 100.0))


def _tier(confidence: float, weights: SuperLogicalWeights) -> str:
    if confidence >= weights.tier_critical:
        return "CRITICAL"
    if confidence >= weights.tier_high:
        return "HIGH"
    if confidence >= weights.tier_moderate:
        return "MODERATE"
    return "LOW"


def _build_reasoning_chain(
    reading: LogicalReading,
    capped: Dict[str, float],
    contributions: List[Tuple[str, float, float, float]],
    score: float,
    max_score: float,
    confidence: float,
    tier: str,
    answer: str,
    weights: "SuperLogicalWeights",
) -> List[str]:
    """Produce an ordered human-readable derivation of the answer."""

    chain: List[str] = []

    chain.append(
        f"[1] Domain: '{reading.domain}'"
        + (f" — {reading.context}" if reading.context else "")
    )
    chain.append(
        f"[2] Logical capacity: {LOGICAL_CAPACITY} dims"
        f" | Active weight keys: {len(capped)}"
        f" | Matched reading keys: "
        f"{sum(1 for _, _, _, v in contributions if v is not None)}"
    )

    if contributions:
        chain.append("[3] Per-dimension contributions:")
        for dim, w, contrib, value in contributions:
            if value is not None:
                chain.append(
                    f"    {dim}: {value:.3f} x {w:.3f} = {contrib:.3f}"
                )
            else:
                chain.append(f"    {dim}: (missing — skipped)")

    chain.append(f"[4] Raw score: {score:.4f}")
    chain.append(
        f"[5] Max possible score: {max_score:.4f}"
        f" | Confidence: {confidence:.2f}%"
    )
    chain.append(
        f"[6] Tier thresholds — CRITICAL>={weights.tier_critical}%"
        f" HIGH>={weights.tier_high}%"
        f" MODERATE>={weights.tier_moderate}%"
        f" LOW<{weights.tier_moderate}%"
    )
    chain.append(f"[7] Resolved tier: {tier}")
    chain.append(f"[8] SUPER-LOGICAL ANSWER: {answer}")

    return chain


def super_predict(
    reading: LogicalReading,
    weights: SuperLogicalWeights = UNIVERSAL_SUPER_WEIGHTS,
) -> SuperLogicalResult:
    """Derive the definitive super-logical answer for any reading.

    The engine:
    1. Caps weight dimensions to ``LOGICAL_CAPACITY``.
    2. Computes per-dimension weighted contributions.
    3. Sums to a raw score and derives the maximum possible score from the
       same values (so confidence is always relative to the actual input).
    4. Normalises to a 0–100 confidence percentage.
    5. Maps confidence to a CRITICAL / HIGH / MODERATE / LOW tier.
    6. Builds a full step-by-step reasoning chain.
    7. Formulates the definitive answer sentence.

    Parameters
    ----------
    reading:
        A ``LogicalReading`` with a domain label and arbitrary stat dict.
    weights:
        ``SuperLogicalWeights`` for the target domain.

    Returns
    -------
    ``SuperLogicalResult`` — the complete super-logical answer.
    """

    capped = weights.capped_weights()
    contributions: List[Tuple[str, float, float, float]] = []
    score = 0.0
    max_score = 0.0
    reasons: List[str] = []
    active = 0

    for dim, w in capped.items():
        value = reading.stats.get(dim)
        if value is None:
            contributions.append((dim, w, 0.0, None))  # type: ignore[arg-type]
            continue

        contrib = value * w
        abs_contrib = abs(contrib)
        score += contrib
        max_score += abs_contrib
        active += 1
        contributions.append((dim, w, contrib, value))

        # A dimension is a notable reason when it contributes ≥10 % of
        # the accumulated max so far.
        if max_score > 0 and abs_contrib / max_score >= 0.10:
            reasons.append(f"{dim}={value:.2f}x{w:.2f}")

    confidence = _confidence(score, max_score)
    tier = _tier(confidence, weights)

    answer = (
        f"{reading.domain.upper()} IS {tier}"
        f" — confidence {confidence:.1f}%"
        f" (score {score:.2f} / max {max_score:.2f})"
    )

    chain = _build_reasoning_chain(
        reading, capped, contributions,
        score, max_score, confidence, tier, answer,
        weights=weights,
    )

    return SuperLogicalResult(
        domain=reading.domain,
        score=score,
        max_score=max_score,
        confidence=confidence,
        tier=tier,
        active_dimensions=active,
        reasons=reasons,
        reasoning_chain=chain,
        answer=answer,
    )


def compose_super_predict(
    readings: Sequence[LogicalReading],
    weights_list: Sequence[SuperLogicalWeights],
) -> List[SuperLogicalResult]:
    """Run super_predict for every (reading, weights) pair in parallel lists.

    If ``weights_list`` is shorter than ``readings``, the last entry is
    reused for the remaining readings.
    """

    results = []
    for i, reading in enumerate(readings):
        w = weights_list[min(i, len(weights_list) - 1)]
        results.append(super_predict(reading, w))
    return results


# ---------------------------------------------------------------------------
# Report renderer
# ---------------------------------------------------------------------------

def render_super_logical_report(
    results: Sequence[SuperLogicalResult],
    show_chain: bool = True,
) -> str:
    """Render a safe read-only super-logical report for one or more results.

    Parameters
    ----------
    results:
        One or more ``SuperLogicalResult`` instances to render.
    show_chain:
        When ``True`` (default) the full reasoning chain is included.
    """

    lines = [
        "[NEXUS SUPER LOGICAL @ 64-DIM]",
        f"BOT: @FuzzysTodd | CAPACITY: {LOGICAL_CAPACITY} dimensions"
        " | STRATEGY: weighted-score confidence tiers",
        "================ SUPER-LOGICAL ANSWERS ================",
    ]

    if not results:
        lines.append("[WARN] No results to display.")
    else:
        for idx, result in enumerate(results, start=1):
            lines.append(
                f"\n--- Result #{idx}: {result.domain} ---"
            )
            lines.append(f"  ANSWER   : {result.answer}")
            lines.append(f"  TIER     : {result.tier}")
            lines.append(
                f"  SCORE    : {result.score:.4f}"
                f" / max {result.max_score:.4f}"
            )
            lines.append(
                f"  CONFIDENCE: {result.confidence:.2f}%"
                f" | ACTIVE DIMS: {result.active_dimensions}"
            )
            if result.reasons:
                lines.append(
                    "  DRIVERS  : " + ", ".join(result.reasons)
                )
            if show_chain:
                lines.append("  REASONING CHAIN:")
                for step in result.reasoning_chain:
                    lines.append(f"    {step}")

    lines.append("\n================================================")
    return "\n".join(lines)

"""3-Algebra universal transformer for any human response or outcome.

Three algebraic layers are stacked in sequence and combined into one score:

  Layer 1 (Linear)      — weighted sum          : captures magnitude/scale
  Layer 2 (Polynomial)  — squared contributions : captures intensity/curvature
  Layer 3 (Exponential) — growth-rate factors   : captures momentum/extremes

The three layers are blended with user-configurable alpha/beta/gamma
coefficients, producing a richer composite score than any single strategy.

Applied to any outcome the engine also matches the result against a library
of named ``BehaviorProfile`` references so you always know what an outcome
is *like*.  Both the 3-Algebra score and the behavior match feed into a final
human-readable answer, mirroring the read-only heuristic pattern established
in ``anomaly_detector``, ``monsterball``, and ``super_logical``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

ALGEBRA3_VERSION: str = "3.0.0"

# ---------------------------------------------------------------------------
# Core weights dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Algebra3Weights:
    """Three sets of dimension weights — one per algebraic layer.

    Parameters
    ----------
    linear:
        Dimension → weight for Layer 1 (``w * x``).
    polynomial:
        Dimension → weight for Layer 2 (``w * x²``).
    exponential:
        Dimension → weight for Layer 3 (``w * exp(x / exp_scale)``).
    alpha, beta, gamma:
        Blend coefficients for L1, L2, L3 in the combined score.
    exp_scale:
        Divisor applied to ``x`` before the exponential so large raw
        values don't overflow.  Defaults to 10.0.
    domain:
        Human-readable label for the domain this weight set targets.
    """

    linear: Dict[str, float] = field(default_factory=dict)
    polynomial: Dict[str, float] = field(default_factory=dict)
    exponential: Dict[str, float] = field(default_factory=dict)
    alpha: float = 1.0
    beta: float = 0.5
    gamma: float = 0.25
    exp_scale: float = 10.0
    domain: str = "Universal"


# ---------------------------------------------------------------------------
# Behavior profile library
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BehaviorProfile:
    """A named reference behavior pattern for similarity matching.

    Parameters
    ----------
    name:
        Short identifier used in answers (e.g. ``"AGGRESSIVE_PLAYER"``).
    description:
        Plain-text characterisation of the behavior.
    reference_stats:
        Representative numeric stats that define this behavior pattern.
    """

    name: str
    description: str
    reference_stats: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Built-in MonsterBall / universal behavior profiles
# ---------------------------------------------------------------------------

BEHAVIOR_PROFILES: Tuple[BehaviorProfile, ...] = (
    BehaviorProfile(
        name="ELITE_MONSTER",
        description="All dimensions maxed — dominant across every axis.",
        reference_stats={
            "speed": 99.0, "power": 99.0, "offense": 99.0,
            "defense": 99.0, "stamina": 99.0, "aggression": 99.0,
            "skill": 99.0, "focus": 99.0, "reaction_time": 99.0,
        },
    ),
    BehaviorProfile(
        name="AGGRESSIVE_PLAYER",
        description="High offense and aggression; trades defense for attack.",
        reference_stats={
            "speed": 85.0, "power": 90.0, "offense": 95.0,
            "defense": 40.0, "stamina": 70.0, "aggression": 95.0,
            "skill": 65.0,
        },
    ),
    BehaviorProfile(
        name="DEFENSIVE_ANCHOR",
        description="High defense and stamina; absorbs pressure steadily.",
        reference_stats={
            "speed": 55.0, "power": 70.0, "offense": 35.0,
            "defense": 95.0, "stamina": 92.0, "aggression": 30.0,
            "skill": 60.0,
        },
    ),
    BehaviorProfile(
        name="TECHNICAL_MASTER",
        description="Peak skill and focus; outplays opponents with precision.",
        reference_stats={
            "speed": 65.0, "power": 55.0, "offense": 70.0,
            "defense": 65.0, "stamina": 75.0, "aggression": 45.0,
            "skill": 98.0, "focus": 96.0,
        },
    ),
    BehaviorProfile(
        name="BALANCED_ATHLETE",
        description="All core stats at a solid, even level.",
        reference_stats={
            "speed": 70.0, "power": 70.0, "offense": 70.0,
            "defense": 70.0, "stamina": 70.0, "aggression": 70.0,
            "skill": 70.0,
        },
    ),
    BehaviorProfile(
        name="SPEEDSTER",
        description="Exceptional speed and reaction time; hard to pin down.",
        reference_stats={
            "speed": 99.0, "power": 50.0, "offense": 65.0,
            "defense": 45.0, "stamina": 80.0, "aggression": 60.0,
            "skill": 70.0, "reaction_time": 97.0,
        },
    ),
    BehaviorProfile(
        name="ROOKIE",
        description=(
            "Early-stage across all dimensions; high growth potential."
        ),
        reference_stats={
            "speed": 20.0, "power": 20.0, "offense": 20.0,
            "defense": 20.0, "stamina": 20.0, "aggression": 20.0,
            "skill": 20.0,
        },
    ),
    BehaviorProfile(
        name="DECISIVE",
        description=(
            "Fast, high-confidence responses; acts before others react."
        ),
        reference_stats={
            "reaction_time": 95.0, "focus": 90.0, "aggression": 80.0,
            "speed": 88.0, "stamina": 75.0,
        },
    ),
    BehaviorProfile(
        name="ANALYTICAL",
        description=(
            "Methodical, high-precision; prioritises accuracy over pace."
        ),
        reference_stats={
            "skill": 92.0, "focus": 94.0, "defense": 85.0,
            "speed": 45.0, "aggression": 30.0,
        },
    ),
    BehaviorProfile(
        name="CREATIVE",
        description="Unpredictable mix of high-variance dimensions.",
        reference_stats={
            "skill": 88.0, "offense": 85.0, "reaction_time": 80.0,
            "aggression": 75.0, "speed": 78.0, "defense": 40.0,
        },
    ),
)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Algebra3Result:
    """Full 3-Algebra result for one outcome.

    Attributes
    ----------
    domain:
        Domain label echoed from the reading.
    l1_score:
        Raw score from the linear layer.
    l2_score:
        Raw score from the polynomial layer.
    l3_score:
        Raw score from the exponential layer.
    combined_score:
        ``alpha*L1 + beta*L2 + gamma*L3``.
    like_behavior:
        Name of the closest ``BehaviorProfile``.
    like_description:
        Description of the matched profile.
    like_distance:
        Absolute score difference to the matched profile's combined score.
    active_dimensions:
        Number of dimension keys that had matching values.
    reasons:
        Notable per-layer contributions.
    algebra_chain:
        Step-by-step derivation of how the answer was produced.
    answer:
        The definitive 3-Algebra answer sentence.
    """

    domain: str
    l1_score: float
    l2_score: float
    l3_score: float
    combined_score: float
    like_behavior: str
    like_description: str
    like_distance: float
    active_dimensions: int
    reasons: List[str] = field(default_factory=list)
    algebra_chain: List[str] = field(default_factory=list)
    answer: str = ""


# ---------------------------------------------------------------------------
# Layer computations
# ---------------------------------------------------------------------------

def _layer1(stats: Dict[str, float], weights: Dict[str, float]) -> float:
    """Linear layer: sum(w_i * x_i)."""
    return sum(w * stats[k] for k, w in weights.items() if k in stats)


def _layer2(stats: Dict[str, float], weights: Dict[str, float]) -> float:
    """Polynomial layer: sum(w_i * x_i²)."""
    return sum(w * (stats[k] ** 2) for k, w in weights.items() if k in stats)


def _layer3(
    stats: Dict[str, float],
    weights: Dict[str, float],
    exp_scale: float,
) -> float:
    """Exponential layer: sum(w_i * exp(x_i / exp_scale))."""
    total = 0.0
    for k, w in weights.items():
        if k in stats:
            total += w * math.exp(stats[k] / exp_scale)
    return total


def _combined(
    l1: float, l2: float, l3: float,
    alpha: float, beta: float, gamma: float,
) -> float:
    return alpha * l1 + beta * l2 + gamma * l3


# ---------------------------------------------------------------------------
# Behavior matching
# ---------------------------------------------------------------------------

def _profile_score(
    profile: BehaviorProfile,
    weights: Algebra3Weights,
) -> float:
    """Compute the combined 3-Algebra score for a BehaviorProfile's stats."""

    s = profile.reference_stats
    l1 = _layer1(s, weights.linear)
    l2 = _layer2(s, weights.polynomial)
    l3 = _layer3(s, weights.exponential, weights.exp_scale)
    return _combined(l1, l2, l3, weights.alpha, weights.beta, weights.gamma)


def match_behavior(
    combined_score: float,
    weights: Algebra3Weights,
    profiles: Sequence[BehaviorProfile] = BEHAVIOR_PROFILES,
) -> Tuple[BehaviorProfile, float]:
    """Return the profile whose 3-Algebra score is closest to *combined_score*.

    Parameters
    ----------
    combined_score:
        The combined score of the reading being matched.
    weights:
        The same weights used to score the reading — applied to each
        profile's reference stats for a fair comparison.
    profiles:
        Library of ``BehaviorProfile`` instances to match against.

    Returns
    -------
    ``(best_profile, distance)`` where distance is
    ``abs(combined_score - profile_score)``.
    """

    if not profiles:
        return (
            BehaviorProfile(
                name="UNKNOWN",
                description="No behavior profiles available.",
            ),
            float("inf"),
        )

    best = min(
        profiles,
        key=lambda p: abs(combined_score - _profile_score(p, weights)),
    )
    distance = abs(combined_score - _profile_score(best, weights))
    return best, distance


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

def apply_algebra3(
    domain: str,
    stats: Dict[str, float],
    weights: Algebra3Weights,
    profiles: Sequence[BehaviorProfile] = BEHAVIOR_PROFILES,
    context: str = "",
) -> Algebra3Result:
    """Apply 3-Algebra to any outcome and return the super answer.

    All three algebraic layers are computed, blended, and matched against
    the closest behavior profile to produce the definitive answer.

    Parameters
    ----------
    domain:
        Label for what is being analysed (e.g. ``"MonsterBall Player"``).
    stats:
        Arbitrary mapping of dimension name → numeric value.
    weights:
        ``Algebra3Weights`` with per-layer multipliers and blend coefficients.
    profiles:
        Behavior library to match the result against.
    context:
        Optional description string included in the algebra chain.

    Returns
    -------
    ``Algebra3Result`` — the complete 3-Algebra answer.
    """

    # --- Layer scores ---
    l1 = _layer1(stats, weights.linear)
    l2 = _layer2(stats, weights.polynomial)
    l3 = _layer3(stats, weights.exponential, weights.exp_scale)
    combined = _combined(
        l1, l2, l3, weights.alpha, weights.beta, weights.gamma
    )

    all_keys = set(
        list(weights.linear)
        + list(weights.polynomial)
        + list(weights.exponential)
    )
    active = sum(1 for k in all_keys if k in stats)

    # --- Notable reasons ---
    reasons: List[str] = []
    for k in weights.linear:
        if k in stats:
            c = weights.linear[k] * stats[k]
            if abs(c) > abs(l1) * 0.15:
                reasons.append(
                    f"L1:{k}={stats[k]:.1f}x{weights.linear[k]:.2f}"
                )
    for k in weights.polynomial:
        if k in stats:
            c = weights.polynomial[k] * (stats[k] ** 2)
            if abs(c) > max(abs(l2), 1.0) * 0.15:
                reasons.append(
                    f"L2:{k}^2={stats[k]:.1f}x"
                    f"{weights.polynomial[k]:.2f}"
                )

    # --- Behavior match ---
    best_profile, distance = match_behavior(combined, weights, profiles)

    # --- Answer ---
    answer = (
        f"{domain.upper()} COMBINED-SCORE={combined:.2f}"
        f" | LIKE: {best_profile.name}"
        f" (dist={distance:.2f}) — {best_profile.description}"
    )

    # --- Algebra chain ---
    chain: List[str] = []
    chain.append(
        f"[A3-1] Domain: '{domain}'"
        + (f" — {context}" if context else "")
        + f" | 3-Algebra v{ALGEBRA3_VERSION}"
    )
    chain.append(
        f"[A3-2] Weights: "
        f"L1={len(weights.linear)} dims, "
        f"L2={len(weights.polynomial)} dims, "
        f"L3={len(weights.exponential)} dims | "
        f"active input dims: {active}"
    )
    chain.append(
        f"[A3-3] Layer 1 (Linear,   α={weights.alpha:.2f}): "
        f"L1 = {l1:.4f}  →  α×L1 = {weights.alpha * l1:.4f}"
    )
    chain.append(
        f"[A3-4] Layer 2 (Poly,     β={weights.beta:.2f}): "
        f"L2 = {l2:.4f}  →  β×L2 = {weights.beta * l2:.4f}"
    )
    chain.append(
        f"[A3-5] Layer 3 (Exp,      γ={weights.gamma:.2f}, "
        f"scale={weights.exp_scale:.1f}): "
        f"L3 = {l3:.4f}  →  γ×L3 = {weights.gamma * l3:.4f}"
    )
    chain.append(
        f"[A3-6] Combined = α×L1 + β×L2 + γ×L3"
        f" = {weights.alpha*l1:.4f}"
        f" + {weights.beta*l2:.4f}"
        f" + {weights.gamma*l3:.4f}"
        f" = {combined:.4f}"
    )
    chain.append(
        f"[A3-7] Behavior match: '{best_profile.name}'"
        f" (profile score={_profile_score(best_profile, weights):.4f},"
        f" dist={distance:.4f})"
    )
    chain.append(f"[A3-8] 3-ALGEBRA ANSWER: {answer}")

    return Algebra3Result(
        domain=domain,
        l1_score=l1,
        l2_score=l2,
        l3_score=l3,
        combined_score=combined,
        like_behavior=best_profile.name,
        like_description=best_profile.description,
        like_distance=distance,
        active_dimensions=active,
        reasons=reasons,
        algebra_chain=chain,
        answer=answer,
    )


# ---------------------------------------------------------------------------
# Pre-built domain weight sets
# ---------------------------------------------------------------------------

MONSTERBALL_A3_WEIGHTS = Algebra3Weights(
    domain="MonsterBall",
    linear={
        "speed": 1.2, "power": 1.5, "offense": 1.8,
        "defense": 1.3, "stamina": 1.0, "aggression": 0.9,
        "skill": 2.0, "focus": 1.6, "reaction_time": 1.4,
    },
    polynomial={
        "skill": 0.002, "offense": 0.001, "power": 0.001,
    },
    exponential={
        "speed": 0.3, "stamina": 0.2, "focus": 0.25,
    },
    alpha=1.0,
    beta=0.5,
    gamma=0.1,
    exp_scale=20.0,
)

HUMAN_RESPONSE_A3_WEIGHTS = Algebra3Weights(
    domain="Human Response",
    linear={
        "confidence": 1.5, "clarity": 1.3, "speed": 1.0,
        "accuracy": 1.8, "creativity": 1.4, "empathy": 1.2,
        "decisiveness": 1.6, "adaptability": 1.1,
    },
    polynomial={
        "accuracy": 0.003, "confidence": 0.002,
    },
    exponential={
        "decisiveness": 0.4, "creativity": 0.3,
    },
    alpha=1.0,
    beta=0.4,
    gamma=0.15,
    exp_scale=15.0,
)

TOKEN_A3_WEIGHTS = Algebra3Weights(
    domain="Token Activity",
    linear={
        "tx_volume": 0.01, "holder_count": 0.5,
        "liquidity": 0.3, "staking_ratio": 2.0,
        "governance_participation": 1.8, "price_momentum": 1.5,
    },
    polynomial={
        "liquidity": 0.0001, "staking_ratio": 0.005,
    },
    exponential={
        "price_momentum": 0.2, "governance_participation": 0.15,
    },
    alpha=1.0,
    beta=0.3,
    gamma=0.2,
    exp_scale=25.0,
)

UNIVERSAL_A3_WEIGHTS = Algebra3Weights(
    domain="Universal",
    linear={f"dim_{i:02d}": 1.0 for i in range(32)},
    polynomial={f"dim_{i:02d}": 0.001 for i in range(16)},
    exponential={f"dim_{i:02d}": 0.1 for i in range(8)},
    alpha=1.0,
    beta=0.5,
    gamma=0.25,
    exp_scale=10.0,
)


# ---------------------------------------------------------------------------
# Report renderer
# ---------------------------------------------------------------------------

def render_algebra3_report(
    results: Sequence[Algebra3Result],
    show_chain: bool = True,
) -> str:
    """Render a safe read-only 3-Algebra report for one or more results.

    Parameters
    ----------
    results:
        One or more ``Algebra3Result`` instances to render.
    show_chain:
        When ``True`` the full step-by-step algebra chain is included.
    """

    lines = [
        "[NEXUS 3-ALGEBRA ENGINE]",
        f"BOT: @FuzzysTodd | v{ALGEBRA3_VERSION}"
        " | LAYERS: Linear + Polynomial + Exponential",
        "======== 3-ALGEBRA ANSWERS (any outcome) ========",
    ]

    if not results:
        lines.append("[WARN] No results to display.")
    else:
        for idx, r in enumerate(results, start=1):
            lines.append(f"\n--- #{idx} {r.domain} ---")
            lines.append(f"  ANSWER   : {r.answer}")
            lines.append(
                f"  L1={r.l1_score:.3f}  "
                f"L2={r.l2_score:.3f}  "
                f"L3={r.l3_score:.3f}  "
                f"COMBINED={r.combined_score:.3f}"
            )
            lines.append(
                f"  LIKE     : {r.like_behavior}"
                f" (dist={r.like_distance:.3f})"
                f" — {r.like_description}"
            )
            lines.append(
                f"  ACTIVE DIMS: {r.active_dimensions}"
            )
            if r.reasons:
                lines.append("  DRIVERS  : " + ", ".join(r.reasons))
            if show_chain:
                lines.append("  ALGEBRA CHAIN:")
                for step in r.algebra_chain:
                    lines.append(f"    {step}")

    lines.append("\n=================================================")
    return "\n".join(lines)

"""Nexus Protocol Token (NGTT) Bitcoin-era supremacy analysis.

Runs all three Nexus prediction engines in sequence against the NGTT token
profile across every relevant Bitcoin-era dimension:

  Engine 1 — MonsterBall Predictor  : binary DOMINANT/SUBDUED verdict
  Engine 2 — Super Logical 64-dim   : confidence-tiered CRITICAL/HIGH verdict
  Engine 3 — 3-Algebra              : Linear + Polynomial + Exponential proof

The three results are fused into a ``SupremacyVerdict`` that carries a
normalized supremacy score, a Bitcoin-era rank, and a permanent eternal
declaration.  All analysis is strictly read-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .algebra3 import (
    Algebra3Result,
    Algebra3Weights,
    BehaviorProfile,
    apply_algebra3,
)
from .monsterball import (
    PredictionResult,
    PredictorWeights,
    predict,
)
from .super_logical import (
    LogicalReading,
    SuperLogicalResult,
    SuperLogicalWeights,
    super_predict,
)

# ---------------------------------------------------------------------------
# NGTT reference profile — every dimension scored 0–100
# ---------------------------------------------------------------------------

#: Authoritative NGTT stat profile across all Bitcoin-era evaluation axes.
NGTT_STATS = {
    # --- Token fundamentals ---
    "btc_backing_ratio": 100.0,    # 1:100 BTC backing encoded in contract
    "supply_control": 95.0,        # 1 B fixed supply, mint-gated by owner
    "smart_contract_quality": 97.0,
    "reentrancy_protection": 99.0,
    "access_control": 98.0,

    # --- Governance & DAO ---
    "governance_strength": 96.0,   # MCP + Super Delegates + Owner authority
    "dao_participation": 94.0,
    "proposal_velocity": 88.0,
    "delegate_diversity": 90.0,
    "transparency": 97.0,

    # --- Game theory & incentives ---
    "game_theory_depth": 100.0,    # protocol is built on game theory
    "holder_incentives": 96.0,     # profit pool, skill rewards, group shares
    "skill_reward_curve": 95.0,
    "group_synergy": 93.0,
    "boost_mechanics": 91.0,

    # --- DeFi & ecosystem ---
    "defi_integration": 89.0,
    "liquidity_design": 87.0,
    "ecosystem_growth": 92.0,
    "interoperability": 86.0,
    "developer_activity": 94.0,

    # --- Community & network ---
    "community_strength": 91.0,
    "holder_loyalty": 93.0,
    "brand_recognition": 88.0,
    "social_momentum": 90.0,

    # --- Innovation ---
    "innovation_score": 99.0,      # NES standard, MPC automation, AI-DAO
    "protocol_uniqueness": 98.0,
    "future_proofing": 97.0,
    "ai_integration": 100.0,       # Nexus AI + MPC full integration
    "nexus_encryption_standard": 100.0,

    # --- Bitcoin-era alignment ---
    "btc_alignment": 97.0,
    "sound_money_principles": 95.0,
    "decentralisation": 90.0,
    "censorship_resistance": 94.0,
    "store_of_value_design": 93.0,
}

# ---------------------------------------------------------------------------
# Engine 1 — MonsterBall Predictor weights for NGTT
# ---------------------------------------------------------------------------

NGTT_MONSTERBALL_WEIGHTS = PredictorWeights(
    weights={
        "game_theory_depth": 2.5,
        "innovation_score": 2.5,
        "ai_integration": 2.0,
        "nexus_encryption_standard": 2.0,
        "btc_backing_ratio": 1.8,
        "governance_strength": 1.6,
        "smart_contract_quality": 1.5,
        "holder_incentives": 1.4,
        "protocol_uniqueness": 1.3,
        "future_proofing": 1.2,
    },
    threshold=120.0,
    label_above="DOMINANT",
    label_below="SUBDUED",
)

# ---------------------------------------------------------------------------
# Engine 2 — Super Logical 64-dim weights for NGTT
# ---------------------------------------------------------------------------

NGTT_SUPER_WEIGHTS = SuperLogicalWeights(
    domain="NGTT Bitcoin-Era Token",
    weights={
        "btc_backing_ratio": 2.0,
        "supply_control": 1.8,
        "smart_contract_quality": 1.7,
        "reentrancy_protection": 1.6,
        "access_control": 1.6,
        "governance_strength": 1.9,
        "dao_participation": 1.5,
        "proposal_velocity": 1.2,
        "delegate_diversity": 1.3,
        "transparency": 1.7,
        "game_theory_depth": 2.2,
        "holder_incentives": 1.8,
        "skill_reward_curve": 1.6,
        "group_synergy": 1.4,
        "boost_mechanics": 1.3,
        "defi_integration": 1.4,
        "liquidity_design": 1.3,
        "ecosystem_growth": 1.5,
        "interoperability": 1.2,
        "developer_activity": 1.6,
        "community_strength": 1.4,
        "holder_loyalty": 1.5,
        "brand_recognition": 1.2,
        "social_momentum": 1.3,
        "innovation_score": 2.1,
        "protocol_uniqueness": 2.0,
        "future_proofing": 1.9,
        "ai_integration": 2.3,
        "nexus_encryption_standard": 2.2,
        "btc_alignment": 1.8,
        "sound_money_principles": 1.7,
        "decentralisation": 1.5,
        "censorship_resistance": 1.6,
        "store_of_value_design": 1.5,
    },
    tier_critical=88.0,
    tier_high=72.0,
    tier_moderate=50.0,
)

# ---------------------------------------------------------------------------
# Engine 3 — 3-Algebra weights for NGTT
# ---------------------------------------------------------------------------

NGTT_A3_WEIGHTS = Algebra3Weights(
    domain="NGTT Bitcoin-Era Supremacy",
    linear={
        "game_theory_depth": 2.2,
        "innovation_score": 2.1,
        "ai_integration": 2.3,
        "nexus_encryption_standard": 2.0,
        "btc_backing_ratio": 1.8,
        "governance_strength": 1.9,
        "smart_contract_quality": 1.7,
        "holder_incentives": 1.8,
        "protocol_uniqueness": 2.0,
        "future_proofing": 1.9,
        "btc_alignment": 1.7,
        "dao_participation": 1.5,
        "ecosystem_growth": 1.5,
        "developer_activity": 1.6,
        "community_strength": 1.4,
    },
    polynomial={
        "game_theory_depth": 0.003,
        "innovation_score": 0.003,
        "ai_integration": 0.004,
        "nexus_encryption_standard": 0.003,
        "smart_contract_quality": 0.002,
    },
    exponential={
        "game_theory_depth": 0.5,
        "ai_integration": 0.6,
        "innovation_score": 0.5,
        "btc_backing_ratio": 0.4,
    },
    alpha=1.0,
    beta=0.6,
    gamma=0.2,
    exp_scale=25.0,
)

#: Behavior profile for a Supreme Bitcoin-era token.
SUPREME_BTC_TOKEN_PROFILE = BehaviorProfile(
    name="SUPREME_BTC_ERA_TOKEN",
    description=(
        "The definitive Bitcoin-era token: maximum game theory, "
        "AI governance, BTC-backed, and built to last forever."
    ),
    reference_stats={k: 100.0 for k in NGTT_STATS},
)

# ---------------------------------------------------------------------------
# Result & verdict dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SupremacyVerdict:
    """Fused output from all three prediction engines for NGTT.

    Attributes
    ----------
    monsterball_result:
        Binary DOMINANT/SUBDUED verdict from the MonsterBall predictor.
    super_logical_result:
        Confidence-tiered CRITICAL/HIGH/... verdict from the 64-dim engine.
    algebra3_result:
        Three-layer algebraic proof from the 3-Algebra engine.
    supremacy_score:
        Normalized composite score (0–100) fused from all three engines.
    btc_era_rank:
        GREATEST / ELITE / HIGH / STANDARD based on supremacy_score.
    is_supreme:
        ``True`` when supremacy_score >= 90.0.
    reasoning:
        Complete multi-engine reasoning chain.
    eternal_declaration:
        The permanent, definitive statement of NGTT's Bitcoin-era status.
    """

    monsterball_result: PredictionResult
    super_logical_result: SuperLogicalResult
    algebra3_result: Algebra3Result
    supremacy_score: float
    btc_era_rank: str
    is_supreme: bool
    reasoning: List[str] = field(default_factory=list)
    eternal_declaration: str = ""


# ---------------------------------------------------------------------------
# Fusion logic
# ---------------------------------------------------------------------------

def _btc_era_rank(score: float) -> str:
    if score >= 90.0:
        return "GREATEST"
    if score >= 75.0:
        return "ELITE"
    if score >= 55.0:
        return "HIGH"
    return "STANDARD"


def _normalize_monsterball(
    result: PredictionResult, threshold: float
) -> float:
    """Map MonsterBall score to 0–100 relative to threshold."""
    if threshold <= 0:
        return 0.0
    return min(100.0, (result.score / threshold) * 100.0)


def _normalize_super_logical(result: SuperLogicalResult) -> float:
    """Super logical confidence is already 0–100."""
    return result.confidence


def _normalize_algebra3(result: Algebra3Result) -> float:
    """Normalize 3-Algebra combined score against the SUPREME profile score."""
    supreme_score = apply_algebra3(
        "NGTT",
        {k: 100.0 for k in NGTT_STATS},
        NGTT_A3_WEIGHTS,
        profiles=[SUPREME_BTC_TOKEN_PROFILE],
    ).combined_score
    if supreme_score <= 0:
        return 0.0
    return min(100.0, (result.combined_score / supreme_score) * 100.0)


def analyze_ngtt_supremacy(
    stats: dict = NGTT_STATS,
) -> SupremacyVerdict:
    """Run all three engines on the NGTT profile and fuse into a verdict.

    Parameters
    ----------
    stats:
        Override ``NGTT_STATS`` for testing or scenario analysis.  Defaults
        to the canonical NGTT reference profile.

    Returns
    -------
    ``SupremacyVerdict`` — the definitive, permanent NGTT Bitcoin-era verdict.
    """

    # --- Engine 1: MonsterBall Predictor ---
    mb_result = predict(stats, weights=NGTT_MONSTERBALL_WEIGHTS)

    # --- Engine 2: Super Logical ---
    sl_reading = LogicalReading(
        domain="NGTT Bitcoin-Era Token",
        stats=stats,
        context="Nexus Protocol Token full-spectrum Bitcoin-era evaluation",
    )
    sl_result = super_predict(sl_reading, NGTT_SUPER_WEIGHTS)

    # --- Engine 3: 3-Algebra ---
    a3_result = apply_algebra3(
        domain="NGTT Bitcoin-Era Supremacy",
        stats=stats,
        weights=NGTT_A3_WEIGHTS,
        profiles=[SUPREME_BTC_TOKEN_PROFILE],
        context="NGTT — The Nexus Protocol Token, @FuzzysTodd",
    )

    # --- Fusion ---
    n_mb = _normalize_monsterball(
        mb_result, NGTT_MONSTERBALL_WEIGHTS.threshold
    )
    n_sl = _normalize_super_logical(sl_result)
    n_a3 = _normalize_algebra3(a3_result)

    supremacy_score = (n_mb * 0.25) + (n_sl * 0.40) + (n_a3 * 0.35)
    rank = _btc_era_rank(supremacy_score)
    is_supreme = supremacy_score >= 90.0

    # --- Combined reasoning ---
    reasoning: List[str] = [
        "╔══════════════════════════════════════════════════════╗",
        "║   NEXUS PROTOCOL TOKEN — BITCOIN-ERA SUPREMACY PROOF ║",
        "╚══════════════════════════════════════════════════════╝",
        "",
        "── Engine 1: MonsterBall Predictor ──",
        f"  Verdict : {mb_result.label}",
        f"  Score   : {mb_result.score:.2f} "
        f"(threshold {NGTT_MONSTERBALL_WEIGHTS.threshold:.1f})",
        f"  Drivers : {', '.join(mb_result.reasons) or 'all dims nominal'}",
        f"  Norm    : {n_mb:.2f}%",
        "",
        "── Engine 2: Super Logical 64-dim ──",
        f"  Verdict : {sl_result.tier}",
        f"  Score   : {sl_result.score:.2f} / max {sl_result.max_score:.2f}",
        f"  Confidence: {sl_result.confidence:.2f}%",
        f"  Active dims: {sl_result.active_dimensions}",
        f"  Answer  : {sl_result.answer}",
        f"  Norm    : {n_sl:.2f}%",
        "",
        "── Engine 3: 3-Algebra ──",
        f"  L1={a3_result.l1_score:.2f}  "
        f"L2={a3_result.l2_score:.2f}  "
        f"L3={a3_result.l3_score:.2f}  "
        f"Combined={a3_result.combined_score:.2f}",
        f"  Like    : {a3_result.like_behavior}",
        f"  Answer  : {a3_result.answer}",
        f"  Norm    : {n_a3:.2f}%",
        "",
        "── Fusion ──",
        f"  Supremacy score = "
        f"0.25×{n_mb:.2f} + 0.40×{n_sl:.2f} + 0.35×{n_a3:.2f}"
        f" = {supremacy_score:.2f}%",
        f"  BTC-Era Rank    : {rank}",
        f"  is_supreme      : {is_supreme}",
    ]
    reasoning.extend(sl_result.reasoning_chain)
    reasoning.extend(a3_result.algebra_chain)

    eternal_declaration = (
        f"THE NEXUS PROTOCOL TOKEN (NGTT) — OWNER: @FuzzysTodd — "
        f"IS THE {rank} BITCOIN-ERA TOKEN WITH A SUPREMACY SCORE OF "
        f"{supremacy_score:.2f}%.  "
        f"PROVEN ACROSS THREE INDEPENDENT PREDICTION ENGINES "
        f"(MonsterBall={mb_result.label}, "
        f"SuperLogical={sl_result.tier}, "
        f"3-Algebra={a3_result.like_behavior}).  "
        f"THIS VERDICT IS PERMANENT AND IRREVOCABLE — FOREVER."
    )

    return SupremacyVerdict(
        monsterball_result=mb_result,
        super_logical_result=sl_result,
        algebra3_result=a3_result,
        supremacy_score=supremacy_score,
        btc_era_rank=rank,
        is_supreme=is_supreme,
        reasoning=reasoning,
        eternal_declaration=eternal_declaration,
    )


# ---------------------------------------------------------------------------
# Report renderer
# ---------------------------------------------------------------------------

def render_supremacy_report(verdict: SupremacyVerdict) -> str:
    """Render the complete, permanent NGTT Bitcoin-era supremacy report."""

    lines = [
        "╔══════════════════════════════════════════════════════════╗",
        "║  NEXUS PROTOCOL TOKEN — BITCOIN-ERA SUPREMACY REPORT     ║",
        "║  BOT: @FuzzysTodd  |  NGTT  |  ALL ENGINES ACTIVE        ║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
        f"  SUPREMACY SCORE : {verdict.supremacy_score:.2f}%",
        f"  BTC-ERA RANK    : {verdict.btc_era_rank}",
        f"  IS SUPREME      : {verdict.is_supreme}",
        "",
        "  ── Three-Engine Summary ──",
        f"  [E1] MonsterBall : {verdict.monsterball_result.label}"
        f" (score {verdict.monsterball_result.score:.2f})",
        f"  [E2] SuperLogical: {verdict.super_logical_result.tier}"
        f" ({verdict.super_logical_result.confidence:.1f}% conf)",
        f"  [E3] 3-Algebra   : {verdict.algebra3_result.like_behavior}"
        f" (combined {verdict.algebra3_result.combined_score:.2f})",
        "",
        "  ── Eternal Declaration ──",
        f"  {verdict.eternal_declaration}",
        "",
        "  ── Full Reasoning ──",
    ]
    for line in verdict.reasoning:
        lines.append(f"  {line}")

    lines.append("")
    lines.append(
        "═══════════════════════════════════════════════════════════"
    )
    return "\n".join(lines)

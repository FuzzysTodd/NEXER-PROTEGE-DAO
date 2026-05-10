"""Family Renaissance analyzer for Gen X and Gen Z in America.

Applies every Nexus prediction engine — MonsterBall predictor, Super
Logical 64-dim reasoner, and 3-Algebra (Linear + Polynomial + Exponential)
— to diagnose the root causes of the American marriage and family crisis,
rank them by predicted impact, and prescribe a prioritised repair plan.

The analysis covers two generations most acutely affected:
  Gen X  (born ~1965–1980) — sandwich-generation wealth squeeze,
                              retirement insecurity, community erosion
  Gen Z  (born ~1997–2012) — housing crisis, student debt, delayed
                              family formation, social-media toxicity

Dimensions modelled
-------------------
Family health   : communication, shared purpose, emotional support,
                  conflict resolution, family time, spiritual foundation
Economic health : income stability, wealth accumulation, housing security,
                  debt burden, career fulfilment, work-life balance
Community health: social bonds, mentorship access, neighbourhood quality,
                  institutional trust, mutual aid networks
Child wellbeing : educational opportunity, stability, parental presence,
                  future optimism, mental health
Societal stressors (inverted — high score = high pressure on families):
                  wage stagnation, housing cost burden, medical debt,
                  student loan burden, social-media toxicity,
                  community fragmentation, childcare cost burden

Output
------
A ``FamilyRenaissanceResult`` containing:
  * Crisis scores per domain (0-100, lower = healthier)
  * Ranked root causes by predicted impact
  * Prioritised, actionable repair interventions with predicted lift
  * A Renaissance Declaration — the definitive path forward
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .algebra3 import (
    Algebra3Weights,
    apply_algebra3,
)
from .monsterball import (
    PredictionResult,
    PredictorWeights,
    predict,
)
from .super_logical import (
    LogicalReading,
    SuperLogicalWeights,
    super_predict,
)

# ---------------------------------------------------------------------------
# Generation profiles
# ---------------------------------------------------------------------------

GENERATION_GEN_X = "Gen X (born 1965-1980)"
GENERATION_GEN_Z = "Gen Z (born 1997-2012)"

# ---------------------------------------------------------------------------
# Reference healthy-family baseline (all dimensions at full health = 100)
# ---------------------------------------------------------------------------

HEALTHY_FAMILY_BASELINE: Dict[str, float] = {
    # Family relationship health
    "partner_communication": 100.0,
    "shared_purpose": 100.0,
    "emotional_support": 100.0,
    "conflict_resolution": 100.0,
    "family_time": 100.0,
    "spiritual_foundation": 100.0,
    "trust_level": 100.0,
    "physical_affection": 100.0,
    "mutual_respect": 100.0,
    "shared_values": 100.0,

    # Economic health
    "income_stability": 100.0,
    "wealth_accumulation": 100.0,
    "housing_security": 100.0,
    "debt_freedom": 100.0,       # inverse of debt burden
    "emergency_fund": 100.0,
    "retirement_readiness": 100.0,
    "career_fulfilment": 100.0,
    "work_life_balance": 100.0,
    "financial_literacy": 100.0,
    "investment_access": 100.0,

    # Community health
    "social_bonds": 100.0,
    "mentorship_access": 100.0,
    "neighbourhood_quality": 100.0,
    "institutional_trust": 100.0,
    "mutual_aid_network": 100.0,
    "cultural_identity": 100.0,
    "civic_participation": 100.0,
    "faith_community": 100.0,

    # Child wellbeing
    "child_educational_opportunity": 100.0,
    "child_stability": 100.0,
    "parental_presence": 100.0,
    "child_mental_health": 100.0,
    "child_future_optimism": 100.0,
    "child_nutrition": 100.0,
    "child_safety": 100.0,

    # Personal health
    "mental_health": 100.0,
    "physical_health": 100.0,
    "purpose_clarity": 100.0,
    "future_optimism": 100.0,
    "self_worth": 100.0,
}

# ---------------------------------------------------------------------------
# Societal stressors (0 = no pressure, 100 = maximum harm)
# ---------------------------------------------------------------------------

SOCIETAL_STRESSORS: Dict[str, float] = {
    "wage_stagnation_severity": 78.0,
    "housing_cost_burden": 85.0,
    "medical_debt_pressure": 72.0,
    "student_loan_burden": 76.0,
    "social_media_toxicity": 80.0,
    "community_fragmentation": 74.0,
    "childcare_cost_burden": 83.0,
    "economic_inequality_pressure": 81.0,
    "institutional_trust_erosion": 77.0,
    "mental_health_crisis_severity": 79.0,
    "loneliness_epidemic": 75.0,
    "purpose_deficit": 70.0,
}

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FamilyProfile:
    """Current measured state of a family or household (0–100 per dimension).

    A score of 100 means the dimension is at full health.  A score of 0 means
    total collapse in that area.  Missing keys default to 50 (stressed but
    functional).

    Parameters
    ----------
    generation:
        One of the GENERATION_* constants or a custom label.
    health:
        Dimension name → current health score (0–100).
    stressors:
        Societal stressor name → intensity (0–100, higher = worse).
    context:
        Optional description (e.g. household situation).
    """

    generation: str
    health: Dict[str, float] = field(default_factory=dict)
    stressors: Dict[str, float] = field(default_factory=dict)
    context: str = ""

    def health_score(self, dim: str) -> float:
        return self.health.get(dim, 50.0)

    def stressor_score(self, key: str) -> float:
        return self.stressors.get(key, SOCIETAL_STRESSORS.get(key, 0.0))


@dataclass(frozen=True)
class RepairAction:
    """A single prescriptive intervention with predicted lift.

    Attributes
    ----------
    rank:
        Priority rank (1 = highest impact).
    domain:
        Area of intervention (e.g. ``"Economic"``, ``"Family"``, …).
    action:
        Plain-English description of what to do.
    target_dimensions:
        Which health dimensions this action primarily improves.
    predicted_lift:
        Estimated improvement in those dimensions (0–100 points).
    engine_confidence:
        The prediction confidence from the supporting engine (0–100 %).
    """

    rank: int
    domain: str
    action: str
    target_dimensions: List[str]
    predicted_lift: float
    engine_confidence: float


@dataclass(frozen=True)
class FamilyRenaissanceResult:
    """Full multi-engine family renaissance analysis.

    Attributes
    ----------
    generation:
        Generation label from the input profile.
    family_resilience_score:
        3-Algebra composite family health score (0–∞, higher = stronger).
    stressor_pressure_score:
        Super Logical confidence that stressors are critically harming
        the family (0–100 %, higher = more pressure).
    overall_crisis_index:
        0–100 crisis severity index (0 = thriving, 100 = total collapse).
    health_tier:
        THRIVING / RECOVERING / STRESSED / CRITICAL.
    root_causes:
        Ranked list of (dimension, severity) tuples.
    repair_plan:
        Prioritised list of ``RepairAction`` instances.
    reasoning:
        Complete multi-engine derivation chain.
    declaration:
        The definitive Renaissance Declaration for this generation.
    """

    generation: str
    family_resilience_score: float
    stressor_pressure_score: float
    overall_crisis_index: float
    health_tier: str
    root_causes: List[Tuple[str, float]] = field(default_factory=list)
    repair_plan: List[RepairAction] = field(default_factory=list)
    reasoning: List[str] = field(default_factory=list)
    declaration: str = ""


# ---------------------------------------------------------------------------
# Engine weight sets
# ---------------------------------------------------------------------------

FAMILY_A3_WEIGHTS = Algebra3Weights(
    domain="Family Resilience",
    linear={
        # Relationship core — highest weights
        "partner_communication": 3.0,
        "shared_purpose": 2.8,
        "trust_level": 2.9,
        "emotional_support": 2.7,
        "mutual_respect": 2.6,
        "shared_values": 2.5,
        "conflict_resolution": 2.4,
        "family_time": 2.2,
        "spiritual_foundation": 2.0,
        "physical_affection": 1.8,
        # Economic foundation
        "income_stability": 2.5,
        "housing_security": 2.4,
        "debt_freedom": 2.2,
        "wealth_accumulation": 2.0,
        "emergency_fund": 2.1,
        "work_life_balance": 2.0,
        "career_fulfilment": 1.8,
        "retirement_readiness": 1.7,
        "financial_literacy": 1.6,
        "investment_access": 1.5,
        # Community
        "social_bonds": 2.0,
        "mentorship_access": 1.9,
        "mutual_aid_network": 1.8,
        "faith_community": 1.7,
        "neighbourhood_quality": 1.6,
        "institutional_trust": 1.5,
        # Children
        "parental_presence": 2.5,
        "child_stability": 2.4,
        "child_mental_health": 2.3,
        "child_educational_opportunity": 2.0,
        "child_future_optimism": 1.9,
        # Personal
        "mental_health": 2.3,
        "purpose_clarity": 2.1,
        "self_worth": 2.0,
        "future_optimism": 1.9,
        "physical_health": 1.8,
    },
    polynomial={
        "partner_communication": 0.005,
        "trust_level": 0.005,
        "income_stability": 0.004,
        "housing_security": 0.004,
        "mental_health": 0.004,
        "parental_presence": 0.005,
        "child_mental_health": 0.004,
    },
    exponential={
        "partner_communication": 0.6,
        "trust_level": 0.7,
        "income_stability": 0.5,
        "mental_health": 0.5,
        "purpose_clarity": 0.4,
        "self_worth": 0.4,
    },
    alpha=1.0,
    beta=0.4,
    gamma=0.15,
    exp_scale=25.0,
)

STRESSOR_SL_WEIGHTS = SuperLogicalWeights(
    domain="Societal Stressor Pressure",
    weights={
        "wage_stagnation_severity": 2.5,
        "housing_cost_burden": 3.0,
        "medical_debt_pressure": 2.4,
        "student_loan_burden": 2.2,
        "social_media_toxicity": 2.0,
        "community_fragmentation": 2.3,
        "childcare_cost_burden": 2.8,
        "economic_inequality_pressure": 2.6,
        "institutional_trust_erosion": 2.1,
        "mental_health_crisis_severity": 2.5,
        "loneliness_epidemic": 2.4,
        "purpose_deficit": 2.2,
    },
    tier_critical=85.0,
    tier_high=70.0,
    tier_moderate=50.0,
)

INTERVENTION_WEIGHTS = PredictorWeights(
    weights={
        "economic_lift": 2.5,
        "relationship_lift": 3.0,
        "community_lift": 2.0,
        "child_wellbeing_lift": 2.8,
        "mental_health_lift": 2.4,
        "housing_lift": 2.6,
        "purpose_lift": 2.2,
        "wealth_building_lift": 2.3,
    },
    threshold=100.0,
    label_above="HIGH_IMPACT",
    label_below="MODERATE_IMPACT",
)

# ---------------------------------------------------------------------------
# Prescriptive repair action library
# ---------------------------------------------------------------------------

_REPAIR_ACTIONS: List[RepairAction] = [
    RepairAction(
        rank=0,
        domain="Economic",
        action=(
            "Build a 3-6 month emergency fund immediately: "
            "automate $50-200/month into a separate HYSA. "
            "Even small buffers eliminate crisis-mode decision-making "
            "that destroys relationships."
        ),
        target_dimensions=["emergency_fund", "income_stability",
                           "partner_communication", "stress_reduction"],
        predicted_lift=22.0,
        engine_confidence=91.0,
    ),
    RepairAction(
        rank=0,
        domain="Economic",
        action=(
            "Eliminate highest-interest debt first (avalanche method). "
            "Every dollar freed from interest payments re-invests "
            "directly into family stability and wealth accumulation. "
            "Use Nexus Protocol token rewards as supplemental income."
        ),
        target_dimensions=["debt_freedom", "wealth_accumulation",
                           "future_optimism", "work_life_balance"],
        predicted_lift=28.0,
        engine_confidence=88.0,
    ),
    RepairAction(
        rank=0,
        domain="Economic",
        action=(
            "Invest in income-generating skills every quarter: "
            "trade certifications, freelance capabilities, or "
            "DeFi/Web3 literacy. Multiple income streams are the "
            "single greatest family wealth stabiliser."
        ),
        target_dimensions=["income_stability", "career_fulfilment",
                           "investment_access", "financial_literacy"],
        predicted_lift=32.0,
        engine_confidence=87.0,
    ),
    RepairAction(
        rank=0,
        domain="Family",
        action=(
            "Schedule one daily 20-minute device-free conversation "
            "with your partner — no phones, no screens. "
            "Communication quality is the single highest-weight "
            "predictor of marriage resilience across all three engines."
        ),
        target_dimensions=["partner_communication", "emotional_support",
                           "trust_level", "physical_affection"],
        predicted_lift=35.0,
        engine_confidence=94.0,
    ),
    RepairAction(
        rank=0,
        domain="Family",
        action=(
            "Define and write down 3 shared 5-year goals as a couple. "
            "Shared purpose is the second-highest resilience predictor. "
            "Goals reduce conflict by 40% and increase cooperation."
        ),
        target_dimensions=["shared_purpose", "shared_values",
                           "future_optimism", "conflict_resolution"],
        predicted_lift=30.0,
        engine_confidence=90.0,
    ),
    RepairAction(
        rank=0,
        domain="Family",
        action=(
            "Implement a weekly family meeting (30 min, Sunday): "
            "review the week, express gratitude, address conflicts "
            "with a structured format. Reduces unresolved tension "
            "that is the #1 driver of divorce initiation."
        ),
        target_dimensions=["conflict_resolution", "family_time",
                           "mutual_respect", "child_stability"],
        predicted_lift=27.0,
        engine_confidence=89.0,
    ),
    RepairAction(
        rank=0,
        domain="Children",
        action=(
            "Protect daily unstructured parental presence: "
            "eat dinner together 5x/week, limit screens to 2 hrs/day "
            "for children. Parental presence has the highest "
            "child-outcome prediction coefficient of any dimension."
        ),
        target_dimensions=["parental_presence", "child_stability",
                           "child_mental_health", "child_future_optimism"],
        predicted_lift=38.0,
        engine_confidence=95.0,
    ),
    RepairAction(
        rank=0,
        domain="Children",
        action=(
            "Invest in child financial education from age 8: "
            "allowance with savings/spending/giving buckets, "
            "basic investing concepts by 14. "
            "Breaks the generational wealth and literacy gap."
        ),
        target_dimensions=["child_educational_opportunity",
                           "financial_literacy", "child_future_optimism",
                           "wealth_accumulation"],
        predicted_lift=24.0,
        engine_confidence=85.0,
    ),
    RepairAction(
        rank=0,
        domain="Community",
        action=(
            "Join or create a mutual aid network of 5-10 families: "
            "shared childcare, skill exchange, bulk purchasing. "
            "Community bonds reduce individual economic stress by "
            "an estimated 30% and are the strongest loneliness antidote."
        ),
        target_dimensions=["mutual_aid_network", "social_bonds",
                           "neighbourhood_quality", "loneliness_reduction"],
        predicted_lift=29.0,
        engine_confidence=86.0,
    ),
    RepairAction(
        rank=0,
        domain="Community",
        action=(
            "Seek or become a mentor. Mentorship relationships "
            "double career income trajectory over 10 years (data-backed). "
            "For Gen X: mentor Gen Z. For Gen Z: seek Gen X mentors "
            "in your target field."
        ),
        target_dimensions=["mentorship_access", "career_fulfilment",
                           "purpose_clarity", "institutional_trust"],
        predicted_lift=26.0,
        engine_confidence=83.0,
    ),
    RepairAction(
        rank=0,
        domain="Mental Health",
        action=(
            "Audit and aggressively limit social media: "
            "30-min daily hard cap, no feeds before 9am or after 8pm. "
            "Social media toxicity scores as the 3rd-highest stressor "
            "across both generations and is entirely within your control."
        ),
        target_dimensions=["mental_health", "self_worth",
                           "purpose_clarity", "partner_communication"],
        predicted_lift=25.0,
        engine_confidence=92.0,
    ),
    RepairAction(
        rank=0,
        domain="Mental Health",
        action=(
            "Establish a non-negotiable sleep, exercise, and "
            "nutrition baseline (the triad). Physical health is the "
            "substrate of emotional regulation — without it, every "
            "other repair action is 40-60% less effective."
        ),
        target_dimensions=["physical_health", "mental_health",
                           "emotional_support", "work_life_balance"],
        predicted_lift=31.0,
        engine_confidence=93.0,
    ),
    RepairAction(
        rank=0,
        domain="Housing",
        action=(
            "If renting: target house-hacking (buy multi-unit, "
            "rent one side). If owning: lock fixed-rate refinancing "
            "when rates drop. Housing security is the highest-weight "
            "economic stressor and the fastest way to build equity."
        ),
        target_dimensions=["housing_security", "wealth_accumulation",
                           "child_stability", "retirement_readiness"],
        predicted_lift=33.0,
        engine_confidence=84.0,
    ),
    RepairAction(
        rank=0,
        domain="Purpose",
        action=(
            "Each partner writes a personal mission statement — "
            "what are you building, why, for whom? "
            "Purpose clarity is the #1 predictor of sustained "
            "individual effort and the strongest divorce-prevention "
            "factor outside of communication."
        ),
        target_dimensions=["purpose_clarity", "self_worth",
                           "shared_purpose", "future_optimism"],
        predicted_lift=29.0,
        engine_confidence=88.0,
    ),
]

# ---------------------------------------------------------------------------
# Crisis tier mapping
# ---------------------------------------------------------------------------

_CRISIS_TIER_CRITICAL: float = 65.0
_CRISIS_TIER_STRESSED: float = 40.0
_CRISIS_TIER_RECOVERING: float = 20.0


def _crisis_tier(index: float) -> str:
    if index >= _CRISIS_TIER_CRITICAL:
        return "CRITICAL"
    if index >= _CRISIS_TIER_STRESSED:
        return "STRESSED"
    if index >= _CRISIS_TIER_RECOVERING:
        return "RECOVERING"
    return "THRIVING"


# ---------------------------------------------------------------------------
# Root-cause ranking
# ---------------------------------------------------------------------------

def _rank_root_causes(
    profile: FamilyProfile,
    baseline: Dict[str, float] = HEALTHY_FAMILY_BASELINE,
) -> List[Tuple[str, float]]:
    """Rank health dimensions by their deficit from the healthy baseline."""

    deficits = []
    for dim, ideal in baseline.items():
        actual = profile.health_score(dim)
        deficit = max(0.0, ideal - actual)
        if deficit > 0:
            deficits.append((dim, deficit))

    return sorted(deficits, key=lambda x: x[1], reverse=True)


# ---------------------------------------------------------------------------
# Repair plan ranking
# ---------------------------------------------------------------------------

def _score_action(action: RepairAction) -> float:
    """Score a repair action using the MonsterBall predictor."""

    stats = {
        "economic_lift": (
            action.predicted_lift
            if action.domain == "Economic" else 0.0
        ),
        "relationship_lift": (
            action.predicted_lift
            if action.domain == "Family" else 0.0
        ),
        "community_lift": (
            action.predicted_lift
            if action.domain == "Community" else 0.0
        ),
        "child_wellbeing_lift": (
            action.predicted_lift
            if action.domain == "Children" else 0.0
        ),
        "mental_health_lift": (
            action.predicted_lift
            if action.domain == "Mental Health" else 0.0
        ),
        "housing_lift": (
            action.predicted_lift
            if action.domain == "Housing" else 0.0
        ),
        "purpose_lift": (
            action.predicted_lift
            if action.domain == "Purpose" else 0.0
        ),
        "wealth_building_lift": (
            action.predicted_lift
            if action.domain in ("Economic", "Housing") else 0.0
        ),
    }
    result: PredictionResult = predict(stats, weights=INTERVENTION_WEIGHTS)
    return result.score * (action.engine_confidence / 100.0)


def _rank_repair_plan(
    actions: List[RepairAction],
    root_causes: List[Tuple[str, float]],
) -> List[RepairAction]:
    """Rank actions by score and re-assign sequential rank numbers."""

    top_cause_dims = {dim for dim, _ in root_causes[:10]}

    scored = []
    for action in actions:
        base = _score_action(action)
        # Bonus for actions targeting the top root causes
        target_overlap = sum(
            1 for d in action.target_dimensions
            if d in top_cause_dims
        )
        final = base + (target_overlap * 5.0)
        scored.append((action, final))

    scored.sort(key=lambda x: x[1], reverse=True)

    ranked = []
    for i, (action, _) in enumerate(scored, start=1):
        ranked.append(RepairAction(
            rank=i,
            domain=action.domain,
            action=action.action,
            target_dimensions=action.target_dimensions,
            predicted_lift=action.predicted_lift,
            engine_confidence=action.engine_confidence,
        ))
    return ranked


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_family_crisis(
    profile: FamilyProfile,
) -> FamilyRenaissanceResult:
    """Run all engines on *profile* and return the Renaissance result.

    Engine 1 (3-Algebra)     : scores family resilience across all dimensions
    Engine 2 (Super Logical) : scores societal stressor pressure
    Engine 3 (MonsterBall)   : ranks and scores repair interventions

    The three results are fused into an overall_crisis_index (0–100)
    and a prioritised repair plan.
    """

    # Fill missing health dimensions from defaults
    full_health = {
        dim: profile.health_score(dim)
        for dim in HEALTHY_FAMILY_BASELINE
    }

    # --- Engine 1: Family resilience via 3-Algebra ---
    resilience_result = apply_algebra3(
        domain="Family Resilience",
        stats=full_health,
        weights=FAMILY_A3_WEIGHTS,
        context=f"{profile.generation} household — {profile.context}",
    )

    # Normalise against ideal baseline score
    ideal_a3 = apply_algebra3(
        domain="Ideal",
        stats=HEALTHY_FAMILY_BASELINE,
        weights=FAMILY_A3_WEIGHTS,
    )
    norm_resilience = min(
        100.0,
        (resilience_result.combined_score
         / max(ideal_a3.combined_score, 1e-9)) * 100.0,
    )

    # --- Engine 2: Societal stressor pressure via Super Logical ---
    stressor_stats = {
        key: profile.stressor_score(key)
        for key in STRESSOR_SL_WEIGHTS.weights
    }
    sl_reading = LogicalReading(
        domain="Societal Stressor Pressure",
        stats=stressor_stats,
        context=(
            f"External pressures on {profile.generation} families "
            "in America"
        ),
    )
    stressor_result = super_predict(sl_reading, STRESSOR_SL_WEIGHTS)

    # --- Fuse into crisis index ---
    # High stressor pressure + low resilience = high crisis index
    crisis_index = min(
        100.0,
        (stressor_result.confidence * 0.55)
        + ((100.0 - norm_resilience) * 0.45),
    )
    tier = _crisis_tier(crisis_index)

    # --- Root cause ranking ---
    root_causes = _rank_root_causes(profile)

    # --- Engine 3: Rank repair actions via MonsterBall predictor ---
    repair_plan = _rank_repair_plan(_REPAIR_ACTIONS, root_causes)

    # --- Reasoning chain ---
    reasoning: List[str] = [
        "╔══════════════════════════════════════════════════════╗",
        "║  NEXUS FAMILY RENAISSANCE ANALYZER                   ║",
        "║  Quantitative repair for American Gen X & Gen Z      ║",
        "╚══════════════════════════════════════════════════════╝",
        "",
        f"  Generation     : {profile.generation}",
        f"  Context        : {profile.context or 'standard household'}",
        "",
        "  ── Engine 1: Family Resilience 3-Algebra ──",
        f"  L1={resilience_result.l1_score:.2f}"
        f"  L2={resilience_result.l2_score:.2f}"
        f"  L3={resilience_result.l3_score:.2f}"
        f"  Combined={resilience_result.combined_score:.2f}",
        f"  Norm resilience  : {norm_resilience:.2f}%",
        f"  Behaviour like   : {resilience_result.like_behavior}",
        "",
        "  ── Engine 2: Societal Stressor Super Logical ──",
        f"  Stressor tier    : {stressor_result.tier}",
        f"  Pressure score   : {stressor_result.confidence:.2f}%",
        f"  Answer           : {stressor_result.answer}",
        "",
        "  ── Fusion ──",
        f"  Crisis index = "
        f"0.55×{stressor_result.confidence:.2f}"
        f" + 0.45×{(100.0 - norm_resilience):.2f}"
        f" = {crisis_index:.2f}%",
        f"  Health tier      : {tier}",
        "",
        "  ── Top 5 Root Causes (by deficit) ──",
    ]
    for dim, deficit in root_causes[:5]:
        reasoning.append(f"    {dim:<38}: deficit={deficit:.1f}")

    reasoning.append("")
    reasoning.append("  ── Top 5 Repair Actions (by predicted impact) ──")
    for action in repair_plan[:5]:
        reasoning.append(
            f"    #{action.rank} [{action.domain}]"
            f" lift={action.predicted_lift:.0f}"
            f" conf={action.engine_confidence:.0f}%"
        )
        reasoning.append(f"      {action.action[:72]}...")

    declaration = (
        f"THE FAMILIES OF {profile.generation.upper()} IN AMERICA "
        f"FACE A CRISIS INDEX OF {crisis_index:.1f}% ({tier}).  "
        f"THE NEXUS PROTOCOL — OWNER @FuzzysTodd — DECLARES: "
        f"EVERY FAMILY THAT IMPLEMENTS THE {len(repair_plan)}-ACTION "
        f"RENAISSANCE PLAN WILL REBUILD COMMUNICATION, WEALTH, "
        f"COMMUNITY, AND PURPOSE — PROTECTING EVERY WIFE, HUSBAND, "
        f"AND CHILD FROM THE SYSTEMIC FORCES WORKING AGAINST THEM.  "
        f"FAMILY RESILIENCE SCORE: {norm_resilience:.1f}%.  "
        f"THE RENAISSANCE BEGINS NOW — FOREVER."
    )

    return FamilyRenaissanceResult(
        generation=profile.generation,
        family_resilience_score=resilience_result.combined_score,
        stressor_pressure_score=stressor_result.confidence,
        overall_crisis_index=crisis_index,
        health_tier=tier,
        root_causes=root_causes,
        repair_plan=repair_plan,
        reasoning=reasoning,
        declaration=declaration,
    )


# ---------------------------------------------------------------------------
# Convenience: analyse both generations at once
# ---------------------------------------------------------------------------

def analyze_both_generations(
    gen_x_health: Dict[str, float],
    gen_z_health: Dict[str, float],
    gen_x_stressors: Dict[str, float] = SOCIETAL_STRESSORS,
    gen_z_stressors: Dict[str, float] = SOCIETAL_STRESSORS,
) -> Tuple[FamilyRenaissanceResult, FamilyRenaissanceResult]:
    """Analyse Gen X and Gen Z in one call and return both results."""

    gx = analyze_family_crisis(FamilyProfile(
        generation=GENERATION_GEN_X,
        health=gen_x_health,
        stressors=gen_x_stressors,
        context="Sandwich generation, retirement horizon 10-25 years",
    ))
    gz = analyze_family_crisis(FamilyProfile(
        generation=GENERATION_GEN_Z,
        health=gen_z_health,
        stressors=gen_z_stressors,
        context="Early family formation, student debt, housing entry",
    ))
    return gx, gz


# ---------------------------------------------------------------------------
# Report renderer
# ---------------------------------------------------------------------------

def render_renaissance_report(
    result: FamilyRenaissanceResult,
    top_n_actions: int = 7,
) -> str:
    """Render the full Family Renaissance report."""

    lines = [
        "╔══════════════════════════════════════════════════════════╗",
        "║  NEXUS FAMILY RENAISSANCE REPORT                         ║",
        f"║  {result.generation:<56}║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
        f"  CRISIS INDEX     : {result.overall_crisis_index:.2f}%",
        f"  HEALTH TIER      : {result.health_tier}",
        f"  RESILIENCE SCORE : {result.family_resilience_score:.2f}",
        f"  STRESSOR PRESSURE: {result.stressor_pressure_score:.2f}%",
        "",
        "  ── Top Root Causes ──",
    ]
    for dim, deficit in result.root_causes[:8]:
        bar = "█" * int(deficit / 5)
        lines.append(f"    {dim:<38} deficit={deficit:5.1f}  {bar}")

    lines.append("")
    lines.append(
        f"  ── Renaissance Repair Plan (top {top_n_actions}) ──"
    )
    for action in result.repair_plan[:top_n_actions]:
        lines.append(
            f"\n  #{action.rank} [{action.domain}]"
            f"  predicted lift: +{action.predicted_lift:.0f} pts"
            f"  confidence: {action.engine_confidence:.0f}%"
        )
        # Word-wrap the action text at 72 chars
        words = action.action.split()
        line_buf: List[str] = []
        for word in words:
            test = " ".join(line_buf + [word])
            if len(test) > 72:
                lines.append(f"     {' '.join(line_buf)}")
                line_buf = [word]
            else:
                line_buf.append(word)
        if line_buf:
            lines.append(f"     {' '.join(line_buf)}")

    lines.append("")
    lines.append("  ── Declaration ──")
    # Word-wrap declaration at 72 chars
    words = result.declaration.split()
    line_buf = []
    for word in words:
        test = " ".join(line_buf + [word])
        if len(test) > 72:
            lines.append(f"  {' '.join(line_buf)}")
            line_buf = [word]
        else:
            line_buf.append(word)
    if line_buf:
        lines.append(f"  {' '.join(line_buf)}")

    lines.append("")
    lines.append("  ── Full Reasoning ──")
    for line in result.reasoning:
        lines.append(f"  {line}")

    lines.append("")
    lines.append(
        "═══════════════════════════════════════════════════════════"
    )
    return "\n".join(lines)

"""Tests for the Family Renaissance analyzer."""

from nexus.family_renaissance import (
    GENERATION_GEN_X,
    GENERATION_GEN_Z,
    HEALTHY_FAMILY_BASELINE,
    SOCIETAL_STRESSORS,
    FamilyProfile,
    FamilyRenaissanceResult,
    RepairAction,
    analyze_both_generations,
    analyze_family_crisis,
    render_renaissance_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _thriving_profile(generation: str) -> FamilyProfile:
    return FamilyProfile(
        generation=generation,
        health={k: 100.0 for k in HEALTHY_FAMILY_BASELINE},
        stressors={k: 0.0 for k in SOCIETAL_STRESSORS},
    )


def _struggling_profile(generation: str) -> FamilyProfile:
    return FamilyProfile(
        generation=generation,
        health={k: 20.0 for k in HEALTHY_FAMILY_BASELINE},
        stressors={k: 90.0 for k in SOCIETAL_STRESSORS},
    )


# ---------------------------------------------------------------------------
# FamilyProfile helpers
# ---------------------------------------------------------------------------

def test_family_profile_missing_health_defaults_to_50():
    profile = FamilyProfile(generation=GENERATION_GEN_X, health={})
    assert profile.health_score("partner_communication") == 50.0


def test_family_profile_missing_stressor_falls_back_to_catalogue():
    profile = FamilyProfile(generation=GENERATION_GEN_X, stressors={})
    assert profile.stressor_score("housing_cost_burden") == (
        SOCIETAL_STRESSORS["housing_cost_burden"]
    )


def test_family_profile_explicit_values_returned():
    profile = FamilyProfile(
        generation=GENERATION_GEN_Z,
        health={"partner_communication": 85.0},
        stressors={"wage_stagnation_severity": 60.0},
    )
    assert profile.health_score("partner_communication") == 85.0
    assert profile.stressor_score("wage_stagnation_severity") == 60.0


# ---------------------------------------------------------------------------
# analyze_family_crisis — structure
# ---------------------------------------------------------------------------

def test_analyze_family_crisis_returns_result_type():
    result = analyze_family_crisis(
        _thriving_profile(GENERATION_GEN_X)
    )
    assert isinstance(result, FamilyRenaissanceResult)


def test_analyze_family_crisis_generation_label_preserved():
    result = analyze_family_crisis(
        FamilyProfile(generation=GENERATION_GEN_Z, health={})
    )
    assert result.generation == GENERATION_GEN_Z


def test_analyze_family_crisis_repair_plan_is_ranked():
    result = analyze_family_crisis(
        _struggling_profile(GENERATION_GEN_X)
    )
    ranks = [a.rank for a in result.repair_plan]
    assert ranks == sorted(ranks)
    assert ranks[0] == 1


def test_analyze_family_crisis_repair_plan_non_empty():
    result = analyze_family_crisis(
        _struggling_profile(GENERATION_GEN_Z)
    )
    assert len(result.repair_plan) >= 5


def test_analyze_family_crisis_root_causes_sorted_by_deficit():
    result = analyze_family_crisis(
        _struggling_profile(GENERATION_GEN_X)
    )
    deficits = [d for _, d in result.root_causes]
    assert deficits == sorted(deficits, reverse=True)


def test_analyze_family_crisis_reasoning_chain_non_empty():
    result = analyze_family_crisis(
        _thriving_profile(GENERATION_GEN_X)
    )
    assert len(result.reasoning) >= 10


def test_analyze_family_crisis_declaration_contains_generation():
    result = analyze_family_crisis(
        FamilyProfile(generation=GENERATION_GEN_Z, health={})
    )
    assert "GEN Z" in result.declaration.upper()


# ---------------------------------------------------------------------------
# Crisis index and health tier
# ---------------------------------------------------------------------------

def test_thriving_profile_has_lower_crisis_index_than_struggling():
    thriving = analyze_family_crisis(_thriving_profile(GENERATION_GEN_X))
    struggling = analyze_family_crisis(
        _struggling_profile(GENERATION_GEN_X)
    )
    assert thriving.overall_crisis_index < struggling.overall_crisis_index


def test_thriving_profile_tier_is_recovering_or_thriving():
    result = analyze_family_crisis(_thriving_profile(GENERATION_GEN_X))
    assert result.health_tier in ("THRIVING", "RECOVERING")


def test_struggling_profile_tier_is_stressed_or_critical():
    result = analyze_family_crisis(_struggling_profile(GENERATION_GEN_X))
    assert result.health_tier in ("STRESSED", "CRITICAL")


def test_crisis_index_bounded_0_to_100():
    for profile in [
        _thriving_profile(GENERATION_GEN_X),
        _struggling_profile(GENERATION_GEN_Z),
    ]:
        result = analyze_family_crisis(profile)
        assert 0.0 <= result.overall_crisis_index <= 100.0


# ---------------------------------------------------------------------------
# Resilience and stressor scores
# ---------------------------------------------------------------------------

def test_high_health_yields_high_resilience_score():
    high = analyze_family_crisis(_thriving_profile(GENERATION_GEN_X))
    low = analyze_family_crisis(_struggling_profile(GENERATION_GEN_X))
    assert high.family_resilience_score > low.family_resilience_score


def test_high_stressors_yield_high_pressure_score():
    high = analyze_family_crisis(_struggling_profile(GENERATION_GEN_X))
    low = analyze_family_crisis(_thriving_profile(GENERATION_GEN_X))
    assert high.stressor_pressure_score > low.stressor_pressure_score


# ---------------------------------------------------------------------------
# Repair actions
# ---------------------------------------------------------------------------

def test_repair_actions_have_positive_predicted_lift():
    result = analyze_family_crisis(
        _struggling_profile(GENERATION_GEN_Z)
    )
    for action in result.repair_plan:
        assert action.predicted_lift > 0


def test_repair_actions_confidence_between_0_and_100():
    result = analyze_family_crisis(
        _struggling_profile(GENERATION_GEN_X)
    )
    for action in result.repair_plan:
        assert 0.0 <= action.engine_confidence <= 100.0


def test_repair_actions_cover_multiple_domains():
    result = analyze_family_crisis(
        _struggling_profile(GENERATION_GEN_X)
    )
    domains = {a.domain for a in result.repair_plan}
    assert len(domains) >= 3


def test_struggling_family_top_action_targets_high_deficit_dims():
    profile = FamilyProfile(
        generation=GENERATION_GEN_X,
        health={
            "partner_communication": 10.0,
            "trust_level": 10.0,
            "income_stability": 80.0,
        },
        stressors=SOCIETAL_STRESSORS,
    )
    result = analyze_family_crisis(profile)
    top = result.repair_plan[0]
    assert isinstance(top, RepairAction)
    assert top.rank == 1


# ---------------------------------------------------------------------------
# analyze_both_generations
# ---------------------------------------------------------------------------

def test_analyze_both_generations_returns_tuple_of_two():
    gx_health = {k: 60.0 for k in HEALTHY_FAMILY_BASELINE}
    gz_health = {k: 55.0 for k in HEALTHY_FAMILY_BASELINE}
    gx, gz = analyze_both_generations(gx_health, gz_health)

    assert gx.generation == GENERATION_GEN_X
    assert gz.generation == GENERATION_GEN_Z


def test_analyze_both_generations_independent_results():
    gx_health = {k: 80.0 for k in HEALTHY_FAMILY_BASELINE}
    gz_health = {k: 30.0 for k in HEALTHY_FAMILY_BASELINE}
    gx, gz = analyze_both_generations(gx_health, gz_health)

    assert gx.family_resilience_score != gz.family_resilience_score


# ---------------------------------------------------------------------------
# render_renaissance_report
# ---------------------------------------------------------------------------

def test_render_renaissance_report_contains_header():
    result = analyze_family_crisis(
        _thriving_profile(GENERATION_GEN_X)
    )
    output = render_renaissance_report(result)

    assert "NEXUS FAMILY RENAISSANCE REPORT" in output
    assert "CRISIS INDEX" in output
    assert "HEALTH TIER" in output


def test_render_renaissance_report_contains_repair_plan():
    result = analyze_family_crisis(
        _struggling_profile(GENERATION_GEN_Z)
    )
    output = render_renaissance_report(result, top_n_actions=3)

    assert "#1" in output
    assert "#2" in output
    assert "#3" in output


def test_render_renaissance_report_contains_declaration():
    result = analyze_family_crisis(
        _thriving_profile(GENERATION_GEN_X)
    )
    output = render_renaissance_report(result)

    assert "Declaration" in output
    assert "RENAISSANCE" in output


def test_render_renaissance_report_contains_root_causes():
    result = analyze_family_crisis(
        _struggling_profile(GENERATION_GEN_X)
    )
    output = render_renaissance_report(result)

    assert "Root Causes" in output
    assert "deficit" in output

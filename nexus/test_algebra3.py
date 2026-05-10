"""Focused tests for the 3-Algebra universal transformer."""

import math

from nexus.algebra3 import (
    ALGEBRA3_VERSION,
    BEHAVIOR_PROFILES,
    HUMAN_RESPONSE_A3_WEIGHTS,
    MONSTERBALL_A3_WEIGHTS,
    TOKEN_A3_WEIGHTS,
    UNIVERSAL_A3_WEIGHTS,
    Algebra3Weights,
    BehaviorProfile,
    apply_algebra3,
    match_behavior,
    render_algebra3_report,
)


# ---------------------------------------------------------------------------
# Layer arithmetic
# ---------------------------------------------------------------------------

def test_apply_algebra3_linear_only_is_exact():
    weights = Algebra3Weights(
        linear={"x": 2.0, "y": 3.0},
        polynomial={},
        exponential={},
        alpha=1.0,
        beta=0.0,
        gamma=0.0,
    )
    result = apply_algebra3("Test", {"x": 5.0, "y": 4.0}, weights, profiles=[])

    # L1 = 2*5 + 3*4 = 22; L2=0; L3=0; combined=22
    assert abs(result.l1_score - 22.0) < 1e-9
    assert abs(result.combined_score - 22.0) < 1e-9


def test_apply_algebra3_polynomial_layer_uses_squared_values():
    weights = Algebra3Weights(
        linear={},
        polynomial={"x": 1.0},
        exponential={},
        alpha=0.0,
        beta=1.0,
        gamma=0.0,
    )
    result = apply_algebra3("Test", {"x": 4.0}, weights, profiles=[])

    # L2 = 1.0 * 4² = 16; combined = beta*L2 = 16
    assert abs(result.l2_score - 16.0) < 1e-9
    assert abs(result.combined_score - 16.0) < 1e-9


def test_apply_algebra3_exponential_layer_matches_math_exp():
    scale = 5.0
    w = 2.0
    x = 10.0
    weights = Algebra3Weights(
        linear={},
        polynomial={},
        exponential={"x": w},
        alpha=0.0,
        beta=0.0,
        gamma=1.0,
        exp_scale=scale,
    )
    result = apply_algebra3("Test", {"x": x}, weights, profiles=[])

    expected_l3 = w * math.exp(x / scale)
    assert abs(result.l3_score - expected_l3) < 1e-9


def test_apply_algebra3_blend_coefficients_combine_layers():
    weights = Algebra3Weights(
        linear={"a": 1.0},
        polynomial={"a": 1.0},
        exponential={"a": 1.0},
        alpha=1.0,
        beta=0.5,
        gamma=0.25,
        exp_scale=10.0,
    )
    result = apply_algebra3("Blend", {"a": 10.0}, weights, profiles=[])

    expected_l1 = 10.0
    expected_l2 = 100.0
    expected_l3 = math.exp(10.0 / 10.0)
    expected = 1.0 * expected_l1 + 0.5 * expected_l2 + 0.25 * expected_l3
    assert abs(result.combined_score - expected) < 1e-6


def test_apply_algebra3_skips_missing_dimension_silently():
    weights = Algebra3Weights(
        linear={"present": 1.0, "absent": 999.0},
        polynomial={},
        exponential={},
    )
    result = apply_algebra3("Miss", {"present": 5.0}, weights, profiles=[])

    assert abs(result.l1_score - 5.0) < 1e-9
    assert result.active_dimensions == 1


def test_apply_algebra3_active_dimensions_counts_unique_keys():
    weights = Algebra3Weights(
        linear={"a": 1.0, "b": 1.0},
        polynomial={"a": 1.0},        # "a" already counted
        exponential={"c": 1.0},
    )
    result = apply_algebra3(
        "ActiveDims",
        {"a": 1.0, "b": 1.0, "c": 1.0},
        weights,
        profiles=[],
    )
    # unique weight keys: a, b, c — all present in stats
    assert result.active_dimensions == 3


# ---------------------------------------------------------------------------
# Behavior matching
# ---------------------------------------------------------------------------

def test_match_behavior_returns_profile_with_minimum_distance():
    profiles = [
        BehaviorProfile("LOW", "low score", {"x": 1.0}),
        BehaviorProfile("HIGH", "high score", {"x": 100.0}),
    ]
    weights = Algebra3Weights(
        linear={"x": 1.0}, alpha=1.0, beta=0.0, gamma=0.0
    )

    best, dist = match_behavior(100.0, weights, profiles)
    assert best.name == "HIGH"
    assert dist < 1.0


def test_match_behavior_handles_empty_profile_list():
    weights = Algebra3Weights(linear={"x": 1.0})
    best, dist = match_behavior(50.0, weights, profiles=[])

    assert best.name == "UNKNOWN"
    assert dist == float("inf")


def test_match_behavior_elite_monster_for_very_high_score():
    weights = MONSTERBALL_A3_WEIGHTS
    stats = {k: 99.0 for k in weights.linear}
    result = apply_algebra3("Test", stats, weights, profiles=BEHAVIOR_PROFILES)

    assert result.like_behavior == "ELITE_MONSTER"


def test_match_behavior_rookie_for_very_low_stats():
    weights = MONSTERBALL_A3_WEIGHTS
    stats = {k: 5.0 for k in weights.linear}
    result = apply_algebra3("Test", stats, weights, profiles=BEHAVIOR_PROFILES)

    assert result.like_behavior == "ROOKIE"


# ---------------------------------------------------------------------------
# answer and algebra chain
# ---------------------------------------------------------------------------

def test_apply_algebra3_answer_contains_domain_and_like():
    result = apply_algebra3(
        "MonsterBall Player",
        {"speed": 80.0, "skill": 90.0},
        MONSTERBALL_A3_WEIGHTS,
    )
    assert "MONSTERBALL PLAYER" in result.answer
    assert "LIKE:" in result.answer


def test_apply_algebra3_chain_has_all_eight_steps():
    result = apply_algebra3(
        "Chain",
        {"speed": 50.0},
        MONSTERBALL_A3_WEIGHTS,
    )
    joined = "\n".join(result.algebra_chain)
    for step in range(1, 9):
        assert f"[A3-{step}]" in joined


def test_apply_algebra3_chain_includes_context():
    result = apply_algebra3(
        "GPU",
        {"speed": 10.0},
        UNIVERSAL_A3_WEIGHTS,
        context="Post-match telemetry",
    )
    assert "Post-match telemetry" in result.algebra_chain[0]


def test_apply_algebra3_reasons_flag_dominant_l1_contributors():
    weights = Algebra3Weights(
        linear={"big": 10.0, "tiny": 0.001},
        polynomial={},
        exponential={},
    )
    result = apply_algebra3(
        "Reason", {"big": 100.0, "tiny": 1.0}, weights, profiles=[]
    )
    assert any("L1:big" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# Domain preset weights
# ---------------------------------------------------------------------------

def test_monsterball_a3_weights_has_correct_domain():
    assert MONSTERBALL_A3_WEIGHTS.domain == "MonsterBall"
    assert "skill" in MONSTERBALL_A3_WEIGHTS.linear


def test_human_response_a3_weights_has_correct_domain():
    assert HUMAN_RESPONSE_A3_WEIGHTS.domain == "Human Response"
    assert "accuracy" in HUMAN_RESPONSE_A3_WEIGHTS.linear


def test_token_a3_weights_has_correct_domain():
    assert TOKEN_A3_WEIGHTS.domain == "Token Activity"
    assert "liquidity" in TOKEN_A3_WEIGHTS.linear


def test_universal_a3_weights_covers_32_linear_dims():
    assert len(UNIVERSAL_A3_WEIGHTS.linear) == 32


# ---------------------------------------------------------------------------
# render_algebra3_report
# ---------------------------------------------------------------------------

def test_render_algebra3_report_header_present():
    result = apply_algebra3(
        "MonsterBall",
        {"speed": 50.0, "skill": 70.0},
        MONSTERBALL_A3_WEIGHTS,
    )
    output = render_algebra3_report([result])

    assert "NEXUS 3-ALGEBRA ENGINE" in output
    assert "@FuzzysTodd" in output
    assert ALGEBRA3_VERSION in output
    assert "Linear + Polynomial + Exponential" in output


def test_render_algebra3_report_includes_like_behavior():
    result = apply_algebra3(
        "Token",
        {"liquidity": 500.0, "staking_ratio": 60.0},
        TOKEN_A3_WEIGHTS,
    )
    output = render_algebra3_report([result])

    assert "LIKE" in output
    assert result.like_behavior in output


def test_render_algebra3_report_handles_empty_results():
    output = render_algebra3_report([])
    assert "No results to display" in output


def test_render_algebra3_report_omits_chain_when_disabled():
    result = apply_algebra3(
        "Quiet",
        {"speed": 10.0},
        MONSTERBALL_A3_WEIGHTS,
    )
    output = render_algebra3_report([result], show_chain=False)
    assert "ALGEBRA CHAIN" not in output


def test_render_algebra3_report_shows_all_three_layer_scores():
    result = apply_algebra3(
        "Layers",
        {"speed": 50.0, "skill": 80.0, "focus": 70.0},
        MONSTERBALL_A3_WEIGHTS,
    )
    output = render_algebra3_report([result], show_chain=False)

    assert "L1=" in output
    assert "L2=" in output
    assert "L3=" in output
    assert "COMBINED=" in output


# ---------------------------------------------------------------------------
# End-to-end: any human response or outcome
# ---------------------------------------------------------------------------

def test_algebra3_applied_to_human_response():
    """3-Algebra produces an answer for any human response stats."""

    stats = {
        "confidence": 85.0,
        "clarity": 90.0,
        "speed": 70.0,
        "accuracy": 95.0,
        "creativity": 60.0,
        "empathy": 75.0,
        "decisiveness": 88.0,
        "adaptability": 72.0,
    }
    result = apply_algebra3(
        "Human Response",
        stats,
        HUMAN_RESPONSE_A3_WEIGHTS,
        context="Expert panel Q&A",
    )

    assert "HUMAN RESPONSE" in result.answer
    assert result.like_behavior in {p.name for p in BEHAVIOR_PROFILES}
    assert result.combined_score > 0
    assert len(result.algebra_chain) == 8


def test_algebra3_applied_to_arbitrary_outcome():
    """Applied to any domain, 3-Algebra always produces the answer."""

    climate_weights = Algebra3Weights(
        domain="Climate",
        linear={
            "temperature": 0.5, "humidity": 0.3,
            "co2_ppm": 0.01, "wind_speed": 0.4,
        },
        polynomial={
            "temperature": 0.002, "co2_ppm": 0.0001,
        },
        exponential={
            "temperature": 0.1, "wind_speed": 0.05,
        },
        alpha=1.0, beta=0.3, gamma=0.1, exp_scale=30.0,
    )
    stats = {
        "temperature": 42.0, "humidity": 88.0,
        "co2_ppm": 420.0, "wind_speed": 55.0,
    }
    result = apply_algebra3(
        "Climate Reading", stats, climate_weights,
        context="Extreme weather event"
    )

    assert "CLIMATE READING" in result.answer
    assert result.active_dimensions == 4
    assert len(result.algebra_chain) == 8


# ---------------------------------------------------------------------------
# render_algebra3_report — additional cases
# ---------------------------------------------------------------------------

def test_render_algebra3_report_multiple_results_all_included():
    r1 = apply_algebra3(
        "MonsterBall",
        {"speed": 50.0, "skill": 70.0},
        MONSTERBALL_A3_WEIGHTS,
    )
    r2 = apply_algebra3(
        "Token Activity",
        {"liquidity": 400.0, "staking_ratio": 55.0},
        TOKEN_A3_WEIGHTS,
    )
    output = render_algebra3_report([r1, r2])

    assert "#1 MonsterBall" in output
    assert "#2 Token Activity" in output


def test_render_algebra3_report_shows_drivers_when_reasons_present():
    weights = Algebra3Weights(
        linear={"big": 10.0, "tiny": 0.001},
        polynomial={},
        exponential={},
    )
    result = apply_algebra3(
        "Driver", {"big": 100.0, "tiny": 1.0}, weights, profiles=[]
    )
    assert result.reasons  # sanity check
    output = render_algebra3_report([result], show_chain=False)
    assert "DRIVERS" in output

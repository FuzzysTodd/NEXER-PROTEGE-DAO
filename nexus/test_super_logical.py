"""Focused tests for the Super Logical 64-dimension universal reasoner."""

from nexus.super_logical import (
    LOGICAL_CAPACITY,
    GPU_SUPER_WEIGHTS,
    MONSTERBALL_SUPER_WEIGHTS,
    TOKEN_SUPER_WEIGHTS,
    UNIVERSAL_SUPER_WEIGHTS,
    LogicalReading,
    SuperLogicalResult,
    SuperLogicalWeights,
    _confidence,
    compose_super_predict,
    render_super_logical_report,
    super_predict,
)


# ---------------------------------------------------------------------------
# super_predict core behaviour
# ---------------------------------------------------------------------------

def test_super_predict_returns_critical_for_near_perfect_stats():
    weights = SuperLogicalWeights(
        domain="Test",
        weights={"a": 1.0, "b": 1.0},
        tier_critical=90.0,
        tier_high=75.0,
        tier_moderate=50.0,
    )
    reading = LogicalReading(domain="Test", stats={"a": 100.0, "b": 100.0})
    result = super_predict(reading, weights)

    assert result.tier == "CRITICAL"
    assert result.confidence >= 90.0


def test_super_predict_returns_low_for_minimal_stats():
    # Confidence is 0% when score is zero → tier must be LOW
    w2 = SuperLogicalWeights(
        domain="Test",
        weights={"x": 1.0},
        tier_critical=90.0,
        tier_high=75.0,
        tier_moderate=50.0,
    )
    r = super_predict(
        LogicalReading(domain="Test", stats={"x": 0.0}), w2
    )
    assert r.confidence == 0.0
    assert r.tier == "LOW"


def test_super_predict_skips_missing_dimensions_silently():
    weights = SuperLogicalWeights(
        domain="Test",
        weights={"present": 2.0, "absent": 99.0},
    )
    reading = LogicalReading(domain="Test", stats={"present": 5.0})
    result = super_predict(reading, weights)

    assert result.active_dimensions == 1
    assert abs(result.score - 10.0) < 1e-9


def test_super_predict_caps_to_logical_capacity():
    oversize = {f"dim_{i:03d}": 1.0 for i in range(LOGICAL_CAPACITY + 20)}
    weights = SuperLogicalWeights(domain="BigTest", weights=oversize)
    assert len(weights.capped_weights()) == LOGICAL_CAPACITY


def test_super_predict_active_dimensions_counts_matched_keys():
    weights = SuperLogicalWeights(
        domain="Counter",
        weights={"a": 1.0, "b": 1.0, "c": 1.0},
    )
    reading = LogicalReading(
        domain="Counter", stats={"a": 10.0, "c": 20.0}
    )
    result = super_predict(reading, weights)

    assert result.active_dimensions == 2


def test_super_predict_answer_contains_domain_and_tier():
    reading = LogicalReading(
        domain="MonsterBall",
        stats={
            "speed": 10.0, "power": 10.0, "offense": 10.0,
            "defense": 10.0, "stamina": 10.0, "aggression": 10.0,
            "skill": 10.0,
        },
    )
    result = super_predict(reading, MONSTERBALL_SUPER_WEIGHTS)

    assert "MONSTERBALL" in result.answer
    assert result.tier in result.answer
    assert result.confidence >= 0.0


def test_super_predict_reasoning_chain_has_all_steps():
    reading = LogicalReading(
        domain="GPU", stats={"power_draw": 130.0, "temperature": 70.0}
    )
    result = super_predict(reading, GPU_SUPER_WEIGHTS)

    joined = "\n".join(result.reasoning_chain)
    assert "[1]" in joined  # domain step
    assert "[2]" in joined  # capacity step
    assert "[3]" in joined  # contributions
    assert "[8] SUPER-LOGICAL ANSWER:" in joined


def test_super_predict_reasons_flag_dominant_contributors():
    weights = SuperLogicalWeights(
        domain="Reason",
        weights={"big": 10.0, "small": 0.01},
    )
    reading = LogicalReading(
        domain="Reason", stats={"big": 50.0, "small": 1.0}
    )
    result = super_predict(reading, weights)

    assert any("big" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# Domain preset weights
# ---------------------------------------------------------------------------

def test_monsterball_super_weights_domain_label():
    assert MONSTERBALL_SUPER_WEIGHTS.domain == "MonsterBall"
    assert "skill" in MONSTERBALL_SUPER_WEIGHTS.weights


def test_token_super_weights_domain_label():
    assert TOKEN_SUPER_WEIGHTS.domain == "Token Activity"
    assert "liquidity" in TOKEN_SUPER_WEIGHTS.weights


def test_universal_super_weights_has_64_dimensions():
    assert len(UNIVERSAL_SUPER_WEIGHTS.weights) == LOGICAL_CAPACITY


def test_monsterball_super_predict_elite_profile_is_high_or_critical():
    reading = LogicalReading(
        domain="MonsterBall",
        stats={
            "speed": 95.0,
            "power": 95.0,
            "offense": 95.0,
            "defense": 95.0,
            "stamina": 95.0,
            "aggression": 95.0,
            "skill": 99.0,
            "goals_per_game": 3.0,
            "assists_per_game": 2.5,
            "win_rate": 0.85,
            "clutch_factor": 90.0,
            "team_synergy": 80.0,
            "recovery_rate": 88.0,
            "reaction_time": 92.0,
            "focus": 90.0,
        },
    )
    result = super_predict(reading, MONSTERBALL_SUPER_WEIGHTS)

    assert result.tier in ("CRITICAL", "HIGH")
    assert result.confidence >= 75.0


def test_token_super_predict_active_market():
    reading = LogicalReading(
        domain="Token Activity",
        stats={
            "tx_volume": 50000.0,
            "holder_count": 1200.0,
            "liquidity": 900.0,
            "staking_ratio": 65.0,
            "governance_participation": 40.0,
            "price_momentum": 70.0,
        },
    )
    result = super_predict(reading, TOKEN_SUPER_WEIGHTS)

    assert result.active_dimensions == 6
    assert result.tier in TIER_LABELS_SET


# ---------------------------------------------------------------------------
# compose_super_predict
# ---------------------------------------------------------------------------

TIER_LABELS_SET = {"CRITICAL", "HIGH", "MODERATE", "LOW"}


def test_compose_super_predict_processes_all_readings():
    readings = [
        LogicalReading(domain="A", stats={"dim_00": 50.0}),
        LogicalReading(domain="B", stats={"dim_00": 10.0}),
        LogicalReading(domain="C", stats={"dim_00": 90.0}),
    ]
    results = compose_super_predict(readings, [UNIVERSAL_SUPER_WEIGHTS])

    assert len(results) == 3
    assert all(isinstance(r, SuperLogicalResult) for r in results)


def test_compose_super_predict_reuses_last_weights_when_short():
    readings = [
        LogicalReading(domain="MB", stats={"speed": 80.0}),
        LogicalReading(domain="MB", stats={"speed": 40.0}),
    ]
    w1 = SuperLogicalWeights(
        domain="MB", weights={"speed": 1.0}, tier_critical=90.0,
        tier_high=75.0, tier_moderate=50.0,
    )
    results = compose_super_predict(readings, [w1])

    assert results[0].domain == "MB"
    assert results[1].domain == "MB"


# ---------------------------------------------------------------------------
# render_super_logical_report
# ---------------------------------------------------------------------------

def test_render_super_logical_report_header_present():
    reading = LogicalReading(
        domain="MonsterBall",
        stats={"speed": 50.0, "skill": 70.0},
    )
    result = super_predict(reading, MONSTERBALL_SUPER_WEIGHTS)
    output = render_super_logical_report([result])

    assert "NEXUS SUPER LOGICAL @ 64-DIM" in output
    assert "@FuzzysTodd" in output
    assert str(LOGICAL_CAPACITY) in output


def test_render_super_logical_report_includes_answer_and_tier():
    reading = LogicalReading(
        domain="Token Activity", stats={"liquidity": 200.0}
    )
    result = super_predict(reading, TOKEN_SUPER_WEIGHTS)
    output = render_super_logical_report([result])

    assert result.tier in output
    assert "ANSWER" in output


def test_render_super_logical_report_handles_empty_results():
    output = render_super_logical_report([])

    assert "No results to display" in output


def test_render_super_logical_report_omits_chain_when_disabled():
    reading = LogicalReading(domain="GPU", stats={"power_draw": 100.0})
    result = super_predict(reading, GPU_SUPER_WEIGHTS)
    output = render_super_logical_report([result], show_chain=False)

    assert "REASONING CHAIN" not in output


def test_super_predict_any_arbitrary_domain():
    """Applied to any outcome the engine creates the super-logical answer."""

    weather_weights = SuperLogicalWeights(
        domain="Weather",
        weights={
            "temperature": 0.5,
            "humidity": 0.3,
            "pressure": 0.2,
            "wind_speed": 0.4,
            "cloud_cover": 0.6,
        },
        tier_critical=90.0,
        tier_high=70.0,
        tier_moderate=45.0,
    )
    reading = LogicalReading(
        domain="Weather",
        stats={
            "temperature": 38.0,
            "humidity": 85.0,
            "pressure": 1008.0,
            "wind_speed": 40.0,
            "cloud_cover": 90.0,
        },
        context="Tropical storm conditions",
    )
    result = super_predict(reading, weather_weights)

    assert result.tier in TIER_LABELS_SET
    assert "WEATHER" in result.answer
    assert len(result.reasoning_chain) >= 5


# ---------------------------------------------------------------------------
# _confidence helper
# ---------------------------------------------------------------------------

def test_confidence_returns_zero_when_max_score_is_zero():
    assert _confidence(50.0, 0.0) == 0.0


def test_confidence_returns_zero_for_zero_score():
    assert _confidence(0.0, 100.0) == 0.0


def test_confidence_returns_100_when_score_equals_max():
    assert abs(_confidence(100.0, 100.0) - 100.0) < 1e-9


def test_confidence_is_clamped_to_100_for_overflow():
    # score > max_score should still be capped at 100
    assert _confidence(200.0, 100.0) == 100.0


def test_confidence_midpoint_is_50():
    assert abs(_confidence(50.0, 100.0) - 50.0) < 1e-9


# ---------------------------------------------------------------------------
# compose_super_predict — edge cases
# ---------------------------------------------------------------------------

def test_compose_super_predict_empty_readings_returns_empty():
    results = compose_super_predict([], [UNIVERSAL_SUPER_WEIGHTS])
    assert results == []


def test_compose_super_predict_single_weights_reused():
    readings = [
        LogicalReading(domain="X", stats={"dim_00": 80.0}),
        LogicalReading(domain="Y", stats={"dim_00": 30.0}),
        LogicalReading(domain="Z", stats={"dim_00": 50.0}),
    ]
    results = compose_super_predict(readings, [UNIVERSAL_SUPER_WEIGHTS])
    assert len(results) == 3
    for r in results:
        assert isinstance(r, SuperLogicalResult)


# ---------------------------------------------------------------------------
# render_super_logical_report — shows drivers when present
# ---------------------------------------------------------------------------

def test_render_super_logical_report_shows_drivers_when_present():
    weights = SuperLogicalWeights(
        domain="Driver Test",
        weights={"big": 10.0, "small": 0.001},
    )
    reading = LogicalReading(
        domain="Driver Test",
        stats={"big": 50.0, "small": 1.0},
    )
    result = super_predict(reading, weights)
    # Confirm reasons are populated
    assert any("big" in r for r in result.reasons)

    output = render_super_logical_report([result])
    assert "DRIVERS" in output
    assert "big" in output

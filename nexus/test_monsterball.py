"""Focused tests for the MonsterBall stats and universal predictor."""

from nexus.monsterball import (
    MONSTERBALL_WEIGHTS,
    MatchSnapshot,
    PlayerStats,
    PredictorWeights,
    predict,
    predict_player,
    rank_players,
    render_match_report,
)


def test_predict_returns_dominant_when_score_meets_threshold():
    weights = PredictorWeights(
        weights={"speed": 1.0, "power": 2.0},
        threshold=50.0,
        label_above="DOMINANT",
        label_below="SUBDUED",
    )
    result = predict({"speed": 10.0, "power": 25.0}, weights=weights)

    assert result.score == 60.0
    assert result.label == "DOMINANT"
    assert "DOMINANT" in result.prediction_text


def test_predict_returns_subdued_when_score_below_threshold():
    weights = PredictorWeights(
        weights={"speed": 1.0, "power": 2.0},
        threshold=100.0,
    )
    result = predict({"speed": 5.0, "power": 10.0}, weights=weights)

    assert result.score == 25.0
    assert result.label == "SUBDUED"


def test_predict_skips_missing_stat_keys_silently():
    weights = PredictorWeights(
        weights={"speed": 1.0, "unknown_stat": 99.0},
        threshold=5.0,
    )
    result = predict({"speed": 10.0}, weights=weights)

    assert result.score == 10.0
    assert result.label == "DOMINANT"


def test_predict_reasons_include_notable_contributors():
    weights = PredictorWeights(
        weights={"skill": 2.0, "speed": 1.0},
        threshold=50.0,
    )
    result = predict({"skill": 30.0, "speed": 1.0}, weights=weights)

    assert any("skill" in r for r in result.reasons)


def test_predict_player_flags_elite_monsterball_profile():
    player = PlayerStats(
        name="FuzzysTodd",
        speed=10.0,
        power=10.0,
        offense=10.0,
        defense=10.0,
        stamina=10.0,
        aggression=10.0,
        skill=10.0,
        games_played=50,
        goals=30,
        assists=15,
    )
    result = predict_player(player)

    expected_score = sum(
        v * w for v, w in zip(
            [10.0] * 7,
            [1.2, 1.5, 1.8, 1.3, 1.0, 0.9, 2.0],
        )
    )
    assert abs(result.score - expected_score) < 1e-6


def test_predict_player_subdued_for_low_stats():
    player = PlayerStats(
        name="Rookie",
        speed=1.0,
        power=1.0,
        offense=1.0,
        defense=1.0,
        stamina=1.0,
        aggression=1.0,
        skill=1.0,
    )
    result = predict_player(player, weights=MONSTERBALL_WEIGHTS)

    assert result.label == "SUBDUED"
    assert result.score < MONSTERBALL_WEIGHTS.threshold


def test_rank_players_orders_highest_score_first():
    low = PlayerStats(
        name="Low", speed=1.0, power=1.0, offense=1.0,
        defense=1.0, stamina=1.0, aggression=1.0, skill=1.0,
    )
    high = PlayerStats(
        name="High", speed=20.0, power=20.0, offense=20.0,
        defense=20.0, stamina=20.0, aggression=20.0, skill=20.0,
    )
    ranked = rank_players([low, high])

    assert ranked[0][0].name == "High"
    assert ranked[1][0].name == "Low"


def test_render_match_report_includes_player_names_and_labels():
    player = PlayerStats(
        name="FuzzysTodd",
        speed=15.0, power=15.0, offense=15.0,
        defense=15.0, stamina=15.0, aggression=15.0, skill=15.0,
        games_played=10, goals=7, assists=3,
    )
    snapshot = MatchSnapshot(
        players=[player],
        match_id="MB-001",
        round_number=2,
    )
    output = render_match_report(snapshot)

    assert "MONSTERBALL NEXUS PREDICTOR" in output
    assert "FuzzysTodd" in output
    assert "MB-001" in output
    assert "Round: 2" in output
    assert any(lbl in output for lbl in ("DOMINANT", "SUBDUED"))


def test_render_match_report_handles_empty_player_list():
    snapshot = MatchSnapshot(players=[], match_id="EMPTY")
    output = render_match_report(snapshot)

    assert "No player data available" in output


def test_render_match_report_surfaces_warnings():
    snapshot = MatchSnapshot(
        players=[],
        match_id="WARN-TEST",
        warnings=["stat feed offline"],
    )
    output = render_match_report(snapshot)

    assert "[WARN] stat feed offline" in output


def test_universal_predictor_works_for_arbitrary_domain():
    """Same strategy applies to any stat domain, not just MonsterBall."""

    token_weights = PredictorWeights(
        weights={"tx_volume": 0.01, "holder_count": 0.5, "liquidity": 0.3},
        threshold=200.0,
        label_above="BULLISH",
        label_below="BEARISH",
    )
    stats = {"tx_volume": 5000.0, "holder_count": 200.0, "liquidity": 150.0}
    result = predict(stats, weights=token_weights)

    assert result.label in ("BULLISH", "BEARISH")
    assert result.score > 0

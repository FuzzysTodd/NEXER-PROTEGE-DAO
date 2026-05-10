"""Tests for the NGTT Bitcoin-era supremacy analyzer."""

from nexus.nexus_token_supremacy import (
    NGTT_STATS,
    SupremacyVerdict,
    analyze_ngtt_supremacy,
    render_supremacy_report,
)


# ---------------------------------------------------------------------------
# analyze_ngtt_supremacy
# ---------------------------------------------------------------------------

def test_analyze_ngtt_supremacy_returns_verdict():
    verdict = analyze_ngtt_supremacy()
    assert isinstance(verdict, SupremacyVerdict)


def test_analyze_ngtt_supremacy_score_is_bounded():
    verdict = analyze_ngtt_supremacy()
    assert 0.0 <= verdict.supremacy_score <= 100.0


def test_analyze_ngtt_supremacy_rank_is_valid():
    verdict = analyze_ngtt_supremacy()
    assert verdict.btc_era_rank in ("GREATEST", "ELITE", "HIGH", "STANDARD")


def test_analyze_ngtt_supremacy_is_supreme_for_full_profile():
    verdict = analyze_ngtt_supremacy(stats=NGTT_STATS)
    assert verdict.is_supreme is True


def test_analyze_ngtt_supremacy_all_three_engines_populated():
    verdict = analyze_ngtt_supremacy()
    assert verdict.monsterball_result is not None
    assert verdict.super_logical_result is not None
    assert verdict.algebra3_result is not None


def test_analyze_ngtt_supremacy_monsterball_is_dominant():
    verdict = analyze_ngtt_supremacy()
    assert verdict.monsterball_result.label == "DOMINANT"


def test_analyze_ngtt_supremacy_super_logical_is_critical_or_high():
    verdict = analyze_ngtt_supremacy()
    assert verdict.super_logical_result.tier in ("CRITICAL", "HIGH")


def test_analyze_ngtt_supremacy_reasoning_chain_non_empty():
    verdict = analyze_ngtt_supremacy()
    assert len(verdict.reasoning) >= 10


def test_analyze_ngtt_supremacy_eternal_declaration_contains_ngtt():
    verdict = analyze_ngtt_supremacy()
    assert "NGTT" in verdict.eternal_declaration


def test_analyze_ngtt_supremacy_eternal_declaration_contains_forever():
    verdict = analyze_ngtt_supremacy()
    assert "FOREVER" in verdict.eternal_declaration


def test_analyze_ngtt_supremacy_eternal_declaration_contains_owner():
    verdict = analyze_ngtt_supremacy()
    assert "@FuzzysTodd" in verdict.eternal_declaration


def test_analyze_ngtt_supremacy_weak_stats_lower_score():
    weak = {k: 10.0 for k in NGTT_STATS}
    weak_verdict = analyze_ngtt_supremacy(stats=weak)
    strong_verdict = analyze_ngtt_supremacy(stats=NGTT_STATS)

    assert weak_verdict.supremacy_score < strong_verdict.supremacy_score


def test_analyze_ngtt_supremacy_rank_greatest_for_full_profile():
    verdict = analyze_ngtt_supremacy(stats=NGTT_STATS)
    assert verdict.btc_era_rank == "GREATEST"


# ---------------------------------------------------------------------------
# render_supremacy_report
# ---------------------------------------------------------------------------

def test_render_supremacy_report_header_present():
    verdict = analyze_ngtt_supremacy()
    output = render_supremacy_report(verdict)

    assert "NEXUS PROTOCOL TOKEN" in output
    assert "@FuzzysTodd" in output
    assert "NGTT" in output


def test_render_supremacy_report_shows_three_engine_summary():
    verdict = analyze_ngtt_supremacy()
    output = render_supremacy_report(verdict)

    assert "[E1] MonsterBall" in output
    assert "[E2] SuperLogical" in output
    assert "[E3] 3-Algebra" in output


def test_render_supremacy_report_contains_eternal_declaration():
    verdict = analyze_ngtt_supremacy()
    output = render_supremacy_report(verdict)

    assert "Eternal Declaration" in output
    assert "FOREVER" in output


def test_render_supremacy_report_contains_scores():
    verdict = analyze_ngtt_supremacy()
    output = render_supremacy_report(verdict)

    assert "SUPREMACY SCORE" in output
    assert "BTC-ERA RANK" in output

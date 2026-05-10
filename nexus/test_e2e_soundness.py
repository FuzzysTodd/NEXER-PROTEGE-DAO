"""Tests for the end-to-end soundness validator."""

from __future__ import annotations

import pytest

from nexus.e2e_soundness import (
    BUILDER_FUND_RULES,
    FINANCIAL_OPS_RULES,
    MATCH_CLOSE_PCT,
    NEXUS_DIMENSION_RANGES,
    SIGNAL_BUS_RULES,
    TIER_MODERATE,
    NetworkResponse,
    SoundnessRule,
    WebAnswer,
    _evaluate_field,
    _in_range,
    _range_for,
    batch_validate,
    render_soundness_report,
    validate_network_only,
    validate_soundness,
)


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def _net(payload, source="test-rest", context=""):
    return NetworkResponse(source=source, payload=payload, context=context)


def _web(payload, surface="test-dashboard", context=""):
    return WebAnswer(surface=surface, payload=payload, context=context)


# ---------------------------------------------------------------------------
# NEXUS_DIMENSION_RANGES catalogue
# ---------------------------------------------------------------------------

def test_dimension_ranges_contains_required_keys():
    required = {"eventCount", "clients", "filesScanned", "preErrorCount",
                "totalCalls", "placementBps", "balanceEth", "latencyMs"}
    assert required.issubset(set(NEXUS_DIMENSION_RANGES))


def test_all_ranges_are_valid_lo_lt_hi():
    for dim, (lo, hi) in NEXUS_DIMENSION_RANGES.items():
        assert lo < hi, f"{dim}: lo={lo} >= hi={hi}"


# ---------------------------------------------------------------------------
# _range_for
# ---------------------------------------------------------------------------

def test_range_for_returns_catalogue_default():
    assert _range_for("clients", None) == (0.0, 10_000.0)


def test_range_for_honours_rule_override():
    rule = SoundnessRule("clients", expected_range=(0.0, 50.0))
    assert _range_for("clients", rule) == (0.0, 50.0)


def test_range_for_unknown_dim_returns_none():
    assert _range_for("unknownDimension_xyz", None) is None


def test_range_for_rule_without_override_falls_back_to_catalogue():
    rule = SoundnessRule("clients")   # no expected_range
    assert _range_for("clients", rule) == (0.0, 10_000.0)


# ---------------------------------------------------------------------------
# _in_range
# ---------------------------------------------------------------------------

def test_in_range_value_inside():
    assert _in_range(50.0, (0.0, 100.0)) is True


def test_in_range_value_on_lo_boundary():
    assert _in_range(0.0, (0.0, 100.0)) is True


def test_in_range_value_on_hi_boundary():
    assert _in_range(100.0, (0.0, 100.0)) is True


def test_in_range_value_below_lo():
    assert _in_range(-1.0, (0.0, 100.0)) is False


def test_in_range_value_above_hi():
    assert _in_range(101.0, (0.0, 100.0)) is False


def test_in_range_none_range_always_true():
    assert _in_range(999_999.0, None) is True


# ---------------------------------------------------------------------------
# _evaluate_field — both values present
# ---------------------------------------------------------------------------

def test_evaluate_field_exact_match():
    fr = _evaluate_field("clients", 42.0, 42.0, None)
    assert fr.match_grade == "EXACT"
    assert fr.relative_diff_pct == 0.0


def test_evaluate_field_close_match_within_tolerance():
    # 3 % difference, tolerance 5 % → CLOSE
    fr = _evaluate_field("clients", 100.0, 103.0, None)
    assert fr.match_grade == "CLOSE"
    assert fr.relative_diff_pct is not None
    assert fr.relative_diff_pct < MATCH_CLOSE_PCT


def test_evaluate_field_diverged_exceeds_tolerance():
    fr = _evaluate_field("clients", 100.0, 120.0, None)
    assert fr.match_grade == "DIVERGED"


def test_evaluate_field_out_of_range_network():
    rule = SoundnessRule("clients", expected_range=(0.0, 10.0))
    fr = _evaluate_field("clients", 9999.0, 5.0, rule)
    assert fr.match_grade == "OUT_OF_RANGE"
    assert fr.in_range_network is False
    assert fr.in_range_web is True


def test_evaluate_field_out_of_range_web():
    rule = SoundnessRule("clients", expected_range=(0.0, 10.0))
    fr = _evaluate_field("clients", 5.0, 9999.0, rule)
    assert fr.match_grade == "OUT_OF_RANGE"
    assert fr.in_range_network is True
    assert fr.in_range_web is False


def test_evaluate_field_out_of_range_both():
    rule = SoundnessRule("clients", expected_range=(0.0, 10.0))
    fr = _evaluate_field("clients", 9998.0, 9999.0, rule)
    assert fr.match_grade == "OUT_OF_RANGE"
    assert fr.in_range_network is False
    assert fr.in_range_web is False


def test_evaluate_field_no_range_defined_does_not_flag_out_of_range():
    # Dimension not in catalogue, no rule → no range → EXACT if values match
    fr = _evaluate_field("customDim", 500.0, 500.0, None)
    assert fr.match_grade == "EXACT"


# ---------------------------------------------------------------------------
# _evaluate_field — missing values
# ---------------------------------------------------------------------------

def test_evaluate_field_both_missing():
    fr = _evaluate_field("clients", None, None, None)
    assert fr.match_grade == "MISSING"
    assert fr.relative_diff_pct is None


def test_evaluate_field_missing_network():
    fr = _evaluate_field("clients", None, 42.0, None)
    assert fr.match_grade == "MISSING"
    assert fr.network_value is None
    assert fr.web_value == 42.0


def test_evaluate_field_missing_web():
    fr = _evaluate_field("clients", 42.0, None, None)
    assert fr.match_grade == "MISSING"
    assert fr.network_value == 42.0
    assert fr.web_value is None


# ---------------------------------------------------------------------------
# _evaluate_field — custom tolerance via rule
# ---------------------------------------------------------------------------

def test_evaluate_field_custom_tight_tolerance_downgrades_close_to_diverged():
    rule = SoundnessRule("clients", tolerance_pct=1.0)
    # 3 % difference; tight 1 % tolerance → DIVERGED
    fr = _evaluate_field("clients", 100.0, 103.0, rule)
    assert fr.match_grade == "DIVERGED"


def test_evaluate_field_custom_loose_tolerance_upgrades_diverged_to_close():
    rule = SoundnessRule("clients", tolerance_pct=25.0)
    # 20 % difference; 25 % tolerance → CLOSE
    fr = _evaluate_field("clients", 100.0, 120.0, rule)
    assert fr.match_grade == "CLOSE"


# ---------------------------------------------------------------------------
# validate_soundness — tier and score
# ---------------------------------------------------------------------------

def test_validate_soundness_all_exact_returns_sound():
    payload = {"clients": 5.0, "eventCount": 100.0}
    result = validate_soundness(_net(payload), _web(payload))
    assert result.tier == "SOUND"
    assert result.soundness_score == 100.0
    assert result.dimensions_matched == 2


def test_validate_soundness_empty_payloads_returns_sound():
    result = validate_soundness(_net({}), _web({}))
    assert result.tier == "SOUND"
    assert result.soundness_score == 100.0
    assert result.dimensions_evaluated == 0


def test_validate_soundness_all_diverged_returns_unsound():
    net_payload = {"a": 1.0, "b": 2.0}
    web_payload = {"a": 1000.0, "b": 2000.0}
    result = validate_soundness(_net(net_payload), _web(web_payload))
    assert result.tier == "UNSOUND"
    assert result.soundness_score == 0.0


def test_validate_soundness_partial_match_returns_moderate():
    # 4 dims: 2 exact, 2 diverged → 50 % → MODERATE
    net_payload = {"a": 10.0, "b": 20.0, "c": 1.0, "d": 2.0}
    web_payload = {"a": 10.0, "b": 20.0, "c": 999.0, "d": 999.0}
    result = validate_soundness(_net(net_payload), _web(web_payload))
    assert result.soundness_score == pytest.approx(50.0)
    assert result.tier == "MODERATE"


def test_validate_soundness_score_75_returns_high():
    # 4 dims: 3 exact, 1 diverged → 75 % → HIGH
    net_payload = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0}
    web_payload = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 999.0}
    result = validate_soundness(_net(net_payload), _web(web_payload))
    assert result.soundness_score == pytest.approx(75.0)
    assert result.tier == "HIGH"


def test_validate_soundness_counts_missing_not_as_matched():
    net_payload = {"a": 1.0}
    web_payload = {"b": 2.0}
    result = validate_soundness(_net(net_payload), _web(web_payload))
    assert result.dimensions_missing == 2
    assert result.dimensions_matched == 0
    assert result.tier == "UNSOUND"


def test_validate_soundness_dimensions_evaluated_is_union():
    net_payload = {"a": 1.0, "b": 2.0}
    web_payload = {"b": 2.0, "c": 3.0}
    result = validate_soundness(_net(net_payload), _web(web_payload))
    assert result.dimensions_evaluated == 3


def test_validate_soundness_field_results_cover_all_dims():
    net_payload = {"x": 1.0}
    web_payload = {"y": 2.0}
    result = validate_soundness(_net(net_payload), _web(web_payload))
    dims = {fr.dimension for fr in result.field_results}
    assert "x" in dims
    assert "y" in dims


def test_validate_soundness_source_and_surface_echoed():
    result = validate_soundness(
        _net({}, source="my-api"),
        _web({}, surface="my-ui"),
    )
    assert result.network_source == "my-api"
    assert result.web_surface == "my-ui"


def test_validate_soundness_verdict_contains_tier():
    payload = {"clients": 5.0}
    result = validate_soundness(_net(payload), _web(payload))
    assert "SOUND" in result.verdict


def test_validate_soundness_reasoning_chain_has_ten_steps():
    result = validate_soundness(_net({"a": 1.0}), _web({"a": 1.0}))
    # Chain always contains exactly 10 labeled steps (E2E-1 through E2E-10)
    assert len(result.reasoning_chain) == 10
    assert any("E2E-1" in s for s in result.reasoning_chain)
    assert any("VERDICT" in s for s in result.reasoning_chain)


def test_validate_soundness_with_rule_override_exact_tolerance():
    rule = SoundnessRule("eventCount", tolerance_pct=0.1)
    net_payload = {"eventCount": 100.0}
    web_payload = {"eventCount": 100.5}
    # 0.5 % diff, 0.1 % tolerance → DIVERGED
    result = validate_soundness(_net(net_payload), _web(web_payload), rules=[rule])
    assert result.dimensions_matched == 0
    assert result.field_results[0].match_grade == "DIVERGED"


def test_validate_soundness_required_rule_missing_dim_counted():
    rule = SoundnessRule("eventCount", required=True)
    # neither layer has eventCount
    result = validate_soundness(_net({}), _web({}), rules=[rule])
    assert result.dimensions_missing == 1


def test_validate_soundness_close_match_counted_as_matched():
    # 3 % difference < 5 % default → CLOSE → counted as matched
    net_payload = {"clients": 100.0}
    web_payload = {"clients": 103.0}
    result = validate_soundness(_net(net_payload), _web(web_payload))
    assert result.dimensions_matched == 1
    assert result.tier == "SOUND"


# ---------------------------------------------------------------------------
# validate_soundness — context strings
# ---------------------------------------------------------------------------

def test_validate_soundness_context_appears_in_chain():
    result = validate_soundness(
        _net({"a": 1.0}, context="snapshot A"),
        _web({"a": 1.0}, context="render B"),
    )
    assert any("snapshot A" in step for step in result.reasoning_chain)
    assert any("render B" in step for step in result.reasoning_chain)


# ---------------------------------------------------------------------------
# validate_network_only
# ---------------------------------------------------------------------------

def test_validate_network_only_all_in_range_returns_sound():
    payload = {"clients": 5.0, "eventCount": 200.0, "latencyMs": 50.0}
    result = validate_network_only(_net(payload))
    assert result.tier == "SOUND"
    assert result.dimensions_matched == 3
    assert result.web_surface == "(network-only)"


def test_validate_network_only_out_of_range_value_flagged():
    payload = {"clients": 99999.0}   # exceeds (0, 10_000)
    result = validate_network_only(_net(payload))
    assert result.dimensions_out_of_range == 1
    assert result.tier == "UNSOUND"


def test_validate_network_only_unknown_dim_treated_as_in_range():
    payload = {"customMetric_xyz": 999999.0}
    result = validate_network_only(_net(payload))
    assert result.dimensions_matched == 1   # no range → in range → EXACT


def test_validate_network_only_empty_payload_returns_sound():
    result = validate_network_only(_net({}))
    assert result.tier == "SOUND"
    assert result.soundness_score == 100.0


def test_validate_network_only_all_field_results_have_no_web_value():
    payload = {"clients": 5.0, "eventCount": 10.0}
    result = validate_network_only(_net(payload))
    for fr in result.field_results:
        assert fr.web_value is None


def test_validate_network_only_reasoning_chain_present():
    result = validate_network_only(_net({"clients": 5.0}))
    # Chain contains at least the source, dimensions, and verdict steps
    assert any("E2E-1" in s for s in result.reasoning_chain)
    assert any("VERDICT" in s for s in result.reasoning_chain)


# ---------------------------------------------------------------------------
# batch_validate
# ---------------------------------------------------------------------------

def test_batch_validate_returns_results_in_order():
    pairs = [
        (_net({"a": 1.0}, source="api-1"), _web({"a": 1.0}, surface="ui-1")),
        (_net({"b": 2.0}, source="api-2"), _web({"b": 9999.0}, surface="ui-2")),
    ]
    results = batch_validate(pairs)
    assert len(results) == 2
    assert results[0].network_source == "api-1"
    assert results[1].network_source == "api-2"


def test_batch_validate_empty_list_returns_empty():
    assert batch_validate([]) == []


def test_batch_validate_applies_shared_rules_to_all_pairs():
    rule = SoundnessRule("clients", expected_range=(0.0, 10.0))
    pairs = [
        (_net({"clients": 5.0}), _web({"clients": 5.0})),
        (_net({"clients": 9999.0}), _web({"clients": 5.0})),
    ]
    results = batch_validate(pairs, rules=[rule])
    # First pair: both in range → EXACT → SOUND
    assert results[0].tier == "SOUND"
    # Second pair: network out of range → OUT_OF_RANGE → UNSOUND
    assert results[1].field_results[0].match_grade == "OUT_OF_RANGE"


# ---------------------------------------------------------------------------
# Pre-built rule sets
# ---------------------------------------------------------------------------

def test_signal_bus_rules_cover_expected_dimensions():
    dims = {r.dimension for r in SIGNAL_BUS_RULES}
    assert "eventCount" in dims
    assert "clients" in dims
    assert "port" in dims


def test_financial_ops_rules_cover_expected_dimensions():
    dims = {r.dimension for r in FINANCIAL_OPS_RULES}
    assert "filesScanned" in dims
    assert "preErrorCount" in dims
    assert "withdrawSignalCount" in dims
    assert "placementSignalCount" in dims


def test_builder_fund_rules_cover_expected_dimensions():
    dims = {r.dimension for r in BUILDER_FUND_RULES}
    assert "totalCalls" in dims
    assert "placementBps" in dims


def test_signal_bus_rules_all_required():
    assert all(r.required for r in SIGNAL_BUS_RULES)


def test_financial_ops_rules_all_required():
    assert all(r.required for r in FINANCIAL_OPS_RULES)


def test_builder_fund_rules_all_required():
    assert all(r.required for r in BUILDER_FUND_RULES)


# ---------------------------------------------------------------------------
# render_soundness_report
# ---------------------------------------------------------------------------

def test_render_soundness_report_contains_tier_label():
    payload = {"clients": 5.0}
    result = validate_soundness(_net(payload), _web(payload))
    report = render_soundness_report(result)
    assert "SOUND" in report


def test_render_soundness_report_contains_source_and_surface():
    result = validate_soundness(
        _net({}, source="my-rest"),
        _web({}, surface="my-ui"),
    )
    report = render_soundness_report(result)
    assert "my-rest" in report
    assert "my-ui" in report


def test_render_soundness_report_contains_verdict():
    payload = {"a": 1.0}
    result = validate_soundness(_net(payload), _web(payload))
    report = render_soundness_report(result)
    assert "VERDICT" in report


def test_render_soundness_report_show_fields_false_omits_field_table():
    payload = {"clients": 5.0}
    result = validate_soundness(_net(payload), _web(payload))
    report = render_soundness_report(result, show_fields=False)
    assert "Field results" not in report


def test_render_soundness_report_show_chain_false_omits_chain():
    payload = {"clients": 5.0}
    result = validate_soundness(_net(payload), _web(payload))
    report = render_soundness_report(result, show_chain=False)
    assert "Reasoning chain" not in report


def test_render_soundness_report_is_plain_string():
    result = validate_soundness(_net({}), _web({}))
    report = render_soundness_report(result)
    assert isinstance(report, str)


def test_render_soundness_report_ends_with_separator():
    result = validate_soundness(_net({}), _web({}))
    report = render_soundness_report(result)
    assert report.endswith("============================================")


# ---------------------------------------------------------------------------
# SoundnessResult dataclass immutability
# ---------------------------------------------------------------------------

def test_soundness_result_is_frozen():
    payload = {"a": 1.0}
    result = validate_soundness(_net(payload), _web(payload))
    with pytest.raises((AttributeError, TypeError)):
        result.tier = "UNSOUND"  # type: ignore[misc]


def test_field_result_is_frozen():
    fr = _evaluate_field("clients", 5.0, 5.0, None)
    with pytest.raises((AttributeError, TypeError)):
        fr.match_grade = "DIVERGED"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Tier boundary conditions
# ---------------------------------------------------------------------------

def test_soundness_score_exactly_90_is_sound():
    # 9 exact + 1 diverged = 90 % → SOUND
    net_payload = {f"d{i}": float(i) for i in range(9)}
    web_payload = dict(net_payload)
    net_payload["d_bad"] = 1.0
    web_payload["d_bad"] = 9999.0
    result = validate_soundness(_net(net_payload), _web(web_payload))
    assert result.soundness_score == pytest.approx(90.0)
    assert result.tier == "SOUND"


def test_soundness_score_exactly_75_is_high():
    # 3 exact + 1 diverged = 75 % → HIGH
    net_payload = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0}
    web_payload = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 99999.0}
    result = validate_soundness(_net(net_payload), _web(web_payload))
    assert result.soundness_score == pytest.approx(75.0)
    assert result.tier == "HIGH"


def test_soundness_score_exactly_50_is_moderate():
    net_payload = {"a": 1.0, "b": 2.0}
    web_payload = {"a": 1.0, "b": 99999.0}
    result = validate_soundness(_net(net_payload), _web(web_payload))
    assert result.soundness_score == pytest.approx(50.0)
    assert result.tier == "MODERATE"


def test_soundness_score_below_50_is_unsound():
    net_payload = {"a": 1.0, "b": 2.0, "c": 3.0}
    web_payload = {"a": 9999.0, "b": 9999.0, "c": 3.0}
    result = validate_soundness(_net(net_payload), _web(web_payload))
    # 1/3 = 33.3 % → UNSOUND
    assert result.soundness_score < TIER_MODERATE
    assert result.tier == "UNSOUND"


# ---------------------------------------------------------------------------
# Real-world Nexus signal-bus scenario
# ---------------------------------------------------------------------------

def test_signal_bus_scenario_exact_match():
    net_payload = {"clients": 3.0, "eventCount": 42.0, "port": 8790.0}
    web_payload = {"clients": 3.0, "eventCount": 42.0, "port": 8790.0}
    result = validate_soundness(
        _net(net_payload, source="signal-bus/health"),
        _web(web_payload, surface="dashboard.html"),
        rules=SIGNAL_BUS_RULES,
    )
    assert result.tier == "SOUND"
    assert result.dimensions_matched == 3


def test_signal_bus_scenario_stale_client_count_diverges():
    net_payload = {"clients": 10.0, "eventCount": 500.0, "port": 8790.0}
    web_payload = {"clients": 1.0, "eventCount": 500.0, "port": 8790.0}
    result = validate_soundness(
        _net(net_payload, source="signal-bus/health"),
        _web(web_payload, surface="dashboard.html"),
        rules=SIGNAL_BUS_RULES,
    )
    # clients diverges by 90 %, others exact → 2/3 = 66.7 % → MODERATE
    assert result.tier == "MODERATE"
    client_fr = next(fr for fr in result.field_results if fr.dimension == "clients")
    assert client_fr.match_grade == "DIVERGED"


def test_financial_ops_scenario_all_matching():
    payload = {
        "filesScanned": 120.0,
        "preErrorCount": 3.0,
        "withdrawSignalCount": 0.0,
        "placementSignalCount": 5.0,
    }
    result = validate_soundness(
        _net(payload, source="financial-ops-rest"),
        _web(payload, surface="financial-ops-dashboard.html"),
        rules=FINANCIAL_OPS_RULES,
    )
    assert result.tier == "SOUND"
    assert result.soundness_score == 100.0

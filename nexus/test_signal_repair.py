"""Tests for the 1,000-particle exchange signal degradation solver."""

from nexus.signal_repair import (
    EXCHANGE_SIGNAL_RANGES,
    PARTICLE_COUNT,
    DegradedSignal,
    _majority,
    _median,
    evaluate_particle,
    generate_particles,
    render_repair_report,
    repair_signal,
)


# ---------------------------------------------------------------------------
# Particle generation
# ---------------------------------------------------------------------------

def test_generate_particles_returns_correct_count():
    particles = generate_particles(PARTICLE_COUNT)
    assert len(particles) == PARTICLE_COUNT


def test_generate_particles_is_deterministic():
    p1 = generate_particles(10)
    p2 = generate_particles(10)
    for a, b in zip(p1, p2):
        assert a.alpha == b.alpha
        assert a.beta == b.beta
        assert a.gamma == b.gamma
        assert a.sensitivity == b.sensitivity


def test_generate_particles_all_have_unique_ids():
    particles = generate_particles(100)
    ids = [p.particle_id for p in particles]
    assert len(set(ids)) == 100


def test_generate_particles_bounds():
    particles = generate_particles(PARTICLE_COUNT)
    for p in particles:
        assert 0.5 <= p.alpha <= 1.0
        assert 0.05 <= p.beta <= 0.55
        assert 0.02 <= p.gamma <= 0.22
        assert 0.5 <= p.sensitivity <= 1.5


# ---------------------------------------------------------------------------
# Single-particle evaluation
# ---------------------------------------------------------------------------

def test_evaluate_particle_clean_signal_scores_near_zero():
    particles = generate_particles(1)
    signal = DegradedSignal(
        exchange="TestEx",
        dimensions={
            "tick_completeness": 95.0,
            "latency_ms": 50.0,
            "noise_floor": 1.0,
        },
    )
    vote = evaluate_particle(signal, particles[0])

    assert vote.degradation_score < 15.0
    assert vote.classification in ("CLEAN", "NOISY")


def test_evaluate_particle_out_of_range_scores_high():
    particles = generate_particles(1)
    signal = DegradedSignal(
        exchange="TestEx",
        dimensions={"tick_completeness": 5.0},  # ideal: 90–100
    )
    vote = evaluate_particle(signal, particles[0])

    assert vote.degradation_score > 50.0
    assert vote.classification in ("DEGRADED", "CRITICAL")


def test_evaluate_particle_corrected_value_closer_to_ideal():
    particles = generate_particles(1)
    # tick_completeness ideal: 90–100, observed: 5 (very low)
    signal = DegradedSignal(
        exchange="TestEx",
        dimensions={"tick_completeness": 5.0},
    )
    vote = evaluate_particle(signal, particles[0])

    assert vote.corrected["tick_completeness"] > 5.0


def test_evaluate_particle_unknown_dim_passed_through():
    particles = generate_particles(1)
    signal = DegradedSignal(
        exchange="TestEx",
        dimensions={"mystery_metric": 42.0},
        expected_ranges={},
    )
    vote = evaluate_particle(signal, particles[0])

    assert vote.corrected["mystery_metric"] == 42.0


# ---------------------------------------------------------------------------
# repair_signal (small particle set for speed)
# ---------------------------------------------------------------------------

def _small_particles():
    return generate_particles(50)


def test_repair_signal_clean_signal_returns_clean():
    signal = DegradedSignal(
        exchange="CleanEx",
        dimensions={
            "tick_completeness": 95.0,
            "latency_ms": 30.0,
            "noise_floor": 0.5,
            "packet_loss_pct": 0.001,
        },
    )
    result = repair_signal(signal, particles=_small_particles())

    assert result.consensus_classification in ("CLEAN", "NOISY")
    assert result.consensus_degradation < 20.0


def test_repair_signal_degraded_signal_returns_degraded_or_critical():
    signal = DegradedSignal(
        exchange="DegEx",
        dimensions={
            "tick_completeness": 10.0,   # ideal 90–100
            "packet_loss_pct": 50.0,     # ideal 0–1
            "feed_staleness_s": 300.0,   # ideal 0–5
        },
    )
    result = repair_signal(signal, particles=_small_particles())

    assert result.consensus_classification in ("DEGRADED", "CRITICAL")
    assert result.consensus_degradation > 30.0


def test_repair_signal_corrected_values_present_for_all_dims():
    signal = DegradedSignal(
        exchange="ValEx",
        dimensions={
            "spread_signal": 0.5,
            "noise_floor": 1.0,
        },
    )
    result = repair_signal(signal, particles=_small_particles())

    assert "spread_signal" in result.corrected_signal
    assert "noise_floor" in result.corrected_signal


def test_repair_signal_particle_count_matches_input():
    particles = generate_particles(20)
    signal = DegradedSignal(
        exchange="CountEx",
        dimensions={"latency_ms": 50.0},
    )
    result = repair_signal(signal, particles=particles)

    assert result.particle_count == 20


def test_repair_signal_particle_agreement_is_valid_percentage():
    signal = DegradedSignal(
        exchange="AgrEx",
        dimensions={"noise_floor": 1.0},
    )
    result = repair_signal(signal, particles=_small_particles())

    assert 0.0 <= result.particle_agreement <= 100.0


def test_repair_signal_chain_has_all_steps():
    signal = DegradedSignal(
        exchange="ChainEx",
        dimensions={"latency_ms": 100.0},
    )
    result = repair_signal(signal, particles=_small_particles())
    joined = "\n".join(result.repair_chain)

    for step in range(1, 10):
        assert f"[SR-{step}]" in joined


def test_repair_signal_verdict_contains_exchange_name():
    signal = DegradedSignal(
        exchange="NexusExchange",
        dimensions={"spread_signal": 0.1},
    )
    result = repair_signal(signal, particles=_small_particles())

    assert "NexusExchange" in result.verdict


def test_repair_signal_original_signal_preserved():
    orig = {"spread_signal": 0.1, "noise_floor": 2.5}
    signal = DegradedSignal(exchange="OrigEx", dimensions=dict(orig))
    result = repair_signal(signal, particles=_small_particles())

    assert result.original_signal == orig


def test_repair_signal_custom_expected_ranges():
    signal = DegradedSignal(
        exchange="CustomEx",
        dimensions={"custom_metric": 50.0},
        expected_ranges={"custom_metric": (45.0, 55.0)},
    )
    result = repair_signal(signal, particles=_small_particles())

    assert result.consensus_classification in ("CLEAN", "NOISY")


def test_repair_signal_degradation_type_detected():
    # All values pinned at low boundary → DROPPED
    signal = DegradedSignal(
        exchange="TypeEx",
        dimensions={
            "tick_completeness": 0.0,
            "order_book_depth": 0.0,
            "liquidity_signal": 0.0,
        },
    )
    result = repair_signal(signal, particles=_small_particles())

    assert result.degradation_type in (
        "DROPPED", "CLIPPED", "CRITICALLY_ILL",
        "SPIKED", "DEGRADED", "NOISY",
    )


# ---------------------------------------------------------------------------
# render_repair_report
# ---------------------------------------------------------------------------

def test_render_repair_report_header_present():
    signal = DegradedSignal(
        exchange="RenderEx",
        dimensions={"latency_ms": 50.0},
    )
    result = repair_signal(signal, particles=_small_particles())
    output = render_repair_report(result)

    assert "NEXUS SIGNAL REPAIR ENGINE" in output
    assert "@FuzzysTodd" in output
    assert str(PARTICLE_COUNT) in output


def test_render_repair_report_shows_corrected_values():
    signal = DegradedSignal(
        exchange="ShowEx",
        dimensions={"spread_signal": 3.0, "noise_floor": 0.5},
    )
    result = repair_signal(signal, particles=_small_particles())
    output = render_repair_report(result, show_corrections=True)

    assert "spread_signal" in output
    assert "noise_floor" in output


def test_render_repair_report_omits_chain_when_disabled():
    signal = DegradedSignal(
        exchange="QuietEx",
        dimensions={"latency_ms": 100.0},
    )
    result = repair_signal(signal, particles=_small_particles())
    output = render_repair_report(result, show_chain=False)

    assert "Repair chain" not in output


def test_exchange_signal_ranges_catalogue_populated():
    assert len(EXCHANGE_SIGNAL_RANGES) >= 10
    for key, (lo, hi) in EXCHANGE_SIGNAL_RANGES.items():
        assert hi >= lo, f"Range for {key} invalid: [{lo}, {hi}]"


# ---------------------------------------------------------------------------
# _median helper
# ---------------------------------------------------------------------------

def test_median_empty_list_returns_zero():
    assert _median([]) == 0.0


def test_median_single_element():
    assert _median([42.0]) == 42.0


def test_median_odd_count():
    assert _median([3.0, 1.0, 2.0]) == 2.0


def test_median_even_count_averages_middle_two():
    assert _median([1.0, 2.0, 3.0, 4.0]) == 2.5


def test_median_unsorted_input():
    assert _median([10.0, 1.0, 5.0, 3.0]) == 4.0


# ---------------------------------------------------------------------------
# _majority helper
# ---------------------------------------------------------------------------

def test_majority_empty_labels_returns_clean_100():
    label, pct = _majority([])
    assert label == "CLEAN"
    assert pct == 100.0


def test_majority_unanimous_labels():
    label, pct = _majority(["NOISY", "NOISY", "NOISY"])
    assert label == "NOISY"
    assert abs(pct - 100.0) < 1e-9


def test_majority_majority_wins():
    labels = ["CLEAN", "CLEAN", "NOISY"]
    label, pct = _majority(labels)
    assert label == "CLEAN"
    assert abs(pct - (2 / 3) * 100) < 1e-6


# ---------------------------------------------------------------------------
# DegradedSignal.range_for
# ---------------------------------------------------------------------------

def test_degraded_signal_range_for_custom_range_overrides_catalogue():
    signal = DegradedSignal(
        exchange="TestEx",
        dimensions={"my_dim": 50.0},
        expected_ranges={"my_dim": (40.0, 60.0)},
    )
    rng = signal.range_for("my_dim")
    assert rng == (40.0, 60.0)


def test_degraded_signal_range_for_falls_back_to_catalogue():
    signal = DegradedSignal(
        exchange="TestEx",
        dimensions={"latency_ms": 100.0},
    )
    rng = signal.range_for("latency_ms")
    assert rng is not None
    assert rng == EXCHANGE_SIGNAL_RANGES["latency_ms"]


def test_degraded_signal_range_for_unknown_returns_none():
    signal = DegradedSignal(
        exchange="TestEx",
        dimensions={"totally_unknown": 42.0},
    )
    assert signal.range_for("totally_unknown") is None


# ---------------------------------------------------------------------------
# render_repair_report — show_corrections=False
# ---------------------------------------------------------------------------

def test_render_repair_report_omits_corrections_when_disabled():
    signal = DegradedSignal(
        exchange="NoCorr",
        dimensions={"latency_ms": 50.0, "noise_floor": 1.0},
    )
    result = repair_signal(signal, particles=generate_particles(20))
    output = render_repair_report(result, show_corrections=False, show_chain=True)

    assert "Corrected signal values" not in output
    assert "Repair chain" in output

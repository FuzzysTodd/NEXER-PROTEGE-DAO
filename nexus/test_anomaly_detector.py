"""Dedicated tests for the anomaly_detector module."""

from nexus.anomaly_detector import (
    GPUReading,
    MLWeights,
    TelemetrySnapshot,
    detect_anomalies,
    invoke_ml_predictive_repair,
)


# ---------------------------------------------------------------------------
# MLWeights
# ---------------------------------------------------------------------------

def test_ml_weights_default_values():
    w = MLWeights()
    assert w.fractal_precision == 9191.0
    assert w.threshold == 140.5
    assert w.sensitivity == 0.05


def test_ml_weights_custom_values():
    w = MLWeights(fractal_precision=1000.0, threshold=200.0, sensitivity=0.1)
    assert w.threshold == 200.0
    assert w.sensitivity == 0.1


# ---------------------------------------------------------------------------
# GPUReading
# ---------------------------------------------------------------------------

def test_gpu_reading_model_defaults_to_unknown():
    reading = GPUReading(
        index="0",
        power_draw=100.0,
        temperature=60.0,
        fan_speed=50,
    )
    assert reading.model == "Unknown"


def test_gpu_reading_raw_line_defaults_to_empty():
    reading = GPUReading(
        index="1",
        power_draw=None,
        temperature=None,
        fan_speed=None,
    )
    assert reading.raw_line == ""


def test_gpu_reading_stores_all_fields():
    reading = GPUReading(
        index="2",
        power_draw=130.0,
        temperature=75.0,
        fan_speed=80,
        model="RTX 4090",
        raw_line="raw csv line",
    )
    assert reading.index == "2"
    assert reading.power_draw == 130.0
    assert reading.temperature == 75.0
    assert reading.fan_speed == 80
    assert reading.model == "RTX 4090"
    assert reading.raw_line == "raw csv line"


# ---------------------------------------------------------------------------
# TelemetrySnapshot
# ---------------------------------------------------------------------------

def test_telemetry_snapshot_defaults():
    snap = TelemetrySnapshot(gpus=[])
    assert snap.pipe_status == "unknown"
    assert snap.telemetry_source == "nvidia-smi"
    assert snap.warnings == []


def test_telemetry_snapshot_custom_fields():
    reading = GPUReading(index="0", power_draw=100.0, temperature=50.0, fan_speed=40)
    snap = TelemetrySnapshot(
        gpus=[reading],
        pipe_status="eth0",
        telemetry_source="mock",
        warnings=["test warning"],
    )
    assert len(snap.gpus) == 1
    assert snap.pipe_status == "eth0"
    assert snap.warnings == ["test warning"]


# ---------------------------------------------------------------------------
# invoke_ml_predictive_repair
# ---------------------------------------------------------------------------

def test_invoke_ml_predictive_repair_returns_false_when_power_is_none():
    assert invoke_ml_predictive_repair(None, 80.0) is False


def test_invoke_ml_predictive_repair_returns_false_when_temp_is_none():
    assert invoke_ml_predictive_repair(130.0, None) is False


def test_invoke_ml_predictive_repair_returns_false_when_both_none():
    assert invoke_ml_predictive_repair(None, None) is False


def test_invoke_ml_predictive_repair_below_threshold_is_false():
    # power=100, temp=20, sensitivity=0.05 → load=101 < 140.5
    weights = MLWeights(threshold=140.5, sensitivity=0.05)
    assert invoke_ml_predictive_repair(100.0, 20.0, weights=weights) is False


def test_invoke_ml_predictive_repair_above_threshold_is_true():
    # power=140, temp=20, sensitivity=0.05 → load=141 > 140.5
    weights = MLWeights(threshold=140.5, sensitivity=0.05)
    assert invoke_ml_predictive_repair(140.0, 20.0, weights=weights) is True


def test_invoke_ml_predictive_repair_exact_threshold_boundary():
    # load == threshold → not strictly greater, so False
    weights = MLWeights(threshold=100.0, sensitivity=0.0)
    assert invoke_ml_predictive_repair(100.0, 50.0, weights=weights) is False


def test_invoke_ml_predictive_repair_custom_sensitivity():
    # power=50, temp=200, sensitivity=0.5 → load = 50 + 100 = 150 > 140.5
    weights = MLWeights(threshold=140.5, sensitivity=0.5)
    assert invoke_ml_predictive_repair(50.0, 200.0, weights=weights) is True


# ---------------------------------------------------------------------------
# detect_anomalies
# ---------------------------------------------------------------------------

def test_detect_anomalies_empty_list_returns_empty():
    results = detect_anomalies([])
    assert results == []


def test_detect_anomalies_nominal_gpu_no_anomaly():
    readings = [
        GPUReading(
            index="0",
            power_draw=100.0,
            temperature=60.0,
            fan_speed=50,
            model="RTX 3080",
        )
    ]
    result = detect_anomalies(readings)[0]
    assert result.anomaly_predicted is False
    assert result.reasons == []


def test_detect_anomalies_insufficient_telemetry_not_anomaly():
    """Missing power and temp → insufficient-telemetry but NOT a predicted anomaly."""
    readings = [
        GPUReading(index="0", power_draw=None, temperature=None, fan_speed=50)
    ]
    result = detect_anomalies(readings)[0]
    assert "insufficient-telemetry" in result.reasons
    assert result.anomaly_predicted is False


def test_detect_anomalies_missing_only_power_insufficient_telemetry():
    readings = [
        GPUReading(index="0", power_draw=None, temperature=70.0, fan_speed=50)
    ]
    result = detect_anomalies(readings)[0]
    assert "insufficient-telemetry" in result.reasons
    assert result.anomaly_predicted is False


def test_detect_anomalies_fan_zero_is_anomaly():
    """Fan speed of zero alone (with valid power/temp) is a predicted anomaly."""
    readings = [
        GPUReading(
            index="0",
            power_draw=100.0,
            temperature=60.0,
            fan_speed=0,
        )
    ]
    result = detect_anomalies(readings)[0]
    assert "fan-reported-zero" in result.reasons
    assert result.anomaly_predicted is True


def test_detect_anomalies_power_over_soft_limit():
    """power_draw > 141 adds power-over-soft-limit reason."""
    readings = [
        GPUReading(index="0", power_draw=142.0, temperature=60.0, fan_speed=50)
    ]
    result = detect_anomalies(readings)[0]
    assert "power-over-soft-limit" in result.reasons
    assert result.anomaly_predicted is True


def test_detect_anomalies_predictive_threshold_reason():
    """When load exceeds threshold the predictive-threshold reason is added."""
    weights = MLWeights(threshold=140.5, sensitivity=0.05)
    readings = [
        GPUReading(index="0", power_draw=140.0, temperature=20.0, fan_speed=50)
    ]
    result = detect_anomalies(readings, weights=weights)[0]
    assert "predictive-threshold" in result.reasons
    assert result.anomaly_predicted is True


def test_detect_anomalies_predictive_load_computed_correctly():
    weights = MLWeights(threshold=200.0, sensitivity=0.1)
    readings = [
        GPUReading(index="0", power_draw=100.0, temperature=80.0, fan_speed=50)
    ]
    result = detect_anomalies(readings, weights=weights)[0]
    # load = 100 + 0.1 * 80 = 108 < 200
    assert result.predictive_load is not None
    assert abs(result.predictive_load - 108.0) < 1e-9
    assert result.anomaly_predicted is False


def test_detect_anomalies_reading_echoed_in_result():
    reading = GPUReading(
        index="3", power_draw=120.0, temperature=65.0, fan_speed=60, model="A100"
    )
    result = detect_anomalies([reading])[0]
    assert result.reading is reading


def test_detect_anomalies_multiple_readings_each_evaluated():
    readings = [
        GPUReading(index="0", power_draw=100.0, temperature=50.0, fan_speed=40),
        GPUReading(index="1", power_draw=145.0, temperature=80.0, fan_speed=0),
    ]
    results = detect_anomalies(readings)
    assert len(results) == 2
    assert results[0].anomaly_predicted is False
    assert results[1].anomaly_predicted is True


def test_detect_anomalies_only_insufficient_telemetry_no_fan_zero():
    """fan_speed==0 with missing power/temp adds both reasons but anomaly_predicted is True."""
    readings = [
        GPUReading(index="0", power_draw=None, temperature=None, fan_speed=0)
    ]
    result = detect_anomalies(readings)[0]
    assert "fan-reported-zero" in result.reasons
    assert "insufficient-telemetry" in result.reasons
    # reasons list has two items; "fan-reported-zero" makes it an anomaly
    assert result.anomaly_predicted is True


def test_detect_anomalies_predictive_load_none_when_telemetry_missing():
    readings = [
        GPUReading(index="0", power_draw=None, temperature=70.0, fan_speed=50)
    ]
    result = detect_anomalies(readings)[0]
    assert result.predictive_load is None

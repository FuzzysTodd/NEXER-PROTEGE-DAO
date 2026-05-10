"""Focused tests for the safe Nexus telemetry monitor."""

from nexus.anomaly_detector import (
    GPUReading,
    MLWeights,
    TelemetrySnapshot,
    detect_anomalies,
    invoke_ml_predictive_repair,
)
from nexus.telemetry_monitor import (
    _parse_float,
    _parse_int,
    collect_gpu_telemetry,
    detect_pipe_status,
    parse_gpu_csv,
    render_dashboard,
)


def test_predictive_detector_flags_threshold_crossing():
    weights = MLWeights(threshold=140.5, sensitivity=0.05)

    assert invoke_ml_predictive_repair(140.0, 20.0, weights=weights)
    assert not invoke_ml_predictive_repair(100.0, 20.0, weights=weights)


def test_detect_anomalies_includes_power_and_fan_reasons():
    readings = [
        GPUReading(
            index="0",
            power_draw=145.0,
            temperature=70.0,
            fan_speed=0,
            model="5090 Ti",
        )
    ]

    result = detect_anomalies(readings)[0]

    assert result.anomaly_predicted is True
    assert "predictive-threshold" in result.reasons
    assert "power-over-soft-limit" in result.reasons
    assert "fan-reported-zero" in result.reasons


def test_parse_gpu_csv_handles_missing_or_malformed_values():
    readings = parse_gpu_csv(
        [
            "0, 139.5, 55, 44, NVIDIA GeForce RTX 5090",
            "1, [N/A], Not Supported, [N/A], NVIDIA GeForce RTX 5090 Ti",
            "bad,line",
        ]
    )

    assert readings[0].power_draw == 139.5
    assert readings[0].temperature == 55.0
    assert readings[1].power_draw is None
    assert readings[1].temperature is None
    assert readings[2].index == "unknown"


def test_collect_gpu_telemetry_falls_back_cleanly_when_command_missing():
    def failing_runner(_command):
        raise FileNotFoundError("nvidia-smi missing")

    snapshot = collect_gpu_telemetry(command_runner=failing_runner)

    assert snapshot.gpus == []
    assert snapshot.telemetry_source == "unavailable"
    assert snapshot.warnings


def test_render_dashboard_marks_nominal_and_warning_states():
    def stub_runner(command):
        if command[:1] == ["nvidia-smi"]:
            return "0, 120, 50, 40, NVIDIA GeForce RTX 5090"
        return "eth0    UP"

    snapshot = collect_gpu_telemetry(command_runner=stub_runner)
    output = render_dashboard(snapshot)

    assert "ML-ENHANCED BOT" in output
    assert "UUC: STABLE" in output
    assert "eth0" in output
    assert "Bit-Level Topology v20" in output


def test_render_dashboard_marks_predicted_anomalies_as_lock():
    output = render_dashboard(
        collect_gpu_telemetry(
            command_runner=lambda command: (
                "0, 145, 70, 0, NVIDIA GeForce RTX 5090 Ti"
                if command[:1] == ["nvidia-smi"]
                else "eth0    UP"
            )
        )
    )

    assert "UUC: LOCK" in output
    assert "predictive-threshold" in output


# ---------------------------------------------------------------------------
# _parse_float
# ---------------------------------------------------------------------------

def test_parse_float_plain_number():
    assert _parse_float("  139.5  ") == 139.5


def test_parse_float_strips_watt_suffix():
    assert _parse_float("120.0W") == 120.0


def test_parse_float_strips_celsius_suffix():
    assert _parse_float("75C") == 75.0


def test_parse_float_returns_none_for_na():
    assert _parse_float("[N/A]") is None
    assert _parse_float("N/A") is None
    assert _parse_float("Not Supported") is None


def test_parse_float_returns_none_for_empty_string():
    assert _parse_float("") is None
    assert _parse_float("   ") is None


def test_parse_float_returns_none_for_non_numeric():
    assert _parse_float("abc") is None


# ---------------------------------------------------------------------------
# _parse_int
# ---------------------------------------------------------------------------

def test_parse_int_rounds_float_down():
    assert _parse_int("  44.2  ") == 44


def test_parse_int_rounds_float_up():
    assert _parse_int("44.9") == 45


def test_parse_int_returns_none_for_na():
    assert _parse_int("[N/A]") is None


# ---------------------------------------------------------------------------
# parse_gpu_csv — additional edge cases
# ---------------------------------------------------------------------------

def test_parse_gpu_csv_empty_input_returns_empty():
    assert parse_gpu_csv([]) == []


def test_parse_gpu_csv_blank_lines_are_skipped():
    readings = parse_gpu_csv(["", "   ", "\n"])
    assert readings == []


def test_parse_gpu_csv_five_column_row_extracts_model():
    readings = parse_gpu_csv(
        ["0, 130.0, 65, 50, NVIDIA GeForce RTX 4090"]
    )
    assert len(readings) == 1
    assert readings[0].model == "NVIDIA GeForce RTX 4090"
    assert readings[0].power_draw == 130.0


def test_parse_gpu_csv_four_column_row_model_unknown():
    readings = parse_gpu_csv(["0, 130.0, 65, 50"])
    assert readings[0].model == "Unknown"


# ---------------------------------------------------------------------------
# detect_pipe_status
# ---------------------------------------------------------------------------

def test_detect_pipe_status_uses_ip_command_output():
    def stub_runner(command):
        if command[:2] == ["ip", "-br"]:
            return "eth0   UP   192.168.1.1/24\nlo     UNKNOWN\n"
        raise OSError("unexpected command")

    status = detect_pipe_status(command_runner=stub_runner)
    assert "eth0" in status


def test_detect_pipe_status_falls_back_when_ip_fails():
    def failing_runner(_command):
        raise OSError("ip not available")

    # Just verify it returns a non-empty string (socket fallback)
    status = detect_pipe_status(command_runner=failing_runner)
    assert isinstance(status, str)


# ---------------------------------------------------------------------------
# render_dashboard — no GPUs case
# ---------------------------------------------------------------------------

def test_render_dashboard_no_gpus_shows_no_telemetry_message():
    snap = TelemetrySnapshot(
        gpus=[],
        pipe_status="eth0",
        telemetry_source="unavailable",
        warnings=["nvidia-smi not found"],
    )
    output = render_dashboard(snap)
    assert "No GPU telemetry available" in output
    assert "[WARN] nvidia-smi not found" in output

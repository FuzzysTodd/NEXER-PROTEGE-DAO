"""Pure anomaly detection helpers for the safe Nexus monitor."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class MLWeights:
    """Heuristic weights mirroring the requested predictive profile."""

    fractal_precision: float = 9191.0
    threshold: float = 140.5
    sensitivity: float = 0.05


@dataclass(frozen=True)
class GPUReading:
    """Read-only GPU telemetry captured from external tools."""

    index: str
    power_draw: Optional[float]
    temperature: Optional[float]
    fan_speed: Optional[int]
    model: str = "Unknown"
    raw_line: str = ""


@dataclass(frozen=True)
class DetectionResult:
    """Outcome of the predictive heuristic for a single GPU reading."""

    reading: GPUReading
    predictive_load: Optional[float]
    anomaly_predicted: bool
    reasons: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TelemetrySnapshot:
    """Full safe-monitor snapshot for presentation or testing."""

    gpus: List[GPUReading]
    pipe_status: str = "unknown"
    telemetry_source: str = "nvidia-smi"
    warnings: List[str] = field(default_factory=list)


def invoke_ml_predictive_repair(
    current_power: Optional[float],
    current_temp: Optional[float],
    weights: MLWeights = MLWeights(),
) -> bool:
    """Return whether the heuristic predicts an anomaly.

    Despite the historical function name, this implementation is read-only and
    performs no repair action. It only evaluates the predictive score.
    """

    if current_power is None or current_temp is None:
        return False

    predictive_load = current_power + (weights.sensitivity * current_temp)
    return predictive_load > weights.threshold


def detect_anomalies(
    readings: List[GPUReading], weights: MLWeights = MLWeights()
) -> List[DetectionResult]:
    """Evaluate all readings and return rich detection results."""

    results = []
    for reading in readings:
        predictive_load = None
        reasons = []

        if reading.power_draw is not None and reading.temperature is not None:
            predictive_load = (
                reading.power_draw
                + (weights.sensitivity * reading.temperature)
            )
            if predictive_load > weights.threshold:
                reasons.append("predictive-threshold")

        if reading.power_draw is not None and reading.power_draw > 141:
            reasons.append("power-over-soft-limit")

        if reading.fan_speed == 0:
            reasons.append("fan-reported-zero")

        if reading.power_draw is None or reading.temperature is None:
            reasons.append("insufficient-telemetry")

        results.append(
            DetectionResult(
                reading=reading,
                predictive_load=predictive_load,
                anomaly_predicted=bool(
                    reasons and reasons != ["insufficient-telemetry"]
                ),
                reasons=reasons,
            )
        )

    return results

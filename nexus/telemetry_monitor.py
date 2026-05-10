"""Read-only Nexus telemetry monitor with defensive parsing and CLI output."""

from __future__ import annotations

import argparse
import csv
import io
import socket
import subprocess
import time
from typing import Callable, Iterable, List, Optional

from .anomaly_detector import (
    GPUReading,
    MLWeights,
    TelemetrySnapshot,
    detect_anomalies,
)

CommandRunner = Callable[[List[str]], str]

GPU_QUERY = (
    "--query-gpu=index,power.draw,temperature.gpu,fan.speed,name "
    "--format=csv,noheader,nounits"
)


def _run_command(command: List[str]) -> str:
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _parse_float(value: str) -> Optional[float]:
    cleaned = value.strip().replace("W", "").replace("C", "")
    if not cleaned or cleaned in {"[N/A]", "N/A", "Not Supported"}:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_int(value: str) -> Optional[int]:
    number = _parse_float(value)
    if number is None:
        return None
    return int(round(number))


def parse_gpu_csv(lines: Iterable[str]) -> List[GPUReading]:
    """Parse read-only `nvidia-smi` CSV output into normalized readings."""

    readings = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        row = next(csv.reader(io.StringIO(line), skipinitialspace=True))
        if len(row) < 4:
            readings.append(
                GPUReading(
                    index="unknown",
                    power_draw=None,
                    temperature=None,
                    fan_speed=None,
                    raw_line=line,
                )
            )
            continue

        index = row[0].strip()
        model = (
            row[4].strip() if len(row) > 4 and row[4].strip() else "Unknown"
        )
        readings.append(
            GPUReading(
                index=index,
                power_draw=_parse_float(row[1]),
                temperature=_parse_float(row[2]),
                fan_speed=_parse_int(row[3]),
                model=model,
                raw_line=line,
            )
        )

    return readings


def collect_gpu_telemetry(
    command_runner: CommandRunner = _run_command,
) -> TelemetrySnapshot:
    """Collect telemetry without mutating system state."""

    warnings = []
    source = "nvidia-smi"
    try:
        output = command_runner(["nvidia-smi", *GPU_QUERY.split()])
        readings = parse_gpu_csv(output.splitlines())
        if not readings:
            warnings.append(
                "No GPU telemetry lines were returned by nvidia-smi."
            )
    except (OSError, subprocess.SubprocessError) as exc:
        readings = []
        source = "unavailable"
        warnings.append(f"GPU telemetry unavailable: {exc}")

    return TelemetrySnapshot(
        gpus=readings,
        pipe_status=detect_pipe_status(command_runner=command_runner),
        telemetry_source=source,
        warnings=warnings,
    )


def detect_pipe_status(
    command_runner: CommandRunner = _run_command,
) -> str:
    """Summarize active network links in a cross-platform, read-only way."""

    try:
        output = command_runner(["ip", "-br", "link", "show", "up"])
        interfaces = []
        for line in output.splitlines():
            parts = line.split()
            if parts:
                interfaces.append(parts[0])
        if interfaces:
            return ", ".join(interfaces)
    except (OSError, subprocess.SubprocessError):
        pass

    try:
        interfaces = [
            name for _, name in socket.if_nameindex() if name != "lo"
        ]
        if interfaces:
            return ", ".join(sorted(interfaces))
    except OSError:
        pass

    return "unknown"


def render_dashboard(
    snapshot: TelemetrySnapshot,
    weights: MLWeights = MLWeights(),
) -> str:
    """Render a safe dashboard that recommends action but never enforces it."""

    lines = [
        "[NEXUS SOVEREIGN: ML-ENHANCED BOT]",
        "BOT: @FuzzysTodd | ML-PRECISION: "
        f"{weights.fractal_precision:.0f}th Fractal",
        "---------------- BAREBONE TRUTH ----------------",
    ]

    if not snapshot.gpus:
        lines.append("[GPU] No GPU telemetry available")

    for result in detect_anomalies(snapshot.gpus, weights=weights):
        reading = result.reading
        model = (
            reading.model
            if reading.model != "Unknown"
            else f"GPU {reading.index}"
        )
        power_text = (
            "?" if reading.power_draw is None else f"{reading.power_draw:.1f}"
        )
        temp_text = (
            "?"
            if reading.temperature is None
            else f"{reading.temperature:.1f}"
        )
        fan_text = "?" if reading.fan_speed is None else str(reading.fan_speed)
        status = "LOCK" if result.anomaly_predicted else "STABLE"
        reasons = ", ".join(result.reasons) if result.reasons else "nominal"
        lines.append(
            f"[{model}] {power_text} W | {temp_text} °C | Fan: {fan_text}%"
            f" | UUC: {status} | Reasons: {reasons}"
        )

    lines.append(
        "[PIPE] Status: "
        f"{snapshot.pipe_status} | [ML] Status: PREDICTIVE-READONLY"
    )
    lines.append(f"[SOURCE] GPU telemetry: {snapshot.telemetry_source}")
    lines.append("[MAP] Mapping Depth: Bit-Level Topology v20")
    for warning in snapshot.warnings:
        lines.append(f"[WARN] {warning}")
    lines.append("------------------------------------------------")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point for safe monitor execution."""

    parser = argparse.ArgumentParser(
        description="Safe read-only Nexus telemetry monitor"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of snapshots to capture before exiting.",
    )
    parser.add_argument(
        "--sleep-ms",
        type=int,
        default=50,
        help="Delay between snapshots in milliseconds.",
    )
    parser.add_argument(
        "--mock-csv",
        default="",
        help="Optional semicolon-separated GPU CSV lines for dry-run demos.",
    )
    args = parser.parse_args(argv)

    mock_lines = [
        part.strip() for part in args.mock_csv.split(";") if part.strip()
    ]

    def runner(command: List[str]) -> str:
        if args.mock_csv and command[:1] == ["nvidia-smi"]:
            return "\n".join(mock_lines)
        return _run_command(command)

    for iteration in range(max(args.iterations, 1)):
        snapshot = collect_gpu_telemetry(command_runner=runner)
        print(render_dashboard(snapshot))
        if iteration < args.iterations - 1:
            time.sleep(max(args.sleep_ms, 0) / 1000)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

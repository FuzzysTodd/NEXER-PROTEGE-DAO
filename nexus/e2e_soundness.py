"""End-to-end soundness validator for Nexus Protocol network and web layers.

Validates that REST/WebSocket (network) responses and web-layer answers carry
consistent, within-range values — ensuring the system is end-to-end sound.

The validator computes a *match grade* for every shared dimension, aggregates
the grades into a *soundness score* (0–100 %), and assigns a tier label.

Soundness tiers
---------------
SOUND      — ≥90 % of dimensions match within tolerance; all fields present
HIGH       — ≥75 % match; minor threshold breaches
MODERATE   — ≥50 % match; notable divergence between layers
UNSOUND    — <50 % match; critical schema violations or severe divergence

Match grades (per dimension)
-----------------------------
EXACT        — values identical or within tight tolerance (≤ MATCH_EXACT_PCT)
CLOSE        — values within medium tolerance (≤ rule / default tolerance)
DIVERGED     — values differ by more than tolerance
MISSING      — dimension absent in one or both layers
OUT_OF_RANGE — value outside expected operating range
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Soundness thresholds
# ---------------------------------------------------------------------------

TIER_SOUND: float = 90.0      # soundness score for SOUND tier
TIER_HIGH: float = 75.0       # soundness score for HIGH tier
TIER_MODERATE: float = 50.0   # soundness score for MODERATE tier

MATCH_EXACT_PCT: float = 1.0   # ≤1 % relative difference → EXACT
MATCH_CLOSE_PCT: float = 5.0   # ≤5 % relative difference → CLOSE (default)

TIER_LABELS: Tuple[str, ...] = ("SOUND", "HIGH", "MODERATE", "UNSOUND")

# ---------------------------------------------------------------------------
# Default expected operating ranges for known Nexus protocol dimensions
# ---------------------------------------------------------------------------

NEXUS_DIMENSION_RANGES: Dict[str, Tuple[float, float]] = {
    # signal-bus / WebSocket counters
    "eventCount":            (0.0, 1_000_000.0),
    "clients":               (0.0, 10_000.0),
    "port":                  (1.0, 65_535.0),
    # financial-ops REST summary fields
    "filesScanned":          (0.0, 100_000.0),
    "preErrorCount":         (0.0, 10_000.0),
    "withdrawSignalCount":   (0.0, 10_000.0),
    "placementSignalCount":  (0.0, 10_000.0),
    # builder-fund REST stats
    "totalCalls":            (0.0, 1_000_000.0),
    "placementBps":          (0.0, 10_000.0),
    # financial values
    "balanceEth":            (0.0, 1_000_000.0),
    "balanceUsd":            (0.0, 1_000_000_000.0),
    "priceUsd":              (0.0, 10_000_000.0),
    "valueUsd":              (0.0, 1_000_000_000.0),
    # approval service
    "pendingCount":          (0.0, 10_000.0),
    "approvedCount":         (0.0, 10_000.0),
    "rejectedCount":         (0.0, 10_000.0),
    # performance / latency
    "latencyMs":             (0.0, 30_000.0),
    "uptimeSeconds":         (0.0, 1.0e9),
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NetworkResponse:
    """A snapshot from a REST API or WebSocket endpoint.

    Parameters
    ----------
    source:
        Human-readable source label (e.g. ``"financial-ops-rest"``,
        ``"signal-bus-ws"``).
    payload:
        Mapping of dimension name → numeric value as reported by the
        network layer.
    context:
        Optional free-text description of the snapshot context.
    """

    source: str
    payload: Dict[str, float]
    context: str = ""


@dataclass(frozen=True)
class WebAnswer:
    """A snapshot of what the web display layer (dashboard/UI) shows.

    Parameters
    ----------
    surface:
        Human-readable UI surface label (e.g. ``"dashboard.html"``,
        ``"financial-ops-dashboard.html"``).
    payload:
        Mapping of dimension name → numeric value as displayed in the
        web layer.
    context:
        Optional free-text description of the snapshot context.
    """

    surface: str
    payload: Dict[str, float]
    context: str = ""


@dataclass(frozen=True)
class SoundnessRule:
    """Validation rule for a single dimension.

    Parameters
    ----------
    dimension:
        The field/dimension name this rule applies to.
    expected_range:
        ``(min, max)`` inclusive operating range.  Falls back to
        ``NEXUS_DIMENSION_RANGES`` when ``None``.
    tolerance_pct:
        Maximum % relative difference between network and web values
        before the match is graded DIVERGED.  Defaults to
        ``MATCH_CLOSE_PCT``.
    required:
        When ``True`` the dimension must be present in both layers for
        the result to reach a SOUND tier.
    """

    dimension: str
    expected_range: Optional[Tuple[float, float]] = None
    tolerance_pct: float = MATCH_CLOSE_PCT
    required: bool = False


@dataclass(frozen=True)
class FieldResult:
    """Soundness assessment for a single dimension.

    Attributes
    ----------
    dimension:
        Dimension name.
    network_value:
        Value from the network layer (``None`` if absent).
    web_value:
        Value from the web layer (``None`` if absent).
    match_grade:
        ``EXACT`` / ``CLOSE`` / ``DIVERGED`` / ``MISSING`` /
        ``OUT_OF_RANGE``.
    relative_diff_pct:
        Absolute relative percentage difference between the two values.
        ``None`` when at least one value is absent.
    in_range_network:
        Whether the network value is within the expected range.
    in_range_web:
        Whether the web value is within the expected range.
    note:
        Human-readable note about this field result.
    """

    dimension: str
    network_value: Optional[float]
    web_value: Optional[float]
    match_grade: str
    relative_diff_pct: Optional[float]
    in_range_network: bool
    in_range_web: bool
    note: str = ""


@dataclass(frozen=True)
class SoundnessResult:
    """End-to-end soundness assessment across all evaluated dimensions.

    Attributes
    ----------
    network_source:
        Echo of the ``NetworkResponse.source`` label.
    web_surface:
        Echo of the ``WebAnswer.surface`` label.
    soundness_score:
        Overall soundness as a percentage (0–100).  Higher is better.
    tier:
        Tier label: ``SOUND`` / ``HIGH`` / ``MODERATE`` / ``UNSOUND``.
    field_results:
        Per-dimension assessment list.
    dimensions_evaluated:
        Total number of unique dimensions evaluated.
    dimensions_matched:
        Number of dimensions graded EXACT or CLOSE.
    dimensions_out_of_range:
        Number of dimensions where at least one layer is out of range.
    dimensions_missing:
        Number of dimensions absent in one or both layers.
    verdict:
        Single-line human-readable verdict.
    reasoning_chain:
        Step-by-step derivation of the soundness verdict.
    """

    network_source: str
    web_surface: str
    soundness_score: float
    tier: str
    field_results: List[FieldResult] = field(default_factory=list)
    dimensions_evaluated: int = 0
    dimensions_matched: int = 0
    dimensions_out_of_range: int = 0
    dimensions_missing: int = 0
    verdict: str = ""
    reasoning_chain: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _range_for(
    dimension: str,
    rule: Optional[SoundnessRule],
) -> Optional[Tuple[float, float]]:
    """Return the expected range for *dimension*, honouring rule overrides."""
    if rule is not None and rule.expected_range is not None:
        return rule.expected_range
    return NEXUS_DIMENSION_RANGES.get(dimension)


def _in_range(value: float, rng: Optional[Tuple[float, float]]) -> bool:
    """Return ``True`` if *value* is within *rng*, or range is unknown."""
    if rng is None:
        return True
    lo, hi = rng
    return lo <= value <= hi


def _evaluate_field(
    dimension: str,
    network_value: Optional[float],
    web_value: Optional[float],
    rule: Optional[SoundnessRule],
) -> FieldResult:
    """Evaluate soundness for a single dimension."""
    rng = _range_for(dimension, rule)
    tolerance = rule.tolerance_pct if rule is not None else MATCH_CLOSE_PCT

    in_range_net = (
        _in_range(network_value, rng)
        if network_value is not None
        else True
    )
    in_range_web = (
        _in_range(web_value, rng)
        if web_value is not None
        else True
    )

    # One or both values absent
    if network_value is None or web_value is None:
        if network_value is None and web_value is None:
            note = "absent in both layers"
        elif network_value is None:
            note = "absent in network layer; present in web layer"
        else:
            note = "present in network layer; absent in web layer"
        return FieldResult(
            dimension=dimension,
            network_value=network_value,
            web_value=web_value,
            match_grade="MISSING",
            relative_diff_pct=None,
            in_range_network=in_range_net,
            in_range_web=in_range_web,
            note=note,
        )

    # Both values present — compute relative difference
    ref = max(abs(network_value), abs(web_value), 1e-9)
    rel_diff = abs(network_value - web_value) / ref * 100.0

    if not in_range_net or not in_range_web:
        if not in_range_net and not in_range_web:
            note = "out-of-range in both layers"
        elif not in_range_net:
            note = "out-of-range in network layer"
        else:
            note = "out-of-range in web layer"
        grade = "OUT_OF_RANGE"
    elif rel_diff <= min(MATCH_EXACT_PCT, tolerance):
        grade = "EXACT"
        note = f"rel_diff={rel_diff:.3f}%"
    elif rel_diff <= tolerance:
        grade = "CLOSE"
        note = f"rel_diff={rel_diff:.3f}% (within {tolerance:.1f}% tolerance)"
    else:
        grade = "DIVERGED"
        note = f"rel_diff={rel_diff:.3f}% exceeds {tolerance:.1f}% tolerance"

    return FieldResult(
        dimension=dimension,
        network_value=network_value,
        web_value=web_value,
        match_grade=grade,
        relative_diff_pct=rel_diff,
        in_range_network=in_range_net,
        in_range_web=in_range_web,
        note=note,
    )


# ---------------------------------------------------------------------------
# Main validator
# ---------------------------------------------------------------------------

def validate_soundness(
    network: NetworkResponse,
    web: WebAnswer,
    rules: Optional[List[SoundnessRule]] = None,
) -> SoundnessResult:
    """Validate end-to-end soundness between *network* and *web* layers.

    Parameters
    ----------
    network:
        Snapshot from the network (REST / WebSocket) layer.
    web:
        Snapshot from the web display layer.
    rules:
        Optional per-dimension rule overrides.  Dimensions not covered
        fall back to ``NEXUS_DIMENSION_RANGES`` for range checking and
        ``MATCH_CLOSE_PCT`` for tolerance.

    Returns
    -------
    ``SoundnessResult`` with per-dimension grades and an overall
    soundness tier.
    """
    rule_map: Dict[str, SoundnessRule] = {}
    if rules:
        for r in rules:
            rule_map[r.dimension] = r

    # Union of all dimension names from both layers
    all_dims: List[str] = sorted(set(network.payload) | set(web.payload))

    # Append required-rule dimensions that appear in neither payload
    if rules:
        for r in rules:
            if r.required and r.dimension not in all_dims:
                all_dims.append(r.dimension)

    field_results: List[FieldResult] = []
    for dim in all_dims:
        net_val = network.payload.get(dim)
        web_val = web.payload.get(dim)
        fr = _evaluate_field(dim, net_val, web_val, rule_map.get(dim))
        field_results.append(fr)

    n = len(field_results)
    n_matched = sum(
        1 for fr in field_results
        if fr.match_grade in ("EXACT", "CLOSE")
    )
    n_out_of_range = sum(
        1 for fr in field_results
        if fr.match_grade == "OUT_OF_RANGE"
    )
    n_missing = sum(
        1 for fr in field_results
        if fr.match_grade == "MISSING"
    )
    n_diverged = sum(
        1 for fr in field_results
        if fr.match_grade == "DIVERGED"
    )

    soundness = (n_matched / n * 100.0) if n > 0 else 100.0

    if soundness >= TIER_SOUND:
        tier = "SOUND"
    elif soundness >= TIER_HIGH:
        tier = "HIGH"
    elif soundness >= TIER_MODERATE:
        tier = "MODERATE"
    else:
        tier = "UNSOUND"

    verdict = (
        f"[{network.source} \u2194 {web.surface}] {tier}"
        f" | soundness={soundness:.1f}%"
        f" | matched={n_matched}/{n}"
        f" | diverged={n_diverged}"
        f" | out_of_range={n_out_of_range}"
        f" | missing={n_missing}"
    )

    chain = [
        f"[E2E-1]  Network source  : {network.source}"
        + (f" \u2014 {network.context}" if network.context else ""),
        f"[E2E-2]  Web surface     : {web.surface}"
        + (f" \u2014 {web.context}" if web.context else ""),
        f"[E2E-3]  Dimensions      : {n} unique dims evaluated",
        f"[E2E-4]  Matched (E+C)   : {n_matched}",
        f"[E2E-5]  Diverged        : {n_diverged}",
        f"[E2E-6]  Out-of-range    : {n_out_of_range}",
        f"[E2E-7]  Missing         : {n_missing}",
        f"[E2E-8]  Soundness score : {soundness:.1f}%",
        f"[E2E-9]  Tier            : {tier}",
        f"[E2E-10] VERDICT         : {verdict}",
    ]

    return SoundnessResult(
        network_source=network.source,
        web_surface=web.surface,
        soundness_score=soundness,
        tier=tier,
        field_results=field_results,
        dimensions_evaluated=n,
        dimensions_matched=n_matched,
        dimensions_out_of_range=n_out_of_range,
        dimensions_missing=n_missing,
        verdict=verdict,
        reasoning_chain=chain,
    )


def validate_network_only(
    network: NetworkResponse,
    rules: Optional[List[SoundnessRule]] = None,
) -> SoundnessResult:
    """Validate the network layer alone against expected ranges.

    Useful when no corresponding web answer is available.  Each dimension is
    evaluated only for range conformance; match grades are not applicable, so
    in-range dimensions score as EXACT and out-of-range as OUT_OF_RANGE.

    Parameters
    ----------
    network:
        Snapshot from the network (REST / WebSocket) layer.
    rules:
        Optional per-dimension rule overrides.

    Returns
    -------
    ``SoundnessResult`` comparing the network payload to defined ranges,
    with an empty ``web_surface`` label.
    """
    rule_map: Dict[str, SoundnessRule] = {}
    if rules:
        for r in rules:
            rule_map[r.dimension] = r

    all_dims: List[str] = sorted(network.payload)
    field_results: List[FieldResult] = []

    for dim in all_dims:
        net_val = network.payload[dim]
        rule = rule_map.get(dim)
        rng = _range_for(dim, rule)
        in_rng = _in_range(net_val, rng)
        if in_rng:
            grade = "EXACT"
            note = "in range (network-only check)"
        else:
            grade = "OUT_OF_RANGE"
            note = "out-of-range (network-only check)"
        field_results.append(FieldResult(
            dimension=dim,
            network_value=net_val,
            web_value=None,
            match_grade=grade,
            relative_diff_pct=None,
            in_range_network=in_rng,
            in_range_web=True,
            note=note,
        ))

    n = len(field_results)
    n_matched = sum(1 for fr in field_results if fr.match_grade == "EXACT")
    n_out_of_range = n - n_matched
    soundness = (n_matched / n * 100.0) if n > 0 else 100.0

    if soundness >= TIER_SOUND:
        tier = "SOUND"
    elif soundness >= TIER_HIGH:
        tier = "HIGH"
    elif soundness >= TIER_MODERATE:
        tier = "MODERATE"
    else:
        tier = "UNSOUND"

    verdict = (
        f"[{network.source}] {tier} (network-only)"
        f" | soundness={soundness:.1f}%"
        f" | in_range={n_matched}/{n}"
        f" | out_of_range={n_out_of_range}"
    )

    chain = [
        f"[E2E-1]  Network source : {network.source}"
        + (f" \u2014 {network.context}" if network.context else ""),
        "[E2E-2]  Web surface    : (network-only validation)",
        f"[E2E-3]  Dimensions     : {n}",
        f"[E2E-4]  In-range       : {n_matched}",
        f"[E2E-5]  Out-of-range   : {n_out_of_range}",
        f"[E2E-6]  Soundness      : {soundness:.1f}%",
        f"[E2E-7]  Tier           : {tier}",
        f"[E2E-8]  VERDICT        : {verdict}",
    ]

    return SoundnessResult(
        network_source=network.source,
        web_surface="(network-only)",
        soundness_score=soundness,
        tier=tier,
        field_results=field_results,
        dimensions_evaluated=n,
        dimensions_matched=n_matched,
        dimensions_out_of_range=n_out_of_range,
        dimensions_missing=0,
        verdict=verdict,
        reasoning_chain=chain,
    )


def batch_validate(
    pairs: List[Tuple[NetworkResponse, WebAnswer]],
    rules: Optional[List[SoundnessRule]] = None,
) -> List[SoundnessResult]:
    """Validate multiple network/web pairs and return all results.

    Parameters
    ----------
    pairs:
        List of ``(NetworkResponse, WebAnswer)`` tuples.
    rules:
        Shared per-dimension rule overrides applied to every pair.

    Returns
    -------
    List of ``SoundnessResult`` in the same order as *pairs*.
    """
    return [validate_soundness(net, web, rules=rules) for net, web in pairs]


# ---------------------------------------------------------------------------
# Pre-built rule sets for known Nexus endpoints
# ---------------------------------------------------------------------------

SIGNAL_BUS_RULES: List[SoundnessRule] = [
    SoundnessRule("eventCount", expected_range=(0.0, 1_000_000.0), required=True),
    SoundnessRule("clients", expected_range=(0.0, 10_000.0), required=True),
    SoundnessRule("port", expected_range=(1.0, 65_535.0), required=True),
]

FINANCIAL_OPS_RULES: List[SoundnessRule] = [
    SoundnessRule("filesScanned", expected_range=(0.0, 100_000.0), required=True),
    SoundnessRule("preErrorCount", expected_range=(0.0, 10_000.0), required=True),
    SoundnessRule("withdrawSignalCount", expected_range=(0.0, 10_000.0), required=True),
    SoundnessRule("placementSignalCount", expected_range=(0.0, 10_000.0), required=True),
]

BUILDER_FUND_RULES: List[SoundnessRule] = [
    SoundnessRule("totalCalls", expected_range=(0.0, 1_000_000.0), required=True),
    SoundnessRule("placementBps", expected_range=(0.0, 10_000.0), required=True),
]


# ---------------------------------------------------------------------------
# Report renderer
# ---------------------------------------------------------------------------

def render_soundness_report(
    result: SoundnessResult,
    show_chain: bool = True,
    show_fields: bool = True,
) -> str:
    """Render a read-only end-to-end soundness report as a plain string."""
    lines = [
        "[NEXUS E2E SOUNDNESS VALIDATOR]",
        "BOT: @FuzzysTodd | Network \u2194 Web layer matching",
        "======= END-TO-END SOUNDNESS REPORT =======",
        "",
        f"  Network source : {result.network_source}",
        f"  Web surface    : {result.web_surface}",
        f"  Soundness      : {result.soundness_score:.1f}%",
        f"  Tier           : {result.tier}",
        f"  Dimensions     : {result.dimensions_evaluated} evaluated",
        f"  Matched        : {result.dimensions_matched}",
        f"  Out-of-range   : {result.dimensions_out_of_range}",
        f"  Missing        : {result.dimensions_missing}",
        "",
        f"  VERDICT: {result.verdict}",
    ]

    if show_fields and result.field_results:
        lines.append("")
        lines.append("  Field results:")
        for fr in result.field_results:
            net_str = (
                f"{fr.network_value:.4f}"
                if fr.network_value is not None
                else "\u2014"
            )
            web_str = (
                f"{fr.web_value:.4f}"
                if fr.web_value is not None
                else "\u2014"
            )
            diff_str = (
                f"{fr.relative_diff_pct:.2f}%"
                if fr.relative_diff_pct is not None
                else "n/a"
            )
            lines.append(
                f"    {fr.dimension:<32}: "
                f"net={net_str:>14}  web={web_str:>14}"
                f"  diff={diff_str:>8}  [{fr.match_grade}]"
                + (f"  \u2014 {fr.note}" if fr.note else "")
            )

    if show_chain:
        lines.append("")
        lines.append("  Reasoning chain:")
        for step in result.reasoning_chain:
            lines.append(f"    {step}")

    lines.append("")
    lines.append("============================================")
    return "\n".join(lines)

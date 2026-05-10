"""MonsterBall stats and universal weighted predictor for the Nexus Protocol.

The same heuristic-weight strategy from anomaly_detector is generalized here:
any named numeric stat can be fed through configurable PredictorWeights to
score and predict outcomes across domains — MonsterBall, GPU telemetry, token
activity, or any arbitrary stat surface.  The predictor is strictly read-only
and never modifies game state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Universal predictor core
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PredictorWeights:
    """Configurable weights for the universal predictor.

    Each weight multiplies its matching stat key before summing into the
    overall score.  Keys not present in a reading are silently skipped.
    A ``threshold`` splits predictions into two labelled outcome buckets.
    """

    weights: Dict[str, float] = field(default_factory=dict)
    threshold: float = 100.0
    label_above: str = "DOMINANT"
    label_below: str = "SUBDUED"


@dataclass(frozen=True)
class PredictionResult:
    """Outcome of the universal predictor for a single stat reading."""

    label: str
    score: float
    reasons: List[str] = field(default_factory=list)
    prediction_text: str = ""


def predict(
    stats: Dict[str, float],
    weights: PredictorWeights = PredictorWeights(),
) -> PredictionResult:
    """Universal weighted predictor — knows anything given the right weights.

    Parameters
    ----------
    stats:
        Mapping of stat name → numeric value.  Keys absent from
        ``weights.weights`` are ignored; weight keys absent from stats
        are skipped.
    weights:
        ``PredictorWeights`` that define per-key multipliers and the
        decision threshold.

    Returns
    -------
    PredictionResult with score, outcome label, and contributing reasons.
    """

    score = 0.0
    reasons: List[str] = []

    for key, w in weights.weights.items():
        value = stats.get(key)
        if value is None:
            continue
        contribution = value * w
        score += contribution
        if contribution > weights.threshold * 0.25:
            reasons.append(f"{key}={value:.1f}x{w:.1f}")

    label = (
        weights.label_above
        if score >= weights.threshold
        else weights.label_below
    )
    threshold_op = ">=" if score >= weights.threshold else "<"
    prediction_text = (
        f"Score {score:.1f} {threshold_op} "
        f"threshold {weights.threshold:.1f} -> {label}"
    )

    return PredictionResult(
        label=label,
        score=score,
        reasons=reasons,
        prediction_text=prediction_text,
    )


# ---------------------------------------------------------------------------
# MonsterBall domain model
# ---------------------------------------------------------------------------

MONSTERBALL_WEIGHTS = PredictorWeights(
    weights={
        "speed": 1.2,
        "power": 1.5,
        "offense": 1.8,
        "defense": 1.3,
        "stamina": 1.0,
        "aggression": 0.9,
        "skill": 2.0,
    },
    threshold=120.0,
    label_above="DOMINANT",
    label_below="SUBDUED",
)


@dataclass(frozen=True)
class PlayerStats:
    """Read-only snapshot of a MonsterBall player's stat profile."""

    name: str
    speed: float = 0.0
    power: float = 0.0
    offense: float = 0.0
    defense: float = 0.0
    stamina: float = 0.0
    aggression: float = 0.0
    skill: float = 0.0
    games_played: int = 0
    goals: int = 0
    assists: int = 0
    raw_rating: Optional[float] = None

    def to_stat_dict(self) -> Dict[str, float]:
        """Return a dict of the numeric combat stats used by the predictor."""

        return {
            "speed": self.speed,
            "power": self.power,
            "offense": self.offense,
            "defense": self.defense,
            "stamina": self.stamina,
            "aggression": self.aggression,
            "skill": self.skill,
        }


@dataclass(frozen=True)
class MatchSnapshot:
    """Aggregated MonsterBall match context for a single round."""

    players: List[PlayerStats]
    match_id: str = "unknown"
    round_number: int = 1
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# MonsterBall prediction helpers
# ---------------------------------------------------------------------------

def predict_player(
    player: PlayerStats,
    weights: PredictorWeights = MONSTERBALL_WEIGHTS,
) -> PredictionResult:
    """Predict a MonsterBall player's performance from their stat snapshot."""

    return predict(player.to_stat_dict(), weights=weights)


def rank_players(
    players: List[PlayerStats],
    weights: PredictorWeights = MONSTERBALL_WEIGHTS,
) -> List[Tuple[PlayerStats, PredictionResult]]:
    """Rank all players by predicted score, highest first (read-only)."""

    results = [(p, predict_player(p, weights=weights)) for p in players]
    return sorted(results, key=lambda x: x[1].score, reverse=True)


def render_match_report(
    snapshot: MatchSnapshot,
    weights: PredictorWeights = MONSTERBALL_WEIGHTS,
) -> str:
    """Render a safe read-only match performance report."""

    lines = [
        "[MONSTERBALL NEXUS PREDICTOR]",
        f"BOT: @FuzzysTodd | Match: {snapshot.match_id}"
        f" | Round: {snapshot.round_number}",
        "---------------- PLAYER PREDICTIONS ----------------",
    ]

    if not snapshot.players:
        lines.append("[PLAYERS] No player data available")
    else:
        ranked = rank_players(snapshot.players, weights=weights)
        for rank, (player, result) in enumerate(ranked, start=1):
            lines.append(
                f"[#{rank} {player.name}]"
                f" Score: {result.score:.1f}"
                f" | {result.label}"
                f" | GP: {player.games_played}"
                f" | G: {player.goals} A: {player.assists}"
                f" | {result.prediction_text}"
            )

    for warning in snapshot.warnings:
        lines.append(f"[WARN] {warning}")

    lines.append("------------------------------------------------")
    return "\n".join(lines)

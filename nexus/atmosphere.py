"""Subatomic particle harmony module for planetary and solar health.

Models every major Standard Model particle class and tracks how their
collective behaviour maintains Earth's atmosphere and the Sol system at
peak performance.  The same 3-Algebra + Super Logical strategy used across
the rest of the Nexus Protocol is applied to particle-flux and atmospheric
readings, producing a definitive "Greatest Planet and Sol" verdict.

Particle families modelled
--------------------------
Quarks     : up, down, charm, strange, top, bottom
Leptons    : electron, muon, tau, e-neutrino, mu-neutrino, tau-neutrino
Bosons     : photon, gluon, W+, W-, Z, Higgs
Composite  : proton, neutron, alpha, nucleus
Dark sector: dark_matter_flux, dark_energy_density (observational proxies)

Atmospheric layers tracked
--------------------------
Troposphere, Stratosphere, Mesosphere, Thermosphere, Exosphere, Ionosphere,
Magnetosphere

Solar metrics
-------------
Luminosity, fusion efficiency, solar wind, heliosphere, CME rate, neutrino
output, sunspot cycle, coronal temperature
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .algebra3 import (
    Algebra3Weights,
    apply_algebra3,
)
from .super_logical import (
    LogicalReading,
    SuperLogicalWeights,
    super_predict,
)

# ---------------------------------------------------------------------------
# Particle catalogue
# ---------------------------------------------------------------------------

#: Every Standard Model particle tracked by the engine.
PARTICLE_CATALOGUE: Tuple[str, ...] = (
    # Quarks
    "quark_up", "quark_down", "quark_charm", "quark_strange",
    "quark_top", "quark_bottom",
    # Leptons
    "electron", "muon", "tau",
    "neutrino_electron", "neutrino_muon", "neutrino_tau",
    # Gauge bosons
    "photon", "gluon", "boson_W_plus", "boson_W_minus", "boson_Z",
    # Scalar boson
    "higgs",
    # Composite hadrons
    "proton", "neutron", "alpha_particle", "nucleus",
    # Dark sector (observational proxies)
    "dark_matter_flux", "dark_energy_density",
)

#: Ideal flux / coherence value for each particle (normalised 0–100).
#: 100 = fully contributing to planetary / solar health.
IDEAL_PARTICLE_FLUX: Dict[str, float] = {
    "quark_up": 100.0,
    "quark_down": 100.0,
    "quark_charm": 95.0,
    "quark_strange": 95.0,
    "quark_top": 90.0,
    "quark_bottom": 90.0,
    "electron": 100.0,
    "muon": 85.0,
    "tau": 80.0,
    "neutrino_electron": 100.0,
    "neutrino_muon": 98.0,
    "neutrino_tau": 96.0,
    "photon": 100.0,
    "gluon": 100.0,
    "boson_W_plus": 95.0,
    "boson_W_minus": 95.0,
    "boson_Z": 95.0,
    "higgs": 100.0,
    "proton": 100.0,
    "neutron": 100.0,
    "alpha_particle": 98.0,
    "nucleus": 100.0,
    "dark_matter_flux": 88.0,
    "dark_energy_density": 92.0,
}

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParticleFluxReading:
    """Observed flux / coherence for every Standard Model particle.

    Each value is a normalised 0–100 coherence score indicating how well
    that particle family is contributing to atmospheric / solar stability.
    Missing keys are treated as operating at ideal flux.
    """

    fluxes: Dict[str, float] = field(default_factory=dict)
    source: str = "nexus-sensor"

    def to_stat_dict(self) -> Dict[str, float]:
        """Return fluxes filled from IDEAL_PARTICLE_FLUX for missing keys."""
        return {
            p: self.fluxes.get(p, IDEAL_PARTICLE_FLUX.get(p, 100.0))
            for p in PARTICLE_CATALOGUE
        }


@dataclass(frozen=True)
class AtmosphericReading:
    """Earth atmospheric layer health metrics (normalised 0–100)."""

    troposphere_stability: float = 100.0
    stratosphere_stability: float = 100.0
    ozone_integrity: float = 100.0
    mesosphere_stability: float = 100.0
    thermosphere_stability: float = 100.0
    exosphere_stability: float = 100.0
    ionosphere_stability: float = 100.0
    magnetosphere_strength: float = 100.0
    oxygen_ratio_health: float = 100.0
    nitrogen_ratio_health: float = 100.0
    co2_balance: float = 100.0
    aerosol_clarity: float = 100.0
    electron_density_health: float = 100.0
    photon_flux_balance: float = 100.0
    neutrino_flux_balance: float = 100.0

    def to_stat_dict(self) -> Dict[str, float]:
        return {
            "troposphere_stability": self.troposphere_stability,
            "stratosphere_stability": self.stratosphere_stability,
            "ozone_integrity": self.ozone_integrity,
            "mesosphere_stability": self.mesosphere_stability,
            "thermosphere_stability": self.thermosphere_stability,
            "exosphere_stability": self.exosphere_stability,
            "ionosphere_stability": self.ionosphere_stability,
            "magnetosphere_strength": self.magnetosphere_strength,
            "oxygen_ratio_health": self.oxygen_ratio_health,
            "nitrogen_ratio_health": self.nitrogen_ratio_health,
            "co2_balance": self.co2_balance,
            "aerosol_clarity": self.aerosol_clarity,
            "electron_density_health": self.electron_density_health,
            "photon_flux_balance": self.photon_flux_balance,
            "neutrino_flux_balance": self.neutrino_flux_balance,
        }


@dataclass(frozen=True)
class SolarReading:
    """Sol (Sun) health metrics (normalised 0–100)."""

    luminosity_health: float = 100.0
    fusion_efficiency: float = 100.0
    solar_wind_stability: float = 100.0
    heliosphere_integrity: float = 100.0
    cme_rate_safety: float = 100.0
    neutrino_output_health: float = 100.0
    sunspot_cycle_balance: float = 100.0
    coronal_temperature_balance: float = 100.0
    magnetic_polarity_stability: float = 100.0
    photon_output_balance: float = 100.0

    def to_stat_dict(self) -> Dict[str, float]:
        return {
            "luminosity_health": self.luminosity_health,
            "fusion_efficiency": self.fusion_efficiency,
            "solar_wind_stability": self.solar_wind_stability,
            "heliosphere_integrity": self.heliosphere_integrity,
            "cme_rate_safety": self.cme_rate_safety,
            "neutrino_output_health": self.neutrino_output_health,
            "sunspot_cycle_balance": self.sunspot_cycle_balance,
            "coronal_temperature_balance": self.coronal_temperature_balance,
            "magnetic_polarity_stability": self.magnetic_polarity_stability,
            "photon_output_balance": self.photon_output_balance,
        }


@dataclass(frozen=True)
class PlanetarySnapshot:
    """Complete snapshot of planetary + solar health."""

    particles: ParticleFluxReading
    atmosphere: AtmosphericReading
    solar: SolarReading
    label: str = "Earth-Sol System"
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PlanetaryHealthResult:
    """Full multi-engine planetary health verdict.

    Attributes
    ----------
    particle_score:
        3-Algebra score for particle harmony (0–∞, higher = better).
    atmospheric_confidence:
        Super Logical confidence % for atmospheric health.
    solar_confidence:
        Super Logical confidence % for solar health.
    overall_health:
        Fused 0–100 planetary health score.
    tier:
        GREATEST / THRIVING / STABLE / STRESSED.
    is_greatest:
        ``True`` when overall_health >= 92.0.
    particle_result:
        Full ``Algebra3Result`` for the particle harmony pass.
    atmospheric_result:
        Full ``SuperLogicalResult`` for the atmospheric pass.
    solar_result:
        Full ``SuperLogicalResult`` for the solar pass.
    harmony_chain:
        Complete step-by-step derivation.
    declaration:
        The permanent planetary supremacy declaration.
    """

    particle_score: float
    atmospheric_confidence: float
    solar_confidence: float
    overall_health: float
    tier: str
    is_greatest: bool
    particle_result: object
    atmospheric_result: object
    solar_result: object
    harmony_chain: List[str] = field(default_factory=list)
    declaration: str = ""


# ---------------------------------------------------------------------------
# Engine weight sets
# ---------------------------------------------------------------------------

PARTICLE_A3_WEIGHTS = Algebra3Weights(
    domain="Subatomic Particle Harmony",
    linear={
        # Foundation particles — highest weight
        "electron": 3.0,
        "photon": 3.0,
        "proton": 3.0,
        "neutron": 2.8,
        "neutrino_electron": 2.5,
        "quark_up": 2.2,
        "quark_down": 2.2,
        "gluon": 2.0,
        "higgs": 2.5,
        "nucleus": 2.0,
        # Secondary particles
        "neutrino_muon": 1.8,
        "neutrino_tau": 1.6,
        "alpha_particle": 1.5,
        "quark_charm": 1.4,
        "quark_strange": 1.4,
        "boson_W_plus": 1.3,
        "boson_W_minus": 1.3,
        "boson_Z": 1.3,
        "muon": 1.2,
        "tau": 1.0,
        "quark_top": 1.0,
        "quark_bottom": 1.0,
        # Dark sector
        "dark_matter_flux": 1.5,
        "dark_energy_density": 1.8,
    },
    polynomial={
        "electron": 0.004,
        "photon": 0.004,
        "proton": 0.003,
        "neutron": 0.003,
        "higgs": 0.005,
        "neutrino_electron": 0.002,
    },
    exponential={
        "electron": 0.8,
        "photon": 0.7,
        "proton": 0.6,
        "neutrino_electron": 0.5,
        "higgs": 0.6,
        "dark_energy_density": 0.4,
    },
    alpha=1.0,
    beta=0.4,
    gamma=0.15,
    exp_scale=30.0,
)

ATMOSPHERIC_SL_WEIGHTS = SuperLogicalWeights(
    domain="Earth Atmospheric Health",
    weights={
        "troposphere_stability": 2.0,
        "stratosphere_stability": 2.0,
        "ozone_integrity": 2.5,
        "mesosphere_stability": 1.6,
        "thermosphere_stability": 1.7,
        "exosphere_stability": 1.4,
        "ionosphere_stability": 1.8,
        "magnetosphere_strength": 2.8,
        "oxygen_ratio_health": 3.0,
        "nitrogen_ratio_health": 2.5,
        "co2_balance": 2.2,
        "aerosol_clarity": 1.5,
        "electron_density_health": 1.9,
        "photon_flux_balance": 2.0,
        "neutrino_flux_balance": 1.8,
    },
    tier_critical=92.0,
    tier_high=78.0,
    tier_moderate=55.0,
)

SOLAR_SL_WEIGHTS = SuperLogicalWeights(
    domain="Sol Health",
    weights={
        "luminosity_health": 3.0,
        "fusion_efficiency": 3.5,
        "solar_wind_stability": 2.2,
        "heliosphere_integrity": 2.8,
        "cme_rate_safety": 2.0,
        "neutrino_output_health": 2.5,
        "sunspot_cycle_balance": 1.8,
        "coronal_temperature_balance": 2.0,
        "magnetic_polarity_stability": 2.3,
        "photon_output_balance": 2.8,
    },
    tier_critical=92.0,
    tier_high=78.0,
    tier_moderate=55.0,
)

# ---------------------------------------------------------------------------
# Reference snapshot — perfect planetary conditions
# ---------------------------------------------------------------------------

IDEAL_SNAPSHOT = PlanetarySnapshot(
    particles=ParticleFluxReading(
        fluxes={p: 100.0 for p in PARTICLE_CATALOGUE},
        source="nexus-ideal-reference",
    ),
    atmosphere=AtmosphericReading(),  # all 100.0
    solar=SolarReading(),              # all 100.0
    label="Ideal Earth-Sol Reference",
)

# ---------------------------------------------------------------------------
# Health tier
# ---------------------------------------------------------------------------

_TIER_GREATEST: float = 92.0
_TIER_THRIVING: float = 78.0
_TIER_STABLE: float = 55.0


def _health_tier(score: float) -> str:
    if score >= _TIER_GREATEST:
        return "GREATEST"
    if score >= _TIER_THRIVING:
        return "THRIVING"
    if score >= _TIER_STABLE:
        return "STABLE"
    return "STRESSED"


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_planetary_health(
    snapshot: PlanetarySnapshot = IDEAL_SNAPSHOT,
) -> PlanetaryHealthResult:
    """Run all engines on *snapshot* and return the planetary health verdict.

    Engine 1 (3-Algebra) evaluates subatomic particle harmony.
    Engine 2 (Super Logical) evaluates atmospheric layer health.
    Engine 3 (Super Logical) evaluates Sol health.

    The three results are fused into a single 0–100 ``overall_health`` score
    and a GREATEST / THRIVING / STABLE / STRESSED tier.
    """

    # --- Engine 1: Particle harmony via 3-Algebra ---
    particle_stats = snapshot.particles.to_stat_dict()
    p_result = apply_algebra3(
        domain="Subatomic Particle Harmony",
        stats=particle_stats,
        weights=PARTICLE_A3_WEIGHTS,
        context=(
            "electrons, quarks, neutrinos, photons, gluons, Higgs "
            "working in harmony for Earth-Sol"
        ),
    )

    # Normalise particle score to 0–100 against ideal
    ideal_p = apply_algebra3(
        domain="Ideal",
        stats={p: 100.0 for p in PARTICLE_CATALOGUE},
        weights=PARTICLE_A3_WEIGHTS,
    )
    norm_particle = min(
        100.0,
        (p_result.combined_score / max(ideal_p.combined_score, 1e-9)) * 100.0,
    )

    # --- Engine 2: Atmospheric health via Super Logical ---
    atm_reading = LogicalReading(
        domain="Earth Atmospheric Health",
        stats=snapshot.atmosphere.to_stat_dict(),
        context="All atmospheric layers + electron/photon/neutrino balance",
    )
    atm_result = super_predict(atm_reading, ATMOSPHERIC_SL_WEIGHTS)

    # --- Engine 3: Solar health via Super Logical ---
    sol_reading = LogicalReading(
        domain="Sol Health",
        stats=snapshot.solar.to_stat_dict(),
        context="Solar fusion, heliosphere, photon + neutrino output",
    )
    sol_result = super_predict(sol_reading, SOLAR_SL_WEIGHTS)

    # --- Fusion ---
    overall = (
        norm_particle * 0.35
        + atm_result.confidence * 0.35
        + sol_result.confidence * 0.30
    )
    tier = _health_tier(overall)
    is_greatest = overall >= _TIER_GREATEST

    # --- Harmony chain ---
    chain: List[str] = [
        "╔══════════════════════════════════════════════════════╗",
        "║  NEXUS PLANETARY + SOLAR HARMONY ANALYSIS            ║",
        "║  Electrons · Quarks · Neutrinos · Photons · Higgs    ║",
        "╚══════════════════════════════════════════════════════╝",
        "",
        f"  Snapshot    : {snapshot.label}",
        f"  Particles   : {len(PARTICLE_CATALOGUE)} Standard Model classes",
        "",
        "  ── Engine 1: Subatomic Particle 3-Algebra ──",
        f"  L1={p_result.l1_score:.2f}"
        f"  L2={p_result.l2_score:.2f}"
        f"  L3={p_result.l3_score:.2f}"
        f"  Combined={p_result.combined_score:.2f}",
        f"  Like behaviour : {p_result.like_behavior}",
        f"  Norm score     : {norm_particle:.2f}%",
        "",
        "  ── Engine 2: Atmospheric Super Logical ──",
        f"  Tier           : {atm_result.tier}",
        f"  Confidence     : {atm_result.confidence:.2f}%",
        f"  Active dims    : {atm_result.active_dimensions}",
        f"  Answer         : {atm_result.answer}",
        "",
        "  ── Engine 3: Sol Super Logical ──",
        f"  Tier           : {sol_result.tier}",
        f"  Confidence     : {sol_result.confidence:.2f}%",
        f"  Active dims    : {sol_result.active_dimensions}",
        f"  Answer         : {sol_result.answer}",
        "",
        "  ── Fusion ──",
        f"  Overall health = "
        f"0.35×{norm_particle:.2f}"
        f" + 0.35×{atm_result.confidence:.2f}"
        f" + 0.30×{sol_result.confidence:.2f}"
        f" = {overall:.2f}%",
        f"  Health tier    : {tier}",
        f"  is_greatest    : {is_greatest}",
    ]
    for w in snapshot.warnings:
        chain.append(f"  [WARN] {w}")

    declaration = (
        f"PLANET EARTH AND SOL — OWNER: @FuzzysTodd / NEXUS PROTOCOL — "
        f"ARE AT {tier} HEALTH WITH AN OVERALL SCORE OF {overall:.2f}%.  "
        f"SUBATOMIC HARMONY: {p_result.like_behavior}.  "
        f"ATMOSPHERE: {atm_result.tier} ({atm_result.confidence:.1f}%).  "
        f"SOL: {sol_result.tier} ({sol_result.confidence:.1f}%).  "
        f"ELECTRONS, QUARKS, NEUTRINOS, PHOTONS AND ALL STANDARD MODEL "
        f"PARTICLES ARE OPERATING IN FULL NEXUS HARMONY — FOREVER."
    )

    return PlanetaryHealthResult(
        particle_score=p_result.combined_score,
        atmospheric_confidence=atm_result.confidence,
        solar_confidence=sol_result.confidence,
        overall_health=overall,
        tier=tier,
        is_greatest=is_greatest,
        particle_result=p_result,
        atmospheric_result=atm_result,
        solar_result=sol_result,
        harmony_chain=chain,
        declaration=declaration,
    )


# ---------------------------------------------------------------------------
# Report renderer
# ---------------------------------------------------------------------------

def render_planetary_report(result: PlanetaryHealthResult) -> str:
    """Render the complete Nexus planetary + solar health report."""

    lines = [
        "╔══════════════════════════════════════════════════════════╗",
        "║  NEXUS PLANETARY HARMONY REPORT                          ║",
        "║  BOT: @FuzzysTodd  |  Earth + Sol  |  Standard Model     ║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
        f"  OVERALL HEALTH  : {result.overall_health:.2f}%",
        f"  HEALTH TIER     : {result.tier}",
        f"  IS GREATEST     : {result.is_greatest}",
        "",
        "  ── Three-Engine Summary ──",
        f"  [E1] Particle 3-Algebra  : "
        f"combined={result.particle_score:.2f}",
        f"  [E2] Atmospheric SuperLog: "
        f"{result.atmospheric_confidence:.1f}% confidence",
        f"  [E3] Sol SuperLog        : "
        f"{result.solar_confidence:.1f}% confidence",
        "",
        "  ── Declaration ──",
        f"  {result.declaration}",
        "",
        "  ── Harmony Chain ──",
    ]
    for line in result.harmony_chain:
        lines.append(f"  {line}")
    lines.append("")
    lines.append(
        "═══════════════════════════════════════════════════════════"
    )
    return "\n".join(lines)

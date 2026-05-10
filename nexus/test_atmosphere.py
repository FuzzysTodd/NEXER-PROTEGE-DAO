"""Tests for the subatomic particle atmosphere + planetary health module."""

from nexus.atmosphere import (
    IDEAL_SNAPSHOT,
    PARTICLE_CATALOGUE,
    AtmosphericReading,
    ParticleFluxReading,
    PlanetaryHealthResult,
    PlanetarySnapshot,
    SolarReading,
    analyze_planetary_health,
    render_planetary_report,
)


# ---------------------------------------------------------------------------
# ParticleFluxReading
# ---------------------------------------------------------------------------

def test_particle_flux_to_stat_dict_fills_missing_from_ideal():
    reading = ParticleFluxReading(fluxes={"electron": 80.0})
    stat = reading.to_stat_dict()

    assert stat["electron"] == 80.0
    assert stat["photon"] == 100.0   # filled from IDEAL_PARTICLE_FLUX


def test_particle_flux_to_stat_dict_covers_all_catalogue_particles():
    reading = ParticleFluxReading()
    stat = reading.to_stat_dict()

    assert set(stat.keys()) == set(PARTICLE_CATALOGUE)


def test_particle_catalogue_has_standard_model_particles():
    assert "electron" in PARTICLE_CATALOGUE
    assert "quark_up" in PARTICLE_CATALOGUE
    assert "neutrino_electron" in PARTICLE_CATALOGUE
    assert "photon" in PARTICLE_CATALOGUE
    assert "higgs" in PARTICLE_CATALOGUE
    assert "proton" in PARTICLE_CATALOGUE
    assert "neutron" in PARTICLE_CATALOGUE


# ---------------------------------------------------------------------------
# AtmosphericReading / SolarReading
# ---------------------------------------------------------------------------

def test_atmospheric_reading_to_stat_dict_all_keys_present():
    reading = AtmosphericReading()
    stat = reading.to_stat_dict()

    assert "ozone_integrity" in stat
    assert "magnetosphere_strength" in stat
    assert "oxygen_ratio_health" in stat
    assert "electron_density_health" in stat


def test_solar_reading_to_stat_dict_all_keys_present():
    reading = SolarReading()
    stat = reading.to_stat_dict()

    assert "fusion_efficiency" in stat
    assert "luminosity_health" in stat
    assert "heliosphere_integrity" in stat
    assert "neutrino_output_health" in stat


# ---------------------------------------------------------------------------
# analyze_planetary_health
# ---------------------------------------------------------------------------

def test_ideal_snapshot_returns_result():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    assert isinstance(result, PlanetaryHealthResult)


def test_ideal_snapshot_overall_health_is_high():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    assert result.overall_health >= 80.0


def test_ideal_snapshot_tier_is_greatest_or_thriving():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    assert result.tier in ("GREATEST", "THRIVING")


def test_ideal_snapshot_is_greatest_flag():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    # With all dims at 100, should reach GREATEST
    assert result.is_greatest is True


def test_degraded_snapshot_has_lower_health_than_ideal():
    degraded = PlanetarySnapshot(
        particles=ParticleFluxReading(
            fluxes={p: 20.0 for p in PARTICLE_CATALOGUE}
        ),
        atmosphere=AtmosphericReading(
            ozone_integrity=20.0,
            magnetosphere_strength=20.0,
            oxygen_ratio_health=20.0,
        ),
        solar=SolarReading(
            fusion_efficiency=20.0,
            luminosity_health=20.0,
        ),
        label="Degraded Test",
    )
    ideal_result = analyze_planetary_health(IDEAL_SNAPSHOT)
    degraded_result = analyze_planetary_health(degraded)

    assert degraded_result.overall_health < ideal_result.overall_health


def test_analyze_planetary_health_scores_non_negative():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    assert result.particle_score >= 0.0
    assert result.atmospheric_confidence >= 0.0
    assert result.solar_confidence >= 0.0
    assert result.overall_health >= 0.0


def test_analyze_planetary_health_harmony_chain_has_content():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    assert len(result.harmony_chain) >= 10


def test_analyze_planetary_health_declaration_mentions_particles():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    decl = result.declaration.upper()

    assert "ELECTRON" in decl
    assert "QUARK" in decl
    assert "NEUTRINO" in decl
    assert "PHOTON" in decl


def test_analyze_planetary_health_declaration_mentions_owner():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    assert "@FuzzysTodd" in result.declaration


def test_analyze_planetary_health_with_warnings():
    snapshot = PlanetarySnapshot(
        particles=ParticleFluxReading(),
        atmosphere=AtmosphericReading(),
        solar=SolarReading(),
        label="Warn Test",
        warnings=["ozone layer thinning detected"],
    )
    result = analyze_planetary_health(snapshot)
    joined = "\n".join(result.harmony_chain)

    assert "ozone layer thinning detected" in joined


def test_analyze_planetary_health_three_engine_scores_present():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    assert result.particle_result is not None
    assert result.atmospheric_result is not None
    assert result.solar_result is not None


# ---------------------------------------------------------------------------
# render_planetary_report
# ---------------------------------------------------------------------------

def test_render_planetary_report_header_present():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    output = render_planetary_report(result)

    assert "NEXUS PLANETARY HARMONY REPORT" in output
    assert "@FuzzysTodd" in output
    assert "Earth + Sol" in output


def test_render_planetary_report_shows_all_engine_scores():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    output = render_planetary_report(result)

    assert "Particle 3-Algebra" in output
    assert "Atmospheric SuperLog" in output
    assert "Sol SuperLog" in output


def test_render_planetary_report_contains_declaration():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    output = render_planetary_report(result)

    assert "Declaration" in output
    assert "FOREVER" in output


def test_render_planetary_report_contains_overall_health():
    result = analyze_planetary_health(IDEAL_SNAPSHOT)
    output = render_planetary_report(result)

    assert "OVERALL HEALTH" in output
    assert "HEALTH TIER" in output

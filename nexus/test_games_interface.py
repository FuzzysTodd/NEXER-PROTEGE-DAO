"""Tests for the Nexus browser games interface."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_games_html_exists():
    assert (REPO_ROOT / "games.html").is_file()


def test_games_js_exists():
    assert (REPO_ROOT / "games.js").is_file()


def test_games_html_has_arcade_title_and_script():
    html = (REPO_ROOT / "games.html").read_text()
    assert "<title>Nexus Protocol — Games Arcade</title>" in html
    assert '<script src="./games.js"></script>' in html


def test_games_html_has_navigation_links():
    html = (REPO_ROOT / "games.html").read_text()
    assert 'href="./index.html"' in html
    assert 'href="./user-guide.html"' in html
    assert 'href="./chimera.html"' in html
    assert 'href="./withdraw.html"' in html


def test_games_html_has_age_group_catalog_and_arcade():
    html = (REPO_ROOT / "games.html").read_text()
    assert 'id="age-group-buttons"' in html
    assert 'id="catalog-list"' in html
    assert 'id="arcade"' in html
    assert "Memory Match MCP" in html
    assert "Token Trading Academy" in html
    assert "DAO Governance Sprint" in html


def test_games_html_has_playable_controls():
    html = (REPO_ROOT / "games.html").read_text()
    for control_id in [
        'id="memory-reset"',
        'id="trader-reset"',
        'id="governance-reset"',
        'id="governance-next"',
    ]:
        assert control_id in html

    for trader_action in ['buy', 'hold', 'sell']:
        assert f'data-trader-action="{trader_action}"' in html


def test_games_js_defines_age_groups_and_featured_games():
    script = (REPO_ROOT / "games.js").read_text()
    assert "const AGE_GROUPS = [" in script
    assert "Children (Ages 5-10)" in script
    assert "Seniors (Ages 60+)" in script
    assert "const FEATURED_GAMES = {" in script
    assert "recommendedGame" in script


def test_games_js_exposes_arcade_behaviors():
    script = (REPO_ROOT / "games.js").read_text()
    for function_name in [
        "initializeApp",
        "renderMemoryGame",
        "handleTraderAction",
        "submitGovernanceAnswer",
    ]:
        assert f"function {function_name}" in script

    assert "window.NexusGames" in script


def test_games_js_avoids_eval_like_execution():
    script = (REPO_ROOT / "games.js").read_text()
    assert "eval(" not in script
    assert "new Function(" not in script


def test_index_links_to_games_arcade():
    index_html = (REPO_ROOT / "index.html").read_text()
    assert 'href="./games.html"' in index_html
    assert "Games Arcade" in index_html
    assert "🎮 Play Games" in index_html


def test_readme_mentions_games_arcade():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "[Games Arcade](games.html)" in readme
    assert "games.js" in readme

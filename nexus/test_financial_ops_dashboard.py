"""Tests for the financial ops dashboard real-time refresh UI."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_financial_ops_dashboard_has_live_refresh_controls():
    html = (REPO_ROOT / "financial-ops-dashboard.html").read_text()
    assert 'id="refresh-report"' in html
    assert 'id="live-status"' in html
    assert 'id="last-checked"' in html
    assert 'id="source-snapshot"' in html
    assert 'id="chain-snapshot"' in html
    assert 'id="chain-outputs"' in html
    assert 'aria-live="polite"' in html
    assert 'Open REST Adapter' in html


def test_financial_ops_dashboard_polls_for_updates():
    html = (REPO_ROOT / "financial-ops-dashboard.html").read_text()
    assert "const REFRESH_INTERVAL_MS = 15000;" in html
    assert "window.setInterval(loadReport, REFRESH_INTERVAL_MS);" in html
    assert "const REPORT_ADAPTER_URL = 'http://127.0.0.1:8788/api/report';" in html
    assert "fetchReportSnapshot()" in html
    assert "sourceSnapshot.textContent" in html
    assert "chainSnapshot.textContent" in html


def test_financial_ops_rest_server_supports_websocket_sources():
    js = (REPO_ROOT / "financial-ops-rest-server.js").read_text()
    assert "function isWebSocketSource(sourceUrl)" in js
    assert "async function callRpcOverWebSocket(method, params = [])" in js
    assert 'parsed.protocol === "ws:" || parsed.protocol === "wss:"' in js
    assert "if (isWebSocketSource(SOURCE_URL))" in js
    assert "function isDuneSnapshotPayload(report)" in js
    assert "function normalizeDuneReport(report, source)" in js
    assert "sourceType: \"dune-snapshot\"" in js
    assert "duneSnapshot:" in js


def test_financial_ops_dashboard_formats_dune_snapshots():
    html = (REPO_ROOT / "financial-ops-dashboard.html").read_text()
    assert "if (report.duneSnapshot)" in html
    assert "Dune snapshot for" in html
    assert "Top holdings" in html
    assert "Chain breakdown" in html
    assert "function formatCurrency(value)" in html


def test_financial_ops_dashboard_replaces_previous_rendered_items():
    html = (REPO_ROOT / "financial-ops-dashboard.html").read_text()
    for reset_line in [
        "botList.innerHTML = '';",
        "findingList.innerHTML = '';",
        "signalList.innerHTML = '';",
        "logList.innerHTML = '';",
        "actionList.innerHTML = '';",
    ]:
        assert reset_line in html

"""Tests for crypto expert guide and money flow dashboard."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# crypto-expert-guide.html
# ---------------------------------------------------------------------------

def test_crypto_expert_guide_exists():
    assert (REPO_ROOT / "crypto-expert-guide.html").is_file()


def test_crypto_expert_guide_has_hero_section():
    html = (REPO_ROOT / "crypto-expert-guide.html").read_text()
    assert "Nexus Protocol Crypto Expert Dashboard" in html
    assert "100% Expert-Level Money Flow Analysis" in html


def test_crypto_expert_guide_has_calculator():
    html = (REPO_ROOT / "crypto-expert-guide.html").read_text()
    assert 'id="investment"' in html
    assert 'id="timeframe"' in html
    assert 'id="strategy"' in html
    assert "calculateReturns()" in html


def test_crypto_expert_guide_has_10_revenue_streams():
    html = (REPO_ROOT / "crypto-expert-guide.html").read_text()
    assert "10 Primary Revenue Streams" in html
    assert "Dividend Distributions" in html
    assert "Game-to-Earn Rewards" in html
    assert "NFT Staking" in html
    assert "Liquidity Provision" in html
    assert "Reflection Fees" in html
    assert "Buyback & Burn" in html
    assert "MCP Group Profits" in html
    assert "Arbitrage Trading" in html
    assert "Governance Rewards" in html
    assert "Lending & Borrowing" in html


def test_crypto_expert_guide_has_apy_ranges():
    html = (REPO_ROOT / "crypto-expert-guide.html").read_text()
    assert "5-20% APY" in html
    assert "50-300% APY" in html
    assert "100-500% APY" in html


def test_crypto_expert_guide_has_risk_indicators():
    html = (REPO_ROOT / "crypto-expert-guide.html").read_text()
    assert "risk-low" in html
    assert "risk-medium" in html
    assert "risk-high" in html


def test_crypto_expert_guide_has_money_flow_diagram():
    html = (REPO_ROOT / "crypto-expert-guide.html").read_text()
    assert "Money Flow Architecture" in html
    assert "Transaction Flow" in html
    assert "Fee Distribution Breakdown" in html


def test_crypto_expert_guide_has_expert_strategies():
    html = (REPO_ROOT / "crypto-expert-guide.html").read_text()
    assert "Expert-Level Strategies" in html
    assert "The Compounding King Strategy" in html
    assert "The Game Theory Maximalist" in html
    assert "The Ultimate Hybrid Stack" in html


def test_crypto_expert_guide_has_quick_actions():
    html = (REPO_ROOT / "crypto-expert-guide.html").read_text()
    assert "Quick Actions" in html
    assert 'href="./withdraw.html"' in html
    assert 'href="./chimera.html"' in html


def test_crypto_expert_guide_loads_money_flow_script():
    html = (REPO_ROOT / "crypto-expert-guide.html").read_text()
    assert '<script src="./money-flow.js"></script>' in html


# ---------------------------------------------------------------------------
# money-flow.js
# ---------------------------------------------------------------------------

def test_money_flow_js_exists():
    assert (REPO_ROOT / "money-flow.js").is_file()


def test_money_flow_js_defines_revenue_streams():
    script = (REPO_ROOT / "money-flow.js").read_text()
    assert "REVENUE_STREAMS" in script
    assert "dividends" in script
    assert "gameToEarn" in script
    assert "nftStaking" in script
    assert "liquidityProvision" in script


def test_money_flow_js_defines_strategies():
    script = (REPO_ROOT / "money-flow.js").read_text()
    assert "STRATEGIES" in script
    assert "conservative" in script
    assert "balanced" in script
    assert "aggressive" in script
    assert "expert" in script


def test_money_flow_js_has_calculate_returns():
    script = (REPO_ROOT / "money-flow.js").read_text()
    assert "function calculateReturns()" in script
    assert "getElementById('investment')" in script
    assert "getElementById('timeframe')" in script
    assert "getElementById('strategy')" in script


def test_money_flow_js_has_format_currency():
    script = (REPO_ROOT / "money-flow.js").read_text()
    assert "function formatCurrency(" in script or "formatCurrency =" in script


def test_money_flow_js_has_timeframes():
    script = (REPO_ROOT / "money-flow.js").read_text()
    assert "TIMEFRAMES" in script
    assert "daily" in script
    assert "weekly" in script
    assert "monthly" in script
    assert "yearly" in script


def test_money_flow_js_calculates_apy():
    script = (REPO_ROOT / "money-flow.js").read_text()
    assert "apy" in script.lower()
    assert "minAPY" in script
    assert "maxAPY" in script


def test_money_flow_js_has_expert_recommendations():
    script = (REPO_ROOT / "money-flow.js").read_text()
    has_recommendations = (
        "getExpertRecommendations" in script
        or "recommendations" in script.lower()
    )
    assert has_recommendations


# ---------------------------------------------------------------------------
# CRYPTO_REVENUE_GUIDE.md
# ---------------------------------------------------------------------------

def test_crypto_revenue_guide_exists():
    assert (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").is_file()


def test_crypto_revenue_guide_has_title():
    md = (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").read_text()
    assert "Nexus Protocol Crypto Expert Guide" in md
    assert "The Complete Path to Maximum Money Flow" in md


def test_crypto_revenue_guide_has_authority():
    md = (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").read_text()
    assert "@FuzzysTodd" in md
    assert "The-Nexus-Protocol-Token-DOA" in md


def test_crypto_revenue_guide_explains_10_streams():
    md = (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").read_text()
    assert "10 Revenue Streams" in md
    assert "Dividend Distributions" in md
    assert "Game-to-Earn Rewards" in md
    assert "NFT Staking" in md
    assert "Arbitrage Trading" in md


def test_crypto_revenue_guide_has_apy_details():
    md = (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").read_text()
    assert "APY Range" in md
    assert "Risk Level" in md
    assert "Investment Required" in md


def test_crypto_revenue_guide_has_example_calculations():
    md = (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").read_text()
    assert "Example Calculation" in md
    # Should have multiple calculation examples
    assert md.count("```") >= 10


def test_crypto_revenue_guide_has_expert_strategies():
    md = (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").read_text()
    assert "Expert-Level Strategies" in md
    assert "Strategy 1:" in md or "The Compounding King" in md
    assert "200%+ APY" in md or "300%+ APY" in md


def test_crypto_revenue_guide_has_risk_management():
    md = (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").read_text()
    assert "Risk Management" in md
    assert "Never invest more than you can afford to lose" in md


def test_crypto_revenue_guide_has_getting_started():
    md = (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").read_text()
    assert "Getting Started" in md
    assert "Step 1:" in md
    assert "MetaMask" in md or "wallet" in md


def test_crypto_revenue_guide_has_roi_comparison():
    md = (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").read_text()
    assert "ROI Comparison" in md or "Comparison Table" in md
    # Should have a table
    assert "|" in md


def test_crypto_revenue_guide_references_ngtt():
    md = (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").read_text()
    assert "NGTT" in md
    assert "Nexus Game Theory Token" in md or "Nexus Protocol Token" in md


def test_crypto_revenue_guide_has_tools_resources():
    md = (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").read_text()
    assert "Tools" in md or "Resources" in md
    assert "Uniswap" in md or "Aave" in md


def test_crypto_revenue_guide_has_success_milestones():
    md = (REPO_ROOT / "CRYPTO_REVENUE_GUIDE.md").read_text()
    assert "Milestone" in md or "Success" in md
    # Should have checkboxes for milestones
    assert "[ ]" in md or "- [ ]" in md

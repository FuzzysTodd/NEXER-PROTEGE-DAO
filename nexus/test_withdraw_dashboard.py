"""Tests for the Nexus Contract Withdrawal Manager dashboard files."""

import json
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")


def run_node(script: str) -> str:
    assert NODE, "node runtime is required for dashboard helper tests"
    result = subprocess.run(
        [NODE, "-e", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# withdraw.html
# ---------------------------------------------------------------------------

def test_withdraw_html_exists():
    assert (REPO_ROOT / "withdraw.html").is_file()


def test_withdraw_html_loads_ethers_and_withdraw_script():
    html = (REPO_ROOT / "withdraw.html").read_text()
    assert "ethers" in html and "umd.min.js" in html
    assert '<script src="./withdraw.js"></script>' in html


def test_withdraw_html_has_wallet_connect_button():
    html = (REPO_ROOT / "withdraw.html").read_text()
    assert 'id="connect-btn"' in html
    assert "Connect Wallet" in html


def test_withdraw_html_has_add_contract_form():
    html = (REPO_ROOT / "withdraw.html").read_text()
    assert 'id="add-contract-form"' in html
    assert 'id="input-address"' in html
    assert 'id="input-method"' in html


def test_withdraw_html_has_contract_list_section():
    html = (REPO_ROOT / "withdraw.html").read_text()
    assert 'id="contract-list"' in html
    assert "My Contracts" in html


def test_withdraw_html_has_json_import_and_settlement_controls():
    html = (REPO_ROOT / "withdraw.html").read_text()
    assert 'id="json-import-input"' in html
    assert 'id="json-import-file"' in html
    assert 'id="import-summary"' in html
    assert 'id="import-collectible-table"' in html
    assert 'Direction' in html
    assert 'Recipient' in html
    assert 'id="settlement-destination"' in html
    assert "Coinbase settlement destination" in html
    assert "Enter your own Coinbase deposit address" in html
    assert "collectibles" in html
    assert "Send to Coinbase" in html or "Transfer" in html


def test_withdraw_html_loads_money_flow_helpers():
    html = (REPO_ROOT / "withdraw.html").read_text()
    assert '<script src="./money-flow.js"></script>' in html


def test_withdraw_html_has_withdraw_methods_in_select():
    html = (REPO_ROOT / "withdraw.html").read_text()
    for method in [
        "withdraw()", "withdrawAll()", "release(address)", "claimRewards()"
    ]:
        assert method in html


def test_withdraw_html_explains_proxy_pattern():
    html = (REPO_ROOT / "withdraw.html").read_text()
    assert "EIP-1967" in html
    assert "fallback" in html
    assert "implementation" in html


def test_withdraw_html_mentions_local_storage_only():
    html = (REPO_ROOT / "withdraw.html").read_text()
    assert "Local-only storage" in html


# ---------------------------------------------------------------------------
# withdraw.js – proxy ABI
# ---------------------------------------------------------------------------

def test_withdraw_js_exists():
    assert (REPO_ROOT / "withdraw.js").is_file()


def test_withdraw_js_embeds_proxy_abi_events():
    script = (REPO_ROOT / "withdraw.js").read_text()
    for event in ["AdminChanged", "BeaconUpgraded", "Upgraded"]:
        assert event in script


def test_withdraw_js_proxy_abi_has_fallback_and_receive():
    script = (REPO_ROOT / "withdraw.js").read_text()
    assert '"fallback"' in script
    assert '"receive"' in script


def test_withdraw_js_proxy_abi_constructor_fields():
    script = (REPO_ROOT / "withdraw.js").read_text()
    for param in ["_logic", "admin_", "_data"]:
        assert param in script


def test_withdraw_js_proxy_abi_is_valid_json_embedded():
    """Extract PROXY_ABI array literal and verify it parses as JSON."""
    script = (REPO_ROOT / "withdraw.js").read_text()
    start = script.index("const PROXY_ABI = [")
    # Grab from the opening bracket
    start = script.index("[", start)
    # Walk to the matching closing bracket
    depth = 0
    end = start
    for i, ch in enumerate(script[start:], start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i
                break
    raw = script[start:end + 1]
    parsed = json.loads(raw)
    assert isinstance(parsed, list)
    assert len(parsed) >= 5  # constructor + 3 events + fallback + receive


# ---------------------------------------------------------------------------
# withdraw.js – withdraw methods
# ---------------------------------------------------------------------------

def test_withdraw_js_has_withdraw_method_selectors():
    script = (REPO_ROOT / "withdraw.js").read_text()
    # Standard 4-byte selectors
    assert "0x3ccfd60b" in script   # withdraw()
    assert "0x853828b6" in script   # withdrawAll()
    assert "0x19165587" in script   # release(address)


def test_withdraw_js_encodes_release_with_saved_destination_address():
    script = (REPO_ROOT / "withdraw.js").read_text()
    release_branch = 'if (method === "release(address)")'
    custom_branch = 'else if (method === "custom" && customSelector)'
    assert release_branch in script
    assert custom_branch in script
    assert script.index(release_branch) < script.index(custom_branch)
    assert 'encodeFunctionData("release", [settlementDestination])' in script
    assert "Configure and verify a destination address before using release(address)." in script


def test_withdraw_js_defines_storage_key():
    script = (REPO_ROOT / "withdraw.js").read_text()
    assert "nexus_withdraw_contracts" in script


def test_withdraw_js_defines_import_and_destination_storage_keys():
    script = (REPO_ROOT / "withdraw.js").read_text()
    assert "nexus_imported_wallet_data" in script
    assert "nexus_settlement_destination" in script
    assert "DEFAULT_SETTLEMENT_DESTINATION" in script
    assert "MAX_DISPLAYED_BALANCES" in script
    assert "MAX_DISPLAYED_COLLECTIBLES" in script
    assert "No destination configured" in script


def test_withdraw_js_exports_nexus_withdraw_namespace():
    script = (REPO_ROOT / "withdraw.js").read_text()
    assert "NexusWithdraw" in script
    assert "connectWallet" in script
    assert "withdrawFromContract" in script


def test_withdraw_js_escape_html_helper_present():
    script = (REPO_ROOT / "withdraw.js").read_text()
    assert "escapeHtml" in script


def test_withdraw_js_uses_escaped_balance_ids_for_render_and_lookup():
    script = (REPO_ROOT / "withdraw.js").read_text()
    assert 'id="bal-${escapeHtml(c.address)}"' in script
    assert 'document.getElementById("bal-" + escapeHtml(c.address))' in script


def test_withdraw_js_handles_custom_selector():
    script = (REPO_ROOT / "withdraw.js").read_text()
    assert (
        "customSelector" in script
        or "custom-selector" in script
        or "custom_selector" in script
    )


def test_withdraw_js_can_parse_balances_and_transactions_payloads():
    script = (REPO_ROOT / "withdraw.js").read_text()
    assert "parseImportedPayload" in script
    assert "payload.balances" in script
    assert "payload.transactions" in script
    assert "payload.entries" in script
    assert "renderImportedData" in script


def test_withdraw_js_runtime_labels_transaction_direction():
    output = run_node(
        """
        const withdraw = require('./withdraw.js');
        const wallet = '0xeCE999c86452c573Adfdd7F0C9226e673477973a';
        const parsed = withdraw.parseImportedPayload(JSON.stringify({
          wallet_address: wallet,
          transactions: [
            {
              chain: 'ethereum',
              transaction_type: 'Sent USDT',
              from: wallet,
              to: '0x1111111111111111111111111111111111111111',
              amount: '1000000',
              decimals: 6,
              symbol: 'USDT'
            },
            {
              chain: 'ethereum',
              transaction_type: 'Received USDT',
              from: '0x1111111111111111111111111111111111111111',
              to: wallet,
              amount: '2000000',
              decimals: 6,
              symbol: 'USDT'
            }
          ]
        }));
        console.log(JSON.stringify(parsed.transactions.map(tx => ({
          direction: tx.direction,
          directionLabel: tx.directionLabel,
          recipientStatus: tx.recipientStatus,
          recipientLabel: tx.recipientLabel,
          recipientWarning: tx.recipientWarning,
          amountLabel: tx.amountLabel
        }))));
        """
    )
    parsed = json.loads(output)
    assert parsed[0]["direction"] == "out"
    assert parsed[0]["directionLabel"] == "Outgoing"
    assert parsed[0]["recipientStatus"] == "mismatch"
    assert parsed[0]["recipientLabel"] == "Different recipient"
    assert "will not credit" in parsed[0]["recipientWarning"]
    assert parsed[0]["amountLabel"].startswith("-1")
    assert parsed[1]["direction"] == "in"
    assert parsed[1]["directionLabel"] == "Incoming"
    assert parsed[1]["recipientStatus"] == "match"
    assert parsed[1]["recipientLabel"] == "Matches wallet"
    assert parsed[1]["amountLabel"].startswith("+2")


def test_money_flow_js_exports_import_helpers():
    script = (REPO_ROOT / "money-flow.js").read_text()
    assert "summarizeImportedBalances" in script
    assert "classifyOffRamp" in script
    assert "window.NexusMoneyFlow" in script


def test_withdraw_js_runtime_helpers_cover_formatting_and_parsing():
    output = run_node(
        """
        const withdraw = require('./withdraw.js');
        const validPayload = withdraw.parseImportedPayload(JSON.stringify({
          wallet_address: '0xabc',
          balances: [{
            chain: 'ethereum',
            address: 'native',
            amount: '1500000000000000000',
            symbol: 'ETH',
            decimals: 18,
            value_usd: 3200
          }]
        }));
        const invalidJson = (() => {
          try { withdraw.parseImportedPayload('{'); } catch (error) { return error.message; }
        })();
        const nonObject = (() => {
          try { withdraw.parseImportedPayload('[]'); } catch (error) { return error.message; }
        })();
        const emptyPayload = (() => {
          try {
            withdraw.parseImportedPayload(JSON.stringify({ balances: [], transactions: [] }));
          } catch (error) {
            return error.message;
          }
        })();
        console.log(JSON.stringify({
          large: withdraw.formatTokenAmount('1000000000000', 6),
          medium: withdraw.formatTokenAmount('1500000', 6),
          small: withdraw.formatTokenAmount('12345', 8),
          wallet: validPayload.walletAddress,
          balances: validPayload.balances.length,
          invalidJson,
          nonObject,
          emptyPayload
        }));
        """
    )
    parsed = json.loads(output)
    assert parsed["large"] == "1,000,000"
    assert parsed["medium"] == "1.5"
    assert parsed["small"] == "0.00012345"
    assert parsed["wallet"] == "0xabc"
    assert parsed["balances"] == 1
    assert parsed["invalidJson"] == "Invalid JSON format."
    expected_error = (
        "JSON must include a balances array, a transactions array, "
        "or a collectibles entries array."
    )
    assert parsed["nonObject"] == expected_error
    assert parsed["emptyPayload"] == expected_error


def test_withdraw_js_runtime_builds_imported_balance_transfer_requests():
    output = run_node(
        """
        const withdraw = require('./withdraw.js');
        const readyBalance = {
          assetType: 'balance',
          chain: 'base',
          chainId: 8453,
          address: '0x1234',
          rawAmount: '2500000',
          offRamp: {
            status: 'ready',
            settlement: {
              network: 'Base',
              supportsDirectTransfer: true
            }
          }
        };
        const nativeBalance = {
          assetType: 'balance',
          chain: 'ethereum',
          chainId: 1,
          address: 'native',
          rawAmount: '1000000000000000000',
          offRamp: {
            status: 'ready',
            settlement: {
              network: 'Ethereum',
              supportsDirectTransfer: true
            }
          }
        };
        const reviewBalance = {
          assetType: 'balance',
          chain: 'base',
          chainId: 8453,
          address: '0x9999',
          rawAmount: '1',
          offRamp: {
            status: 'review',
            settlement: {
              network: 'Base',
              supportsDirectTransfer: true
            }
          }
        };
        const tokenRequest = withdraw.buildImportedBalanceTransferRequest(
          readyBalance,
          '0x1EF9950fc2d9433Ab9d253881fd461f8e2098Eac'
        );
        const nativeRequest = withdraw.buildImportedBalanceTransferRequest(
          nativeBalance,
          '0x1EF9950fc2d9433Ab9d253881fd461f8e2098Eac'
        );
        const invalidStatus = withdraw.validateImportedBalanceTransfer(
          reviewBalance,
          '0x1EF9950fc2d9433Ab9d253881fd461f8e2098Eac',
          8453
        );
        const wrongChain = withdraw.validateImportedBalanceTransfer(
          readyBalance,
          '0x1EF9950fc2d9433Ab9d253881fd461f8e2098Eac',
          1
        );
        console.log(JSON.stringify({
          canSendReady: withdraw.canSendImportedBalance(readyBalance),
          canSendReview: withdraw.canSendImportedBalance(reviewBalance),
          tokenRequest,
          nativeRequest,
          invalidStatus,
          wrongChain
        }));
        """
    )
    parsed = json.loads(output)
    assert parsed["canSendReady"] is True
    assert parsed["canSendReview"] is False
    assert parsed["tokenRequest"]["kind"] == "erc20"
    assert parsed["tokenRequest"]["tokenAddress"] == "0x1234"
    assert parsed["tokenRequest"]["amount"] == "2500000"
    assert parsed["nativeRequest"]["kind"] == "native"
    assert parsed["nativeRequest"]["transaction"]["value"] == "1000000000000000000"
    assert parsed["invalidStatus"] == "This asset is not eligible for a direct Coinbase transfer."
    assert parsed["wrongChain"] == "Switch your wallet to Base before sending this asset."


def test_withdraw_js_runtime_can_normalize_dune_collectibles_payload():
    output = run_node(
        """
        const withdraw = require('./withdraw.js');
        const imported = withdraw.parseImportedPayload(JSON.stringify({
          address: '0xd8da6bf26964af9d7eed9e03e53415d37aa96045',
          entries: [{
            contract_address: '0x1234',
            token_standard: 'ERC721',
            token_id: '1',
            chain: 'base',
            chain_id: 8453,
            name: 'Base Genesis',
            symbol: 'BG',
            balance: '1',
            is_spam: false,
            last_acquired: '2026-04-06T18:15:47+00:00'
          }, {
            contract_address: '0xabcd',
            token_standard: 'ERC1155',
            token_id: '9',
            chain: 'ethereum',
            chain_id: 1,
            name: 'Spam Drop',
            symbol: 'DROP',
            balance: '2',
            is_spam: true
          }]
        }));
        console.log(JSON.stringify({
          wallet: imported.walletAddress,
          source: imported.source,
          balances: imported.balances.length,
          collectibles: imported.collectibles.length,
          baseNetwork: imported.collectibles[0].offRamp.settlement.network,
          baseDestination: imported.collectibles[0].offRamp.settlement.destination,
          spamStatus: imported.collectibles[1].offRamp.status
        }));
        """
    )
    parsed = json.loads(output)
    assert parsed["wallet"] == "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
    assert parsed["source"] == "dune-collectibles"
    assert parsed["balances"] == 0
    assert parsed["collectibles"] == 2
    assert parsed["baseNetwork"] == "Base"
    assert parsed["baseDestination"] == "Base wallet review"
    assert parsed["spamStatus"] == "blocked"


def test_withdraw_js_runtime_settlement_destination_validation():
    output = run_node(
        """
        global.document = {
          getElementById: () => ({ value: '0x1EF9950fc2d9433Ab9d253881fd461f8e2098Eac' })
        };
        global.ethers = {
          utils: {
            isAddress: (value) => /^0x[a-fA-F0-9]{40}$/.test(value)
          }
        };
        const withdraw = require('./withdraw.js');
        const valid = withdraw.getSettlementDestination();
        global.document = {
          getElementById: () => ({ value: '   ' })
        };
        const blank = withdraw.getSettlementDestination();
        global.document = {
          getElementById: () => ({ value: 'not-an-address' })
        };
        const invalid = withdraw.getSettlementDestination();
        console.log(JSON.stringify({ valid, blank, invalid }));
        """
    )
    parsed = json.loads(output)
    assert parsed["valid"] == "0x1EF9950fc2d9433Ab9d253881fd461f8e2098Eac"
    assert parsed["blank"] == "0x1EF9950fc2d9433Ab9d253881fd461f8e2098Eac"
    assert parsed["invalid"] is None


def test_money_flow_runtime_import_classification_and_summary():
    output = run_node(
        """
        const moneyFlow = require('./money-flow.js');
        const parsed = {
          padded: moneyFlow.parseDecimalAmount('12345', 4),
          whole: moneyFlow.parseDecimalAmount('42', 0),
          invalid: Number.isNaN(moneyFlow.parseDecimalAmount('abc', 18)),
          ready: moneyFlow.classifyOffRamp({ chain: 'ethereum', symbol: 'ETH', value_usd: 10, address: 'native' }),
          blocked: moneyFlow.classifyOffRamp({ chain: 'sepolia', symbol: 'ETH', value_usd: 10, address: 'native' }),
          review: moneyFlow.classifyOffRamp({ chain: 'ethereum', symbol: 'TEST', value_usd: 10, low_liquidity: true }),
          swap: moneyFlow.classifyOffRamp({ chain: 'ethereum', symbol: 'ABC', value_usd: 10, pool_size: 250000 }),
          collectible: moneyFlow.classifyOffRamp({
            chain: 'base',
            asset_type: 'collectible',
            token_standard: 'ERC721',
            symbol: 'NFT',
            is_spam: false
          })
        };
        const summary = moneyFlow.summarizeImportedBalances([
          { chain: 'ethereum', address: 'native', symbol: 'ETH', value_usd: 100 },
          { chain: 'ethereum', address: '0x1', symbol: 'ABC', value_usd: 50, pool_size: 250000 },
          { chain: 'sepolia', address: 'native', symbol: 'ETH', value_usd: 25 },
          { chain: 'ethereum', address: '0x2', symbol: 'LOW', value_usd: 10, low_liquidity: true },
          { chain: 'base', address: '0x3', symbol: 'MISS' }
        ]);
        console.log(JSON.stringify({ parsed, summary }));
        """
    )
    parsed = json.loads(output)
    assert parsed["parsed"]["padded"] == 1.2345
    assert parsed["parsed"]["whole"] == 42
    assert parsed["parsed"]["invalid"] is True
    assert parsed["parsed"]["ready"]["status"] == "ready"
    assert parsed["parsed"]["blocked"]["status"] == "blocked"
    assert parsed["parsed"]["review"]["status"] == "review"
    assert parsed["parsed"]["swap"]["status"] == "swap"
    assert parsed["parsed"]["ready"]["settlement"]["destination"] == "Coinbase Ethereum deposit"
    assert parsed["parsed"]["collectible"]["status"] == "review"
    assert parsed["parsed"]["collectible"]["settlement"]["destination"] == "Base wallet review"
    assert parsed["summary"]["totalValueUsd"] == 185
    assert parsed["summary"]["readyValueUsd"] == 100
    assert parsed["summary"]["swapValueUsd"] == 50
    assert parsed["summary"]["blockedValueUsd"] == 25
    assert parsed["summary"]["reviewValueUsd"] == 10
    assert parsed["summary"]["nativeAssetCount"] == 2
    assert parsed["summary"]["coinbaseReadyCount"] == 1
    assert parsed["summary"]["baseReadyCount"] == 0
    assert parsed["summary"]["unpricedAssetCount"] == 1


def test_withdraw_js_no_private_key_literals():
    """Ensure no hard-coded private key placeholder was left in the script."""
    script = (REPO_ROOT / "withdraw.js").read_text()
    assert "YOUR_PRIVATE_KEY" not in script
    assert "PRIVATE_KEY" not in script

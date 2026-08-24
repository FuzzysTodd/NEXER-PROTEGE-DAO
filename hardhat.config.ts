import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import "@openzeppelin/hardhat-upgrades";
import "hardhat-gas-reporter";
import "solidity-coverage";
import * as dotenv from "dotenv";

dotenv.config();

/**
 * hardhat.config.ts — Nexus Protocol DAO
 *
 * Networks:
 *   hardhat  — in-process local node (default), GPU mining via --gpu flag
 *   localhost — external `npx hardhat node` instance on :8545
 *   nexus-devnet — NEXER GPU devnet node on :8546 (RTX 5060 Ti accelerated)
 *   sepolia  — Ethereum Sepolia testnet
 *   mainnet  — Ethereum mainnet (require explicit --network mainnet)
 *
 * Solidity:
 *   0.8.20 with optimizer (200 runs) — EIP-170 safe for all Nexus contracts
 *
 * Gas reporter:
 *   Set REPORT_GAS=true to enable — outputs table after test run
 *
 * Agent assignments:
 *   mcp-004 AI Data Pipeline Manager  — feeds gas/deployment data for training
 *   nexus-security-audit              — slither/mythril CI integration
 */
const config: HardhatUserConfig = {
    solidity: {
        version: "0.8.20",
        settings: {
            optimizer: {
                enabled: true,
                runs: 200,
            },
            viaIR: false,
        },
    },

    networks: {
        // ------------------------------------------------------------------
        // Local in-process node (default for tests)
        // ------------------------------------------------------------------
        hardhat: {
            chainId: 31337,
            mining: {
                auto: true,
                interval: 0,
            },
            accounts: {
                count: 20,
                initialIndex: 0,
                path: "m/44'/60'/0'/0",
                // 1 million ETH per test account for gas-free testing
                accountsBalance: "1000000000000000000000000",
            },
            gas: "auto",
            blockGasLimit: 30_000_000,
            allowUnlimitedContractSize: false,
        },

        // ------------------------------------------------------------------
        // Localhost — external `npx hardhat node --port 8545`
        // ------------------------------------------------------------------
        localhost: {
            url: "http://127.0.0.1:8545",
            chainId: 31337,
            timeout: 60000,
        },

        // ------------------------------------------------------------------
        // Nexus GPU devnet — RTX 5060 Ti accelerated local node (:8546)
        // Agent mcp-004 + mcp-005 use this network for AI/GPU workloads.
        // ------------------------------------------------------------------
        "nexus-devnet": {
            url: process.env.NEXUS_DEVNET_RPC || "http://127.0.0.1:8546",
            chainId: 13337,
            accounts: process.env.NEXUS_DEVNET_PRIVKEY
                ? [process.env.NEXUS_DEVNET_PRIVKEY]
                : { mnemonic: process.env.MNEMONIC || "test test test test test test test test test test test junk" },
            timeout: 120000,
        },

        // ------------------------------------------------------------------
        // Sepolia testnet
        // ------------------------------------------------------------------
        sepolia: {
            url: process.env.SEPOLIA_RPC_URL || "https://rpc.sepolia.org",
            chainId: 11155111,
            accounts: process.env.DEPLOYER_PRIVATE_KEY
                ? [process.env.DEPLOYER_PRIVATE_KEY]
                : [],
            gasMultiplier: 1.2,
            timeout: 120000,
        },

        // ------------------------------------------------------------------
        // Mainnet (explicit flag required)
        // ------------------------------------------------------------------
        mainnet: {
            url: process.env.MAINNET_RPC_URL || "https://cloudflare-eth.com",
            chainId: 1,
            accounts: process.env.DEPLOYER_PRIVATE_KEY
                ? [process.env.DEPLOYER_PRIVATE_KEY]
                : [],
            gasMultiplier: 1.1,
            timeout: 300000,
        },
    },

    // -----------------------------------------------------------------------
    // Etherscan / Sourcify verification
    // -----------------------------------------------------------------------
    etherscan: {
        apiKey: {
            mainnet:          process.env.ETHERSCAN_API_KEY || "",
            sepolia:          process.env.ETHERSCAN_API_KEY || "",
        },
    },

    // -----------------------------------------------------------------------
    // Gas reporter
    // -----------------------------------------------------------------------
    gasReporter: {
        enabled:      process.env.REPORT_GAS === "true",
        currency:     "USD",
        coinmarketcap: process.env.CMC_API_KEY,
        outputFile:   "ops/reports/gas-report.txt",
        noColors:     true,
        excludeContracts: [],
    },

    // -----------------------------------------------------------------------
    // Paths
    // -----------------------------------------------------------------------
    paths: {
        sources:   "./contracts",
        tests:     "./test",
        cache:     "./cache",
        artifacts: "./artifacts",
    },

    // -----------------------------------------------------------------------
    // Mocha test runner
    // -----------------------------------------------------------------------
    mocha: {
        timeout: 120_000,
        reporter: "spec",
    },
};

export default config;

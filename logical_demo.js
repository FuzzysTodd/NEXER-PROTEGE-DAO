// Optional wallet demo helpers for Project Chimera.
// This file is intentionally separate from logical.js so the browser-facing
// dashboard stays static and free of privileged or backend-only examples.

// --- Required imports (assuming you're using a bundler like Vite or Webpack) ---
// import { ethers } from "ethers";
// import NexusFinancialContractABI from "./abis/NexusFinancialContract.json";
// import NexusGreenTokenABI from "./abis/NexusGreenToken.json";

function notifyUser(message) {
    if (typeof window !== "undefined" && typeof window.alert === "function") {
        window.alert(message);
        return;
    }
    console.warn(message);
}

// --- Contract Addresses (replace with your deployed addresses) ---
const nexusFinancialContractAddress = "0x...";
const nexusGreenTokenAddress = "0x...";

let provider;
let signer;
let nexusFinancialContract;
let nexusGreenToken;

/**
 * Connects to the user's Ethereum wallet (e.g., MetaMask).
 */
async function connectWallet() {
    if (typeof window.ethereum !== "undefined") {
        try {
            provider = new ethers.providers.Web3Provider(window.ethereum);
            await provider.send("eth_requestAccounts", []);
            signer = provider.getSigner();

            nexusFinancialContract = new ethers.Contract(
                nexusFinancialContractAddress,
                NexusFinancialContractABI.abi,
                signer
            );
            nexusGreenToken = new ethers.Contract(
                nexusGreenTokenAddress,
                NexusGreenTokenABI.abi,
                signer
            );

            console.log("Wallet connected:", await signer.getAddress());
        } catch (error) {
            console.error("User rejected connection:", error);
        }
    } else {
        console.error("MetaMask is not installed!");
    }
}

/**
 * Listens for events from the NexusFinancialContract.
 */
function setupEventListeners() {
    if (!nexusFinancialContract) return;

    nexusFinancialContract.on(
        "TransactionInitiated",
        (transactionId, initiator, principal) => {
            console.log(
                "Transaction Initiated:",
                `ID=${transactionId}, User=${initiator},`,
                `Amount=${ethers.utils.formatEther(principal)}`
            );
        }
    );

    nexusFinancialContract.on(
        "TransactionStateChanged",
        (transactionId, newState) => {
            console.log(
                "Transaction State Changed:",
                `ID=${transactionId}, New State=${newState}`
            );
        }
    );

    nexusFinancialContract.on(
        "ProposalCreated",
        (proposalId, proposer, description) => {
            console.log(
                "New Proposal:",
                `ID=${proposalId}, Proposer=${proposer}, Desc=${description}`
            );
        }
    );
}

/**
 * Example function to be called from the UI to create a DAO proposal.
 * Note: In the real dApp, this would be an admin/backend function.
 * @param {string} description The text description of the proposal.
 */
async function createProposal(description) {
    if (!nexusFinancialContract) {
        notifyUser("Please connect your wallet first.");
        return;
    }
    try {
        const tx = await nexusFinancialContract.createProposal(description);
        console.log("Creating proposal... TX hash:", tx.hash);
        await tx.wait();
        console.log("Proposal created successfully!");
    } catch (error) {
        console.error("Error creating proposal:", error);
    }
}

/**
 * Example function to vote on a proposal.
 * @param {number} proposalId The ID of the proposal to vote on.
 */
async function voteOnProposal(proposalId) {
    if (!nexusFinancialContract) {
        notifyUser("Please connect your wallet first.");
        return;
    }
    try {
        const tx = await nexusFinancialContract.vote(proposalId);
        console.log(`Voting on proposal ${proposalId}... TX hash:`, tx.hash);
        await tx.wait();
        console.log("Voted successfully!");
    } catch (error) {
        console.error("Error voting:", error);
    }
}

// Backend-owned signing must stay server-side and out of browser bundles.
// Any owner key, MPC signer, or privileged automation should be injected only
// in protected server processes and never hard-coded into repository web assets.

if (typeof window !== "undefined") {
    window.NexusWalletDemo = {
        connectWallet,
        setupEventListeners,
        createProposal,
        voteOnProposal,
    };
}

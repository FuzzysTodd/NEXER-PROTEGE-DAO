// This file contains example JavaScript code to interact with the Project Chimera smart contracts.
// It uses the ethers.js library, a popular alternative to web3.js.
// You would integrate this logic into the interactive web application's frontend.

// --- Required imports (assuming you're using a bundler like Vite or Webpack) ---
// import { ethers } from "ethers";
// import NexusFinancialContractABI from './abis/NexusFinancialContract.json';
// import NexusGreenTokenABI from './abis/NexusGreenToken.json';

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
    if (typeof window.ethereum !== 'undefined') {
        try {
            provider = new ethers.providers.Web3Provider(window.ethereum);
            await provider.send("eth_requestAccounts", []);
            signer = provider.getSigner();

            nexusFinancialContract = new ethers.Contract(nexusFinancialContractAddress, NexusFinancialContractABI.abi, signer);
            nexusGreenToken = new ethers.Contract(nexusGreenTokenAddress, NexusGreenTokenABI.abi, signer);

            console.log("Wallet connected:", await signer.getAddress());
            // Add UI logic to show connected state
        } catch (error) {
            console.error("User rejected connection:", error);
            // Add UI logic to show connection error
        }
    } else {
        console.error("MetaMask is not installed!");
        // Add UI logic to prompt user to install MetaMask
    }
}

/**
 * Listens for events from the NexusFinancialContract.
 */
function setupEventListeners() {
    if (!nexusFinancialContract) return;

    nexusFinancialContract.on("TransactionInitiated", (transactionId, initiator, principal) => {
        console.log(`Transaction Initiated: ID=${transactionId}, User=${initiator}, Amount=${ethers.utils.formatEther(principal)}`);
        // Add UI logic to display a notification or update a transaction list.
    });

    nexusFinancialContract.on("TransactionStateChanged", (transactionId, newState) => {
        console.log(`Transaction State Changed: ID=${transactionId}, New State=${newState}`);
        // Update the UI to reflect the new state of the transaction.
    });

    nexusFinancialContract.on("ProposalCreated", (proposalId, proposer, description) => {
        console.log(`New Proposal: ID=${proposalId}, Proposer=${proposer}, Desc=${description}`);
        // Add the new proposal to the DAO voting section of the UI.
    });
}


/**
 * Example function to be called from the UI to create a DAO proposal.
 * Note: In the real dApp, this would be an admin/backend function.
 * @param {string} description The text description of the proposal.
 */
async function createProposal(description) {
    if (!nexusFinancialContract) {
        alert("Please connect your wallet first.");
        return;
    }
    try {
        const tx = await nexusFinancialContract.createProposal(description);
        console.log("Creating proposal... TX hash:", tx.hash);
        await tx.wait();
        console.log("Proposal created successfully!");
        // Add UI feedback
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
        alert("Please connect your wallet first.");
        return;
    }
    try {
        const tx = await nexusFinancialContract.vote(proposalId);
        console.log(`Voting on proposal ${proposalId}... TX hash:`, tx.hash);
        await tx.wait();
        console.log("Voted successfully!");
        // Add UI feedback
    } catch (error) {
        console.error("Error voting:", error);
    }
}


// --- Pseudo-code for how the off-chain system would interact ---
// This part is NOT for the frontend but illustrates the backend process.

/**
 * [BACKEND ONLY] Simulates the autonomous system initiating a transaction.
 * @param {string} userAddress The user's wallet address.
 * @param {number} amount The principal amount.
 */
async function backend_initiateTransaction(userAddress, amount) {
    // This requires a signer with owner privileges on the contract.
    const ownerSigner = new ethers.Wallet("YOUR_PRIVATE_KEY", provider);
    const contractAsOwner = nexusFinancialContract.connect(ownerSigner);

    const principal = ethers.utils.parseEther(amount.toString());
    const metadataUri = `https://api.projectchimera.dev/transactions/${Date.now()}`;

    const tx = await contractAsOwner.initiateTransaction(userAddress, principal, metadataUri);
    await tx.wait();
    // ... then backend monitors and calls updateTransactionState and distributeValue
}

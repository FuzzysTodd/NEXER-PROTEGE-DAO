// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title NexusRWARegistry
 * @notice Real-World Asset tokenization registry.
 *         Each ERC-721 token represents a property title on-chain.
 *         Valuation and annual rent can be updated by authorized appraisers.
 *         Assets can be fractionalised into ERC-20 share contracts.
 *
 * Events match nexus-signal-bus.js RWA_ABI exactly.
 *
 * Agent assignments:
 *   mcp-007 NFT Minting & Trading Agent  — mint, marketplace, ownership
 *   nexus-nft-studio                     — ERC-721A / RWA patterns
 *   nexus-treasury-ops                   — fractional yield routing
 *
 * @author Nexus Protocol DAO  (nexus-nft-studio)
 */
contract NexusRWARegistry is ERC721, ERC721URIStorage, AccessControl, Pausable {
    // -----------------------------------------------------------------------
    // Roles
    // -----------------------------------------------------------------------
    bytes32 public constant MINTER_ROLE    = keccak256("MINTER_ROLE");
    bytes32 public constant APPRAISER_ROLE = keccak256("APPRAISER_ROLE");
    bytes32 public constant PAUSER_ROLE    = keccak256("PAUSER_ROLE");

    // -----------------------------------------------------------------------
    // Asset metadata
    // -----------------------------------------------------------------------
    struct AssetInfo {
        bytes32 titleHash;           // sha256(deed document bytes)
        string  documentCid;         // IPFS CID of the legal deed
        string  propertyAddress;     // human-readable address
        uint256 valuationUsdCents;   // appraisal value in USD cents
        uint256 annualRentUsdCents;  // annual rent in USD cents
        address fractionContract;    // ERC-20 fractional contract (if set)
    }

    uint256 private _nextTokenId;
    mapping(uint256 => AssetInfo) private _assets;

    // -----------------------------------------------------------------------
    // Events (match signal-bus ABI)
    // -----------------------------------------------------------------------
    event AssetMinted(
        uint256 indexed tokenId,
        address indexed owner,
        bytes32 titleHash,
        string  documentCid,
        string  propertyAddress
    );
    event ValuationUpdated(uint256 indexed tokenId, uint256 newValueUsdCents);
    event RentUpdated(uint256 indexed tokenId, uint256 newAnnualRentUsdCents);
    event AssetFractionalised(uint256 indexed tokenId, address fractionContract);

    // -----------------------------------------------------------------------
    // Constructor
    // -----------------------------------------------------------------------
    constructor(address admin)
        ERC721("Nexus Real-World Asset", "NRWA")
    {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MINTER_ROLE, admin);
        _grantRole(APPRAISER_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
    }

    // -----------------------------------------------------------------------
    // Minting
    // -----------------------------------------------------------------------
    function mintAsset(
        address to,
        bytes32 titleHash,
        string calldata documentCid,
        string calldata propertyAddress,
        uint256 valuationUsdCents,
        uint256 annualRentUsdCents,
        string calldata tokenURIStr
    ) external onlyRole(MINTER_ROLE) whenNotPaused returns (uint256 tokenId) {
        tokenId = _nextTokenId++;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURIStr);
        _assets[tokenId] = AssetInfo({
            titleHash:          titleHash,
            documentCid:        documentCid,
            propertyAddress:    propertyAddress,
            valuationUsdCents:  valuationUsdCents,
            annualRentUsdCents: annualRentUsdCents,
            fractionContract:   address(0)
        });
        emit AssetMinted(tokenId, to, titleHash, documentCid, propertyAddress);
    }

    // -----------------------------------------------------------------------
    // Appraisal
    // -----------------------------------------------------------------------
    function updateValuation(uint256 tokenId, uint256 newValueUsdCents) external onlyRole(APPRAISER_ROLE) {
        require(_ownerOf(tokenId) != address(0), "NexusRWA: nonexistent token");
        _assets[tokenId].valuationUsdCents = newValueUsdCents;
        emit ValuationUpdated(tokenId, newValueUsdCents);
    }

    function updateRent(uint256 tokenId, uint256 newAnnualRentUsdCents) external onlyRole(APPRAISER_ROLE) {
        require(_ownerOf(tokenId) != address(0), "NexusRWA: nonexistent token");
        _assets[tokenId].annualRentUsdCents = newAnnualRentUsdCents;
        emit RentUpdated(tokenId, newAnnualRentUsdCents);
    }

    // -----------------------------------------------------------------------
    // Fractionalisation
    // -----------------------------------------------------------------------
    function fractionalise(uint256 tokenId, address fractionContract) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_ownerOf(tokenId) != address(0), "NexusRWA: nonexistent token");
        require(_assets[tokenId].fractionContract == address(0), "NexusRWA: already fractionalised");
        _assets[tokenId].fractionContract = fractionContract;
        emit AssetFractionalised(tokenId, fractionContract);
    }

    // -----------------------------------------------------------------------
    // View
    // -----------------------------------------------------------------------
    function assetInfo(uint256 tokenId) external view returns (AssetInfo memory) {
        return _assets[tokenId];
    }

    // -----------------------------------------------------------------------
    // Pause
    // -----------------------------------------------------------------------
    function pause()   external onlyRole(PAUSER_ROLE) { _pause(); }
    function unpause() external onlyRole(PAUSER_ROLE) { _unpause(); }

    // -----------------------------------------------------------------------
    // Required overrides
    // -----------------------------------------------------------------------
    function tokenURI(uint256 tokenId)
        public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public view override(ERC721, ERC721URIStorage, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}

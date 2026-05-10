// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/// @title NexusRWA — Real-World Asset NFT
/// @notice ERC-721 contract representing tokenized real-world property deeds
///         and physical assets within the Nexus Protocol DAO ecosystem.
///
/// Each token encodes:
///   - An IPFS/Arweave CID pointing to the full legal deed document.
///   - A keccak256 hash of the title string for on-chain integrity checks.
///   - A valuation in USD cents (updatable by APPRAISER_ROLE).
///   - An active rental yield stream (set by OPERATOR_ROLE; actual payment
///     is handled off-chain or via Superfluid streams).
///
/// Ownership of the NFT = beneficial ownership of the underlying LLC that
/// holds the deed (Wyoming DAO LLC structure compatible with US property law).
///
/// NES: this contract is a Nexus-authored surface governed by the
/// Nexus Encryption Standard as documented in docs/NEXUS_ENCRYPTION_STANDARD.md.
contract NexusRWA is ERC721, AccessControl, ReentrancyGuard {
    using Counters for Counters.Counter;

    // -------------------------------------------------------------------------
    // Roles
    // -------------------------------------------------------------------------

    /// @notice May mint new RWA tokens (restricted to DAO or authorized minters).
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    /// @notice May update valuations for existing tokens.
    bytes32 public constant APPRAISER_ROLE = keccak256("APPRAISER_ROLE");

    /// @notice May update rental yield information.
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");

    // -------------------------------------------------------------------------
    // Token metadata
    // -------------------------------------------------------------------------

    struct AssetMetadata {
        bytes32  titleHash;          // keccak256 of the legal title string
        string   documentCid;        // IPFS/Arweave content identifier for deed
        string   propertyAddress;    // Human-readable location (US or global)
        uint256  valuationUsdCents;  // Appraised value in USD cents (0 = unset)
        uint256  annualRentUsdCents; // Annual rental income in USD cents (0 = none)
        bool     fractionalised;     // True if wrapped by NexusFractionalize
        uint256  mintedAt;           // block.timestamp at mint
    }

    mapping(uint256 => AssetMetadata) private _metadata;
    Counters.Counter private _tokenIdCounter;

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    /// @notice Emitted when a new RWA token is minted.
    event AssetMinted(
        uint256 indexed tokenId,
        address indexed owner,
        bytes32 titleHash,
        string  documentCid,
        string  propertyAddress
    );

    /// @notice Emitted when the on-chain valuation is updated.
    event ValuationUpdated(uint256 indexed tokenId, uint256 newValueUsdCents);

    /// @notice Emitted when the annual rent estimate is updated.
    event RentUpdated(uint256 indexed tokenId, uint256 newAnnualRentUsdCents);

    /// @notice Emitted when a token is marked as fractionalised.
    event AssetFractionalised(uint256 indexed tokenId, address fractionContract);

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    /// @notice Deploys the RWA NFT contract.
    /// @param admin The DEFAULT_ADMIN_ROLE holder (owner wallet).
    constructor(address admin) ERC721("Nexus Real-World Asset", "NRWA") {
        require(admin != address(0), "NexusRWA: zero admin");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MINTER_ROLE, admin);
        _grantRole(APPRAISER_ROLE, admin);
        _grantRole(OPERATOR_ROLE, admin);
    }

    // -------------------------------------------------------------------------
    // Minting
    // -------------------------------------------------------------------------

    /// @notice Mints a new RWA token to the specified owner.
    /// @param to              Beneficial owner address.
    /// @param titleString     Legal title string (will be hashed on-chain).
    /// @param documentCid     IPFS/Arweave CID of the deed document.
    /// @param propertyAddress Human-readable location string.
    /// @param valuationUsdCents  Initial appraised value in USD cents (0 = TBD).
    /// @return tokenId The newly minted token identifier.
    function mintAsset(
        address to,
        string calldata titleString,
        string calldata documentCid,
        string calldata propertyAddress,
        uint256 valuationUsdCents
    ) external onlyRole(MINTER_ROLE) nonReentrant returns (uint256 tokenId) {
        require(to != address(0), "NexusRWA: zero recipient");
        require(bytes(documentCid).length > 0, "NexusRWA: empty CID");

        _tokenIdCounter.increment();
        tokenId = _tokenIdCounter.current();

        bytes32 titleHash = keccak256(abi.encodePacked(titleString));

        _metadata[tokenId] = AssetMetadata({
            titleHash: titleHash,
            documentCid: documentCid,
            propertyAddress: propertyAddress,
            valuationUsdCents: valuationUsdCents,
            annualRentUsdCents: 0,
            fractionalised: false,
            mintedAt: block.timestamp
        });

        _safeMint(to, tokenId);

        emit AssetMinted(tokenId, to, titleHash, documentCid, propertyAddress);
    }

    // -------------------------------------------------------------------------
    // Metadata updates
    // -------------------------------------------------------------------------

    /// @notice Updates the USD valuation for a token.
    /// @param tokenId           Token to update.
    /// @param newValueUsdCents  New appraised value in USD cents.
    function updateValuation(uint256 tokenId, uint256 newValueUsdCents)
        external
        onlyRole(APPRAISER_ROLE)
    {
        require(_exists(tokenId), "NexusRWA: nonexistent token");
        _metadata[tokenId].valuationUsdCents = newValueUsdCents;
        emit ValuationUpdated(tokenId, newValueUsdCents);
    }

    /// @notice Updates the annual rental yield estimate for a token.
    /// @param tokenId                  Token to update.
    /// @param newAnnualRentUsdCents    New annual rent in USD cents.
    function updateRent(uint256 tokenId, uint256 newAnnualRentUsdCents)
        external
        onlyRole(OPERATOR_ROLE)
    {
        require(_exists(tokenId), "NexusRWA: nonexistent token");
        _metadata[tokenId].annualRentUsdCents = newAnnualRentUsdCents;
        emit RentUpdated(tokenId, newAnnualRentUsdCents);
    }

    /// @notice Marks a token as fractionalised and records the fraction contract.
    /// @param tokenId          Token that has been fractionalised.
    /// @param fractionContract Address of the NexusFractionalize contract.
    function markFractionalised(uint256 tokenId, address fractionContract)
        external
        onlyRole(OPERATOR_ROLE)
    {
        require(_exists(tokenId), "NexusRWA: nonexistent token");
        require(fractionContract != address(0), "NexusRWA: zero fraction contract");
        _metadata[tokenId].fractionalised = true;
        emit AssetFractionalised(tokenId, fractionContract);
    }

    // -------------------------------------------------------------------------
    // View helpers
    // -------------------------------------------------------------------------

    /// @notice Returns full metadata for a token.
    /// @param tokenId The token to query.
    /// @return metadata The full AssetMetadata struct.
    function getMetadata(uint256 tokenId) external view returns (AssetMetadata memory metadata) {
        require(_exists(tokenId), "NexusRWA: nonexistent token");
        return _metadata[tokenId];
    }

    /// @notice Returns the total number of RWA tokens minted.
    /// @return count Total supply.
    function totalSupply() external view returns (uint256 count) {
        return _tokenIdCounter.current();
    }

    // -------------------------------------------------------------------------
    // ERC-165 override
    // -------------------------------------------------------------------------

    /// @inheritdoc ERC721
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}

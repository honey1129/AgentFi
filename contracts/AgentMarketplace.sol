// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC721Minimal {
    function ownerOf(uint256 tokenId) external view returns (address);
    function transferFrom(address from, address to, uint256 tokenId) external;
}

interface IERC721Receiver {
    function onERC721Received(
        address operator,
        address from,
        uint256 tokenId,
        bytes calldata data
    ) external returns (bytes4);
}

contract AgentMarketplace is IERC721Receiver {
    enum ListingStatus {
        NONE,
        OPEN,
        SOLD,
        CANCELLED
    }

    struct Listing {
        uint256 tokenId;
        uint256 price;
        address seller;
        ListingStatus status;
    }

    IERC721Minimal public immutable nft;
    uint256 public nextListingId = 1;

    mapping(uint256 => Listing) public listings;

    bool private _entered;

    event ListingCreated(
        uint256 indexed listingId,
        address indexed seller,
        uint256 indexed tokenId,
        uint256 price
    );
    event ListingCancelled(
        uint256 indexed listingId,
        address indexed seller,
        uint256 indexed tokenId
    );
    event ListingPurchased(
        uint256 indexed listingId,
        address indexed buyer,
        address indexed seller,
        uint256 tokenId,
        uint256 price
    );

    modifier nonReentrant() {
        require(!_entered, "Reentrant call");
        _entered = true;
        _;
        _entered = false;
    }

    constructor(address nftAddress) {
        require(nftAddress != address(0), "Invalid NFT");
        nft = IERC721Minimal(nftAddress);
    }

    function createListing(uint256 tokenId, uint256 price) external nonReentrant returns (uint256 listingId) {
        require(price > 0, "Invalid price");
        require(nft.ownerOf(tokenId) == msg.sender, "Not token owner");

        listingId = nextListingId;
        nextListingId += 1;

        listings[listingId] = Listing({
            tokenId: tokenId,
            price: price,
            seller: msg.sender,
            status: ListingStatus.OPEN
        });

        nft.transferFrom(msg.sender, address(this), tokenId);
        emit ListingCreated(listingId, msg.sender, tokenId, price);
    }

    function cancelListing(uint256 listingId) external nonReentrant {
        Listing storage listing = listings[listingId];
        require(listing.status == ListingStatus.OPEN, "Listing not open");
        require(listing.seller == msg.sender, "Not listing seller");

        listing.status = ListingStatus.CANCELLED;
        nft.transferFrom(address(this), listing.seller, listing.tokenId);
        emit ListingCancelled(listingId, listing.seller, listing.tokenId);
    }

    function buyListing(uint256 listingId) external payable nonReentrant {
        Listing storage listing = listings[listingId];
        require(listing.status == ListingStatus.OPEN, "Listing not open");
        require(msg.sender != listing.seller, "Seller cannot buy");
        require(msg.value == listing.price, "Incorrect payment");

        listing.status = ListingStatus.SOLD;

        (bool paid, ) = payable(listing.seller).call{value: msg.value}("");
        require(paid, "Seller payout failed");

        nft.transferFrom(address(this), msg.sender, listing.tokenId);
        emit ListingPurchased(listingId, msg.sender, listing.seller, listing.tokenId, listing.price);
    }

    function onERC721Received(
        address,
        address,
        uint256,
        bytes calldata
    ) external pure override returns (bytes4) {
        return IERC721Receiver.onERC721Received.selector;
    }
}

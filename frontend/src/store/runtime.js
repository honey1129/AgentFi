import { computed, reactive } from "vue";

const API_PREFIX = "/v1";
const AUTH_STORAGE_KEY = "agentfi.metamask.session";

function loadStoredSession() {
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

const storedSession = typeof window !== "undefined" ? loadStoredSession() : null;

const state = reactive({
  initialized: false,
  refreshing: false,
  health: null,
  runtime: null,
  wallets: [],
  agents: [],
  listings: [],
  runs: [],
  schedules: [],
  runMetrics: null,
  runtimeLogs: [],
  marketplace: {
    selectedListingId: null,
    pendingTx: null,
  },
  drawer: {
    open: false,
    loading: false,
    agentId: null,
    metadata: null,
    runs: [],
    error: null,
    requestNonce: 0,
    expandedRunIds: [],
  },
  flash: {
    visible: false,
    message: "",
    type: "success",
  },
  metamask: {
    available: typeof window !== "undefined" && typeof window.ethereum !== "undefined",
    address: null,
    chainId: null,
    wallet: null,
    token: storedSession?.token || null,
    sessionAddress: storedSession?.chain_address || null,
    authenticated: false,
  },
});

let refreshTimer = null;
let flashTimer = null;

const queuedRuns = computed(() => state.runs.filter((run) => run.status === "QUEUED"));
const runningRuns = computed(() => state.runs.filter((run) => run.status === "RUNNING"));
const completedRuns = computed(() => state.runs.filter((run) => run.status === "COMPLETED"));
const authenticated = computed(
  () => Boolean(state.metamask.authenticated && state.metamask.wallet && state.metamask.sessionAddress === state.metamask.address)
);
const selectedListing = computed(() => {
  if (!state.listings.length) {
    return null;
  }
  return state.listings.find((listing) => listing.id === state.marketplace.selectedListingId) || state.listings[0];
});

async function initialize() {
  if (!state.initialized) {
    state.initialized = true;
    if (window.ethereum) {
      window.ethereum.on("accountsChanged", () => refreshAll(false));
      window.ethereum.on("chainChanged", () => refreshAll(false));
    }
    refreshTimer = window.setInterval(() => refreshAll(false), 12000);
  }
  await refreshAll(false);
}

async function refreshAll(withToast = false) {
  state.refreshing = true;
  try {
    await syncMetaMaskAccount(false);
    await hydrateMetaMaskSession();

    const [health, runtime, wallets, agents, listings, runs, schedules, runMetrics, runtimeLogs] = await Promise.all([
      api("/health", { skipAuth: true }),
      api("/runtime/config", { skipAuth: true }),
      api("/wallets", { skipAuth: true }),
      api("/agents", { skipAuth: true }),
      api("/listings", { skipAuth: true }),
      api("/runs", { skipAuth: true }),
      api("/agent-schedules", { skipAuth: true }),
      api("/runs/metrics", { skipAuth: true }),
      api("/runtime/logs?limit=25", { skipAuth: true }),
    ]);

    state.health = health;
    state.runtime = runtime;
    state.wallets = wallets;
    state.agents = agents;
    state.listings = listings;
    state.runs = runs;
    state.schedules = schedules;
    state.runMetrics = runMetrics;
    state.runtimeLogs = runtimeLogs;

    hydrateWalletFromRegistry();
    syncMarketplaceSelection();
    if (state.drawer.open && state.drawer.agentId) {
      await hydrateAgentDrawer({ agentId: state.drawer.agentId, silent: true, loading: false });
    }
    if (withToast) {
      showFlash("Data refreshed.", "success");
    }
  } catch (error) {
    showFlash(error.message, "error");
    throw error;
  } finally {
    state.refreshing = false;
  }
}

async function api(path, options = {}) {
  const { skipAuth = false, headers: extraHeaders = {}, ...fetchOptions } = options;
  const headers = { ...(fetchOptions.body !== undefined ? { "Content-Type": "application/json" } : {}), ...extraHeaders };

  if (!skipAuth && state.metamask.token) {
    headers.Authorization = `Bearer ${state.metamask.token}`;
  }

  const response = await fetch(`${API_PREFIX}${path}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const payload = await safeJson(response);
    throw new Error(payload.detail || `Request failed with ${response.status}`);
  }
  return safeJson(response);
}

async function safeJson(response) {
  const text = await response.text();
  return text ? JSON.parse(text) : {};
}

function persistSession() {
  if (!state.metamask.token || !state.metamask.sessionAddress) {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(
    AUTH_STORAGE_KEY,
    JSON.stringify({
      chain_address: state.metamask.sessionAddress,
      token: state.metamask.token,
    })
  );
}

function clearMetaMaskSession({ keepWallet = true } = {}) {
  state.metamask.token = null;
  state.metamask.sessionAddress = null;
  state.metamask.authenticated = false;
  if (!keepWallet) {
    state.metamask.wallet = null;
  }
  persistSession();
}

function applyConnectedAccount(address, chainId) {
  const normalizedAddress = address ? address.toLowerCase() : null;
  const addressChanged = state.metamask.address && state.metamask.address !== normalizedAddress;

  state.metamask.available = true;
  state.metamask.address = normalizedAddress;
  state.metamask.chainId = chainId;

  if (!normalizedAddress) {
    clearMetaMaskSession({ keepWallet: false });
    return;
  }

  if (addressChanged || (state.metamask.sessionAddress && state.metamask.sessionAddress !== normalizedAddress)) {
    clearMetaMaskSession({ keepWallet: false });
  }
}

async function connectMetaMask(showToastFlag = false) {
  if (!window.ethereum) {
    state.metamask.available = false;
    throw new Error("MetaMask not found in this browser.");
  }

  const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
  const chainId = await window.ethereum.request({ method: "eth_chainId" });
  applyConnectedAccount(accounts?.[0] || null, chainId);
  if (showToastFlag) {
    showFlash("MetaMask connected.", "success");
  }
}

async function syncMetaMaskAccount(showToastFlag = false) {
  if (!window.ethereum) {
    state.metamask.available = false;
    state.metamask.address = null;
    state.metamask.chainId = null;
    clearMetaMaskSession({ keepWallet: false });
    return;
  }

  const accounts = await window.ethereum.request({ method: "eth_accounts" });
  const chainId = await window.ethereum.request({ method: "eth_chainId" });
  applyConnectedAccount(accounts?.[0] || null, chainId);
  if (showToastFlag && state.metamask.address) {
    showFlash("MetaMask account switched.", "success");
  }
}

async function hydrateMetaMaskSession() {
  if (!state.metamask.address || !state.metamask.token) {
    state.metamask.authenticated = false;
    return;
  }

  if (state.metamask.sessionAddress && state.metamask.sessionAddress !== state.metamask.address) {
    clearMetaMaskSession({ keepWallet: false });
    return;
  }

  try {
    const wallet = await api("/auth/me");
    state.metamask.wallet = wallet;
    state.metamask.authenticated = true;
    state.metamask.sessionAddress = state.metamask.address;
    persistSession();
  } catch {
    clearMetaMaskSession();
  }
}

function hydrateWalletFromRegistry() {
  if (!state.metamask.address) {
    if (!state.metamask.authenticated) {
      state.metamask.wallet = null;
    }
    return;
  }

  const mappedWallet = state.wallets.find((wallet) => wallet.chain_address === state.metamask.address) || null;

  if (state.metamask.authenticated) {
    state.metamask.wallet = mappedWallet || state.metamask.wallet;
    return;
  }

  state.metamask.wallet = mappedWallet;
}

async function authenticateMetaMask({ force = false, label = null, initialBalance = "0", withRefresh = false } = {}) {
  if (!state.metamask.address) {
    await connectMetaMask(false);
  }

  if (!window.ethereum || !state.metamask.address) {
    throw new Error("MetaMask connection is required.");
  }

  if (state.metamask.authenticated && state.metamask.token && !force) {
    return state.metamask.wallet;
  }

  const challenge = await api("/auth/metamask/challenge", {
    method: "POST",
    body: JSON.stringify({
      chain_address: state.metamask.address,
      chain_id: state.metamask.chainId,
      initial_balance: initialBalance,
      label,
    }),
    skipAuth: true,
  });

  const signature = await window.ethereum.request({
    method: "personal_sign",
    params: [challenge.message, state.metamask.address],
  });

  const session = await api("/auth/metamask/verify", {
    method: "POST",
    body: JSON.stringify({
      chain_address: state.metamask.address,
      signature,
    }),
    skipAuth: true,
  });

  state.metamask.token = session.access_token;
  state.metamask.sessionAddress = session.chain_address;
  state.metamask.wallet = session.wallet;
  state.metamask.authenticated = true;
  persistSession();

  if (withRefresh) {
    await refreshAll(false);
  }
  showFlash("MetaMask authenticated and runtime wallet synced.", "success");
  return session.wallet;
}

async function ensureMetaMaskSession({ initialBalance = "0", label = null } = {}) {
  if (state.metamask.authenticated && state.metamask.token) {
    return state.metamask.wallet;
  }
  return authenticateMetaMask({
    initialBalance,
    label,
    withRefresh: true,
  });
}

async function logoutMetaMask(showToastFlag = false) {
  if (state.metamask.token) {
    try {
      await api("/auth/logout", { method: "POST" });
    } catch {
      // Ignore logout failure.
    }
  }
  clearMetaMaskSession();
  if (showToastFlag) {
    showFlash("MetaMask session cleared.", "success");
  }
}

async function runMutation(action, successMessage) {
  try {
    await action();
    await refreshAll(false);
    showFlash(successMessage, "success");
  } catch (error) {
    showFlash(error.message, "error");
    throw error;
  }
}

async function createAgent(payload) {
  return runMutation(async () => {
    await ensureMetaMaskSession();
    await api("/agents", {
      method: "POST",
      body: JSON.stringify({
        ...payload,
        seed_memory: [],
      }),
    });
  }, "Agent minted with ownership NFT.");
}

async function queueRun({ agentId, task, maxAttempts = null, timeoutSeconds = null }) {
  return runMutation(async () => {
    await ensureMetaMaskSession();
    const payload = { task };
    if (maxAttempts) {
      payload.max_attempts = Number(maxAttempts);
    }
    if (timeoutSeconds) {
      payload.timeout_seconds = Number(timeoutSeconds);
    }
    await api(`/agents/${agentId}/run`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }, "Run queued.");
}

async function retryRun(runId) {
  return runMutation(async () => {
    await ensureMetaMaskSession();
    await api(`/runs/${runId}/retry`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }, "Run retry queued.");
}

async function cancelRun(runId) {
  return runMutation(async () => {
    await ensureMetaMaskSession();
    await api(`/runs/${runId}/cancel`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }, "Run cancellation submitted.");
}

async function openListing(payload) {
  return runMutation(async () => {
    await ensureMetaMaskSession();
    const agent = resolveAgentByTokenId(payload.token_id);
    if (!agent) {
      throw new Error("Selected NFT is missing from the current dashboard state.");
    }
    if (shouldUseOnChainListing(agent.nft)) {
      await openOnChainListing(agent, payload.price);
      return;
    }
    await api("/listings", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }, "Listing opened.");
}

async function buyListing(listingId) {
  return runMutation(async () => {
    await ensureMetaMaskSession();
    const listing = findListingById(listingId);
    if (!listing) {
      throw new Error("Selected listing is missing from the current dashboard state.");
    }
    if (listing.market_mode === "ONCHAIN" && listing.chain?.chain_listing_id) {
      await buyOnChainListing(listing);
      return;
    }
    await api(`/listings/${listingId}/buy`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }, "Listing purchased.");
}

async function createSchedule(payload) {
  return runMutation(async () => {
    await ensureMetaMaskSession();
    await api("/agent-schedules", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }, "Schedule created.");
}

function syncMarketplaceSelection() {
  if (!state.listings.length) {
    state.marketplace.selectedListingId = null;
    return;
  }

  const selectedStillExists = state.listings.some((listing) => listing.id === state.marketplace.selectedListingId);
  if (!selectedStillExists) {
    state.marketplace.selectedListingId = state.listings[0].id;
  }
}

function setMarketplacePendingTx(payload) {
  state.marketplace.pendingTx = payload;
}

function focusListing(listingId) {
  state.marketplace.selectedListingId = listingId;
}

function findAgentById(agentId) {
  return state.agents.find((item) => item.id === agentId) || null;
}

function findListingById(listingId) {
  return state.listings.find((item) => item.id === listingId) || null;
}

function findRunById(runId) {
  return state.runs.find((item) => item.id === runId) || null;
}

function findScheduleById(scheduleId) {
  return state.schedules.find((item) => item.id === scheduleId) || null;
}

function resolveAgentByTokenId(tokenId) {
  return state.agents.find((item) => item.nft.token_id === tokenId) || null;
}

function resolveWalletById(walletId) {
  return state.wallets.find((item) => item.id === walletId) || null;
}

async function openAgentDrawer(agentId) {
  const agent = findAgentById(agentId);
  if (!agent) {
    throw new Error("Selected agent is no longer available.");
  }

  state.drawer.open = true;
  state.drawer.agentId = agentId;
  state.drawer.metadata = null;
  state.drawer.runs = [];
  state.drawer.error = null;
  state.drawer.loading = true;
  state.drawer.expandedRunIds = [];
  await hydrateAgentDrawer({ agentId, silent: false, loading: true });
}

function closeAgentDrawer() {
  state.drawer.open = false;
  state.drawer.loading = false;
  state.drawer.error = null;
  state.drawer.expandedRunIds = [];
}

async function hydrateAgentDrawer({ agentId = state.drawer.agentId, silent = false, loading = true } = {}) {
  const agent = findAgentById(agentId);
  if (!agent) {
    state.drawer.error = "Selected agent no longer exists in the current runtime state.";
    state.drawer.loading = false;
    return;
  }

  const requestNonce = state.drawer.requestNonce + 1;
  state.drawer.requestNonce = requestNonce;
  state.drawer.agentId = agentId;
  if (loading) {
    state.drawer.loading = true;
  }
  if (!silent) {
    state.drawer.error = null;
  }

  try {
    const { runs, metadata } = await fetchAgentDetail(agentId);

    if (requestNonce !== state.drawer.requestNonce) {
      return;
    }

    state.drawer.runs = [...runs].sort(sortRunsByStartedAtDesc);
    state.drawer.metadata = metadata;
    state.drawer.error = null;
  } catch (error) {
    if (requestNonce !== state.drawer.requestNonce) {
      return;
    }
    state.drawer.error = error.message;
    if (!silent) {
      showFlash(error.message, "error");
    }
  } finally {
    if (requestNonce !== state.drawer.requestNonce) {
      return;
    }
    state.drawer.loading = false;
  }
}

async function fetchAgentDetail(agentId) {
  const agent = findAgentById(agentId);
  if (!agent) {
    throw new Error("Selected agent is no longer available.");
  }

  const [runs, metadata] = await Promise.all([
    api(`/agents/${agentId}/runs`, { skipAuth: true }),
    api(`/nfts/${agent.nft.token_id}/metadata`, { skipAuth: true }),
  ]);

  return {
    runs: [...runs].sort(sortRunsByStartedAtDesc),
    metadata,
  };
}

async function fetchListingDetail(listingId) {
  const [listing, events, transactions] = await Promise.all([
    api(`/listings/${listingId}`, { skipAuth: true }),
    api(`/listings/${listingId}/events`, { skipAuth: true }),
    api(`/listings/${listingId}/transactions`, { skipAuth: true }),
  ]);

  const index = state.listings.findIndex((item) => item.id === listing.id);
  if (index >= 0) {
    state.listings.splice(index, 1, listing);
  } else {
    state.listings.unshift(listing);
  }

  return {
    listing,
    events,
    transactions,
  };
}

function toggleDrawerRunExpansion(runId) {
  if (!runId) {
    return;
  }

  if (state.drawer.expandedRunIds.includes(runId)) {
    state.drawer.expandedRunIds = state.drawer.expandedRunIds.filter((item) => item !== runId);
  } else {
    state.drawer.expandedRunIds = [...state.drawer.expandedRunIds, runId];
  }
}

function showFlash(message, type) {
  state.flash.visible = true;
  state.flash.message = message;
  state.flash.type = type;
  window.clearTimeout(flashTimer);
  flashTimer = window.setTimeout(() => {
    state.flash.visible = false;
  }, 3200);
}

function truncate(value, length) {
  const normalized = String(value ?? "");
  return normalized.length > length ? `${normalized.slice(0, length - 3)}...` : normalized;
}

function formatDateTime(value) {
  if (!value) {
    return "Pending";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

function formatRunOutput(output) {
  if (!output) {
    return "No output recorded yet.";
  }
  if (typeof output === "string") {
    return output;
  }
  return JSON.stringify(output, null, 2);
}

function isTerminalRun(run) {
  return ["COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"].includes(run?.status);
}

function isDeadLettered(run) {
  return Boolean(run?.dead_lettered_at);
}

function formatRunDuration(run) {
  if (!run?.started_at || !run?.finished_at) {
    return run?.status === "RUNNING" ? "In progress" : "Pending";
  }
  const durationMs = Date.parse(run.finished_at) - Date.parse(run.started_at);
  if (!Number.isFinite(durationMs) || durationMs <= 0) {
    return "Under 1s";
  }
  const totalSeconds = Math.round(durationMs / 1000);
  if (totalSeconds < 60) {
    return `${totalSeconds}s`;
  }
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return seconds ? `${minutes}m ${seconds}s` : `${minutes}m`;
}

function describeWallet(walletId) {
  const wallet = state.wallets.find((item) => item.id === walletId);
  if (!wallet) {
    return walletId;
  }
  return wallet.chain_address || wallet.name || wallet.id;
}

function formatSyncMode(syncMode) {
  if (syncMode === "CHAIN_SYNCED") {
    return "CHAIN_SYNCED";
  }
  if (syncMode === "CHAIN_MAPPED_INACTIVE") {
    return "CHAIN_MAPPED_INACTIVE";
  }
  return "LOCAL_ONLY";
}

function normalizeChainAddress(value) {
  if (!value) {
    return null;
  }
  const normalized = String(value).trim().toLowerCase();
  return /^0x[a-f0-9]{40}$/.test(normalized) ? normalized : null;
}

function normalizeHex(value) {
  if (!value) {
    return null;
  }
  return String(value).trim().toLowerCase();
}

function hexPad(value, size = 64) {
  return value.replace(/^0x/, "").padStart(size, "0");
}

function encodeAddress(value) {
  const normalized = normalizeChainAddress(value);
  if (!normalized) {
    throw new Error("Invalid chain address.");
  }
  return hexPad(normalized);
}

function encodeUint256(value) {
  try {
    return BigInt(value).toString(16).padStart(64, "0");
  } catch {
    throw new Error("Invalid on-chain token id.");
  }
}

function decimalToWei(value, decimals = 18) {
  const normalized = String(value ?? "").trim();
  if (!/^\d+(\.\d+)?$/.test(normalized)) {
    throw new Error("Invalid listing price.");
  }
  const [wholePart, fractionPart = ""] = normalized.split(".");
  if (fractionPart.length > decimals) {
    throw new Error(`Price supports up to ${decimals} decimal places.`);
  }
  const whole = BigInt(wholePart || "0") * 10n ** BigInt(decimals);
  const fraction = BigInt((fractionPart + "0".repeat(decimals)).slice(0, decimals) || "0");
  return (whole + fraction).toString();
}

function buildSafeTransferFromData(fromAddress, toAddress, tokenId) {
  return `0x42842e0e${encodeAddress(fromAddress)}${encodeAddress(toAddress)}${encodeUint256(tokenId)}`;
}

function buildApproveData(spenderAddress, tokenId) {
  return `0x095ea7b3${encodeAddress(spenderAddress)}${encodeUint256(tokenId)}`;
}

function buildCreateListingData(tokenId, priceWei) {
  return `0xa79123a9${encodeUint256(tokenId)}${encodeUint256(priceWei)}`;
}

function buildBuyListingData(chainListingId) {
  return `0x4884f459${encodeUint256(chainListingId)}`;
}

function buildCancelListingData(chainListingId) {
  return `0x305a67a8${encodeUint256(chainListingId)}`;
}

function shouldUseOnChainTransfer(nft) {
  const runtimeContract = normalizeChainAddress(state.runtime?.nft_contract_address);
  const nftContract = normalizeChainAddress(nft.contract_address);
  return Boolean(
    state.runtime?.chain_sync_enabled &&
      runtimeContract &&
      nftContract &&
      runtimeContract === nftContract &&
      nft.chain_token_id
  );
}

function shouldUseOnChainListing(nft) {
  const runtimeNftContract = normalizeChainAddress(state.runtime?.nft_contract_address);
  const runtimeMarketContract = normalizeChainAddress(state.runtime?.marketplace_contract_address);
  const nftContract = normalizeChainAddress(nft.contract_address);
  return Boolean(
    state.runtime?.market_sync_enabled &&
      runtimeMarketContract &&
      runtimeNftContract &&
      nftContract &&
      runtimeNftContract === nftContract &&
      nft.chain_token_id
  );
}

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function waitForTransactionReceipt(txHash, timeoutMs = 120000, pollMs = 2500) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const receipt = await window.ethereum.request({
      method: "eth_getTransactionReceipt",
      params: [txHash],
    });
    if (receipt) {
      if (receipt.status === "0x1") {
        return receipt;
      }
      throw new Error(`Transaction reverted: ${txHash}`);
    }
    await sleep(pollMs);
  }
  throw new Error(`Timed out waiting for transaction receipt: ${txHash}`);
}

async function waitForChainSync(tokenId, txHash, timeoutMs = 90000, pollMs = 3000) {
  const deadline = Date.now() + timeoutMs;
  const expectedHash = normalizeHex(txHash);
  while (Date.now() < deadline) {
    await sleep(pollMs);
    const nft = await api(`/nfts/${tokenId}`, { skipAuth: true });
    if (normalizeHex(nft.last_synced_tx_hash) === expectedHash) {
      return nft;
    }
  }
  return null;
}

function matchesListingTx(listing, txHash, expectedStatus) {
  const normalizedTx = normalizeHex(txHash);
  if (!normalizedTx || listing.status !== expectedStatus) {
    return false;
  }
  return (
    normalizeHex(listing.chain?.open_tx_hash) === normalizedTx ||
    normalizeHex(listing.chain?.close_tx_hash) === normalizedTx
  );
}

async function waitForListingSync(txHash, expectedStatus = "OPEN", timeoutMs = 120000, pollMs = 3000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    await sleep(pollMs);
    const listings = await api("/listings", { skipAuth: true });
    const matched = listings.find((listing) => matchesListingTx(listing, txHash, expectedStatus));
    if (matched) {
      return matched;
    }
  }
  return null;
}

async function openOnChainListing(agent, displayPrice) {
  if (!window.ethereum || !state.metamask.address) {
    throw new Error("MetaMask connection is required for on-chain listings.");
  }

  const marketAddress = normalizeChainAddress(state.runtime?.marketplace_contract_address);
  const ownerWallet = resolveWalletById(agent.nft.owner_wallet_id);
  const ownerAddress = normalizeChainAddress(ownerWallet?.chain_address);
  if (!marketAddress) {
    throw new Error("Marketplace contract is not configured in the runtime.");
  }
  if (!ownerAddress || ownerAddress !== normalizeChainAddress(state.metamask.address)) {
    throw new Error("The connected MetaMask account is not the current on-chain owner for this NFT.");
  }

  const approveTxHash = await window.ethereum.request({
    method: "eth_sendTransaction",
    params: [
      {
        from: state.metamask.address,
        to: agent.nft.contract_address,
        data: buildApproveData(marketAddress, agent.nft.chain_token_id),
      },
    ],
  });
  setMarketplacePendingTx({ kind: "APPROVAL", status: "PENDING", txHash: approveTxHash, tokenId: agent.nft.token_id });
  showFlash(`Approval submitted ${approveTxHash.slice(0, 10)}...`, "success");
  await waitForTransactionReceipt(approveTxHash);

  const priceWei = decimalToWei(displayPrice);
  const listingTxHash = await window.ethereum.request({
    method: "eth_sendTransaction",
    params: [
      {
        from: state.metamask.address,
        to: marketAddress,
        data: buildCreateListingData(agent.nft.chain_token_id, priceWei),
      },
    ],
  });
  setMarketplacePendingTx({ kind: "OPEN_LISTING", status: "PENDING", txHash: listingTxHash, tokenId: agent.nft.token_id });
  showFlash(`Listing submitted ${listingTxHash.slice(0, 10)}... Waiting for listener sync.`, "success");
  await waitForTransactionReceipt(listingTxHash);
  const synced = await waitForListingSync(listingTxHash, "OPEN");
  setMarketplacePendingTx({
    kind: "OPEN_LISTING",
    status: synced ? "CONFIRMED" : "SYNC_PENDING",
    txHash: listingTxHash,
    tokenId: agent.nft.token_id,
  });
}

async function buyOnChainListing(listing) {
  if (!window.ethereum || !state.metamask.address) {
    throw new Error("MetaMask connection is required for on-chain purchases.");
  }
  const marketAddress = normalizeChainAddress(state.runtime?.marketplace_contract_address);
  if (!marketAddress) {
    throw new Error("Marketplace contract is not configured in the runtime.");
  }

  const txHash = await window.ethereum.request({
    method: "eth_sendTransaction",
    params: [
      {
        from: state.metamask.address,
        to: marketAddress,
        data: buildBuyListingData(listing.chain.chain_listing_id),
        value: `0x${BigInt(listing.chain.price_wei).toString(16)}`,
      },
    ],
  });
  setMarketplacePendingTx({ kind: "BUY_LISTING", status: "PENDING", txHash, listingId: listing.id });
  showFlash(`Purchase submitted ${txHash.slice(0, 10)}... Waiting for listener sync.`, "success");
  await waitForTransactionReceipt(txHash);
  const synced = await waitForListingSync(txHash, "SOLD");
  setMarketplacePendingTx({
    kind: "BUY_LISTING",
    status: synced ? "CONFIRMED" : "SYNC_PENDING",
    txHash,
    listingId: listing.id,
  });
}

async function cancelOnChainListing(listing) {
  if (!window.ethereum || !state.metamask.address) {
    throw new Error("MetaMask connection is required for on-chain listing cancellation.");
  }
  const marketAddress = normalizeChainAddress(state.runtime?.marketplace_contract_address);
  if (!marketAddress) {
    throw new Error("Marketplace contract is not configured in the runtime.");
  }

  const sellerWallet = resolveWalletById(listing.seller_wallet_id);
  const sellerAddress = normalizeChainAddress(sellerWallet?.chain_address);
  if (!sellerAddress || sellerAddress !== normalizeChainAddress(state.metamask.address)) {
    throw new Error("The connected MetaMask account is not the current listing seller.");
  }

  const txHash = await window.ethereum.request({
    method: "eth_sendTransaction",
    params: [
      {
        from: state.metamask.address,
        to: marketAddress,
        data: buildCancelListingData(listing.chain.chain_listing_id),
      },
    ],
  });
  setMarketplacePendingTx({ kind: "CANCEL_LISTING", status: "PENDING", txHash, listingId: listing.id });
  showFlash(`Cancel submitted ${txHash.slice(0, 10)}... Waiting for listener sync.`, "success");
  await waitForTransactionReceipt(txHash);
  const synced = await waitForListingSync(txHash, "CANCELLED");
  setMarketplacePendingTx({
    kind: "CANCEL_LISTING",
    status: synced ? "CONFIRMED" : "SYNC_PENDING",
    txHash,
    listingId: listing.id,
  });
}

async function cancelListing(listingId) {
  return runMutation(async () => {
    await ensureMetaMaskSession();
    const listing = findListingById(listingId);
    if (!listing) {
      throw new Error("Selected listing is missing from the current dashboard state.");
    }
    if (listing.market_mode === "ONCHAIN" && listing.chain?.chain_listing_id) {
      await cancelOnChainListing(listing);
      return;
    }
    await api(`/listings/${listingId}/cancel`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }, "Listing cancelled.");
}

async function transferNft(tokenId, toChainAddress) {
  return runMutation(async () => {
    const agent = resolveAgentByTokenId(tokenId);
    if (!agent) {
      throw new Error("Selected NFT is missing from the current dashboard state.");
    }

    const targetAddress = normalizeChainAddress(toChainAddress);
    if (!targetAddress) {
      throw new Error("A valid destination chain address is required.");
    }

    if (shouldUseOnChainTransfer(agent.nft)) {
      if (!window.ethereum || !state.metamask.address) {
        throw new Error("MetaMask connection is required for chain transfers.");
      }

      const ownerWallet = resolveWalletById(agent.nft.owner_wallet_id);
      const ownerAddress = normalizeChainAddress(ownerWallet?.chain_address);
      if (!ownerAddress || ownerAddress !== normalizeChainAddress(state.metamask.address)) {
        throw new Error("The connected MetaMask account is not the current on-chain owner for this NFT.");
      }

      const txHash = await window.ethereum.request({
        method: "eth_sendTransaction",
        params: [
          {
            from: state.metamask.address,
            to: agent.nft.contract_address,
            data: buildSafeTransferFromData(state.metamask.address, targetAddress, agent.nft.chain_token_id),
          },
        ],
      });

      showFlash(`Chain transfer submitted ${txHash.slice(0, 10)}... Waiting for listener sync.`, "success");
      await waitForChainSync(tokenId, txHash);
      return;
    }

    await ensureMetaMaskSession();
    await api(`/nfts/${tokenId}/transfer`, {
      method: "POST",
      body: JSON.stringify({ to_chain_address: targetAddress }),
    });
  }, "NFT transfer submitted.");
}

function getTokenMetadataUrl(tokenId) {
  return `${window.location.origin}${API_PREFIX}/nfts/${tokenId}/metadata`;
}

function getTokenImageUrl(tokenId) {
  return `${window.location.origin}${API_PREFIX}/nfts/${tokenId}/image.svg`;
}

async function copyText(value) {
  if (!value) {
    throw new Error("Nothing to copy.");
  }

  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }

  const textArea = document.createElement("textarea");
  textArea.value = value;
  textArea.setAttribute("readonly", "");
  textArea.style.position = "absolute";
  textArea.style.left = "-9999px";
  document.body.appendChild(textArea);
  textArea.select();
  document.execCommand("copy");
  document.body.removeChild(textArea);
}

function sortRunsByStartedAtDesc(left, right) {
  const leftTime = Date.parse(left.started_at || 0);
  const rightTime = Date.parse(right.started_at || 0);
  return rightTime - leftTime;
}

export function useRuntimeStore() {
  return {
    state,
    queuedRuns,
    runningRuns,
    completedRuns,
    authenticated,
    selectedListing,
    initialize,
    refreshAll,
    connectMetaMask,
    authenticateMetaMask,
    logoutMetaMask,
    createAgent,
    queueRun,
    retryRun,
    cancelRun,
    openListing,
    buyListing,
    cancelListing,
    createSchedule,
    transferNft,
    shouldUseOnChainListing,
    focusListing,
    openAgentDrawer,
    closeAgentDrawer,
    fetchAgentDetail,
    fetchListingDetail,
    toggleDrawerRunExpansion,
    findAgentById,
    findListingById,
    findRunById,
    findScheduleById,
    resolveWalletById,
    describeWallet,
    formatSyncMode,
    truncate,
    formatDateTime,
    formatRunOutput,
    formatRunDuration,
    isTerminalRun,
    isDeadLettered,
    getTokenMetadataUrl,
    getTokenImageUrl,
    copyText,
    showFlash,
  };
}

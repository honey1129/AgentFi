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

const storedSession = loadStoredSession();
const PAGE_CONFIG = {
  launchpad: {
    title: "AgentFi Runtime Workspace",
    eyebrow: "Agent Ownership Runtime",
    headline: "Agent Ownership Workspace",
    lede: "把 MetaMask 登录、agent 创建和 ownership NFT 铸造收进同一块 launchpad。",
    missionKicker: "Launchpad",
    missionTitle: "先完成登录、钱包同步和 agent 初始化，再进入后续的 market 或 execution 工作流。",
    workspaceKicker: "Bootstrap",
    workspaceTitle: "从 launchpad 开始，把 runtime operator 和初始 agent 配置起来。",
    workspaceDescription: "这一页只保留初始化动作，让登录、钱包同步和 agent 创建形成一个顺手的起点。",
  },
  wallets: {
    title: "Wallets · AgentFi Runtime Workspace",
    eyebrow: "Wallet Registry",
    headline: "Wallet Workspace",
    lede: "集中查看 runtime wallet、链上映射和本地撮合余额。",
    missionKicker: "Registry",
    missionTitle: "这一页只看 wallet registry，让 operator、chain address 和余额关系更清楚。",
    workspaceKicker: "Wallets",
    workspaceTitle: "把所有 wallet 身份和链上映射放到一个独立视图里。",
    workspaceDescription: "这里没有交易和运行表单，重点是核对当前签名钱包、本地 runtime wallet 和链上映射关系。",
  },
  agents: {
    title: "Agents · AgentFi Runtime Workspace",
    eyebrow: "Agent Registry",
    headline: "Agent Ownership Workspace",
    lede: "查看 agent、owner、NFT 映射和链上同步模式，并从详情抽屉继续深入。",
    missionKicker: "Ownership",
    missionTitle: "专门查看 agent 和 ownership NFT 的绑定关系，而不是把交易和执行信息混在一屏里。",
    workspaceKicker: "Agents",
    workspaceTitle: "把 agent、owner 和 NFT 状态拆成独立页面。",
    workspaceDescription: "这一页适合核对 agent 的控制权、同步模式和 prompt，而不是直接做 market 或 run 操作。",
  },
  market: {
    title: "Market · AgentFi Runtime Workspace",
    eyebrow: "Ownership Market",
    headline: "Marketplace Workspace",
    lede: "把挂牌、购买、转移和当前 ownership NFT 流动性拆到单独的 market 页面。",
    missionKicker: "Market",
    missionTitle: "这一页专门处理 listing、持有人变化和链上映射，不再和其他操作混在同一块表单里。",
    workspaceKicker: "Trade",
    workspaceTitle: "把 market 动作和市场面板聚合到同一路由。",
    workspaceDescription: "在这里完成挂牌、购买和转移，同时对照当前 listing、seller、holder 和 chain state。",
  },
  runs: {
    title: "Runs · AgentFi Runtime Workspace",
    eyebrow: "Execution Workspace",
    headline: "Run Queue Workspace",
    lede: "把 queue run、schedule 和执行历史拆到单独的 execution 页面。",
    missionKicker: "Execution",
    missionTitle: "专门查看队列、运行状态和 schedule，不再在同一页里穿插 market 操作。",
    workspaceKicker: "Run Ops",
    workspaceTitle: "把调度动作和执行回放放在一起。",
    workspaceDescription: "这里适合发起 run、配置 schedule，并直接对照 queued、running、completed 的回放结果。",
  },
};

const state = {
  ui: {
    route: resolveRoute(window.location.pathname),
    routeIntentApplied: false,
  },
  health: null,
  runtime: null,
  wallets: [],
  agents: [],
  listings: [],
  runs: [],
  schedules: [],
  marketplace: {
    selectedListingId: null,
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
  metamask: {
    available: typeof window.ethereum !== "undefined",
    address: null,
    chainId: null,
    wallet: null,
    token: storedSession?.token || null,
    sessionAddress: storedSession?.chain_address || null,
    authenticated: false,
  },
};

const refs = {
  pageEyebrow: document.getElementById("page-eyebrow"),
  pageTitle: document.getElementById("page-title"),
  pageLede: document.getElementById("page-lede"),
  missionKicker: document.getElementById("mission-kicker"),
  missionTitle: document.getElementById("mission-title"),
  topbarNote: document.getElementById("topbar-note"),
  healthPill: document.getElementById("health-pill"),
  walletPill: document.getElementById("wallet-pill"),
  walletAddress: document.getElementById("wallet-address"),
  walletRuntimeId: document.getElementById("wallet-runtime-id"),
  walletSession: document.getElementById("wallet-session"),
  runtimeChain: document.getElementById("runtime-chain"),
  runtimeMint: document.getElementById("runtime-mint"),
  lastRefresh: document.getElementById("last-refresh"),
  missionSummary: document.getElementById("mission-summary"),
  signalAuthCard: document.getElementById("signal-auth-card"),
  signalAuthTitle: document.getElementById("signal-auth-title"),
  signalAuthDetail: document.getElementById("signal-auth-detail"),
  signalChainCard: document.getElementById("signal-chain-card"),
  signalChainTitle: document.getElementById("signal-chain-title"),
  signalChainDetail: document.getElementById("signal-chain-detail"),
  signalMarketCard: document.getElementById("signal-market-card"),
  signalMarketTitle: document.getElementById("signal-market-title"),
  signalMarketDetail: document.getElementById("signal-market-detail"),
  signalQueueCard: document.getElementById("signal-queue-card"),
  signalQueueTitle: document.getElementById("signal-queue-title"),
  signalQueueDetail: document.getElementById("signal-queue-detail"),
  flash: document.getElementById("flash"),
  walletsGrid: document.getElementById("wallets-grid"),
  marketplaceBoard: document.getElementById("marketplace-board"),
  agentsGrid: document.getElementById("agents-grid"),
  listingsGrid: document.getElementById("listings-grid"),
  runsTable: document.getElementById("runs-table"),
  schedulesGrid: document.getElementById("schedules-grid"),
  statWallets: document.getElementById("stat-wallets"),
  statAgents: document.getElementById("stat-agents"),
  statListings: document.getElementById("stat-listings"),
  statQueued: document.getElementById("stat-queued"),
  workspaceKicker: document.getElementById("workspace-kicker"),
  workspaceTitle: document.getElementById("workspace-title"),
  workspaceDescription: document.getElementById("workspace-description"),
  workspaceOperator: document.getElementById("workspace-operator"),
  workspaceMintState: document.getElementById("workspace-mint-state"),
  workspaceMarketState: document.getElementById("workspace-market-state"),
  walletsPanelCount: document.getElementById("wallets-panel-count"),
  agentsPanelCount: document.getElementById("agents-panel-count"),
  marketPanelCount: document.getElementById("market-panel-count"),
  runsPanelCount: document.getElementById("runs-panel-count"),
  schedulesPanelCount: document.getElementById("schedules-panel-count"),
  drawer: document.getElementById("agent-drawer"),
  drawerBackdrop: document.getElementById("agent-drawer-backdrop"),
  drawerCloseButton: document.getElementById("drawer-close-button"),
  drawerAgentName: document.getElementById("drawer-agent-name"),
  drawerAgentMeta: document.getElementById("drawer-agent-meta"),
  drawerBody: document.getElementById("drawer-body"),
};

const forms = {
  walletConnect: document.getElementById("wallet-connect-form"),
  agent: document.getElementById("agent-form"),
  run: document.getElementById("run-form"),
  listing: document.getElementById("listing-form"),
  buy: document.getElementById("buy-form"),
  transfer: document.getElementById("transfer-form"),
  schedule: document.getElementById("schedule-form"),
};

document.getElementById("refresh-button").addEventListener("click", () => refreshAll(true));
document.getElementById("metamask-connect-button").addEventListener("click", () => connectMetaMask(true));
document.getElementById("metamask-logout-button").addEventListener("click", () => logoutMetaMask(true));
refs.drawerCloseButton.addEventListener("click", () => closeAgentDrawer());
refs.drawerBackdrop.addEventListener("click", () => closeAgentDrawer());

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && state.drawer.open) {
    closeAgentDrawer();
  }
});

refs.drawerBody.addEventListener("click", async (event) => {
  const actionButton = event.target.closest("[data-drawer-action]");
  if (!actionButton) {
    return;
  }

  const { drawerAction, value } = actionButton.dataset;
  if (drawerAction === "copy-token-uri") {
    try {
      await copyText(value || "");
      showFlash("tokenURI copied.", "success");
    } catch (error) {
      showFlash(error.message, "error");
    }
  }

  if (drawerAction === "toggle-run-output") {
    toggleDrawerRunExpansion(value);
  }
});

forms.walletConnect.addEventListener("submit", (event) =>
  handleSubmit(
    event,
    async () => {
      await authenticateMetaMask({
        force: true,
        initialBalance: forms.walletConnect.elements.initial_balance.value || "0",
        label: forms.walletConnect.elements.label.value || null,
      });
    },
    "MetaMask authenticated and runtime wallet synced."
  )
);

forms.agent.addEventListener("submit", (event) =>
  handleSubmit(
    event,
    async () => {
      await ensureMetaMaskSession();
      const payload = formToJson(forms.agent, ["name", "description", "system_prompt", "contract_address", "chain_token_id"]);
      payload.seed_memory = [];
      payload.contract_address = payload.contract_address || null;
      payload.chain_token_id = payload.chain_token_id || null;
      await api("/agents", { method: "POST", body: JSON.stringify(payload) });
      forms.agent.reset();
    },
    "Agent minted with ownership NFT."
  )
);

forms.run.addEventListener("submit", (event) =>
  handleSubmit(
    event,
    async () => {
      await ensureMetaMaskSession();
      const payload = formToJson(forms.run, ["task"]);
      const agentId = forms.run.elements.agent_id.value;
      await api(`/agents/${agentId}/run`, { method: "POST", body: JSON.stringify(payload) });
      forms.run.elements.task.value = "";
    },
    "Run queued."
  )
);

forms.listing.addEventListener("submit", (event) =>
  handleSubmit(
    event,
    async () => {
      await ensureMetaMaskSession();
      const payload = formToJson(forms.listing, ["token_id", "price"]);
      await api("/listings", { method: "POST", body: JSON.stringify(payload) });
    },
    "Listing opened."
  )
);

forms.buy.addEventListener("submit", (event) =>
  handleSubmit(
    event,
    async () => {
      await ensureMetaMaskSession();
      const listingId = forms.buy.elements.listing_id.value;
      await api(`/listings/${listingId}/buy`, { method: "POST", body: JSON.stringify({}) });
    },
    "Listing purchased."
  )
);

forms.transfer.addEventListener("submit", (event) =>
  handleSubmit(
    event,
    async () => {
      await ensureMetaMaskSession();
      const tokenId = forms.transfer.elements.token_id.value;
      const payload = formToJson(forms.transfer, ["to_chain_address"]);
      await transferNft(tokenId, payload.to_chain_address);
      forms.transfer.elements.to_chain_address.value = "";
    },
    "NFT transfer submitted."
  )
);

forms.schedule.addEventListener("submit", (event) =>
  handleSubmit(
    event,
    async () => {
      await ensureMetaMaskSession();
      const payload = formToJson(forms.schedule, [
        "agent_id",
        "task",
        "interval_seconds",
        "starts_in_seconds",
      ]);
      await api("/agent-schedules", { method: "POST", body: JSON.stringify(payload) });
    },
    "Schedule created."
  )
);

async function refreshAll(withToast = false) {
  try {
    await syncMetaMaskAccount(false);
    await hydrateMetaMaskSession();

    const [health, runtime, wallets, agents, listings, runs, schedules] = await Promise.all([
      api("/health", { skipAuth: true }),
      api("/runtime/config", { skipAuth: true }),
      api("/wallets", { skipAuth: true }),
      api("/agents", { skipAuth: true }),
      api("/listings", { skipAuth: true }),
      api("/runs", { skipAuth: true }),
      api("/agent-schedules", { skipAuth: true }),
    ]);

    state.health = health;
    state.runtime = runtime;
    state.wallets = wallets;
    state.agents = agents;
    state.listings = listings;
    state.runs = runs;
    state.schedules = schedules;

    hydrateWalletFromRegistry();
    syncMarketplaceSelection();
    if (state.drawer.open && state.drawer.agentId) {
      await hydrateAgentDrawer({ agentId: state.drawer.agentId, silent: true, loading: false });
    }
    render();
    if (withToast) {
      showFlash("Data refreshed.", "success");
    }
  } catch (error) {
    updateHealth("error");
    showFlash(error.message, "error");
  }
}

async function handleSubmit(event, action, successMessage) {
  event.preventDefault();
  try {
    await action();
    await refreshAll();
    showFlash(successMessage, "success");
  } catch (error) {
    showFlash(error.message, "error");
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

function resolveRoute(pathname) {
  const normalized = pathname.replace(/\/+$/, "") || "/";
  if (normalized === "/" || normalized === "/dashboard" || normalized === "/launchpad") {
    return "launchpad";
  }
  if (normalized === "/wallets") {
    return "wallets";
  }
  if (normalized === "/agents") {
    return "agents";
  }
  if (normalized === "/market" || normalized === "/marketplace") {
    return "market";
  }
  if (normalized === "/runs") {
    return "runs";
  }
  return "launchpad";
}

function getPageConfig() {
  return PAGE_CONFIG[state.ui.route] || PAGE_CONFIG.launchpad;
}

function renderPageChrome() {
  const config = getPageConfig();
  document.title = config.title;
  refs.pageEyebrow.textContent = config.eyebrow;
  refs.pageTitle.textContent = config.headline;
  refs.pageLede.textContent = config.lede;
  refs.missionKicker.textContent = config.missionKicker;
  refs.missionTitle.textContent = config.missionTitle;
  refs.workspaceKicker.textContent = config.workspaceKicker;
  refs.workspaceTitle.textContent = config.workspaceTitle;
  refs.workspaceDescription.textContent = config.workspaceDescription;

  document.querySelectorAll("[data-nav-route]").forEach((link) => {
    const active = link.dataset.navRoute === state.ui.route;
    link.classList.toggle("is-active", active);
    link.setAttribute("aria-current", active ? "page" : "false");
  });

  document.querySelectorAll("[data-page-section]").forEach((element) => {
    const pages = String(element.dataset.pageSection || "")
      .split(/\s+/)
      .filter(Boolean);
    element.classList.toggle("route-hidden", !pages.includes(state.ui.route));
  });
}

function applyRouteIntent() {
  if (state.ui.routeIntentApplied) {
    return;
  }

  const params = new URLSearchParams(window.location.search);
  const action = params.get("action");
  const agentId = params.get("agent_id");
  const tokenId = params.get("token_id");
  const listingId = params.get("listing_id");
  let focused = false;

  if (state.ui.route === "runs") {
    if (agentId) {
      if (action === "schedule") {
        forms.schedule.elements.agent_id.value = agentId;
        forms.schedule.elements.task.focus();
        focused = true;
      } else {
        forms.run.elements.agent_id.value = agentId;
        forms.run.elements.task.focus();
        focused = true;
      }
    }
  }

  if (state.ui.route === "market") {
    if (action === "buy" && listingId) {
      forms.buy.elements.listing_id.value = listingId;
      forms.buy.querySelector('button[type="submit"]').focus();
      focused = true;
    } else if (action === "transfer" && tokenId) {
      forms.transfer.elements.token_id.value = tokenId;
      forms.transfer.elements.to_chain_address.focus();
      focused = true;
    } else if (tokenId) {
      forms.listing.elements.token_id.value = tokenId;
      forms.listing.elements.price.focus();
      focused = true;
    }
  }

  state.ui.routeIntentApplied = focused || !window.location.search;
}

function render() {
  const queuedCount = state.runs.filter((run) => run.status === "QUEUED").length;
  renderPageChrome();
  updateHealth("ok");
  renderMetaMaskStatus();
  refs.lastRefresh.textContent = `Last sync ${new Date().toLocaleString()}`;
  refs.statWallets.textContent = String(state.wallets.length);
  refs.statAgents.textContent = String(state.agents.length);
  refs.statListings.textContent = String(state.listings.length);
  refs.statQueued.textContent = String(queuedCount);
  renderDashboardSignals({ queuedCount });

  hydrateSelects();
  applyRouteIntent();
  renderWallets();
  renderAgents();
  renderListings();
  renderRuns();
  renderSchedules();
  renderAgentDrawer();
}

function updateHealth(mode) {
  refs.healthPill.className = `pill ${mode}`;
  refs.healthPill.textContent = mode === "ok" ? "Healthy" : mode === "error" ? "Error" : "Checking";
}

function renderMetaMaskStatus() {
  const metamask = state.metamask;
  const connected = Boolean(metamask.address);
  const authenticated = Boolean(
    metamask.authenticated && metamask.wallet && metamask.sessionAddress === metamask.address
  );

  refs.walletPill.className = `pill ${
    authenticated ? "ok" : connected || metamask.available ? "pending" : "error"
  }`;
  refs.walletPill.textContent = authenticated
    ? "MetaMask Signed"
    : connected
      ? "Signature Required"
      : metamask.available
        ? "MetaMask Ready"
        : "MetaMask Missing";

  refs.walletAddress.textContent = `Address: ${metamask.address || "Not connected"}`;
  refs.walletRuntimeId.textContent = `Runtime Wallet: ${metamask.wallet ? metamask.wallet.id : "Not synced"}`;
  refs.walletSession.textContent = authenticated
    ? `Session: Active on ${metamask.chainId || "unknown chain"}`
    : connected
      ? "Session: Sign the challenge message to unlock runtime actions"
      : "Session: Not authenticated";
  refs.runtimeChain.textContent = formatRuntimeChainStatus(state.runtime);
  refs.runtimeMint.textContent = formatRuntimeMintStatus(state.runtime);
  forms.walletConnect.elements.chain_address.value = metamask.address || "";
}

function renderDashboardSignals({ queuedCount }) {
  const runningCount = state.runs.filter((run) => run.status === "RUNNING").length;
  const completedCount = state.runs.filter((run) => run.status === "COMPLETED").length;
  const authenticated = Boolean(
    state.metamask.authenticated && state.metamask.wallet && state.metamask.sessionAddress === state.metamask.address
  );
  const selectedListing = getSelectedListing();
  const selectedAgent = selectedListing ? findAgentById(selectedListing.agent_id) : null;
  const chainSyncedCount = state.agents.filter((agent) => agent.nft.sync_mode === "CHAIN_SYNCED").length;
  const ownerDriftCount = state.listings.filter((listing) => {
    const listingAgent = findAgentById(listing.agent_id);
    return listingAgent && listing.seller_wallet_id !== listingAgent.nft.owner_wallet_id;
  }).length;

  const operatorTitle = authenticated
    ? `Signed ${shortenAddress(state.metamask.address)}`
    : state.metamask.address
      ? `Connected ${shortenAddress(state.metamask.address)}`
      : state.metamask.available
        ? "Wallet Ready"
        : "MetaMask Missing";
  const operatorDetail = authenticated
    ? `${state.metamask.wallet?.name || state.metamask.wallet?.id || "Runtime wallet"} controls write actions`
    : state.metamask.address
      ? "Sign the challenge message to unlock owner actions"
      : state.metamask.available
        ? "Connect MetaMask to create or trade agent ownership NFTs"
        : "Install MetaMask in this browser to use the console";
  setSignalCard(
    refs.signalAuthCard,
    refs.signalAuthTitle,
    refs.signalAuthDetail,
    authenticated ? "ready" : state.metamask.available ? "pending" : "danger",
    operatorTitle,
    operatorDetail
  );

  const chain = state.runtime?.chain;
  let chainTone = "pending";
  let chainTitle = "Unknown";
  let chainDetail = "Waiting for runtime config.";
  if (chain?.status === "READY") {
    chainTone = "ready";
    chainTitle = `Chain ${chain.chain_id}`;
    chainDetail = `Contract live at block ${chain.latest_block}`;
  } else if (chain?.status === "DISABLED") {
    chainTone = "pending";
    chainTitle = "Off-chain Mode";
    chainDetail = `Missing ${(chain.missing || []).join(", ") || "chain config"}`;
  } else if (chain?.status === "RPC_ERROR") {
    chainTone = "danger";
    chainTitle = "RPC Error";
    chainDetail = "Listener cannot reach the configured Web3 provider.";
  } else if (chain?.status === "CONTRACT_MISSING") {
    chainTone = "danger";
    chainTitle = "Contract Missing";
    chainDetail = "Configured NFT contract address has no bytecode.";
  }
  setSignalCard(refs.signalChainCard, refs.signalChainTitle, refs.signalChainDetail, chainTone, chainTitle, chainDetail);

  const marketTone = state.listings.length ? "live" : "muted";
  const marketTitle = state.listings.length
    ? `${state.listings.length} Live ${pluralize("Listing", state.listings.length)}`
    : "No Listings";
  const marketDetail = state.listings.length
    ? `${ownerDriftCount ? `${ownerDriftCount} owner drift` : "Seller and holder aligned"} · ${chainSyncedCount} chain-synced agents`
    : `${chainSyncedCount} chain-synced agents ready to trade`;
  setSignalCard(refs.signalMarketCard, refs.signalMarketTitle, refs.signalMarketDetail, marketTone, marketTitle, marketDetail);

  const queueTone = runningCount ? "live" : queuedCount ? "pending" : "muted";
  const queueTitle = runningCount
    ? `${runningCount} Running / ${queuedCount} Queued`
    : queuedCount
      ? `${queuedCount} Queued`
      : "Idle Queue";
  const queueDetail = runningCount || queuedCount
    ? `${completedCount} completed runs in current feed`
    : "Use Queue Run or Schedule Agent to warm the worker lane";
  setSignalCard(refs.signalQueueCard, refs.signalQueueTitle, refs.signalQueueDetail, queueTone, queueTitle, queueDetail);

  refs.workspaceOperator.textContent = authenticated
    ? `${shortenAddress(state.metamask.address)} · signed`
    : state.metamask.address
      ? `${shortenAddress(state.metamask.address)} · pending signature`
      : "Unsigned";
  refs.workspaceMintState.textContent = state.runtime?.auto_onchain_mint_enabled ? "On-chain mint ready" : "Local / fallback path";
  refs.workspaceMarketState.textContent = selectedAgent ? `Focus on ${selectedAgent.name}` : "No focused listing";

  refs.walletsPanelCount.textContent = `${state.wallets.length} ${pluralize("wallet", state.wallets.length)}`;
  refs.agentsPanelCount.textContent = `${state.agents.length} ${pluralize("agent", state.agents.length)}`;
  refs.marketPanelCount.textContent = `${state.listings.length} live ${pluralize("listing", state.listings.length)}`;
  refs.runsPanelCount.textContent = `${queuedCount} queued · ${runningCount} running`;
  refs.schedulesPanelCount.textContent = `${state.schedules.length} ${pluralize("schedule", state.schedules.length)}`;

  refs.topbarNote.textContent = [
    authenticated ? `Signed ${shortenAddress(state.metamask.address)}` : state.metamask.address ? `Wallet ${shortenAddress(state.metamask.address)}` : "Guest mode",
    chain?.status || "CHAIN_UNKNOWN",
    `${state.listings.length} live`,
    `${queuedCount} queued`,
  ].join(" · ");
  refs.missionSummary.textContent = authenticated
    ? `当前写操作由 ${state.metamask.wallet?.name || shortenAddress(state.metamask.address)} 持有的 NFT 所有权决定；链上状态、marketplace 和队列会在这里同步回放。`
    : "当前还没有签名 session。连接并签名 MetaMask 后，页面会切换到 owner-bound 控制视图，并同步展示链上和市场状态。";
}

function setSignalCard(cardRef, titleRef, detailRef, tone, title, detail) {
  cardRef.className = `signal-card tone-${tone}`;
  titleRef.textContent = title;
  detailRef.textContent = detail;
}

function hydrateSelects() {
  const agentOptions = state.agents.map((agent) => option(agent.id, `${agent.name} · ${agent.id}`)).join("");
  const nftOptions = state.agents
    .map((agent) => option(agent.nft.token_id, `${agent.name} · ${agent.nft.token_id}`))
    .join("");
  const listingOptions = state.listings
    .map((listing) => option(listing.id, `${listing.id} · ${listing.price}`))
    .join("");

  setOptions(forms.run.elements.agent_id, agentOptions);
  setOptions(forms.listing.elements.token_id, nftOptions);
  setOptions(forms.buy.elements.listing_id, listingOptions);
  setOptions(forms.transfer.elements.token_id, nftOptions);
  setOptions(forms.schedule.elements.agent_id, agentOptions);
  renderMetaMaskStatus();
}

function setOptions(select, optionsHtml) {
  const current = select.value;
  select.innerHTML = `<option value="" ${current ? "" : "selected"} disabled>Select...</option>${optionsHtml}`;
  if (current && [...select.options].some((item) => item.value === current)) {
    select.value = current;
  }
}

function renderWallets() {
  if (!state.wallets.length) {
    refs.walletsGrid.className = "card-grid empty-state";
    refs.walletsGrid.textContent = "No wallets yet. Connect MetaMask to create one.";
    return;
  }
  refs.walletsGrid.className = "card-grid";
  refs.walletsGrid.innerHTML = state.wallets
    .map((wallet) => {
      const isSignedWallet = wallet.id === state.metamask.wallet?.id && state.metamask.authenticated;
      const isConnectedWallet = wallet.chain_address && wallet.chain_address === state.metamask.address;
      const chip = isSignedWallet ? "Signed Session" : isConnectedWallet ? "Connected" : wallet.balance;
      const walletClasses = [
        "wallet-card",
        isSignedWallet ? "wallet-card-signed" : "",
        !isSignedWallet && isConnectedWallet ? "wallet-card-connected" : "",
      ]
        .filter(Boolean)
        .join(" ");
      return `
        <article class="${walletClasses}">
          <div class="card-title">
            <strong>${escapeHtml(wallet.name)}</strong>
            <span class="chip">${escapeHtml(chip)}</span>
          </div>
          <div class="meta-list">
            ${metaRow("Wallet ID", wallet.id)}
            ${metaRow("Chain Address", wallet.chain_address || "Unlinked")}
            ${metaRow("Local Balance", wallet.balance)}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderAgents() {
  if (!state.agents.length) {
    refs.agentsGrid.className = "card-grid empty-state";
    refs.agentsGrid.textContent = "No agents yet. Create one to mint its ownership NFT.";
    return;
  }
  refs.agentsGrid.className = "card-grid";
  refs.agentsGrid.innerHTML = state.agents
    .map(
      (agent) => `
        <article class="agent-card sync-${syncModeClass(agent.nft.sync_mode)}">
          <div class="card-title">
            <strong>${escapeHtml(agent.name)}</strong>
            <span class="chip">${escapeHtml(agent.status)}</span>
          </div>
          <div class="meta-list">
            ${metaRow("Agent ID", agent.id)}
            ${metaRow("Owner Wallet", describeWallet(agent.nft.owner_wallet_id))}
            ${metaRow("Ownership Mode", formatSyncMode(agent.nft.sync_mode))}
            ${metaRow("NFT", agent.nft.token_id)}
            ${metaRow("Chain Token", agent.nft.chain_token_id || "Off-chain only")}
            ${metaRow("Prompt", truncate(agent.system_prompt, 140))}
          </div>
          <div class="card-actions">
            <button type="button" data-action="details" data-agent="${agent.id}">Details</button>
            <button type="button" data-action="run" data-agent="${agent.id}" data-owner="${agent.nft.owner_wallet_id}">Queue Run</button>
            <button
              type="button"
              data-action="list"
              data-token="${agent.nft.token_id}"
              data-owner="${agent.nft.owner_wallet_id}"
              ${agent.nft.local_market_enabled ? "" : "disabled"}
            >${agent.nft.local_market_enabled ? "Open Listing" : "Local Market Disabled"}</button>
            <button type="button" data-action="schedule" data-agent="${agent.id}">Schedule</button>
            <button type="button" data-action="transfer" data-token="${agent.nft.token_id}" data-owner="${agent.nft.owner_wallet_id}">${agent.nft.onchain_transfer_enabled ? "On-Chain Transfer" : "Transfer"}</button>
          </div>
        </article>
      `
    )
    .join("");
  attachCardActions();
}

function renderListings() {
  if (!state.listings.length) {
    refs.marketplaceBoard.className = "marketplace-board empty-state";
    refs.marketplaceBoard.textContent = "No active listings. Open a listing to populate the trading board.";
    refs.listingsGrid.className = "card-grid empty-state";
    refs.listingsGrid.textContent = "No open listings. List an NFT-backed agent to trade it.";
    return;
  }
  const selectedListing = getSelectedListing();
  refs.marketplaceBoard.className = "marketplace-board";
  refs.marketplaceBoard.innerHTML = renderMarketplaceBoard(selectedListing);
  refs.listingsGrid.className = "card-grid";
  refs.listingsGrid.innerHTML = state.listings
    .map(
      (listing) => `
        <article class="listing-card listing-${listing.status.toLowerCase()} ${listing.id === state.marketplace.selectedListingId ? "listing-focused" : ""}">
          <div class="card-title">
            <strong>${escapeHtml(listing.id)}</strong>
            <span class="chip">${escapeHtml(listing.price)}</span>
          </div>
          <div class="meta-list">
            ${metaRow("Agent", listing.agent_id)}
            ${metaRow("NFT", listing.token_id)}
            ${metaRow("Seller", describeWallet(listing.seller_wallet_id))}
            ${metaRow("Status", listing.status)}
          </div>
          <div class="card-actions">
            <button type="button" data-action="focus-listing" data-listing="${listing.id}">Focus</button>
            <button type="button" data-action="buy" data-listing="${listing.id}">Buy Listing</button>
          </div>
        </article>
      `
    )
    .join("");
  attachCardActions();
}

function renderRuns() {
  if (!state.runs.length) {
    refs.runsTable.className = "table-shell empty-state";
    refs.runsTable.textContent = "No runs yet. Queue one from the operations panel.";
    return;
  }
  refs.runsTable.className = "table-shell";
  refs.runsTable.innerHTML = state.runs
    .slice(0, 10)
    .map(
      (run) => `
        <article class="run-row run-${run.status.toLowerCase()}">
          <div class="run-col">
            <span>Run</span>
            <code>${escapeHtml(run.id)}</code>
          </div>
          <div class="run-col">
            <span>Status</span>
            <strong class="status-tag ${run.status.toLowerCase()}">${escapeHtml(run.status)}</strong>
          </div>
          <div class="run-col">
            <span>Task</span>
            <p>${escapeHtml(truncate(run.task_input, 110))}</p>
          </div>
          <div class="run-col">
            <span>Agent</span>
            <code>${escapeHtml(run.agent_id)}</code>
          </div>
          <div class="run-col">
            <span>Owner Wallet</span>
            <code>${escapeHtml(describeWallet(run.requested_by_wallet_id))}</code>
          </div>
        </article>
      `
    )
    .join("");
}

function renderSchedules() {
  if (!state.schedules.length) {
    refs.schedulesGrid.className = "card-grid empty-state";
    refs.schedulesGrid.textContent = "No schedules yet.";
    return;
  }
  refs.schedulesGrid.className = "card-grid";
  refs.schedulesGrid.innerHTML = state.schedules
    .map(
      (schedule) => `
        <article class="schedule-card ${schedule.enabled ? "schedule-enabled" : "schedule-disabled"}">
          <div class="card-title">
            <strong>${escapeHtml(schedule.id)}</strong>
            <span class="chip">${schedule.interval_seconds}s</span>
          </div>
          <div class="meta-list">
            ${metaRow("Agent", schedule.agent_id)}
            ${metaRow("Enabled", String(schedule.enabled))}
            ${metaRow("Next Run", schedule.next_run_at)}
            ${metaRow("Task", truncate(schedule.task_template, 120))}
          </div>
        </article>
      `
    )
    .join("");
}

function attachCardActions() {
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.onclick = async () => {
      const { action, agent, owner, token, listing } = button.dataset;
      if (action === "details") {
        try {
          await openAgentDrawer(agent);
        } catch (error) {
          showFlash(error.message, "error");
        }
      } else if (action === "focus-listing") {
        focusListing(listing);
      } else if (action === "run") {
        if (state.ui.route !== "runs") {
          navigateToRoute("runs", { action: "run", agent_id: agent });
          return;
        }
        forms.run.elements.agent_id.value = agent;
        forms.run.elements.task.focus();
      } else if (action === "list") {
        if (state.ui.route !== "market") {
          navigateToRoute("market", { action: "list", token_id: token });
          return;
        }
        forms.listing.elements.token_id.value = token;
        forms.listing.elements.price.focus();
      } else if (action === "schedule") {
        if (state.ui.route !== "runs") {
          navigateToRoute("runs", { action: "schedule", agent_id: agent });
          return;
        }
        forms.schedule.elements.agent_id.value = agent;
        forms.schedule.elements.task.focus();
      } else if (action === "transfer") {
        if (state.ui.route !== "market") {
          navigateToRoute("market", { action: "transfer", token_id: token });
          return;
        }
        forms.transfer.elements.token_id.value = token;
        forms.transfer.elements.to_chain_address.focus();
      } else if (action === "buy") {
        if (state.ui.route !== "market") {
          navigateToRoute("market", { action: "buy", listing_id: listing });
          return;
        }
        forms.buy.elements.listing_id.value = listing;
        forms.buy.querySelector('button[type="submit"]').focus();
      }
    };
  });
}

function formToJson(form, fields) {
  const data = {};
  fields.forEach((field) => {
    data[field] = form.elements[field].value;
  });
  return data;
}

function metaRow(label, value) {
  return `
    <div class="meta-row">
      <span>${escapeHtml(label)}</span>
      <code>${escapeHtml(value)}</code>
    </div>
  `;
}

function option(value, label) {
  return `<option value="${escapeAttr(value)}">${escapeHtml(label)}</option>`;
}

function truncate(value, length) {
  return value.length > length ? `${value.slice(0, length - 3)}...` : value;
}

function showFlash(message, type) {
  refs.flash.className = `flash ${type}`;
  refs.flash.textContent = message;
  refs.flash.classList.remove("hidden");
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

function getSelectedListing() {
  return state.listings.find((listing) => listing.id === state.marketplace.selectedListingId) || state.listings[0] || null;
}

function focusListing(listingId) {
  state.marketplace.selectedListingId = listingId;
  renderListings();
}

function navigateToRoute(route, params = {}) {
  const path = route === "market" ? "/market" : route === "runs" ? "/runs" : `/${route}`;
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      query.set(key, value);
    }
  });
  window.location.href = query.size ? `${path}?${query.toString()}` : path;
}

function findAgentById(agentId) {
  return state.agents.find((item) => item.id === agentId) || null;
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
  renderAgentDrawer();
  document.body.classList.add("drawer-open");
  await hydrateAgentDrawer({ agentId, silent: false, loading: true });
}

function closeAgentDrawer() {
  state.drawer.open = false;
  state.drawer.loading = false;
  state.drawer.error = null;
  state.drawer.expandedRunIds = [];
  renderAgentDrawer();
  document.body.classList.remove("drawer-open");
}

async function hydrateAgentDrawer({ agentId = state.drawer.agentId, silent = false, loading = true } = {}) {
  const agent = findAgentById(agentId);
  if (!agent) {
    state.drawer.error = "Selected agent no longer exists in the current runtime state.";
    state.drawer.loading = false;
    renderAgentDrawer();
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
  renderAgentDrawer();

  try {
    const [runs, metadata] = await Promise.all([
      api(`/agents/${agentId}/runs`, { skipAuth: true }),
      api(`/nfts/${agent.nft.token_id}/metadata`, { skipAuth: true }),
    ]);

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
    renderAgentDrawer();
  }
}

function renderAgentDrawer() {
  const isOpen = state.drawer.open;
  const agent = findAgentById(state.drawer.agentId);

  refs.drawer.classList.toggle("hidden", !isOpen);
  refs.drawerBackdrop.classList.toggle("hidden", !isOpen);
  refs.drawer.setAttribute("aria-hidden", String(!isOpen));
  document.body.classList.toggle("drawer-open", isOpen);

  if (!isOpen) {
    return;
  }

  if (!agent) {
    refs.drawerAgentName.textContent = "Agent unavailable";
    refs.drawerAgentMeta.textContent = "The selected agent no longer exists in the current dashboard state.";
    refs.drawerBody.innerHTML = `
      <div class="drawer-empty">
        <p>Refresh the dashboard and pick another agent.</p>
      </div>
    `;
    return;
  }

  refs.drawerAgentName.textContent = agent.name;
  refs.drawerAgentMeta.textContent = `${agent.id} · ${formatSyncMode(agent.nft.sync_mode)} · ${agent.nft.token_id}`;

  if (state.drawer.loading) {
    refs.drawerBody.innerHTML = `
      <div class="drawer-empty">
        <p>Loading agent prompt, metadata and recent runs...</p>
      </div>
    `;
    return;
  }

  if (state.drawer.error) {
    refs.drawerBody.innerHTML = `
      <div class="drawer-empty">
        <p>${escapeHtml(state.drawer.error)}</p>
      </div>
    `;
    return;
  }

  refs.drawerBody.innerHTML = buildAgentDrawerMarkup(agent);
}

function buildAgentDrawerMarkup(agent) {
  const ownerWallet = resolveWalletById(agent.nft.owner_wallet_id);
  const metadata = state.drawer.metadata;
  const recentRuns = state.drawer.runs.slice(0, 8);

  return `
    <div class="drawer-grid">
      <section class="drawer-section">
        <div class="drawer-section-head">
          <h3>Owner</h3>
          <span class="chip">${escapeHtml(agent.status)}</span>
        </div>
        <div class="drawer-key-grid">
          ${drawerKey("Runtime Wallet", ownerWallet?.id || agent.nft.owner_wallet_id)}
          ${drawerKey("Wallet Label", ownerWallet?.name || "Unknown")}
          ${drawerKey("Chain Address", ownerWallet?.chain_address || "Unlinked")}
          ${drawerKey("Sync Mode", formatSyncMode(agent.nft.sync_mode))}
          ${drawerKey("NFT Token", agent.nft.token_id)}
          ${drawerKey("Chain Token", agent.nft.chain_token_id || "Off-chain only")}
        </div>
      </section>

      <section class="drawer-section">
        <div class="drawer-section-head">
          <h3>System Prompt</h3>
        </div>
        <pre class="prompt-block">${escapeHtml(agent.system_prompt)}</pre>
      </section>

      <section class="drawer-section">
        <div class="drawer-section-head">
          <h3>Metadata</h3>
          <span class="drawer-caption">${escapeHtml(metadata?.name || "Unavailable")}</span>
        </div>
        ${renderMetadataPanel(metadata, agent)}
      </section>

      <section class="drawer-section drawer-section-wide">
        <div class="drawer-section-head">
          <h3>Recent Runs</h3>
          <span class="drawer-caption">${recentRuns.length} loaded</span>
        </div>
        ${renderDrawerRuns(recentRuns)}
      </section>
    </div>
  `;
}

function renderMetadataPanel(metadata, agent) {
  if (!metadata) {
    return `
      <div class="drawer-empty">
        <p>Metadata is not available for this token yet.</p>
      </div>
    `;
  }

  return `
    <div class="metadata-panel">
      <div class="metadata-preview">
        <div class="metadata-preview-head">
          <span>SVG Preview</span>
          <button type="button" class="ghost ghost-tight" data-drawer-action="copy-token-uri" data-value="${escapeAttr(agent.nft.metadata_uri || "")}">Copy tokenURI</button>
        </div>
        <img class="metadata-image" src="${escapeAttr(metadata.image || "")}" alt="${escapeAttr(metadata.name || agent.name)}" />
      </div>
      <div class="metadata-copy">
        <p class="metadata-description">${escapeHtml(metadata.description || "No description.")}</p>
        <div class="drawer-key-grid compact">
          ${drawerKey("tokenURI", agent.nft.metadata_uri || metadata.external_url || "Unavailable")}
          ${drawerKey("Image", metadata.image || "Unavailable")}
          ${drawerKey("External URL", metadata.external_url || "Unavailable")}
        </div>
      </div>
      <div class="attribute-grid">
        ${(metadata.attributes || []).map(renderAttributeChip).join("") || `<div class="drawer-empty"><p>No attributes.</p></div>`}
      </div>
    </div>
  `;
}

function renderAttributeChip(attribute) {
  const label = attribute.trait_type || attribute.display_type || "Attribute";
  const value = attribute.value ?? "Unknown";
  return `
    <article class="attribute-card">
      <span>${escapeHtml(String(label))}</span>
      <strong>${escapeHtml(String(value))}</strong>
    </article>
  `;
}

function renderDrawerRuns(runs) {
  if (!runs.length) {
    return `
      <div class="drawer-empty">
        <p>No run history yet for this agent.</p>
      </div>
    `;
  }

  return `
    <div class="drawer-run-list">
      ${runs
        .map(
          (run) => `
            <article class="drawer-run-card">
              <div class="drawer-run-head">
                <code>${escapeHtml(run.id)}</code>
                <div class="drawer-run-actions">
                  <strong class="status-tag ${run.status.toLowerCase()}">${escapeHtml(run.status)}</strong>
                  <button
                    type="button"
                    class="ghost ghost-tight"
                    data-drawer-action="toggle-run-output"
                    data-value="${escapeAttr(run.id)}"
                  >${state.drawer.expandedRunIds.includes(run.id) ? "Hide Output" : "Show Output"}</button>
                </div>
              </div>
              <div class="drawer-key-grid compact">
                ${drawerKey("Started", formatDateTime(run.started_at))}
                ${drawerKey("Finished", formatDateTime(run.finished_at))}
                ${drawerKey("Requester", describeWallet(run.requested_by_wallet_id))}
              </div>
              <div class="drawer-run-copy">
                <p><span>Task</span>${escapeHtml(truncate(run.task_input, 240))}</p>
                <p><span>Summary</span>${escapeHtml(truncate(formatRunOutput(run.output), 180))}</p>
                ${
                  state.drawer.expandedRunIds.includes(run.id)
                    ? `<pre class="drawer-output-block">${escapeHtml(formatRunOutput(run.output))}</pre>`
                    : ""
                }
              </div>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderMarketplaceBoard(listing) {
  if (!listing) {
    return "No listing selected.";
  }

  const agent = findAgentById(listing.agent_id);
  if (!agent) {
    return `
      <div class="drawer-empty">
        <p>Listing exists, but the related agent is missing from the current dashboard state.</p>
      </div>
    `;
  }

  const sellerWallet = resolveWalletById(listing.seller_wallet_id);
  const ownerWallet = resolveWalletById(agent.nft.owner_wallet_id);
  const chainState = formatSyncMode(agent.nft.sync_mode);
  const tokenImage = getTokenImageUrl(agent.nft.token_id);
  const tokenUri = getTokenMetadataUrl(agent.nft.token_id);
  const ownerChanged = listing.seller_wallet_id !== agent.nft.owner_wallet_id;

  return `
    <div class="marketplace-spotlight">
      <div class="marketplace-preview">
        <img class="marketplace-image" src="${escapeAttr(tokenImage)}" alt="${escapeAttr(agent.name)}" />
      </div>
      <div class="marketplace-copy">
        <div class="marketplace-head">
          <div>
            <p class="section-kicker">Focused Listing</p>
            <h3>${escapeHtml(agent.name)}</h3>
          </div>
          <span class="chip">${escapeHtml(listing.status)}</span>
        </div>
        <p class="marketplace-description">${escapeHtml(agent.description)}</p>
        <div class="marketplace-price-row">
          <div class="marketplace-price">
            <span>Ask Price</span>
            <strong>${escapeHtml(listing.price)}</strong>
            <small>runtime credits</small>
          </div>
          <div class="marketplace-status">
            <span>Chain Status</span>
            <strong>${escapeHtml(chainState)}</strong>
            <small>${escapeHtml(agent.nft.onchain_transfer_enabled ? "MetaMask transfer path live" : "Local transfer path")}</small>
          </div>
        </div>
        <div class="drawer-key-grid compact">
          ${drawerKey("Listing ID", listing.id)}
          ${drawerKey("Seller", sellerWallet?.chain_address || sellerWallet?.name || listing.seller_wallet_id)}
          ${drawerKey("Current Holder", ownerWallet?.chain_address || ownerWallet?.name || agent.nft.owner_wallet_id)}
          ${drawerKey("Owner Drift", ownerChanged ? "Seller and holder diverged" : "Seller still holds NFT")}
          ${drawerKey("Contract", agent.nft.contract_address || "Off-chain only")}
          ${drawerKey("Chain Token", agent.nft.chain_token_id || "Unmapped")}
          ${drawerKey("tokenURI", tokenUri)}
          ${drawerKey("Image", tokenImage)}
        </div>
        <div class="marketplace-actions">
          <button type="button" data-action="buy" data-listing="${listing.id}">Buy Listing</button>
          <button type="button" class="ghost" data-action="details" data-agent="${agent.id}">View Agent Detail</button>
          <button type="button" class="ghost" data-action="focus-listing" data-listing="${listing.id}">Stay Focused</button>
        </div>
      </div>
    </div>
  `;
}

function drawerKey(label, value) {
  return `
    <div class="drawer-key">
      <span>${escapeHtml(label)}</span>
      <code>${escapeHtml(String(value))}</code>
    </div>
  `;
}

function formatRunOutput(output) {
  if (!output) {
    return "No output recorded yet.";
  }
  if (typeof output === "string") {
    return output;
  }
  return JSON.stringify(output);
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
  renderAgentDrawer();
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
  forms.walletConnect.elements.chain_address.value = normalizedAddress || "";

  if (!normalizedAddress) {
    clearMetaMaskSession({ keepWallet: false });
    return;
  }

  if (addressChanged || (state.metamask.sessionAddress && state.metamask.sessionAddress !== normalizedAddress)) {
    clearMetaMaskSession({ keepWallet: false });
  }
}

async function connectMetaMask(showToast = false) {
  if (!window.ethereum) {
    state.metamask.available = false;
    renderMetaMaskStatus();
    throw new Error("MetaMask not found in this browser.");
  }

  const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
  const chainId = await window.ethereum.request({ method: "eth_chainId" });
  applyConnectedAccount(accounts?.[0] || null, chainId);
  renderMetaMaskStatus();
  if (showToast) {
    showFlash("MetaMask connected.", "success");
  }
}

async function syncMetaMaskAccount(showToast = false) {
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
  renderMetaMaskStatus();
  if (showToast && state.metamask.address) {
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

  const mappedWallet =
    state.wallets.find((wallet) => wallet.chain_address === state.metamask.address) || null;

  if (state.metamask.authenticated) {
    state.metamask.wallet = mappedWallet || state.metamask.wallet;
    return;
  }

  state.metamask.wallet = mappedWallet;
}

async function authenticateMetaMask({ force = false, label = null, initialBalance = "0" } = {}) {
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
  renderMetaMaskStatus();
  return session.wallet;
}

async function ensureMetaMaskSession() {
  if (state.metamask.authenticated && state.metamask.token) {
    return state.metamask.wallet;
  }

  return authenticateMetaMask({
    initialBalance: forms.walletConnect.elements.initial_balance.value || "0",
    label: forms.walletConnect.elements.label.value || null,
  });
}

async function logoutMetaMask(showToast = false) {
  if (state.metamask.token) {
    try {
      await api("/auth/logout", { method: "POST" });
    } catch {
      // Ignore remote logout failures and clear the local session anyway.
    }
  }

  clearMetaMaskSession();
  renderMetaMaskStatus();
  if (showToast) {
    showFlash("MetaMask session cleared.", "success");
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#96;");
}

function shortenAddress(value) {
  if (!value) {
    return "Unknown";
  }
  if (value.length <= 12) {
    return value;
  }
  return `${value.slice(0, 6)}...${value.slice(-4)}`;
}

function pluralize(label, count) {
  return count === 1 ? label : `${label}s`;
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

function syncModeClass(syncMode) {
  return String(syncMode || "LOCAL_ONLY").toLowerCase().replaceAll("_", "-");
}

function formatRuntimeChainStatus(runtime) {
  const chain = runtime?.chain;
  if (!chain) {
    return "Chain Sync: Unknown";
  }
  if (chain.status === "READY") {
    return `Chain Sync: Ready on chain ${chain.chain_id}, block ${chain.latest_block}`;
  }
  if (chain.status === "CONTRACT_MISSING") {
    return "Chain Sync: Contract address has no bytecode";
  }
  if (chain.status === "RPC_ERROR") {
    return "Chain Sync: RPC unreachable";
  }
  if (chain.status === "DISABLED") {
    return `Chain Sync: Off-chain mode (${(chain.missing || []).join(" + ") || "missing config"})`;
  }
  return "Chain Sync: Unknown";
}

function formatRuntimeMintStatus(runtime) {
  if (!runtime) {
    return "Mint: Unknown";
  }
  if (runtime.auto_onchain_mint_enabled) {
    return "Mint: Runtime mint ready";
  }
  if (!runtime.nft_contract_address) {
    return "Mint: Missing NFT_CONTRACT_ADDRESS";
  }
  if (!runtime.web3_provider_configured) {
    return "Mint: Missing WEB3_PROVIDER_URL";
  }
  if (!runtime.nft_minter_configured) {
    return "Mint: Missing NFT_MINTER_PRIVATE_KEY";
  }
  return "Mint: Unknown";
}

function resolveWalletById(walletId) {
  return state.wallets.find((item) => item.id === walletId) || null;
}

function resolveAgentByTokenId(tokenId) {
  return state.agents.find((item) => item.nft.token_id === tokenId) || null;
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

function buildSafeTransferFromData(fromAddress, toAddress, tokenId) {
  return `0x42842e0e${encodeAddress(fromAddress)}${encodeAddress(toAddress)}${encodeUint256(tokenId)}`;
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

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
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

async function transferNft(tokenId, toChainAddress) {
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

    showFlash(
      `Chain transfer submitted ${txHash.slice(0, 10)}... Waiting for listener sync.`,
      "success"
    );

    const syncedNft = await waitForChainSync(tokenId, txHash);
    if (!syncedNft) {
      showFlash(
        "Chain transfer was broadcast, but runtime sync is still pending. Wait for the listener to catch up.",
        "success"
      );
      return;
    }
    return;
  }

  await api(`/nfts/${tokenId}/transfer`, {
    method: "POST",
    body: JSON.stringify({ to_chain_address: targetAddress }),
  });
}

if (window.ethereum) {
  window.ethereum.on("accountsChanged", () => refreshAll(false));
  window.ethereum.on("chainChanged", () => refreshAll(false));
}

refreshAll();
setInterval(() => refreshAll(false), 12000);

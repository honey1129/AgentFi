<template>
  <div v-if="isUserView && agent" class="wallet-page-stack">
    <section class="wallet-page-kpis">
      <article class="wallet-page-kpi">
        <span>Ownership</span>
        <strong>{{ store.describeWallet(agent.nft.owner_wallet_id) }}</strong>
        <p>{{ store.formatSyncMode(agent.nft.sync_mode) }} ownership is currently bound to this wallet.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Token routing</span>
        <strong>{{ agent.nft.chain_token_id || agent.nft.token_id }}</strong>
        <p>{{ agent.nft.contract_address ? `Contract ${agent.nft.contract_address}` : "This NFT is still operating in local-only mode." }}</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Run activity</span>
        <strong>{{ detail.runs.length }}</strong>
        <p>{{ detail.runs[0] ? `Latest run status: ${detail.runs[0].status}.` : "No runs have been recorded for this agent yet." }}</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Status</span>
        <strong>{{ agent.status }}</strong>
        <p>{{ detail.metadata?.name || "Metadata attached to this ownership token." }}</p>
      </article>
    </section>

    <section class="wallet-page-grid">
      <div class="wallet-page-main">
        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Overview</p>
              <h2>{{ agent.name }}</h2>
            </div>
            <span class="wallet-status-pill">{{ store.formatSyncMode(agent.nft.sync_mode) }}</span>
          </header>

          <div class="wallet-detail-grid">
            <div class="wallet-detail-card">
              <span>Agent ID</span>
              <strong>{{ agent.id }}</strong>
            </div>
            <div class="wallet-detail-card">
              <span>NFT token</span>
              <strong>{{ agent.nft.token_id }}</strong>
            </div>
            <div class="wallet-detail-card">
              <span>Chain token</span>
              <strong>{{ agent.nft.chain_token_id || "Off-chain only" }}</strong>
            </div>
            <div class="wallet-detail-card">
              <span>Contract</span>
              <strong>{{ agent.nft.contract_address || "Local only" }}</strong>
            </div>
          </div>

          <div class="wallet-inline-card">
            <span>Description</span>
            <strong>Agent intent</strong>
            <p>{{ agent.description }}</p>
          </div>

          <div class="wallet-card-actions">
            <button class="wallet-home-secondary" type="button" @click="router.push({ path: '/app/runs', query: { agent_id: agent.id } })">Queue run</button>
            <button class="wallet-home-secondary" type="button" @click="router.push({ path: '/app/market', query: { token_id: agent.nft.token_id } })">List</button>
            <button class="wallet-home-secondary" type="button" @click="router.push({ path: '/app/transfers', query: { token_id: agent.nft.token_id } })">Transfer</button>
          </div>
        </article>

        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Prompt</p>
              <h2>System prompt</h2>
            </div>
          </header>
          <pre class="wallet-code-block">{{ agent.system_prompt }}</pre>
        </article>

        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">History</p>
              <h2>Run history</h2>
            </div>
            <span class="wallet-status-pill">{{ detail.runs.length }} runs</span>
          </header>

          <div class="wallet-home-table-shell">
            <div class="wallet-home-table-head wallet-detail-run-table">
              <div>Run</div>
              <div>Timeline</div>
              <div>Task</div>
              <div>Status</div>
              <div>Actions</div>
            </div>

            <template v-for="run in detail.runs" :key="run.id">
              <div class="wallet-home-table-row wallet-detail-run-table">
                <div>
                  <strong>{{ run.id }}</strong>
                  <span>{{ store.describeWallet(run.requested_by_wallet_id) }}</span>
                </div>
                <div>{{ store.formatDateTime(run.queued_at) }}</div>
                <div>{{ store.truncate(run.task_input, 96) }}</div>
                <div><span class="wallet-status-pill" :class="runTone(run.status)">{{ run.status }}</span></div>
                <div class="wallet-home-inline-meta">
                  <button class="wallet-table-button" type="button" @click="toggleRun(run.id)">
                    {{ expandedRunIds.includes(run.id) ? "Hide" : "Output" }}
                  </button>
                  <RouterLink :to="`/app/runs/${run.id}`">Detail</RouterLink>
                </div>
              </div>
              <div v-if="expandedRunIds.includes(run.id)" class="wallet-output-shell">
                <pre class="wallet-code-block">{{ store.formatRunOutput(run.output) }}</pre>
              </div>
            </template>

            <div v-if="!detail.runs.length && !detail.loading" class="empty-state">No runs yet for this agent.</div>
          </div>
        </article>
      </div>

      <aside class="wallet-page-side">
        <article class="wallet-side-card">
          <div class="wallet-side-title">Token metadata</div>
          <div v-if="detail.loading" class="wallet-side-empty">Loading metadata...</div>
          <div v-else-if="detail.error" class="wallet-side-empty">{{ detail.error }}</div>
          <template v-else>
            <div class="wallet-detail-media">
              <img :src="detail.metadata?.image || store.getTokenImageUrl(agent.nft.token_id)" :alt="detail.metadata?.name || agent.name" />
            </div>
            <div class="wallet-side-list">
              <div>
                <strong>{{ detail.metadata?.name || "Token metadata" }}</strong>
                <span>{{ detail.metadata?.description || agent.description }}</span>
              </div>
              <div>
                <strong>tokenURI</strong>
                <span>{{ agent.nft.metadata_uri || detail.metadata?.external_url || "Unavailable" }}</span>
              </div>
              <div>
                <strong>External URL</strong>
                <span>{{ detail.metadata?.external_url || "Unavailable" }}</span>
              </div>
            </div>
            <button class="wallet-home-secondary wide" type="button" @click="copyTokenUri">Copy tokenURI</button>
          </template>
        </article>
      </aside>
    </section>
  </div>

  <div v-else-if="agent" class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Ownership</span>
        <strong>{{ store.describeWallet(agent.nft.owner_wallet_id) }}</strong>
        <p>{{ store.formatSyncMode(agent.nft.sync_mode) }} ownership is currently bound to this runtime wallet.</p>
      </article>
      <article class="metric-card">
        <span>Token Routing</span>
        <strong>{{ agent.nft.chain_token_id || agent.nft.token_id }}</strong>
        <p>{{ agent.nft.contract_address ? `Contract ${agent.nft.contract_address}` : "This NFT is still operating in local-only mode." }}</p>
      </article>
      <article class="metric-card">
        <span>Run Activity</span>
        <strong>{{ detail.runs.length }}</strong>
        <p>{{ detail.runs[0] ? `Latest run status: ${detail.runs[0].status}.` : "No runs have been recorded for this agent yet." }}</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Overview</p>
          <h2>{{ agent.name }}</h2>
        </div>
        <span class="panel-chip">{{ store.formatSyncMode(agent.nft.sync_mode) }}</span>
      </header>
      <div class="stack-grid">
        <dl class="detail-list detail-list-two">
          <div>
            <dt>Agent ID</dt>
            <dd>{{ agent.id }}</dd>
          </div>
          <div>
            <dt>NFT Token</dt>
            <dd>{{ agent.nft.token_id }}</dd>
          </div>
          <div>
            <dt>Owner Wallet</dt>
            <dd>{{ store.describeWallet(agent.nft.owner_wallet_id) }}</dd>
          </div>
          <div>
            <dt>Chain Token</dt>
            <dd>{{ agent.nft.chain_token_id || "Off-chain only" }}</dd>
          </div>
          <div>
            <dt>Metadata URI</dt>
            <dd>{{ agent.nft.metadata_uri || "Unavailable" }}</dd>
          </div>
          <div>
            <dt>Contract</dt>
            <dd>{{ agent.nft.contract_address || "Local only" }}</dd>
          </div>
        </dl>
        <div class="surface-block">
          <p class="surface-kicker">Description</p>
          <h3 class="surface-title">Agent intent</h3>
          <p class="panel-intro compact-panel-intro">{{ agent.description }}</p>
        </div>
      </div>
      <div class="action-row">
        <button class="ghost-button" type="button" @click="router.push({ path: isUserView ? '/app/runs' : '/runs/queue', query: { agent_id: agent.id } })">Queue Run</button>
        <button class="ghost-button" type="button" @click="router.push({ path: isUserView ? '/app/market' : '/market/listings', query: { token_id: agent.nft.token_id } })">List</button>
        <button class="ghost-button" type="button" @click="router.push({ path: isUserView ? '/app/transfers' : '/market/transfers', query: { token_id: agent.nft.token_id } })">Transfer</button>
      </div>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Metadata</p>
          <h2>{{ detail.metadata?.name || "Token metadata" }}</h2>
        </div>
        <button class="ghost-button" type="button" @click="copyTokenUri">Copy tokenURI</button>
      </header>
      <div v-if="detail.loading" class="empty-state">Loading metadata and recent runs...</div>
      <div v-else-if="detail.error" class="empty-state">{{ detail.error }}</div>
      <div v-else class="stack-grid">
        <div class="drawer-metadata">
          <div class="drawer-media">
            <img :src="detail.metadata?.image || store.getTokenImageUrl(agent.nft.token_id)" :alt="detail.metadata?.name || agent.name" />
          </div>
          <div class="drawer-copy">
            <p>{{ detail.metadata?.description || agent.description }}</p>
            <dl class="detail-list">
              <div>
                <dt>tokenURI</dt>
                <dd>{{ agent.nft.metadata_uri || detail.metadata?.external_url || "Unavailable" }}</dd>
              </div>
              <div>
                <dt>Image</dt>
                <dd>{{ detail.metadata?.image || "Unavailable" }}</dd>
              </div>
              <div>
                <dt>External URL</dt>
                <dd>{{ detail.metadata?.external_url || "Unavailable" }}</dd>
              </div>
            </dl>
          </div>
        </div>

        <div v-if="detail.metadata?.attributes?.length" class="attribute-grid">
          <article
            v-for="attribute in detail.metadata.attributes"
            :key="`${attribute.trait_type}-${attribute.value}`"
            class="attribute-card"
          >
            <span>{{ attribute.trait_type || attribute.display_type || "Attribute" }}</span>
            <strong>{{ attribute.value ?? "Unknown" }}</strong>
          </article>
        </div>
      </div>
    </section>

    <section class="panel page-grid-full">
      <header class="panel-header">
        <div>
          <p class="section-label">Prompt</p>
          <h2>System Prompt</h2>
        </div>
      </header>
      <pre class="code-block">{{ agent.system_prompt }}</pre>
    </section>

    <section class="panel page-grid-full">
      <header class="panel-header">
        <div>
          <p class="section-label">History</p>
          <h2>Run History</h2>
        </div>
        <span class="panel-chip">{{ detail.runs.length }} runs</span>
      </header>
      <div v-if="!detail.runs.length && !detail.loading" class="empty-state">No runs yet for this agent.</div>
      <div v-else class="data-table">
        <div class="data-table-head history-table">
          <span>Run</span>
          <span>Requester</span>
          <span>Timeline</span>
          <span>Task</span>
          <span>Actions</span>
          <span>Status</span>
        </div>
        <template v-for="run in detail.runs" :key="run.id">
          <article class="data-table-row history-table">
            <div class="table-cell">
              <strong>{{ run.id }}</strong>
            </div>
            <div class="table-cell">
              <span class="text-muted">{{ store.describeWallet(run.requested_by_wallet_id) }}</span>
            </div>
            <div class="table-cell">
              <div class="cell-stack">
                <span class="text-muted">Start {{ store.formatDateTime(run.started_at) }}</span>
                <span class="text-muted">Finish {{ store.formatDateTime(run.finished_at) }}</span>
              </div>
            </div>
            <div class="table-cell">
              <span class="text-muted">{{ store.truncate(run.task_input, 120) }}</span>
            </div>
            <div class="table-cell">
              <div class="table-actions">
                <button class="ghost-button" type="button" @click="toggleRun(run.id)">
                  {{ expandedRunIds.includes(run.id) ? "Hide Output" : "Show Output" }}
                </button>
                <button class="ghost-button" type="button" @click="router.push(`${routePrefix}/runs${isUserView ? '' : '/history'}/${run.id}`)">Run Detail</button>
              </div>
            </div>
            <div class="table-cell">
              <span class="status-badge">{{ run.status }}</span>
            </div>
          </article>
          <article v-if="expandedRunIds.includes(run.id)" class="data-table-row history-table-expanded">
            <div class="table-cell table-cell-full">
              <pre class="code-block">{{ store.formatRunOutput(run.output) }}</pre>
            </div>
          </article>
        </template>
      </div>
    </section>
  </div>

  <section v-else class="panel">
    <div class="empty-state">Agent not found in the current runtime state.</div>
  </section>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const route = useRoute();
const router = useRouter();
const store = useRuntimeStore();
const isUserView = computed(() => route.meta.audience === "user");
const routePrefix = computed(() => (isUserView.value ? "/app" : ""));

const detail = reactive({
  loading: false,
  error: null,
  metadata: null,
  runs: [],
});

const expandedRunIds = reactive([]);
const agentId = computed(() => String(route.params.agentId || ""));
const agent = computed(() => store.findAgentById(agentId.value));

watch(
  [agentId, () => store.state.agents.length],
  async () => {
    expandedRunIds.splice(0, expandedRunIds.length);
    detail.metadata = null;
    detail.runs = [];
    detail.error = null;

    if (!agent.value) {
      if (!store.state.refreshing) {
        detail.error = "Agent not found in the current runtime state.";
      }
      return;
    }

    detail.loading = true;
    try {
      const payload = await store.fetchAgentDetail(agentId.value);
      detail.metadata = payload.metadata;
      detail.runs = payload.runs;
    } catch (error) {
      detail.error = error.message;
    } finally {
      detail.loading = false;
    }
  },
  { immediate: true }
);

function toggleRun(runId) {
  const index = expandedRunIds.indexOf(runId);
  if (index >= 0) {
    expandedRunIds.splice(index, 1);
    return;
  }
  expandedRunIds.push(runId);
}

async function copyTokenUri() {
  const tokenUri = agent.value?.nft.metadata_uri || detail.metadata?.external_url || "";
  await store.copyText(tokenUri);
  store.showFlash("tokenURI copied.", "success");
}

function runTone(status) {
  if (status === "COMPLETED") {
    return "is-completed";
  }
  if (status === "RUNNING" || status === "QUEUED") {
    return "is-pending";
  }
  return "is-review";
}
</script>

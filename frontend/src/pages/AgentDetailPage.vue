<template>
  <div v-if="agent" class="page-grid">
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
      <div class="action-row">
        <button class="ghost-button" type="button" @click="router.push({ path: '/runs/queue', query: { agent_id: agent.id } })">Queue Run</button>
        <button class="ghost-button" type="button" @click="router.push({ path: '/market/listings', query: { token_id: agent.nft.token_id } })">List</button>
        <button class="ghost-button" type="button" @click="router.push({ path: '/market/transfers', query: { token_id: agent.nft.token_id } })">Transfer</button>
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
      <div v-else class="stack-grid">
        <article v-for="run in detail.runs" :key="run.id" class="entity-card">
          <div class="entity-card-header">
            <strong>{{ run.id }}</strong>
            <div class="action-row">
              <span class="status-badge">{{ run.status }}</span>
              <button class="ghost-button" type="button" @click="toggleRun(run.id)">
                {{ expandedRunIds.includes(run.id) ? "Hide Output" : "Show Output" }}
              </button>
            </div>
          </div>
          <dl class="detail-list detail-list-two">
            <div>
              <dt>Started</dt>
              <dd>{{ store.formatDateTime(run.started_at) }}</dd>
            </div>
            <div>
              <dt>Finished</dt>
              <dd>{{ store.formatDateTime(run.finished_at) }}</dd>
            </div>
            <div>
              <dt>Requester</dt>
              <dd>{{ store.describeWallet(run.requested_by_wallet_id) }}</dd>
            </div>
            <div>
              <dt>Task</dt>
              <dd>{{ store.truncate(run.task_input, 240) }}</dd>
            </div>
          </dl>
          <pre v-if="expandedRunIds.includes(run.id)" class="code-block">{{ store.formatRunOutput(run.output) }}</pre>
        </article>
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
</script>

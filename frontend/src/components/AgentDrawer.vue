<template>
  <div v-if="store.state.drawer.open" class="drawer-shell">
    <button class="drawer-backdrop" type="button" @click="store.closeAgentDrawer()" aria-label="Close drawer"></button>
    <aside class="drawer-panel">
      <header class="drawer-header">
        <div>
          <p class="section-label">Agent Detail</p>
          <h2>{{ agent?.name || "Agent" }}</h2>
          <p class="drawer-subtitle">{{ agent ? `${agent.id} · ${store.formatSyncMode(agent.nft.sync_mode)}` : "" }}</p>
        </div>
        <button class="ghost-button" type="button" @click="store.closeAgentDrawer()">Close</button>
      </header>

      <div v-if="store.state.drawer.loading" class="empty-state">
        Loading agent prompt, metadata, and recent runs...
      </div>
      <div v-else-if="store.state.drawer.error" class="empty-state">
        {{ store.state.drawer.error }}
      </div>
      <div v-else-if="agent" class="drawer-stack">
        <section class="panel panel-soft">
          <header class="panel-header">
            <div>
              <p class="section-label">Owner</p>
              <h3>Ownership</h3>
            </div>
          </header>
          <dl class="detail-list detail-list-two">
            <div>
              <dt>Runtime Wallet</dt>
              <dd>{{ ownerWallet?.id || agent.nft.owner_wallet_id }}</dd>
            </div>
            <div>
              <dt>Wallet Label</dt>
              <dd>{{ ownerWallet?.name || "Unknown" }}</dd>
            </div>
            <div>
              <dt>Chain Address</dt>
              <dd>{{ ownerWallet?.chain_address || "Unlinked" }}</dd>
            </div>
            <div>
              <dt>Sync Mode</dt>
              <dd>{{ store.formatSyncMode(agent.nft.sync_mode) }}</dd>
            </div>
            <div>
              <dt>NFT Token</dt>
              <dd>{{ agent.nft.token_id }}</dd>
            </div>
            <div>
              <dt>Chain Token</dt>
              <dd>{{ agent.nft.chain_token_id || "Off-chain only" }}</dd>
            </div>
          </dl>
        </section>

        <section class="panel panel-soft">
          <header class="panel-header">
            <div>
              <p class="section-label">Prompt</p>
              <h3>System Prompt</h3>
            </div>
          </header>
          <pre class="code-block">{{ agent.system_prompt }}</pre>
        </section>

        <section class="panel panel-soft">
          <header class="panel-header">
            <div>
              <p class="section-label">Metadata</p>
              <h3>{{ store.state.drawer.metadata?.name || "Token metadata" }}</h3>
            </div>
            <button class="ghost-button" type="button" @click="copyTokenUri">Copy tokenURI</button>
          </header>
          <div v-if="store.state.drawer.metadata" class="drawer-metadata">
            <div class="drawer-media">
              <img :src="store.state.drawer.metadata.image" :alt="store.state.drawer.metadata.name || agent.name" />
            </div>
            <div class="drawer-copy">
              <p>{{ store.state.drawer.metadata.description }}</p>
              <dl class="detail-list detail-list-two">
                <div>
                  <dt>tokenURI</dt>
                  <dd>{{ agent.nft.metadata_uri || store.state.drawer.metadata.external_url || "Unavailable" }}</dd>
                </div>
                <div>
                  <dt>Image</dt>
                  <dd>{{ store.state.drawer.metadata.image || "Unavailable" }}</dd>
                </div>
                <div>
                  <dt>External URL</dt>
                  <dd>{{ store.state.drawer.metadata.external_url || "Unavailable" }}</dd>
                </div>
              </dl>
            </div>
          </div>
          <div v-if="store.state.drawer.metadata?.attributes?.length" class="attribute-grid">
            <article
              v-for="attribute in store.state.drawer.metadata.attributes"
              :key="`${attribute.trait_type}-${attribute.value}`"
              class="attribute-card"
            >
              <span>{{ attribute.trait_type || attribute.display_type || "Attribute" }}</span>
              <strong>{{ attribute.value ?? "Unknown" }}</strong>
            </article>
          </div>
        </section>

        <section class="panel panel-soft">
          <header class="panel-header">
            <div>
              <p class="section-label">History</p>
              <h3>Recent Runs</h3>
            </div>
            <span class="panel-chip">{{ recentRuns.length }} loaded</span>
          </header>
          <div v-if="!recentRuns.length" class="empty-state">No run history yet for this agent.</div>
          <div v-else class="drawer-run-list">
            <article v-for="run in recentRuns" :key="run.id" class="entity-card">
              <div class="entity-card-header">
                <strong>{{ run.id }}</strong>
                <div class="action-row">
                  <span class="status-badge">{{ run.status }}</span>
                  <button class="ghost-button" type="button" @click="store.toggleDrawerRunExpansion(run.id)">
                    {{ store.state.drawer.expandedRunIds.includes(run.id) ? "Hide Output" : "Show Output" }}
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
              <pre v-if="store.state.drawer.expandedRunIds.includes(run.id)" class="code-block">{{ store.formatRunOutput(run.output) }}</pre>
            </article>
          </div>
        </section>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { computed } from "vue";

import { useRuntimeStore } from "@/store/runtime";

const store = useRuntimeStore();

const agent = computed(() => store.findAgentById(store.state.drawer.agentId));
const ownerWallet = computed(() => store.resolveWalletById(agent.value?.nft.owner_wallet_id));
const recentRuns = computed(() => store.state.drawer.runs.slice(0, 8));

async function copyTokenUri() {
  const tokenUri = agent.value?.nft.metadata_uri || store.state.drawer.metadata?.external_url || "";
  await store.copyText(tokenUri);
  store.showFlash("tokenURI copied.", "success");
}
</script>

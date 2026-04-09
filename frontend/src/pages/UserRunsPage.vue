<template>
  <div class="wallet-page-stack">
    <section class="wallet-page-kpis">
      <article class="wallet-page-kpi">
        <span>My runs</span>
        <strong>{{ myRuns.length }}</strong>
        <p>{{ activeRuns.length }} active · {{ completedRuns.length }} completed</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Owned agents</span>
        <strong>{{ ownedAgents.length }}</strong>
        <p>Agents currently available for dispatch from this wallet.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Dead letter</span>
        <strong>{{ deadLetterCount }}</strong>
        <p>Terminal runs that need manual retry or review.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Run ready</span>
        <strong>{{ activeRuns.length ? "Busy" : "Idle" }}</strong>
        <p>Use this lane for ad hoc work, retries, and output inspection.</p>
      </article>
    </section>

    <section class="wallet-page-grid">
      <div class="wallet-page-main">
        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Dispatch</p>
              <h2>Queue a run</h2>
            </div>
            <span class="wallet-status-pill is-pending">{{ activeRuns.length }} active</span>
          </header>

          <form class="wallet-form-grid" @submit.prevent="submitRun">
            <label class="wallet-field wallet-field-full">
              <span>Owned agent</span>
              <select v-model="runForm.agent_id" required>
                <option disabled value="">Select one of your agents</option>
                <option v-for="agent in ownedAgents" :key="agent.id" :value="agent.id">
                  {{ agent.name }} · {{ agent.id }}
                </option>
              </select>
            </label>
            <label class="wallet-field wallet-field-full">
              <span>Task</span>
              <textarea v-model="runForm.task" rows="5" placeholder="Draft a market summary for my portfolio." required />
            </label>
            <label class="wallet-field">
              <span>Max attempts</span>
              <input v-model="runForm.max_attempts" type="number" min="1" max="10" step="1" required />
            </label>
            <label class="wallet-field">
              <span>Timeout seconds</span>
              <input v-model="runForm.timeout_seconds" type="number" min="1" max="3600" step="1" required />
            </label>
            <div class="wallet-form-actions wallet-field-full">
              <button class="wallet-home-primary" type="submit">Queue run</button>
            </div>
          </form>
        </article>

        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">History</p>
              <h2>Execution history</h2>
            </div>
            <span class="wallet-status-pill">{{ myRuns.length }} runs</span>
          </header>

          <div class="wallet-home-table-shell">
            <div class="wallet-home-table-head wallet-runs-table">
              <div>Run</div>
              <div>Agent</div>
              <div>Timeline</div>
              <div>Status</div>
              <div>Actions</div>
            </div>

            <div
              v-for="run in myRuns"
              :key="run.id"
              class="wallet-home-table-row wallet-runs-table"
            >
              <div>
                <strong>{{ run.id }}</strong>
                <span>{{ store.truncate(run.task_input, 72) }}</span>
              </div>
              <div>{{ store.findAgentById(run.agent_id)?.name || run.agent_id }}</div>
              <div>{{ store.formatDateTime(run.queued_at) }}</div>
              <div>
                <span class="wallet-status-pill" :class="runTone(run.status)">{{ run.status }}</span>
              </div>
              <div class="wallet-home-inline-meta">
                <button
                  v-if="!store.isTerminalRun(run)"
                  class="wallet-table-button"
                  type="button"
                  @click="store.cancelRun(run.id)"
                >
                  Cancel
                </button>
                <button
                  v-else
                  class="wallet-table-button"
                  type="button"
                  @click="store.retryRun(run.id)"
                >
                  Retry
                </button>
                <RouterLink :to="`/app/runs/${run.id}`">Detail</RouterLink>
              </div>
            </div>

            <div v-if="!myRuns.length" class="empty-state">
              No runs submitted by this wallet yet.
            </div>
          </div>
        </article>
      </div>

      <aside class="wallet-page-side">
        <article class="wallet-side-card">
          <div class="wallet-side-title">Current activity</div>
          <div class="wallet-side-list">
            <div v-for="run in activeRuns.slice(0, 5)" :key="run.id">
              <strong>{{ store.findAgentById(run.agent_id)?.name || run.agent_id }}</strong>
              <span>{{ run.status }} · {{ run.attempt_count }} / {{ run.max_attempts }} attempts</span>
            </div>
            <div v-if="!activeRuns.length" class="wallet-side-empty">No active runs for this wallet right now.</div>
          </div>
        </article>

        <article class="wallet-side-card">
          <div class="wallet-side-title">Execution posture</div>
          <div class="wallet-side-list">
            <div>
              <strong>Active lane</strong>
              <span>{{ activeRuns.length ? "Queue currently busy." : "Queue is ready for a new task." }}</span>
            </div>
            <div>
              <strong>Dead letter</strong>
              <span>{{ deadLetterCount }} runs require manual attention.</span>
            </div>
            <div>
              <strong>Retry path</strong>
              <span>Terminal runs can be retried directly from the table.</span>
            </div>
          </div>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive } from "vue";

import { useRuntimeStore } from "@/store/runtime";

const store = useRuntimeStore();

const runForm = reactive({
  agent_id: "",
  task: "",
  max_attempts: 3,
  timeout_seconds: 90,
});

const currentWalletId = computed(() => store.state.metamask.wallet?.id || null);
const ownedAgents = computed(() =>
  currentWalletId.value ? store.state.agents.filter((agent) => agent.nft.owner_wallet_id === currentWalletId.value) : []
);
const myRuns = computed(() =>
  currentWalletId.value
    ? [...store.state.runs]
        .filter((run) => run.requested_by_wallet_id === currentWalletId.value)
        .sort((left, right) => Date.parse(right.queued_at || right.started_at || 0) - Date.parse(left.queued_at || left.started_at || 0))
    : []
);
const activeRuns = computed(() => myRuns.value.filter((run) => !store.isTerminalRun(run)));
const completedRuns = computed(() => myRuns.value.filter((run) => run.status === "COMPLETED"));
const deadLetterCount = computed(() => myRuns.value.filter((run) => store.isDeadLettered(run)).length);

async function submitRun() {
  await store.queueRun({
    agent_id: runForm.agent_id,
    task: runForm.task,
    max_attempts: Number(runForm.max_attempts),
    timeout_seconds: Number(runForm.timeout_seconds),
  });
  runForm.task = "";
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

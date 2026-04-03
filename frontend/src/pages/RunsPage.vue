<template>
  <div class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Queue Depth</span>
        <strong>{{ store.state.runMetrics?.queue_depth ?? store.queuedRuns.value.length }}</strong>
        <p>{{ store.state.runMetrics?.retry_pending_count ?? 0 }} retry pending</p>
      </article>
      <article class="metric-card">
        <span>Running</span>
        <strong>{{ store.state.runMetrics?.running ?? store.runningRuns.value.length }}</strong>
        <p>{{ store.state.runMetrics?.cancel_requested ?? 0 }} cancel requested</p>
      </article>
      <article class="metric-card">
        <span>Dead Letter</span>
        <strong>{{ store.state.runMetrics?.dead_letter_count ?? 0 }}</strong>
        <p>Terminal runs that exhausted retry budget.</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Dispatch</p>
          <h2>Queue New Run</h2>
        </div>
        <span class="panel-chip">{{ store.queuedRuns.value.length }} queued</span>
      </header>
      <form class="form-grid compact-grid" @submit.prevent="submitRun">
        <label class="field field-full">
          <span>Agent</span>
          <select v-model="runForm.agent_id" required>
            <option disabled value="">Select an agent</option>
            <option v-for="agent in store.state.agents" :key="agent.id" :value="agent.id">
              {{ agent.name }} · {{ agent.id }}
            </option>
          </select>
        </label>
        <label class="field field-full">
          <span>Task</span>
          <textarea v-model="runForm.task" rows="5" placeholder="Research a new NFT collection." required />
        </label>
        <label class="field">
          <span>Max Attempts</span>
          <input v-model="runForm.max_attempts" type="number" min="1" max="10" step="1" required />
        </label>
        <label class="field">
          <span>Timeout Seconds</span>
          <input v-model="runForm.timeout_seconds" type="number" min="1" max="3600" step="1" required />
        </label>
        <div class="action-row field-full">
          <button class="primary-button" type="submit">Queue Run</button>
        </div>
      </form>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Queue</p>
          <h2>Live Execution Lane</h2>
        </div>
        <span class="panel-chip">{{ liveRuns.length }} active</span>
      </header>
      <div v-if="!liveRuns.length" class="empty-state">
        No runs yet. Queue a task to warm the execution lane.
      </div>
      <div v-else class="data-table">
        <div class="data-table-head runs-table">
          <span>Run</span>
          <span>Agent</span>
          <span>Requester</span>
          <span>Attempts</span>
          <span>Status</span>
          <span>Actions</span>
        </div>
        <article
          v-for="run in liveRuns"
          :key="run.id"
          class="data-table-row runs-table"
        >
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ run.id }}</strong>
              <span class="text-muted">{{ store.formatDateTime(run.started_at || run.queued_at) }}</span>
            </div>
          </div>
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ run.agent_id }}</strong>
              <span class="text-muted">{{ store.truncate(run.task_input, 72) }}</span>
            </div>
          </div>
          <div class="table-cell">
            <span class="text-muted">{{ store.describeWallet(run.requested_by_wallet_id) }}</span>
          </div>
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ run.attempt_count }} / {{ run.max_attempts }}</strong>
              <span class="text-muted">{{ run.timeout_seconds }}s timeout</span>
            </div>
          </div>
          <div class="table-cell">
            <span class="status-badge">{{ run.status }}</span>
          </div>
          <div class="table-cell">
            <div class="table-actions">
              <button class="ghost-button" type="button" @click="router.push(`/runs/history/${run.id}`)">Detail</button>
              <button
                v-if="!store.isTerminalRun(run)"
                class="ghost-button"
                type="button"
                @click="store.cancelRun(run.id)"
              >
                Cancel
              </button>
              <button
                v-else
                class="ghost-button"
                type="button"
                @click="store.retryRun(run.id)"
              >
                Retry
              </button>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const route = useRoute();
const router = useRouter();
const store = useRuntimeStore();

const runForm = reactive({
  agent_id: "",
  task: "",
  max_attempts: "3",
  timeout_seconds: "90",
});
const liveRuns = computed(() => [...store.state.runs].filter((run) => run.status === "QUEUED" || run.status === "RUNNING"));

watch(
  () => route.query,
  (query) => {
    if (typeof query.agent_id === "string") {
      runForm.agent_id = query.agent_id;
    }
  },
  { immediate: true }
);

async function submitRun() {
  await store.queueRun({
    agentId: runForm.agent_id,
    task: runForm.task,
    maxAttempts: runForm.max_attempts,
    timeoutSeconds: runForm.timeout_seconds,
  });
  runForm.task = "";
}
</script>

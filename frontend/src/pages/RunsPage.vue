<template>
  <div class="page-grid page-grid-two">
    <section class="panel">
      <header class="panel-header">
        <div>
          <p class="section-label">Actions</p>
          <h2>Run Actions</h2>
        </div>
        <span class="panel-chip">{{ store.queuedRuns.value.length }} queued</span>
      </header>
      <p class="panel-intro">
        Compose a task, choose the agent that should execute it, and send it into the runtime queue. This page is designed for immediate dispatch, not long-term history.
      </p>
      <div class="surface-block">
        <p class="surface-kicker">Dispatch Task</p>
        <h3 class="surface-title">Send a new run into the execution lane</h3>
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
            <textarea v-model="runForm.task" rows="4" placeholder="Research a new NFT collection." required />
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
      </div>
    </section>

    <section class="panel">
      <header class="panel-header">
        <div>
          <p class="section-label">Queue</p>
          <h2>Run Feed</h2>
        </div>
        <span class="panel-chip">{{ liveRuns.length }} active</span>
      </header>
      <p class="panel-intro">
        Monitor the live lane with enough detail to understand what is moving now, while keeping the visual weight lighter than the full history view.
      </p>
      <div class="metric-strip">
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
      </div>
      <div v-if="!liveRuns.length" class="empty-state">
        No runs yet. Queue a task to warm the execution lane.
      </div>
      <div v-else class="stack-grid">
        <article
          v-for="run in liveRuns"
          :key="run.id"
          class="entity-card run-card"
        >
          <div class="entity-card-header">
            <strong>{{ run.id }}</strong>
            <div class="action-row">
              <span class="status-badge">{{ run.status }}</span>
              <button class="ghost-button" type="button" @click="router.push(`/runs/history/${run.id}`)">Detail</button>
            </div>
          </div>
          <dl class="detail-list">
            <div>
              <dt>Agent</dt>
              <dd>{{ run.agent_id }}</dd>
            </div>
            <div>
              <dt>Owner Wallet</dt>
              <dd>{{ store.describeWallet(run.requested_by_wallet_id) }}</dd>
            </div>
            <div>
              <dt>Task</dt>
              <dd>{{ store.truncate(run.task_input, 160) }}</dd>
            </div>
            <div>
              <dt>Attempts</dt>
              <dd>{{ run.attempt_count }} / {{ run.max_attempts }}</dd>
            </div>
            <div>
              <dt>Timeout</dt>
              <dd>{{ run.timeout_seconds }}s</dd>
            </div>
            <div>
              <dt>Started</dt>
              <dd>{{ store.formatDateTime(run.started_at) }}</dd>
            </div>
            <div v-if="run.next_retry_at">
              <dt>Next Retry</dt>
              <dd>{{ store.formatDateTime(run.next_retry_at) }}</dd>
            </div>
          </dl>
          <p v-if="run.failure_reason" class="overview-link-copy">{{ run.failure_reason }}</p>
          <div class="action-row">
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

<template>
  <div class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Total Runs</span>
        <strong>{{ sortedRuns.length }}</strong>
        <p>{{ store.state.runMetrics?.queue_depth ?? 0 }} queued · {{ store.state.runMetrics?.running ?? 0 }} running</p>
      </article>
      <article class="metric-card">
        <span>Average Duration</span>
        <strong>{{ averageDurationLabel }}</strong>
        <p>Derived from completed runs in the current runtime.</p>
      </article>
      <article class="metric-card">
        <span>Dead Lettered</span>
        <strong>{{ store.state.runMetrics?.dead_letter_count ?? 0 }}</strong>
        <p>Runs that exhausted retry budget and need operator review.</p>
      </article>
    </section>

    <section class="panel page-grid-full">
      <header class="panel-header">
        <div>
          <p class="section-label">History</p>
          <h2>Execution History</h2>
        </div>
        <span class="panel-chip">{{ sortedRuns.length }} runs</span>
      </header>
      <div v-if="!sortedRuns.length" class="empty-state">
        No execution history yet.
      </div>
      <div v-else class="data-table">
        <div class="data-table-head history-table">
          <span>Run</span>
          <span>Agent</span>
          <span>Requester</span>
          <span>Attempts</span>
          <span>Timeline</span>
          <span>Actions</span>
        </div>
        <template v-for="run in sortedRuns" :key="run.id">
          <article class="data-table-row history-table">
            <div class="table-cell">
              <div class="cell-stack">
                <strong>{{ run.id }}</strong>
                <div class="table-badge-row">
                  <span class="status-badge">{{ run.status }}</span>
                  <span v-if="store.isDeadLettered(run)" class="status-badge">Dead Letter</span>
                </div>
              </div>
            </div>
            <div class="table-cell">
              <div class="cell-stack">
                <strong>{{ run.agent_id }}</strong>
                <span class="text-muted">{{ store.truncate(run.task_input, 84) }}</span>
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
              <div class="cell-stack">
                <strong>{{ store.formatRunDuration(run) }}</strong>
                <span class="text-muted">{{ store.formatDateTime(run.queued_at) }}</span>
                <span v-if="run.next_retry_at" class="text-muted">Retry {{ store.formatDateTime(run.next_retry_at) }}</span>
              </div>
            </div>
            <div class="table-cell">
              <div class="table-actions">
                <button class="ghost-button" type="button" @click="toggleRun(run.id)">
                  {{ expandedRunIds.includes(run.id) ? "Hide Output" : "Show Output" }}
                </button>
                <button class="ghost-button" type="button" @click="router.push(`/runs/history/${run.id}`)">Detail</button>
                <button class="ghost-button" type="button" @click="router.push(`/agents/${run.agent_id}`)">Agent</button>
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
          <article v-if="expandedRunIds.includes(run.id)" class="data-table-row history-table-expanded">
            <div class="table-cell table-cell-full">
              <div v-if="run.failure_reason" class="surface-block compact-surface-block">
                <p class="surface-kicker">Failure</p>
                <h3 class="surface-title">{{ run.failure_reason }}</h3>
              </div>
              <pre class="code-block">{{ store.formatRunOutput(run.output) }}</pre>
            </div>
          </article>
        </template>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive } from "vue";
import { useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const router = useRouter();
const store = useRuntimeStore();
const expandedRunIds = reactive([]);

const sortedRuns = computed(() =>
  [...store.state.runs].sort((left, right) => {
    const leftTime = Date.parse(left.queued_at || left.started_at || 0);
    const rightTime = Date.parse(right.queued_at || right.started_at || 0);
    return rightTime - leftTime;
  })
);

const averageDurationLabel = computed(() => {
  const value = store.state.runMetrics?.average_duration_seconds;
  if (value === null || value === undefined) {
    return "No data";
  }
  if (value < 60) {
    return `${value}s`;
  }
  const minutes = Math.floor(value / 60);
  const seconds = Math.round(value % 60);
  return seconds ? `${minutes}m ${seconds}s` : `${minutes}m`;
});

function toggleRun(runId) {
  const index = expandedRunIds.indexOf(runId);
  if (index >= 0) {
    expandedRunIds.splice(index, 1);
    return;
  }
  expandedRunIds.push(runId);
}
</script>

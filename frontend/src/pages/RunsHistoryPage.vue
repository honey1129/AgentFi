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

    <section class="panel">
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
      <div v-else class="stack-grid">
        <article v-for="run in sortedRuns" :key="run.id" class="entity-card">
          <div class="entity-card-header">
            <strong>{{ run.id }}</strong>
            <div class="action-row">
              <span class="status-badge">{{ run.status }}</span>
              <span v-if="store.isDeadLettered(run)" class="status-badge">Dead Letter</span>
              <button class="ghost-button" type="button" @click="toggleRun(run.id)">
                {{ expandedRunIds.includes(run.id) ? "Hide Output" : "Show Output" }}
              </button>
              <button class="ghost-button" type="button" @click="router.push(`/runs/history/${run.id}`)">Detail</button>
              <button class="ghost-button" type="button" @click="router.push(`/agents/${run.agent_id}`)">Agent</button>
            </div>
          </div>
          <dl class="detail-list detail-list-two">
            <div>
              <dt>Agent</dt>
              <dd>{{ run.agent_id }}</dd>
            </div>
            <div>
              <dt>Requester</dt>
              <dd>{{ store.describeWallet(run.requested_by_wallet_id) }}</dd>
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
              <dt>Queued</dt>
              <dd>{{ store.formatDateTime(run.queued_at) }}</dd>
            </div>
            <div>
              <dt>Duration</dt>
              <dd>{{ store.formatRunDuration(run) }}</dd>
            </div>
            <div>
              <dt>Task</dt>
              <dd>{{ store.truncate(run.task_input, 220) }}</dd>
            </div>
            <div v-if="run.failure_reason">
              <dt>Failure</dt>
              <dd>{{ run.failure_reason }}</dd>
            </div>
            <div v-if="run.next_retry_at">
              <dt>Next Retry</dt>
              <dd>{{ store.formatDateTime(run.next_retry_at) }}</dd>
            </div>
          </dl>
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
          <pre v-if="expandedRunIds.includes(run.id)" class="code-block">{{ store.formatRunOutput(run.output) }}</pre>
        </article>
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

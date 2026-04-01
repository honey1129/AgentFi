<template>
  <div v-if="schedule" class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Schedule State</span>
        <strong>{{ schedule.enabled ? "Enabled" : "Paused" }}</strong>
        <p>{{ schedule.enabled ? "This automation can enqueue new agent runs on its interval." : "The rule exists but is not currently dispatching runs." }}</p>
      </article>
      <article class="metric-card">
        <span>Next Dispatch</span>
        <strong>{{ nextRunLabel }}</strong>
        <p>{{ schedule.interval_seconds }} second interval for agent {{ schedule.agent_id }}.</p>
      </article>
      <article class="metric-card">
        <span>Recent Activity</span>
        <strong>{{ relatedRuns.length }}</strong>
        <p>{{ relatedRuns[0] ? `Latest run status: ${relatedRuns[0].status}.` : "No recent runs have been linked to this scheduled agent yet." }}</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Automation</p>
          <h2>{{ schedule.id }}</h2>
        </div>
        <span class="panel-chip">{{ schedule.interval_seconds }}s</span>
      </header>
      <dl class="detail-list detail-list-two">
        <div>
          <dt>Agent</dt>
          <dd>{{ schedule.agent_id }}</dd>
        </div>
        <div>
          <dt>Enabled</dt>
          <dd>{{ String(schedule.enabled) }}</dd>
        </div>
        <div>
          <dt>Next Run</dt>
          <dd>{{ store.formatDateTime(schedule.next_run_at) }}</dd>
        </div>
        <div>
          <dt>Interval</dt>
          <dd>{{ schedule.interval_seconds }} seconds</dd>
        </div>
      </dl>
      <div class="action-row">
        <button class="ghost-button" type="button" @click="router.push(`/agents/${schedule.agent_id}`)">Agent Detail</button>
      </div>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Template</p>
          <h2>Task Template</h2>
        </div>
      </header>
      <pre class="code-block">{{ schedule.task_template }}</pre>
    </section>

    <section class="panel page-grid-full">
      <header class="panel-header">
        <div>
          <p class="section-label">Related Runs</p>
          <h2>Recent Agent Activity</h2>
        </div>
        <span class="panel-chip">{{ relatedRuns.length }} runs</span>
      </header>
      <div v-if="!relatedRuns.length" class="empty-state">
        No recent runs for this agent yet.
      </div>
      <div v-else class="stack-grid">
        <article v-for="run in relatedRuns" :key="run.id" class="entity-card">
          <div class="entity-card-header">
            <strong>{{ run.id }}</strong>
            <span class="status-badge">{{ run.status }}</span>
          </div>
          <dl class="detail-list detail-list-two">
            <div>
              <dt>Started</dt>
              <dd>{{ store.formatDateTime(run.started_at) }}</dd>
            </div>
            <div>
              <dt>Requester</dt>
              <dd>{{ store.describeWallet(run.requested_by_wallet_id) }}</dd>
            </div>
            <div>
              <dt>Task</dt>
              <dd>{{ store.truncate(run.task_input, 220) }}</dd>
            </div>
          </dl>
          <div class="action-row">
            <button class="ghost-button" type="button" @click="router.push(`/runs/history/${run.id}`)">Run Detail</button>
          </div>
        </article>
      </div>
    </section>
  </div>

  <section v-else class="panel">
    <div class="empty-state">Schedule not found in the current runtime state.</div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const route = useRoute();
const router = useRouter();
const store = useRuntimeStore();

const scheduleId = computed(() => String(route.params.scheduleId || ""));
const schedule = computed(() => store.findScheduleById(scheduleId.value));
const relatedRuns = computed(() =>
  schedule.value
    ? [...store.state.runs]
        .filter((run) => run.agent_id === schedule.value.agent_id)
        .sort((left, right) => Date.parse(right.started_at || right.created_at || 0) - Date.parse(left.started_at || left.created_at || 0))
        .slice(0, 6)
    : []
);
const nextRunLabel = computed(() => {
  if (!schedule.value?.next_run_at) {
    return "Pending";
  }
  return store.formatDateTime(schedule.value.next_run_at);
});
</script>

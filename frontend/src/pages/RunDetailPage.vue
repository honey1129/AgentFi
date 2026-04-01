<template>
  <div v-if="run" class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Status</span>
        <strong>{{ run.status }}</strong>
        <p>{{ run.finished_at ? "This run has completed and its output is frozen below." : "This run is still in progress or waiting in the runtime." }}</p>
      </article>
      <article class="metric-card">
        <span>Duration</span>
        <strong>{{ durationLabel }}</strong>
        <p>{{ run.started_at ? `Started ${store.formatDateTime(run.started_at)}.` : "Start time has not been recorded yet." }}</p>
      </article>
      <article class="metric-card">
        <span>Requester</span>
        <strong>{{ store.describeWallet(run.requested_by_wallet_id) }}</strong>
        <p>Agent {{ run.agent_id }} was invoked under this wallet's authority.</p>
      </article>
      <article class="metric-card">
        <span>Attempts</span>
        <strong>{{ run.attempt_count }} / {{ run.max_attempts }}</strong>
        <p>{{ run.timeout_seconds }} second timeout per attempt.</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Execution</p>
          <h2>{{ run.id }}</h2>
        </div>
        <span class="panel-chip">{{ run.status }}</span>
      </header>
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
          <dt>Started</dt>
          <dd>{{ store.formatDateTime(run.started_at) }}</dd>
        </div>
        <div>
          <dt>Finished</dt>
          <dd>{{ store.formatDateTime(run.finished_at) }}</dd>
        </div>
        <div>
          <dt>Queued</dt>
          <dd>{{ store.formatDateTime(run.queued_at) }}</dd>
        </div>
        <div>
          <dt>Next Retry</dt>
          <dd>{{ store.formatDateTime(run.next_retry_at) }}</dd>
        </div>
        <div>
          <dt>Parent Run</dt>
          <dd>{{ run.parent_run_id || "Primary run" }}</dd>
        </div>
        <div>
          <dt>Celery Task</dt>
          <dd>{{ run.celery_task_id || "Pending dispatch" }}</dd>
        </div>
        <div>
          <dt>Cancel Requested</dt>
          <dd>{{ store.formatDateTime(run.cancel_requested_at) }}</dd>
        </div>
        <div>
          <dt>Dead Lettered</dt>
          <dd>{{ store.formatDateTime(run.dead_lettered_at) }}</dd>
        </div>
      </dl>
      <div class="action-row">
        <button
          v-if="!store.isTerminalRun(run)"
          class="primary-button"
          type="button"
          @click="store.cancelRun(run.id)"
        >
          Cancel Run
        </button>
        <button
          v-else
          class="primary-button"
          type="button"
          @click="store.retryRun(run.id)"
        >
          Retry Run
        </button>
        <button class="ghost-button" type="button" @click="router.push(`/agents/${run.agent_id}`)">Agent Detail</button>
        <button class="ghost-button" type="button" @click="router.push(`/wallets/${run.requested_by_wallet_id}`)">Requester Wallet</button>
      </div>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Input</p>
          <h2>Task Payload</h2>
        </div>
      </header>
      <pre class="code-block">{{ run.task_input }}</pre>
    </section>

    <section class="panel page-grid-full">
      <header class="panel-header">
        <div>
          <p class="section-label">Output</p>
          <h2>Execution Output</h2>
        </div>
      </header>
      <div v-if="run.failure_reason" class="surface-block">
        <p class="surface-kicker">Failure Reason</p>
        <h3 class="surface-title">{{ run.failure_reason }}</h3>
        <p class="panel-intro">
          {{ store.isDeadLettered(run) ? "This run is now in dead-letter state and requires manual intervention or a retry." : "The latest failure detail recorded by the runtime." }}
        </p>
      </div>
      <pre class="code-block">{{ store.formatRunOutput(run.output) }}</pre>
    </section>
  </div>

  <section v-else class="panel">
    <div class="empty-state">Run not found in the current runtime state.</div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useRuntimeStore } from "@/store/runtime";

const route = useRoute();
const router = useRouter();
const store = useRuntimeStore();

const runId = computed(() => String(route.params.runId || ""));
const run = computed(() => store.findRunById(runId.value));
const durationLabel = computed(() => store.formatRunDuration(run.value));
</script>

<template>
  <div v-if="isUserView && run" class="wallet-page-stack">
    <section class="wallet-page-kpis">
      <article class="wallet-page-kpi">
        <span>Status</span>
        <strong>{{ run.status }}</strong>
        <p>{{ run.finished_at ? "This run has completed and its output is frozen below." : "This run is still active or waiting in the queue." }}</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Duration</span>
        <strong>{{ durationLabel }}</strong>
        <p>{{ run.started_at ? `Started ${store.formatDateTime(run.started_at)}.` : "Start time has not been recorded yet." }}</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Requester</span>
        <strong>{{ store.describeWallet(run.requested_by_wallet_id) }}</strong>
        <p>Agent {{ run.agent_id }} was invoked under this wallet's authority.</p>
      </article>
      <article class="wallet-page-kpi">
        <span>Attempts</span>
        <strong>{{ run.attempt_count }} / {{ run.max_attempts }}</strong>
        <p>{{ run.timeout_seconds }} second timeout per attempt.</p>
      </article>
    </section>

    <section class="wallet-page-grid">
      <div class="wallet-page-main">
        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Execution</p>
              <h2>{{ run.id }}</h2>
            </div>
            <span class="wallet-status-pill" :class="runTone(run.status)">{{ run.status }}</span>
          </header>

          <div class="wallet-detail-grid">
            <div class="wallet-detail-card">
              <span>Agent</span>
              <strong>{{ run.agent_id }}</strong>
            </div>
            <div class="wallet-detail-card">
              <span>Requester</span>
              <strong>{{ store.describeWallet(run.requested_by_wallet_id) }}</strong>
            </div>
            <div class="wallet-detail-card">
              <span>Started</span>
              <strong>{{ store.formatDateTime(run.started_at) }}</strong>
            </div>
            <div class="wallet-detail-card">
              <span>Finished</span>
              <strong>{{ store.formatDateTime(run.finished_at) }}</strong>
            </div>
            <div class="wallet-detail-card">
              <span>Queued</span>
              <strong>{{ store.formatDateTime(run.queued_at) }}</strong>
            </div>
            <div class="wallet-detail-card">
              <span>Next retry</span>
              <strong>{{ store.formatDateTime(run.next_retry_at) }}</strong>
            </div>
          </div>

          <div v-if="run.failure_reason" class="wallet-inline-card">
            <span>Failure reason</span>
            <strong>{{ run.failure_reason }}</strong>
            <p>{{ store.isDeadLettered(run) ? "This run is now in dead-letter state and needs manual intervention or a retry." : "Latest runtime failure detail recorded for this execution." }}</p>
          </div>

          <div class="wallet-card-actions">
            <button
              v-if="!store.isTerminalRun(run)"
              class="wallet-home-primary"
              type="button"
              @click="store.cancelRun(run.id)"
            >
              Cancel run
            </button>
            <button
              v-else
              class="wallet-home-primary"
              type="button"
              @click="store.retryRun(run.id)"
            >
              Retry run
            </button>
            <button class="wallet-home-secondary" type="button" @click="router.push(`${routePrefix}/agents/${run.agent_id}`)">
              Agent detail
            </button>
          </div>
        </article>

        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Input</p>
              <h2>Task payload</h2>
            </div>
          </header>
          <pre class="wallet-code-block">{{ run.task_input }}</pre>
        </article>

        <article class="wallet-card">
          <header class="wallet-card-header">
            <div>
              <p class="wallet-card-kicker">Output</p>
              <h2>Execution output</h2>
            </div>
          </header>
          <pre class="wallet-code-block">{{ store.formatRunOutput(run.output) }}</pre>
        </article>
      </div>

      <aside class="wallet-page-side">
        <article class="wallet-side-card">
          <div class="wallet-side-title">Execution routing</div>
          <div class="wallet-side-list">
            <div>
              <strong>Parent run</strong>
              <span>{{ run.parent_run_id || "Primary run" }}</span>
            </div>
            <div>
              <strong>Celery task</strong>
              <span>{{ run.celery_task_id || "Pending dispatch" }}</span>
            </div>
            <div>
              <strong>Cancel requested</strong>
              <span>{{ store.formatDateTime(run.cancel_requested_at) }}</span>
            </div>
            <div>
              <strong>Dead lettered</strong>
              <span>{{ store.formatDateTime(run.dead_lettered_at) }}</span>
            </div>
          </div>
        </article>

        <article class="wallet-side-card">
          <div class="wallet-side-title">Runtime posture</div>
          <div class="wallet-side-list">
            <div>
              <strong>Timeout</strong>
              <span>{{ run.timeout_seconds }} seconds</span>
            </div>
            <div>
              <strong>Attempts</strong>
              <span>{{ run.attempt_count }} / {{ run.max_attempts }}</span>
            </div>
            <div>
              <strong>Status</strong>
              <span>{{ store.isDeadLettered(run) ? "Needs review" : "Normal flow" }}</span>
            </div>
          </div>
        </article>
      </aside>
    </section>
  </div>

  <div v-else-if="run" class="page-grid">
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
      <div class="stack-grid">
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
        <div v-if="run.failure_reason" class="surface-block">
          <p class="surface-kicker">Failure Reason</p>
          <h3 class="surface-title">{{ run.failure_reason }}</h3>
          <p class="panel-intro compact-panel-intro">
            {{ store.isDeadLettered(run) ? "This run is now in dead-letter state and requires manual intervention or a retry." : "The latest failure detail recorded by the runtime." }}
          </p>
        </div>
      </div>
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
        <button class="ghost-button" type="button" @click="router.push(`${routePrefix}/agents/${run.agent_id}`)">Agent Detail</button>
        <button
          v-if="!isUserView"
          class="ghost-button"
          type="button"
          @click="router.push(`/wallets/${run.requested_by_wallet_id}`)"
        >
          Requester Wallet
        </button>
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
const isUserView = computed(() => route.meta.audience === "user");
const routePrefix = computed(() => (isUserView.value ? "/app" : ""));

const runId = computed(() => String(route.params.runId || ""));
const run = computed(() => store.findRunById(runId.value));
const durationLabel = computed(() => store.formatRunDuration(run.value));

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

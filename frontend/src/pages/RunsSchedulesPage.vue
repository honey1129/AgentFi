<template>
  <div class="page-grid">
    <section class="metric-strip">
      <article class="metric-card">
        <span>Schedules</span>
        <strong>{{ store.state.schedules.length }}</strong>
        <p>Automation rules currently registered in the runtime.</p>
      </article>
      <article class="metric-card">
        <span>Enabled</span>
        <strong>{{ enabledSchedulesCount }}</strong>
        <p>Schedules actively allowed to dispatch new runs.</p>
      </article>
      <article class="metric-card">
        <span>Tracked Agents</span>
        <strong>{{ scheduledAgentsCount }}</strong>
        <p>Distinct agents currently attached to a schedule.</p>
      </article>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Automation</p>
          <h2>Create Schedule</h2>
        </div>
        <span class="panel-chip">{{ store.state.schedules.length }} schedules</span>
      </header>
      <form class="form-grid compact-grid" @submit.prevent="submitSchedule">
        <label class="field field-full">
          <span>Agent</span>
          <select v-model="scheduleForm.agent_id" required>
            <option disabled value="">Select an agent</option>
            <option v-for="agent in store.state.agents" :key="agent.id" :value="agent.id">
              {{ agent.name }} · {{ agent.id }}
            </option>
          </select>
        </label>
        <label class="field field-full">
          <span>Task Template</span>
          <textarea v-model="scheduleForm.task" rows="4" placeholder="Write one market update." required />
        </label>
        <label class="field">
          <span>Interval Seconds</span>
          <input v-model="scheduleForm.interval_seconds" type="number" min="1" step="1" required />
        </label>
        <label class="field">
          <span>Starts In Seconds</span>
          <input v-model="scheduleForm.starts_in_seconds" type="number" min="0" step="1" required />
        </label>
        <div class="action-row field-full">
          <button class="primary-button" type="submit">Schedule Agent</button>
        </div>
      </form>
    </section>

    <section class="panel page-grid-half">
      <header class="panel-header">
        <div>
          <p class="section-label">Registry</p>
          <h2>Schedules</h2>
        </div>
        <span class="panel-chip">{{ store.state.schedules.length }} schedules</span>
      </header>
      <div v-if="!store.state.schedules.length" class="empty-state">
        No schedules yet.
      </div>
      <div v-else class="data-table">
        <div class="data-table-head schedule-table">
          <span>Schedule</span>
          <span>Agent</span>
          <span>State</span>
          <span>Timing</span>
          <span>Template</span>
          <span>Actions</span>
        </div>
        <article v-for="schedule in store.state.schedules" :key="schedule.id" class="data-table-row schedule-table">
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ schedule.id }}</strong>
              <span class="text-muted">{{ schedule.interval_seconds }}s interval</span>
            </div>
          </div>
          <div class="table-cell">
            <span class="text-muted">{{ schedule.agent_id }}</span>
          </div>
          <div class="table-cell">
            <span class="status-badge">{{ schedule.enabled ? "Enabled" : "Paused" }}</span>
          </div>
          <div class="table-cell">
            <div class="cell-stack">
              <strong>{{ store.formatDateTime(schedule.next_run_at) }}</strong>
              <span class="text-muted">Starts in {{ schedule.starts_in_seconds ?? 0 }}s</span>
            </div>
          </div>
          <div class="table-cell">
            <span class="text-muted">{{ store.truncate(schedule.task_template, 120) }}</span>
          </div>
          <div class="table-cell">
            <div class="table-actions">
              <button class="ghost-button" type="button" @click="router.push(`/runs/schedules/${schedule.id}`)">Detail</button>
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

const scheduleForm = reactive({
  agent_id: "",
  task: "",
  interval_seconds: "300",
  starts_in_seconds: "30",
});
const enabledSchedulesCount = computed(() => store.state.schedules.filter((schedule) => schedule.enabled).length);
const scheduledAgentsCount = computed(() => new Set(store.state.schedules.map((schedule) => schedule.agent_id)).size);

watch(
  () => route.query,
  (query) => {
    if (typeof query.agent_id === "string") {
      scheduleForm.agent_id = query.agent_id;
    }
  },
  { immediate: true }
);

async function submitSchedule() {
  await store.createSchedule({ ...scheduleForm });
}
</script>

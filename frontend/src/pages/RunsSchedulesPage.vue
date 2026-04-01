<template>
  <div class="page-grid page-grid-two">
    <section class="panel">
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

    <section class="panel">
      <header class="panel-header">
        <div>
          <p class="section-label">Automation</p>
          <h2>Schedules</h2>
        </div>
      </header>
      <div v-if="!store.state.schedules.length" class="empty-state">
        No schedules yet.
      </div>
      <div v-else class="entity-grid">
        <article v-for="schedule in store.state.schedules" :key="schedule.id" class="entity-card">
          <div class="entity-card-header">
            <strong>{{ schedule.id }}</strong>
            <span class="status-badge">{{ schedule.interval_seconds }}s</span>
          </div>
          <dl class="detail-list">
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
              <dd>{{ schedule.next_run_at }}</dd>
            </div>
            <div>
              <dt>Task</dt>
              <dd>{{ store.truncate(schedule.task_template, 180) }}</dd>
            </div>
          </dl>
          <div class="action-row">
            <button class="ghost-button" type="button" @click="router.push(`/runs/schedules/${schedule.id}`)">Detail</button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, watch } from "vue";
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

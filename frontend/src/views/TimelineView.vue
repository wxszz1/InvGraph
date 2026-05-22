<template>
  <div class="timeline-view">
    <div class="timeline-controls">
      <div class="filter-group">
        <label>时间范围</label>
        <div class="range-row">
          <input type="number" v-model="startYear" min="2010" max="2030" class="year-input" />
          <span class="range-sep">—</span>
          <input type="number" v-model="endYear" min="2010" max="2030" class="year-input" />
          <button @click="loadTimeline" class="btn-sm">查询</button>
        </div>
      </div>
      <div class="legend">
        <span class="legend-item"><span class="dot purple"></span>投资事件</span>
        <span class="legend-item"><span class="dot green"></span>企业节点</span>
        <span class="legend-item"><span class="dot blue"></span>投资机构</span>
      </div>
    </div>

    <div class="timeline-content">
      <div class="timeline-chart">
        <GraphNetwork :nodes="graphData.nodes" :edges="graphData.edges" />
      </div>
      <div class="timeline-sidebar">
        <h3>时间线</h3>
        <div class="timeline-list" v-if="timelineEvents.length">
          <div class="tl-item" v-for="(ev, i) in timelineEvents" :key="i">
            <div class="tl-dot"></div>
            <div class="tl-card">
              <div class="tl-time">{{ ev.time }}</div>
              <div class="tl-desc">
                <span class="tl-head">{{ ev.head }}</span>
                <span class="tl-rel">{{ relLabel(ev.relation) }}</span>
                <span class="tl-tail">{{ ev.tail }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="#444" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <p>选择时间范围查看投融资事件</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'
import GraphNetwork from '../components/GraphNetwork.vue'

export default {
  components: { GraphNetwork },
  data() {
    return {
      startYear: 2010,
      endYear: 2025,
      graphData: { nodes: [], edges: [] }
    }
  },
  computed: {
    timelineEvents() {
      return this.graphData.edges
        .map(e => ({
          head: this.getNodeName(e.from),
          tail: this.getNodeName(e.to),
          relation: e.label,
          time: e.properties?.time || ''
        }))
        .filter(e => e.time)
        .sort((a, b) => a.time.localeCompare(b.time))
    }
  },
  async mounted() {
    await this.loadTimeline()
  },
  methods: {
    getNodeName(id) {
      const node = this.graphData.nodes.find(n => n.id === id)
      return node?.properties?.name || id
    },
    relLabel(rel) {
      const map = { INVEST: '投资', LEAD: '领投', FOLLOW: '跟投', ACQUIRE: '收购' }
      return map[rel] || rel
    },
    async loadTimeline() {
      try {
        const res = await api.filterGraph(String(this.startYear), String(this.endYear))
        this.graphData = res.data.data || { nodes: [], edges: [] }
      } catch (e) { console.error('加载失败:', e) }
    }
  }
}
</script>

<style scoped>
.timeline-view { height: 100%; display: flex; flex-direction: column; gap: 16px; }
.timeline-controls {
  display: flex; justify-content: space-between; align-items: center;
  background: #1a1d2e; border: 1px solid #2a2d3a; border-radius: 12px;
  padding: 14px 20px;
}
.filter-group label { font-size: 13px; color: #888; margin-right: 12px; }
.range-row { display: flex; align-items: center; gap: 8px; }
.year-input {
  width: 80px; padding: 6px 10px;
  background: #12141f; border: 1px solid #2a2d3a;
  border-radius: 6px; color: #e0e0e0; font-size: 14px;
  text-align: center;
}
.year-input:focus { outline: none; border-color: #6c5ce7; }
.range-sep { color: #555; }
.btn-sm {
  padding: 6px 14px; border: none; border-radius: 6px;
  background: linear-gradient(135deg, #6c5ce7, #a855f7);
  color: #fff; font-size: 13px; cursor: pointer;
}
.legend { display: flex; gap: 16px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #888; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.purple { background: #a855f7; }
.dot.green { background: #00b894; }
.dot.blue { background: #74b9ff; }

.timeline-content {
  display: grid; grid-template-columns: 1.6fr 1fr; gap: 16px;
  flex: 1; min-height: 0;
}
.timeline-chart {
  background: #1a1d2e; border: 1px solid #2a2d3a;
  border-radius: 12px; overflow: hidden;
}
.timeline-sidebar {
  background: #1a1d2e; border: 1px solid #2a2d3a;
  border-radius: 12px; display: flex; flex-direction: column;
  overflow: hidden;
}
.timeline-sidebar h3 {
  padding: 14px 20px; font-size: 14px; font-weight: 600;
  border-bottom: 1px solid #2a2d3a;
}
.timeline-list { flex: 1; overflow-y: auto; padding: 16px 20px; }
.tl-item { display: flex; gap: 12px; margin-bottom: 16px; position: relative; }
.tl-item:not(:last-child)::before {
  content: ''; position: absolute; left: 5px; top: 14px; bottom: -8px;
  width: 1px; background: #2a2d3a;
}
.tl-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: #6c5ce7; margin-top: 5px; flex-shrink: 0;
  box-shadow: 0 0 8px rgba(108,92,231,0.4);
}
.tl-card {
  flex: 1; background: #12141f; border-radius: 8px;
  padding: 10px 14px; border: 1px solid #2a2d3a;
}
.tl-time { font-size: 12px; color: #6c5ce7; margin-bottom: 4px; font-weight: 500; }
.tl-desc { font-size: 13px; color: #ccc; }
.tl-head { color: #00b894; font-weight: 500; }
.tl-rel { color: #888; margin: 0 4px; }
.tl-tail { color: #a78bfa; font-weight: 500; }

.empty-state {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 12px;
}
.empty-state p { font-size: 13px; color: #555; }
</style>

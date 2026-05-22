<template>
  <div class="dashboard">
    <div class="stats-row">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-icon" :style="{ background: s.bg }">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" v-html="s.icon"></svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <div class="panels">
      <div class="panel graph-preview">
        <div class="panel-header">
          <h3>图谱预览</h3>
          <router-link to="/graph" class="link-btn">查看完整图谱 →</router-link>
        </div>
        <div class="panel-body graph-body" style="position:relative">
          <GraphNetwork :nodes="graphData.nodes" :edges="graphData.edges" @node-click="showDetail" />
          <transition name="fade">
            <NodeDetail v-if="selectedNode" :node="selectedNode" @close="selectedNode = null" class="dashboard-detail" />
          </transition>
        </div>
      </div>
      <div class="panel quick-extract">
        <div class="panel-header">
          <h3>快速抽取</h3>
          <router-link to="/extract" class="link-btn">完整功能 →</router-link>
        </div>
        <div class="panel-body">
          <textarea v-model="inputText" placeholder="输入投融资新闻文本..." rows="4"></textarea>
          <button @click="doExtract" :disabled="loading" class="btn">
            {{ loading ? '抽取中...' : '开始抽取' }}
          </button>
          <div v-if="extractResult" class="extract-preview">
            <div class="tag-list">
              <span class="tag enterprise" v-for="e in entities" :key="'e'+e.name">{{ e.name }}</span>
              <span class="tag investor" v-for="e in investors" :key="'i'+e.name">{{ e.name }}</span>
              <span class="tag round" v-for="e in rounds" :key="'r'+e.name">{{ e.name }}</span>
            </div>
            <div v-if="extractResult.triples.length" class="triples-preview">
              <div class="triple" v-for="(t, i) in extractResult.triples" :key="i">
                <span class="t-head">{{ t.head }}</span>
                <span class="t-arrow">→</span>
                <span class="t-tail">{{ t.tail }}</span>
                <span class="t-time" v-if="t.time">{{ t.time }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'
import GraphNetwork from '../components/GraphNetwork.vue'
import NodeDetail from '../components/NodeDetail.vue'

export default {
  components: { GraphNetwork, NodeDetail },
  data() {
    return {
      graphData: { nodes: [], edges: [] },
      selectedNode: null,
      inputText: '',
      extractResult: null,
      loading: false,
      statistics: { enterpriseCount: 0, investorCount: 0, industryCount: 0, relationCount: 0 }
    }
  },
  computed: {
    stats() {
      return [
        { label: '企业节点', value: this.statistics.enterpriseCount, bg: 'rgba(108,92,231,0.15)', icon: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>' },
        { label: '投资机构', value: this.statistics.investorCount, bg: 'rgba(0,184,148,0.15)', icon: '<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>' },
        { label: '行业分类', value: this.statistics.industryCount, bg: 'rgba(253,203,110,0.15)', icon: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>' },
        { label: '投资关系', value: this.statistics.relationCount, bg: 'rgba(116,185,255,0.15)', icon: '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>' }
      ]
    },
    entities() { return (this.extractResult?.entities || []).filter(e => e.type === 'Enterprise') },
    investors() { return (this.extractResult?.entities || []).filter(e => e.type === 'Investor') },
    rounds() { return (this.extractResult?.entities || []).filter(e => e.type === 'Round') }
  },
  async mounted() {
    try {
      const [statsRes, graphRes] = await Promise.all([api.getStatistics(), api.getGraph()])
      this.statistics = statsRes.data.data || this.statistics
      const gd = graphRes.data.data || { nodes: [], edges: [] }
      this.graphData = { nodes: [...gd.nodes], edges: [...gd.edges] }
    } catch (e) { console.error('加载失败:', e) }
  },
  methods: {
    async doExtract() {
      if (!this.inputText.trim()) return
      this.loading = true
      try {
        const res = await api.extract(this.inputText)
        this.extractResult = res.data.data
      } catch (e) { console.error('抽取失败:', e) }
      finally { this.loading = false }
    },
    showDetail(nodeId) {
      this.selectedNode = this.graphData.nodes.find(n => n.id === nodeId) || null
    }
  }
}
</script>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 20px; height: 100%; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.stat-card {
  background: #1a1d2e;
  border: 1px solid #2a2d3a;
  border-radius: 12px;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-icon {
  width: 44px; height: 44px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.stat-icon svg { color: #e0e0e0; }
.stat-value { font-size: 26px; font-weight: 700; color: #fff; line-height: 1; }
.stat-label { font-size: 13px; color: #888; margin-top: 4px; }

.panels { display: grid; grid-template-columns: 1.6fr 1fr; gap: 16px; flex: 1; min-height: 0; }
.panel {
  background: #1a1d2e;
  border: 1px solid #2a2d3a;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid #2a2d3a;
}
.panel-header h3 { font-size: 14px; font-weight: 600; color: #e0e0e0; }
.link-btn { font-size: 12px; color: #6c5ce7; text-decoration: none; }
.link-btn:hover { color: #a855f7; }
.panel-body { flex: 1; padding: 16px 20px; overflow-y: auto; }
.graph-body { padding: 0; }

textarea {
  width: 100%; padding: 10px 12px;
  background: #12141f; border: 1px solid #2a2d3a;
  border-radius: 8px; color: #e0e0e0;
  font-size: 13px; resize: none;
  font-family: inherit;
}
textarea:focus { outline: none; border-color: #6c5ce7; }
textarea::placeholder { color: #555; }
.btn {
  margin-top: 10px; width: 100%;
  padding: 9px; border: none; border-radius: 8px;
  background: linear-gradient(135deg, #6c5ce7, #a855f7);
  color: #fff; font-size: 14px; cursor: pointer;
  transition: opacity 0.2s;
}
.btn:hover { opacity: 0.9; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.extract-preview { margin-top: 14px; }
.tag-list { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.tag {
  padding: 3px 10px; border-radius: 12px;
  font-size: 12px; font-weight: 500;
}
.tag.enterprise { background: rgba(108,92,231,0.2); color: #a78bfa; }
.tag.investor { background: rgba(0,184,148,0.2); color: #00b894; }
.tag.round { background: rgba(136,136,136,0.2); color: #aaa; }

.triples-preview { display: flex; flex-direction: column; gap: 6px; }
.triple {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; background: #12141f; border-radius: 8px;
  font-size: 13px;
}
.t-head { color: #00b894; font-weight: 500; }
.t-arrow { color: #555; }
.t-tail { color: #a78bfa; font-weight: 500; }
.t-time { margin-left: auto; color: #666; font-size: 12px; }

.dashboard-detail {
  position: absolute; top: 10px; right: 10px; z-index: 10;
  box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

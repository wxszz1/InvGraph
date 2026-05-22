<template>
  <div class="graph-view">
    <div class="graph-toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input v-model="keyword" placeholder="搜索企业、投资方..." @keyup.enter="doSearch" />
        </div>
        <div class="filter-group">
          <input type="number" v-model="startYear" min="2010" max="2030" class="year-sm" placeholder="起始年" />
          <span class="sep">—</span>
          <input type="number" v-model="endYear" min="2010" max="2030" class="year-sm" placeholder="结束年" />
        </div>
        <button @click="doSearch" class="btn-action">搜索</button>
        <button @click="loadAll" class="btn-outline">重置</button>
      </div>
      <div class="toolbar-right">
        <div class="node-count">
          <span>{{ graphData.nodes.length }} 节点</span>
          <span class="divider">|</span>
          <span>{{ graphData.edges.length }} 关系</span>
        </div>
      </div>
    </div>
    <div class="graph-body">
      <div class="graph-canvas">
        <GraphNetwork
          :nodes="graphData.nodes"
          :edges="graphData.edges"
          @node-click="showDetail"
        />
        <div class="graph-legend">
          <span class="leg-item"><span class="leg-dot" style="background:#6c5ce7"></span>企业</span>
          <span class="leg-item"><span class="leg-dot" style="background:#00b894"></span>投资机构</span>
          <span class="leg-item"><span class="leg-dot" style="background:#fdcb6e"></span>行业</span>
          <span class="leg-item"><span class="leg-dot" style="background:#888"></span>轮次</span>
        </div>
      </div>
      <transition name="slide">
        <NodeDetail v-if="selectedNode" :node="selectedNode" @close="selectedNode = null" />
      </transition>
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
      keyword: '',
      startYear: 2010,
      endYear: 2025,
      graphData: { nodes: [], edges: [] },
      selectedNode: null
    }
  },
  async mounted() {
    await this.loadAll()
  },
  methods: {
    async loadAll() {
      this.keyword = ''
      this.startYear = 2010
      this.endYear = 2025
      try {
        const res = await api.getGraph()
        this.setGraphData(res.data.data)
      } catch (e) { console.error(e) }
    },
    async doSearch() {
      try {
        let res
        if (this.keyword.trim()) {
          res = await api.searchNode(this.keyword.trim())
        } else {
          res = await api.filterGraph(String(this.startYear), String(this.endYear))
        }
        this.setGraphData(res.data.data)
      } catch (e) { console.error(e) }
    },
    setGraphData(data) {
      const d = data || { nodes: [], edges: [] }
      this.graphData = { nodes: [...d.nodes], edges: [...d.edges] }
    },
    showDetail(nodeId) {
      this.selectedNode = this.graphData.nodes.find(n => n.id === nodeId) || null
    }
  }
}
</script>

<style scoped>
.graph-view { height: 100%; display: flex; flex-direction: column; }
.graph-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  background: #1a1d2e; border: 1px solid #2a2d3a; border-radius: 12px;
  padding: 12px 16px; margin-bottom: 16px;
}
.toolbar-left { display: flex; align-items: center; gap: 10px; }
.toolbar-right { display: flex; align-items: center; }
.search-box {
  display: flex; align-items: center; gap: 8px;
  background: #12141f; border: 1px solid #2a2d3a;
  border-radius: 8px; padding: 6px 12px;
}
.search-box svg { color: #666; flex-shrink: 0; }
.search-box input {
  background: none; border: none; color: #e0e0e0;
  font-size: 13px; width: 180px; outline: none;
}
.search-box input::placeholder { color: #555; }
.filter-group { display: flex; align-items: center; gap: 6px; }
.year-sm {
  width: 70px; padding: 6px 8px;
  background: #12141f; border: 1px solid #2a2d3a;
  border-radius: 6px; color: #e0e0e0; font-size: 13px;
  text-align: center;
}
.year-sm:focus { outline: none; border-color: #6c5ce7; }
.sep { color: #555; }
.btn-action {
  padding: 6px 16px; border: none; border-radius: 6px;
  background: linear-gradient(135deg, #6c5ce7, #a855f7);
  color: #fff; font-size: 13px; cursor: pointer;
}
.btn-outline {
  padding: 6px 14px; border: 1px solid #2a2d3a; border-radius: 6px;
  background: transparent; color: #888; font-size: 13px; cursor: pointer;
}
.btn-outline:hover { border-color: #555; color: #ccc; }
.node-count { font-size: 13px; color: #666; }
.divider { margin: 0 8px; color: #333; }

.graph-body {
  flex: 1; display: flex; gap: 16px; min-height: 0;
}
.graph-canvas {
  flex: 1; background: #1a1d2e; border: 1px solid #2a2d3a;
  border-radius: 12px; overflow: hidden; position: relative;
}
.graph-legend {
  position: absolute; bottom: 12px; left: 12px;
  display: flex; gap: 14px;
  background: rgba(22,24,34,0.9); padding: 8px 14px;
  border-radius: 8px; border: 1px solid #2a2d3a;
}
.leg-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #888; }
.leg-dot { width: 8px; height: 8px; border-radius: 50%; }

.slide-enter-active, .slide-leave-active { transition: all 0.3s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(20px); opacity: 0; }
</style>

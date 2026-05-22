<template>
  <div class="risk-path-view">
    <div class="toolbar">
      <div class="search-box">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input v-model="sourceName" placeholder="输入企业或投资方名称..." @keyup.enter="searchPath" />
      </div>
      <div class="depth-control">
        <span>传导深度: {{ depth }}</span>
        <input type="range" v-model.number="depth" min="1" max="5" />
      </div>
      <button @click="searchPath" class="btn-action">查询</button>
    </div>
    <div class="path-body">
      <div ref="chartRef" class="chart-container"></div>
      <div v-if="pathData.nodes.length === 0 && searched" class="empty-tip">
        未找到从「{{ lastQuery }}」出发的传导路径
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import api from '../api'

const typeColors = {
  Enterprise: '#6c5ce7', Investor: '#00b894',
  Industry: '#fdcb6e', Round: '#888'
}

export default {
  data() {
    return {
      sourceName: '',
      depth: 3,
      pathData: { nodes: [], edges: [] },
      chart: null,
      searched: false,
      lastQuery: ''
    }
  },
  mounted() {
    this.chart = echarts.init(this.$refs.chartRef)
    window.addEventListener('resize', () => this.chart?.resize())
  },
  beforeUnmount() {
    this.chart?.dispose()
  },
  methods: {
    async searchPath() {
      if (!this.sourceName.trim()) return
      this.lastQuery = this.sourceName
      this.searched = true
      try {
        const res = await api.getRiskPath(this.sourceName, this.depth)
        this.pathData = res.data.data || { nodes: [], edges: [] }
        this.renderChart()
      } catch {
        this.pathData = { nodes: [], edges: [] }
        this.renderChart()
      }
    },
    renderChart() {
      if (!this.chart) return
      const { nodes, edges } = this.pathData
      if (!nodes.length) {
        this.chart.clear()
        return
      }
      const graphNodes = nodes.map(n => ({
        id: n.id,
        name: n.properties?.name || n.label,
        symbolSize: n.label === 'Investor' ? 35 : 28,
        itemStyle: { color: typeColors[n.label] || '#888' },
        label: { show: true, fontSize: 11 }
      }))
      const graphEdges = edges.map(e => ({
        source: e.from,
        target: e.to,
        label: { show: true, formatter: e.label, fontSize: 10, color: '#aaa' },
        lineStyle: { width: 2, color: '#3a3d4a', curveness: 0.2 }
      }))
      this.chart.setOption({
        tooltip: {},
        series: [{
          type: 'graph',
          layout: 'force',
          data: graphNodes,
          links: graphEdges,
          roam: true,
          force: { repulsion: 300, edgeLength: [80, 200] },
          emphasis: { focus: 'adjacency' }
        }]
      })
    }
  }
}
</script>

<style scoped>
.risk-path-view { height: 100%; display: flex; flex-direction: column; }
.toolbar { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.search-box {
  display: flex; align-items: center; gap: 8px;
  background: #1e2130; border: 1px solid #2a2d3a; border-radius: 8px;
  padding: 8px 12px; flex: 1; max-width: 360px;
}
.search-box input { background: none; border: none; color: #e0e0e0; font-size: 14px; outline: none; width: 100%; }
.depth-control { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #aaa; }
.depth-control input[type="range"] { width: 120px; accent-color: #6c5ce7; }
.btn-action {
  background: linear-gradient(135deg, #6c5ce7, #a855f7); color: #fff;
  border: none; border-radius: 8px; padding: 8px 20px; font-size: 14px; cursor: pointer;
}
.path-body { flex: 1; position: relative; }
.chart-container { width: 100%; height: 100%; min-height: 500px; }
.empty-tip { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #666; font-size: 15px; }
</style>

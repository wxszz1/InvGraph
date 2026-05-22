<template>
  <div class="heatmap-view">
    <div class="toolbar">
      <div class="filter-group">
        <input type="number" v-model.number="startYear" min="2010" max="2030" class="year-sm" />
        <span class="sep">—</span>
        <input type="number" v-model.number="endYear" min="2010" max="2030" class="year-sm" />
      </div>
      <div class="dim-toggle">
        <button :class="{ active: metric === 'count' }" @click="metric = 'count'; loadData()">投资数量</button>
        <button :class="{ active: metric === 'amount' }" @click="metric = 'amount'; loadData()">投资金额</button>
      </div>
      <button @click="loadData" class="btn-action">刷新</button>
    </div>
    <div ref="chartRef" class="chart-container"></div>
    <div v-if="detailIndustry" class="detail-panel">
      <div class="detail-header">
        <span>{{ detailIndustry }} — {{ detailYear }}年</span>
        <button @click="detailIndustry = null" class="close-btn">&times;</button>
      </div>
      <div class="detail-list">
        <div v-for="(item, i) in detailEvents" :key="i" class="event-item">
          <span class="event-name">{{ item.name }}</span>
          <span class="event-info">{{ item.round }} {{ item.amount }}</span>
        </div>
        <div v-if="!detailEvents.length" class="empty">暂无数据</div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import api from '../api'

export default {
  data() {
    return {
      startYear: 2010,
      endYear: 2025,
      metric: 'count',
      chartData: [],
      chart: null,
      detailIndustry: null,
      detailYear: null,
      detailEvents: []
    }
  },
  mounted() {
    this.chart = echarts.init(this.$refs.chartRef)
    window.addEventListener('resize', () => this.chart?.resize())
    this.loadData()
  },
  beforeUnmount() {
    this.chart?.dispose()
  },
  methods: {
    async loadData() {
      try {
        const res = await api.getHeatmap(this.startYear, this.endYear)
        this.chartData = res.data.data || []
        this.renderChart()
      } catch {
        this.chartData = []
        this.renderChart()
      }
    },
    renderChart() {
      if (!this.chart) return
      const data = this.chartData
      if (!data.length) {
        this.chart.clear()
        return
      }
      // Build industry x year matrix from aggregated data
      const industries = [...new Set(data.map(d => d.industry))].sort()
      const years = []
      for (let y = this.startYear; y <= this.endYear; y++) years.push(String(y))

      // Use aggregated data directly (one row per industry)
      const heatData = data.map((d, i) => {
        const val = this.metric === 'count' ? d.investCount : d.totalAmount
        return [0, i, val || 0]
      })

      this.chart.setOption({
        tooltip: { formatter: p => `${industries[p.value[1]]}: ${p.value[2]}` },
        grid: { left: 120, right: 40, top: 20, bottom: 40 },
        xAxis: { type: 'category', data: ['投资热度'], splitLine: { show: false }, axisLabel: { color: '#aaa' } },
        yAxis: { type: 'category', data: industries, axisLabel: { color: '#aaa' } },
        visualMap: {
          min: 0, max: Math.max(...heatData.map(d => d[2]), 1),
          calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
          inRange: { color: ['#1a1a2e', '#16213e', '#0f3460', '#533483', '#e94560'] },
          textStyle: { color: '#aaa' }
        },
        series: [{
          type: 'heatmap',
          data: heatData,
          label: { show: true, color: '#fff', fontSize: 12, formatter: p => p.value[2] },
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } }
        }]
      })
    },
    async showDetail(industry, year) {
      this.detailIndustry = industry
      this.detailYear = year
      try {
        const res = await api.getIndustryEvents(industry, year)
        this.detailEvents = res.data.data || []
      } catch { this.detailEvents = [] }
    }
  }
}
</script>

<style scoped>
.heatmap-view { height: 100%; display: flex; flex-direction: column; }
.toolbar { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.filter-group { display: flex; align-items: center; gap: 6px; }
.year-sm {
  width: 80px; background: #1e2130; border: 1px solid #2a2d3a;
  border-radius: 6px; padding: 6px 10px; color: #e0e0e0; font-size: 14px; text-align: center;
}
.sep { color: #555; }
.dim-toggle { display: flex; border-radius: 8px; overflow: hidden; border: 1px solid #2a2d3a; }
.dim-toggle button {
  background: #1e2130; color: #8a8d9b; border: none; padding: 6px 14px;
  font-size: 13px; cursor: pointer; transition: all 0.2s;
}
.dim-toggle button.active { background: #6c5ce7; color: #fff; }
.btn-action {
  background: linear-gradient(135deg, #6c5ce7, #a855f7); color: #fff;
  border: none; border-radius: 8px; padding: 8px 20px; font-size: 14px; cursor: pointer;
}
.chart-container { flex: 1; min-height: 400px; }
.detail-panel {
  position: fixed; right: 20px; top: 80px; width: 320px; max-height: 500px;
  background: #1e2130; border: 1px solid #2a2d3a; border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.4); overflow: hidden; z-index: 100;
}
.detail-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border-bottom: 1px solid #2a2d3a; font-size: 14px; color: #e0e0e0;
}
.close-btn { background: none; border: none; color: #888; font-size: 18px; cursor: pointer; }
.detail-list { padding: 8px 16px; overflow-y: auto; max-height: 420px; }
.event-item { padding: 8px 0; border-bottom: 1px solid #2a2d3a; }
.event-name { font-size: 13px; color: #e0e0e0; }
.event-info { font-size: 12px; color: #888; margin-left: 8px; }
.empty { color: #555; font-size: 13px; padding: 20px 0; text-align: center; }
</style>

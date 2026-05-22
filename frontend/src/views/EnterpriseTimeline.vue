<template>
  <div class="enterprise-timeline">
    <div class="toolbar">
      <div class="search-box">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input v-model="searchKeyword" placeholder="搜索企业..." @keyup.enter="searchEnterprise" />
      </div>
      <button @click="searchEnterprise" class="btn-action">搜索</button>
    </div>

    <div v-if="!enterprise" class="empty-state">
      <p>搜索企业名称，查看融资历史时间线</p>
    </div>

    <div v-else class="timeline-content">
      <div class="ent-header">
        <h3>{{ enterprise.name }}</h3>
        <span class="ent-meta" v-if="enterprise.industry">行业: {{ enterprise.industry }}</span>
        <span class="ent-meta" v-if="enterprise.founding_date">成立: {{ enterprise.founding_date }}</span>
        <span class="ent-meta" v-if="enterprise.status">状态: {{ statusMap[enterprise.status] || enterprise.status }}</span>
      </div>

      <div class="timeline-track">
        <div class="track-line"></div>
        <div v-for="(event, i) in events" :key="i" class="timeline-node" :style="{ left: nodePosition(event, i) }">
          <div class="node-dot" :class="event.lead_flag ? 'lead' : 'follow'"></div>
          <div class="node-card" :class="i % 2 === 0 ? 'above' : 'below'">
            <div class="card-round">{{ event.round || '未知轮次' }}</div>
            <div class="card-investor">{{ event.investor_name || '未知投资方' }}</div>
            <div class="card-amount" v-if="event.amount">{{ formatAmount(event.amount) }}</div>
            <div class="card-time">{{ event.time || '' }}</div>
            <span v-if="event.lead_flag" class="lead-tag">领投</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'

export default {
  data() {
    return {
      searchKeyword: '',
      enterprise: null,
      events: [],
      statusMap: { active: '运营中', acquired: '被收购', ipo: '已上市', bankrupt: '已破产' }
    }
  },
  methods: {
    async searchEnterprise() {
      if (!this.searchKeyword.trim()) return
      try {
        // First search for the enterprise by name
        const res = await api.get('/data/enterprises', { params: { keyword: this.searchKeyword, size: 1 } })
        const list = res.data.data?.list || []
        if (!list.length) {
          this.enterprise = null
          this.events = []
          return
        }
        this.enterprise = list[0]
        // Load investment history
        const histRes = await api.get(`/data/enterprise/${this.enterprise.id}/history`)
        const histData = histRes.data.data || {}
        this.events = (histData.events || []).sort((a, b) => (a.time || '').localeCompare(b.time || ''))
      } catch {
        this.enterprise = null
        this.events = []
      }
    },
    nodePosition(event, index) {
      if (!this.events.length) return '50%'
      // Distribute evenly across the track
      const pct = this.events.length > 1 ? (index / (this.events.length - 1)) * 90 + 5 : 50
      return pct + '%'
    },
    formatAmount(amount) {
      const num = parseFloat(amount)
      if (isNaN(num)) return amount
      if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿元'
      if (num >= 10000) return (num / 10000).toFixed(0) + '万元'
      return num.toFixed(0) + '元'
    }
  }
}
</script>

<style scoped>
.enterprise-timeline { height: 100%; display: flex; flex-direction: column; }
.toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
.search-box {
  display: flex; align-items: center; gap: 8px;
  background: #1e2130; border: 1px solid #2a2d3a; border-radius: 8px;
  padding: 8px 12px; flex: 1; max-width: 400px;
}
.search-box input { background: none; border: none; color: #e0e0e0; font-size: 14px; outline: none; width: 100%; }
.btn-action {
  background: linear-gradient(135deg, #6c5ce7, #a855f7); color: #fff;
  border: none; border-radius: 8px; padding: 8px 20px; font-size: 14px; cursor: pointer;
}
.empty-state { flex: 1; display: flex; align-items: center; justify-content: center; color: #555; font-size: 15px; }
.timeline-content { flex: 1; display: flex; flex-direction: column; }
.ent-header { margin-bottom: 24px; }
.ent-header h3 { font-size: 20px; color: #fff; margin-bottom: 8px; }
.ent-meta { font-size: 13px; color: #888; margin-right: 16px; }
.timeline-track { position: relative; min-height: 300px; padding: 80px 40px; }
.track-line {
  position: absolute; top: 50%; left: 40px; right: 40px;
  height: 2px; background: #2a2d3a;
}
.timeline-node { position: absolute; top: 50%; transform: translateX(-50%); }
.node-dot {
  width: 14px; height: 14px; border-radius: 50%; margin: 0 auto;
  border: 2px solid #161822; z-index: 2; position: relative;
}
.node-dot.lead { background: #6c5ce7; box-shadow: 0 0 8px rgba(108, 92, 231, 0.5); }
.node-dot.follow { background: #00b894; box-shadow: 0 0 8px rgba(0, 184, 148, 0.5); }
.node-card {
  position: absolute; left: 50%; transform: translateX(-50%);
  width: 160px; background: #1e2130; border: 1px solid #2a2d3a;
  border-radius: 10px; padding: 10px 12px; text-align: center;
}
.node-card.above { bottom: 24px; }
.node-card.below { top: 24px; }
.card-round { font-size: 14px; font-weight: 600; color: #6c5ce7; margin-bottom: 4px; }
.card-investor { font-size: 12px; color: #e0e0e0; margin-bottom: 2px; }
.card-amount { font-size: 11px; color: #fdcb6e; }
.card-time { font-size: 11px; color: #888; margin-top: 2px; }
.lead-tag {
  display: inline-block; background: rgba(108, 92, 231, 0.2); color: #6c5ce7;
  font-size: 10px; padding: 1px 6px; border-radius: 4px; margin-top: 4px;
}
</style>

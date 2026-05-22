<template>
  <div class="node-detail">
    <div class="detail-header">
      <div class="detail-title">
        <span class="type-badge" :class="node?.label?.toLowerCase()">{{ typeLabel }}</span>
        <h3>{{ node?.properties?.name || '节点详情' }}</h3>
      </div>
      <button class="close-btn" @click="$emit('close')">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    <div class="detail-body" v-if="node?.properties">
      <div class="prop-item" v-for="(val, key) in node.properties" :key="key">
        <span class="prop-key">{{ propLabel(key) }}</span>
        <span class="prop-val">{{ val }}</span>
      </div>
    </div>
    <div class="detail-footer">
      <span class="node-id">ID: {{ node?.id }}</span>
    </div>
  </div>
</template>

<script>
export default {
  props: { node: Object },
  computed: {
    typeLabel() {
      const map = { Enterprise: '企业', Investor: '投资机构', Industry: '行业', Round: '融资轮次' }
      return map[this.node?.label] || this.node?.label || '未知'
    }
  },
  methods: {
    propLabel(key) {
      const map = {
        name: '名称', type: '类型', description: '简介',
        status: '经营状态', focus_industry: '关注行业',
        industry_id: '行业ID', mysql_id: 'MySQL ID',
        time: '时间', amount: '金额', round: '轮次',
        lead_flag: '是否领投'
      }
      return map[key] || key
    }
  }
}
</script>

<style scoped>
.node-detail {
  width: 300px; background: #1a1d2e;
  border: 1px solid #2a2d3a; border-radius: 12px;
  display: flex; flex-direction: column;
  overflow: hidden; flex-shrink: 0;
}
.detail-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 16px 16px 12px; border-bottom: 1px solid #2a2d3a;
}
.detail-title { display: flex; flex-direction: column; gap: 6px; }
.detail-title h3 { font-size: 16px; font-weight: 600; color: #fff; }
.type-badge {
  display: inline-block; font-size: 11px; padding: 2px 8px;
  border-radius: 4px; font-weight: 500; width: fit-content;
}
.type-badge.enterprise { background: rgba(108,92,231,0.2); color: #a78bfa; }
.type-badge.investor { background: rgba(0,184,148,0.2); color: #00b894; }
.type-badge.industry { background: rgba(253,203,110,0.2); color: #fdcb6e; }
.type-badge.round { background: rgba(136,136,136,0.2); color: #aaa; }
.close-btn {
  background: none; border: none; color: #666;
  cursor: pointer; padding: 4px;
}
.close-btn:hover { color: #e0e0e0; }

.detail-body { flex: 1; padding: 16px; overflow-y: auto; }
.prop-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-bottom: 1px solid #1e2130;
}
.prop-item:last-child { border-bottom: none; }
.prop-key { font-size: 13px; color: #888; }
.prop-val { font-size: 13px; color: #e0e0e0; font-weight: 500; }

.detail-footer {
  padding: 10px 16px; border-top: 1px solid #2a2d3a;
}
.node-id { font-size: 11px; color: #444; }
</style>

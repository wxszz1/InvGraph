<template>
  <div class="extract-view">
    <div class="extract-layout">
      <div class="input-panel">
        <div class="panel-title">输入文本</div>
        <textarea
          v-model="inputText"
          placeholder="粘贴投融资新闻文本，例如：&#10;&#10;2022年，字节跳动获得红杉资本领投的B轮融资，金额达5亿美元。本轮融资由红杉资本领投，高瓴资本跟投。"
          rows="10"
        ></textarea>
        <button @click="doExtract" :disabled="loading" class="btn-extract">
          <svg v-if="!loading" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          <span class="spinner" v-else></span>
          {{ loading ? '抽取中...' : '开始智能抽取' }}
        </button>
      </div>
      <div class="result-panel" :class="{ 'has-result': result }">
        <div v-if="!result" class="empty-result">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#333" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <p>在左侧输入文本，点击抽取按钮</p>
        </div>
        <template v-else>
          <!-- Entities -->
          <div class="result-section">
            <div class="section-header">
              <span class="section-title">识别实体</span>
              <span class="section-count">{{ result.entities.length }}</span>
            </div>
            <div class="entity-grid">
              <div class="entity-card" v-for="(e, i) in result.entities" :key="i" :class="e.type.toLowerCase()">
                <span class="entity-name">{{ e.name }}</span>
                <span class="entity-badge">{{ typeLabel(e.type) }}</span>
              </div>
            </div>
          </div>
          <!-- Relations -->
          <div class="result-section" v-if="result.relations.length">
            <div class="section-header">
              <span class="section-title">识别关系</span>
              <span class="section-count">{{ result.relations.length }}</span>
            </div>
            <div class="relation-list">
              <div class="relation-item" v-for="(r, i) in result.relations" :key="i">
                <span class="rel-node head">{{ r.head }}</span>
                <span class="rel-arrow">
                  <svg viewBox="0 0 40 12" width="40" height="12"><line x1="0" y1="6" x2="32" y2="6" stroke="#555" stroke-width="1.5"/><polygon points="32,2 40,6 32,10" fill="#555"/></svg>
                </span>
                <span class="rel-label">{{ relLabel(r.relation) }}</span>
                <span class="rel-arrow">
                  <svg viewBox="0 0 40 12" width="40" height="12"><line x1="0" y1="6" x2="32" y2="6" stroke="#555" stroke-width="1.5"/><polygon points="32,2 40,6 32,10" fill="#555"/></svg>
                </span>
                <span class="rel-node tail">{{ r.tail }}</span>
              </div>
            </div>
          </div>
          <!-- Triples -->
          <div class="result-section" v-if="result.triples.length">
            <div class="section-header">
              <span class="section-title">时序四元组</span>
              <span class="section-count">{{ result.triples.length }}</span>
            </div>
            <div class="triple-table">
              <div class="triple-header">
                <span>主体</span><span>关系</span><span>客体</span><span>时间</span>
              </div>
              <div class="triple-row" v-for="(t, i) in result.triples" :key="i">
                <span class="t-subject">{{ t.head }}</span>
                <span class="t-relation">{{ relLabel(t.relation) }}</span>
                <span class="t-object">{{ t.tail }}</span>
                <span class="t-time">{{ t.time || '—' }}</span>
              </div>
            </div>
          </div>
          <button @click="importToGraph" :disabled="importing" class="btn-import">
            {{ importing ? '导入中...' : '导入知识图谱' }}
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'

export default {
  data() {
    return { inputText: '', result: null, loading: false, importing: false }
  },
  methods: {
    typeLabel(t) {
      return { Enterprise: '企业', Investor: '投资方', Round: '轮次', Industry: '行业' }[t] || t
    },
    relLabel(r) {
      return { INVEST: '投资', LEAD: '领投', FOLLOW: '跟投', ACQUIRE: '收购' }[r] || r
    },
    async doExtract() {
      if (!this.inputText.trim()) return
      this.loading = true
      this.result = null
      try {
        const res = await api.extract(this.inputText)
        this.result = res.data.data
      } catch (e) {
        console.error('抽取失败:', e)
      } finally { this.loading = false }
    },
    async importToGraph() {
      if (!this.result?.triples?.length) return
      this.importing = true
      try {
        const typeMap = {}
        for (const e of this.result.entities) {
          typeMap[e.name] = e.type
        }
        const enriched = this.result.triples.map(t => ({
          ...t,
          headType: typeMap[t.head] || 'Enterprise',
          tailType: typeMap[t.tail] || 'Enterprise'
        }))
        await api.importTriples(enriched)
        this.result = null
        this.inputText = ''
      } catch (e) { console.error(e) }
      finally { this.importing = false }
    }
  }
}
</script>

<style scoped>
.extract-view { height: 100%; }
.extract-layout {
  display: grid; grid-template-columns: 380px 1fr; gap: 16px;
  height: 100%;
}
.input-panel {
  background: #1a1d2e; border: 1px solid #2a2d3a;
  border-radius: 12px; padding: 20px;
  display: flex; flex-direction: column;
}
.panel-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #e0e0e0; }
textarea {
  flex: 1; padding: 14px;
  background: #12141f; border: 1px solid #2a2d3a;
  border-radius: 8px; color: #e0e0e0;
  font-size: 13px; resize: none; line-height: 1.7;
  font-family: inherit;
}
textarea:focus { outline: none; border-color: #6c5ce7; }
textarea::placeholder { color: #444; }
.btn-extract {
  margin-top: 12px; padding: 10px;
  border: none; border-radius: 8px;
  background: linear-gradient(135deg, #6c5ce7, #a855f7);
  color: #fff; font-size: 14px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.btn-extract:hover { opacity: 0.9; }
.btn-extract:disabled { opacity: 0.5; cursor: not-allowed; }
.spinner {
  display: inline-block; width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff; border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.result-panel {
  background: #1a1d2e; border: 1px solid #2a2d3a;
  border-radius: 12px; padding: 20px; overflow-y: auto;
}
.empty-result {
  height: 100%; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 12px;
}
.empty-result p { font-size: 13px; color: #444; }

.result-section { margin-bottom: 20px; }
.section-header {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid #2a2d3a;
}
.section-title { font-size: 14px; font-weight: 600; color: #e0e0e0; }
.section-count {
  font-size: 11px; background: rgba(108,92,231,0.2);
  color: #a78bfa; padding: 1px 8px; border-radius: 10px;
}

.entity-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.entity-card {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 14px; border-radius: 8px;
  border: 1px solid #2a2d3a; background: #12141f;
}
.entity-card.enterprise { border-color: rgba(108,92,231,0.3); }
.entity-card.investor { border-color: rgba(0,184,148,0.3); }
.entity-card.round { border-color: rgba(136,136,136,0.3); }
.entity-card.industry { border-color: rgba(253,203,110,0.3); }
.entity-name { font-size: 13px; font-weight: 500; color: #e0e0e0; }
.entity-badge { font-size: 11px; color: #888; }

.relation-list { display: flex; flex-direction: column; gap: 8px; }
.relation-item {
  display: flex; align-items: center; gap: 4px;
  padding: 10px 14px; background: #12141f;
  border-radius: 8px; border: 1px solid #2a2d3a;
}
.rel-node { font-size: 13px; font-weight: 500; }
.rel-node.head { color: #00b894; }
.rel-node.tail { color: #a78bfa; }
.rel-label { font-size: 12px; color: #888; }
.rel-arrow { display: flex; align-items: center; }

.triple-table { border: 1px solid #2a2d3a; border-radius: 8px; overflow: hidden; }
.triple-header {
  display: grid; grid-template-columns: 1fr 80px 1fr 100px;
  padding: 8px 14px; background: #12141f;
  font-size: 12px; color: #666; font-weight: 500;
}
.triple-row {
  display: grid; grid-template-columns: 1fr 80px 1fr 100px;
  padding: 8px 14px; border-top: 1px solid #1e2130;
  font-size: 13px;
}
.t-subject { color: #00b894; font-weight: 500; }
.t-relation { color: #888; }
.t-object { color: #a78bfa; font-weight: 500; }
.t-time { color: #666; }

.btn-import {
  margin-top: 8px; width: 100%; padding: 10px;
  border: 1px solid #6c5ce7; border-radius: 8px;
  background: transparent; color: #6c5ce7;
  font-size: 14px; cursor: pointer; transition: all 0.2s;
}
.btn-import:hover { background: rgba(108,92,231,0.1); }
.btn-import:disabled { opacity: 0.4; cursor: not-allowed; }
</style>

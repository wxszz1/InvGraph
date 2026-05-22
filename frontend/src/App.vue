<template>
  <div id="app">
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <circle cx="5" cy="6" r="2"/>
            <circle cx="19" cy="6" r="2"/>
            <circle cx="5" cy="18" r="2"/>
            <circle cx="19" cy="18" r="2"/>
            <line x1="7" y1="7" x2="10" y2="10"/>
            <line x1="14" y1="10" x2="17" y2="7"/>
            <line x1="7" y1="17" x2="10" y2="14"/>
            <line x1="14" y1="14" x2="17" y2="17"/>
          </svg>
        </div>
        <div class="logo-text">
          <span class="title">知识图谱</span>
          <span class="subtitle">投融资风险分析</span>
        </div>
      </div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item" exact-active-class="active">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
          <span>数据概览</span>
        </router-link>
        <router-link to="/graph" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><line x1="7" y1="6" x2="10" y2="10"/><line x1="14" y1="10" x2="17" y2="6"/><line x1="7" y1="18" x2="10" y2="14"/><line x1="14" y1="14" x2="17" y2="18"/></svg>
          <span>知识图谱</span>
        </router-link>
        <router-link to="/timeline" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="2" x2="12" y2="22"/><circle cx="12" cy="6" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="12" cy="18" r="2"/><line x1="14" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="10" y2="12"/><line x1="14" y1="18" x2="20" y2="18"/></svg>
          <span>时序分析</span>
        </router-link>
        <router-link to="/risk" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <span>风险传导</span>
        </router-link>
        <router-link to="/heatmap" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 3v18"/></svg>
          <span>投资热度</span>
        </router-link>
        <router-link to="/enterprise" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/><line x1="12" y1="12" x2="12" y2="12.01"/></svg>
          <span>企业融资</span>
        </router-link>
        <router-link to="/extract" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          <span>文本抽取</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="status-item"><span class="dot" :class="backendOk ? 'green' : 'red'"></span>后端服务 {{ backendOk ? '运行中' : '未连接' }}</div>
        <div class="status-item"><span class="dot" :class="nlpOk ? 'green' : 'red'"></span>NLP服务 {{ nlpOk ? '运行中' : '未连接' }}</div>
      </div>
    </aside>
    <main class="main-area">
      <header class="topbar">
        <div class="breadcrumb">{{ currentPageTitle }}</div>
        <div class="topbar-right">
          <span class="time-display">{{ currentTime }}</span>
        </div>
      </header>
      <div class="content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script>
export default {
  data() {
    return { currentTime: '', backendOk: false, nlpOk: false }
  },
  computed: {
    currentPageTitle() {
      const map = {
        '/': '数据概览', '/graph': '知识图谱', '/timeline': '时序分析',
        '/risk': '风险传导', '/heatmap': '投资热度', '/enterprise': '企业融资',
        '/extract': '文本抽取'
      }
      return map[this.$route.path] || '知识图谱'
    }
  },
  mounted() {
    this.updateTime()
    setInterval(this.updateTime, 1000)
    this.checkHealth()
    setInterval(this.checkHealth, 15000)
  },
  methods: {
    updateTime() {
      const now = new Date()
      this.currentTime = now.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
    },
    async checkHealth() {
      try {
        await fetch('http://localhost:8080/api/statistics', { signal: AbortSignal.timeout(3000) })
        this.backendOk = true
      } catch { this.backendOk = false }
      try {
        await fetch('http://localhost:8000/api/ner', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: 'test' }),
          signal: AbortSignal.timeout(3000)
        })
        this.nlpOk = true
      } catch { this.nlpOk = false }
    }
  }
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { height: 100%; }
#app {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  display: flex;
  height: 100vh;
  background: #0f1117;
  color: #e0e0e0;
}
.sidebar {
  width: 220px;
  background: #161822;
  border-right: 1px solid #2a2d3a;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px 16px;
  border-bottom: 1px solid #2a2d3a;
}
.logo-icon { color: #6c5ce7; display: flex; }
.logo-text { display: flex; flex-direction: column; }
.logo-text .title { font-size: 15px; font-weight: 600; color: #fff; letter-spacing: 1px; }
.logo-text .subtitle { font-size: 11px; color: #888; margin-top: 2px; }
.nav-menu { flex: 1; padding: 12px 8px; display: flex; flex-direction: column; gap: 2px; }
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 8px;
  color: #8a8d9b; text-decoration: none; font-size: 14px;
  transition: all 0.2s;
}
.nav-item:hover { background: #1e2130; color: #c0c3d0; }
.nav-item.active {
  background: linear-gradient(135deg, #6c5ce7 0%, #a855f7 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(108, 92, 231, 0.3);
}
.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #2a2d3a;
}
.status-item {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; color: #666; margin-bottom: 6px;
}
.dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.dot.green { background: #00b894; box-shadow: 0 0 6px rgba(0, 184, 148, 0.5); }
.dot.red { background: #e74c3c; box-shadow: 0 0 6px rgba(231, 76, 60, 0.5); }
.main-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.topbar {
  height: 52px; background: #161822; border-bottom: 1px solid #2a2d3a;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; flex-shrink: 0;
}
.breadcrumb { font-size: 15px; font-weight: 500; color: #e0e0e0; }
.time-display { font-size: 13px; color: #666; font-variant-numeric: tabular-nums; }
.content { flex: 1; overflow-y: auto; padding: 20px 24px; }
</style>

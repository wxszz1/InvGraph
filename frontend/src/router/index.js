import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import GraphView from '../views/GraphView.vue'
import TimelineView from '../views/TimelineView.vue'
import ExtractView from '../views/ExtractView.vue'
import RiskPathView from '../views/RiskPathView.vue'
import HeatmapView from '../views/HeatmapView.vue'
import EnterpriseTimeline from '../views/EnterpriseTimeline.vue'

const routes = [
  { path: '/', name: 'dashboard', component: DashboardView },
  { path: '/graph', name: 'graph', component: GraphView },
  { path: '/timeline', name: 'timeline', component: TimelineView },
  { path: '/risk', name: 'risk', component: RiskPathView },
  { path: '/heatmap', name: 'heatmap', component: HeatmapView },
  { path: '/enterprise', name: 'enterprise', component: EnterpriseTimeline },
  { path: '/extract', name: 'extract', component: ExtractView }
]

export default createRouter({
  history: createWebHistory(),
  routes
})

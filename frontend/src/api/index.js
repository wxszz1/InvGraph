import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8080/api',
  timeout: 10000
})

export default {
  get: (url, config) => api.get(url, config),
  post: (url, data) => api.post(url, data),
  getGraph: () => api.get('/graph/all'),
  searchNode: (keyword) => api.get('/graph/search', { params: { keyword } }),
  filterGraph: (startTime, endTime, industry) =>
    api.get('/graph/filter', { params: { startTime, endTime, industry } }),
  extract: (text) => api.post('/extract', { text }),
  importTriples: (triples) => api.post('/import', { triples }),
  getStatistics: () => api.get('/statistics'),
  getRiskPath: (source, depth) => api.get('/risk/path', { params: { source, depth } }),
  getHeatmap: (startYear, endYear) => api.get('/analytics/heatmap', { params: { startYear, endYear } }),
  getIndustryEvents: (industry, year) => api.get(`/analytics/industry/${industry}/events`, { params: { year } }),
  getEnterpriseHistory: (name) => api.get(`/enterprise/${encodeURIComponent(name)}/history`),
}

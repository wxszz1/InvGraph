<template>
  <div ref="container" class="graph-container"></div>
</template>

<script>
import { Network } from 'vis-network'
import { DataSet } from 'vis-data'

export default {
  name: 'GraphNetwork',
  props: {
    nodes: { type: Array, default: () => [] },
    edges: { type: Array, default: () => [] }
  },
  data() {
    return { network: null }
  },
  watch: {
    nodes: 'renderGraph',
    edges: 'renderGraph'
  },
  mounted() {
    this.renderGraph()
  },
  methods: {
    renderGraph() {
      const nodeStyles = {
        Enterprise: { color: { background: '#6c5ce7', border: '#a78bfa', highlight: { background: '#a78bfa', border: '#6c5ce7' } }, shape: 'dot', size: 28 },
        Investor:   { color: { background: '#00b894', border: '#55efc4', highlight: { background: '#55efc4', border: '#00b894' } }, shape: 'diamond', size: 26 },
        Industry:   { color: { background: '#fdcb6e', border: '#ffeaa7', highlight: { background: '#ffeaa7', border: '#fdcb6e' } }, shape: 'triangle', size: 24 },
        Round:      { color: { background: '#636e72', border: '#b2bec3', highlight: { background: '#b2bec3', border: '#636e72' } }, shape: 'square', size: 16 }
      }

      const visNodes = new DataSet(
        this.nodes.map(n => {
          const style = nodeStyles[n.label] || nodeStyles.Round
          return {
            id: n.id,
            label: n.properties?.name || n.id,
            color: style.color,
            shape: style.shape,
            size: style.size,
            font: { color: '#ccc', size: 12, face: 'Microsoft YaHei' },
            borderWidth: 2,
            shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 }
          }
        })
      )

      const visEdges = new DataSet(
        this.edges.map(e => ({
          id: e.id,
          from: e.from,
          to: e.to,
          label: e.properties?.time || e.label,
          arrows: { to: { enabled: true, scaleFactor: 0.6 } },
          font: { size: 11, color: '#bbb', face: 'Microsoft YaHei', strokeWidth: 3, strokeColor: '#0f1117' },
          color: { color: '#555', highlight: '#6c5ce7', hover: '#a78bfa' },
          width: 1.5,
          smooth: { type: 'continuous' }
        }))
      )

      const options = {
        physics: {
          solver: 'forceAtlas2Based',
          forceAtlas2Based: { gravitationalConstant: -60, centralGravity: 0.008, springLength: 160, springConstant: 0.04, damping: 0.5 },
          stabilization: { iterations: 150 }
        },
        interaction: { hover: true, tooltipDelay: 150, zoomView: true, dragView: true },
        nodes: { font: { size: 12 } },
        edges: { smooth: { type: 'continuous' } }
      }

      if (this.network) this.network.destroy()
      this.network = new Network(this.$refs.container, { nodes: visNodes, edges: visEdges }, options)

      this.network.on('click', (params) => {
        if (params.nodes.length > 0) {
          this.$emit('node-click', params.nodes[0])
        }
      })
    }
  },
  beforeUnmount() {
    if (this.network) this.network.destroy()
  }
}
</script>

<style scoped>
.graph-container { width: 100%; height: 100%; min-height: 400px; }
</style>

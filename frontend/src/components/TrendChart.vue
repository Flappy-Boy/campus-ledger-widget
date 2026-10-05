<template>
  <div ref="chartRef" class="chart"></div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  trend: {
    type: Object,
    default: () => ({ labels: [], income: [], expense: [] }),
  },
})

const chartRef = ref(null)
let chart = null
let observer = null

const render = () => {
  if (!chart) return
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['收入', '支出'], right: 10 },
    grid: { left: 60, right: 24, top: 46, bottom: 40 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.trend.labels,
      axisLabel: { rotate: props.trend.labels.length > 8 ? 40 : 0 },
    },
    yAxis: { type: 'value', name: '金额(元)' },
    series: [
      {
        name: '收入',
        type: 'line',
        smooth: true,
        data: props.trend.income,
        itemStyle: { color: '#67c23a' },
        areaStyle: { opacity: 0.12 },
      },
      {
        name: '支出',
        type: 'line',
        smooth: true,
        data: props.trend.expense,
        itemStyle: { color: '#f56c6c' },
        areaStyle: { opacity: 0.12 },
      },
    ],
  }, true)
  chart.resize()
}

const resize = () => chart?.resize()

onMounted(() => {
  chart = echarts.init(chartRef.value)
  render()
  // 图表所在的标签页初始为隐藏状态，宽度为 0，需在容器尺寸变化后重新计算尺寸
  observer = new ResizeObserver(resize)
  observer.observe(chartRef.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
  chart?.dispose()
  chart = null
})

watch(() => props.trend, render, { deep: true })
</script>

<style scoped>
.chart {
  width: 100%;
  height: 360px;
}
</style>

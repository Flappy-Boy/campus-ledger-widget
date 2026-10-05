<template>
  <div class="page">
    <div class="header">
      <div>
        <h1 class="app-title">大学生收支管理系统</h1>
        <p class="app-sub">记录每一笔收入与支出，随时查看余额与趋势</p>
      </div>
      <div class="schedule-tip">
        <el-tag type="info" effect="plain">
          <el-icon><Clock /></el-icon>
          定时查询：每天 08:00 自动统计近 {{ scheduled.queryDays }} 天收支
        </el-tag>
        <div class="next-run">
          下次执行：{{ scheduled.nextRunTime || '未启动' }}
        </div>
      </div>
    </div>

    <BalanceCards :summary="summary" />

    <el-row :gutter="16">
      <el-col :xs="24" :sm="12">
        <RecordForm type="income" :categories="categories.income" @added="refreshAll" />
      </el-col>
      <el-col :xs="24" :sm="12">
        <RecordForm type="expense" :categories="categories.expense" @added="refreshAll" />
      </el-col>
    </el-row>

    <el-card shadow="never" class="query-card">
      <h3 class="section-title">收支查询</h3>
      <el-form inline @submit.prevent>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="query.range"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            :shortcuts="shortcuts"
            unlink-panels
          />
        </el-form-item>
        <el-form-item label="记录类型">
          <el-select v-model="query.type" style="width: 130px">
            <el-option label="全部" value="" />
            <el-option label="仅收入" value="income" />
            <el-option label="仅支出" value="expense" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" :loading="loading" @click="loadRecords">
            查询
          </el-button>
          <el-button :icon="RefreshLeft" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="收入支出记录" name="records">
          <el-alert type="info" :closable="false" show-icon class="range-alert">
            <template #title>
              {{ rangeText }}：共 {{ records.length }} 条，收入 ￥{{ money(total.income) }}，
              支出 ￥{{ money(total.expense) }}，结余
              <b>￥{{ money(total.balance) }}</b>
            </template>
          </el-alert>
          <RecordTable :records="records" :loading="loading" @deleted="removeRecord" />
        </el-tab-pane>
        <el-tab-pane label="收支趋势" name="trend">
          <TrendChart :trend="trend" />
        </el-tab-pane>
        <el-tab-pane label="定时查询记录" name="scheduled">
          <el-table :data="scheduled.items" stripe empty-text="暂无定时查询记录">
            <el-table-column prop="createdAt" label="查询时间" width="180" />
            <el-table-column label="统计区间" min-width="200">
              <template #default="{ row }">{{ row.startDate }} ~ {{ row.endDate }}</template>
            </el-table-column>
            <el-table-column label="收入" width="130" align="right">
              <template #default="{ row }">
                <span class="text-income">￥{{ money(row.incomeTotal) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="支出" width="130" align="right">
              <template #default="{ row }">
                <span class="text-expense">￥{{ money(row.expenseTotal) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="结余" width="130" align="right">
              <template #default="{ row }">￥{{ money(row.balance) }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock, RefreshLeft, Search } from '@element-plus/icons-vue'

import BalanceCards from '@/components/BalanceCards.vue'
import RecordForm from '@/components/RecordForm.vue'
import RecordTable from '@/components/RecordTable.vue'
import TrendChart from '@/components/TrendChart.vue'
import {
  deleteRecord,
  getCategories,
  getRecords,
  getScheduledReports,
  getSummary,
  getTrend,
} from '@/api'

const todayStr = () => new Date().toISOString().slice(0, 10)
const monthStartStr = () => todayStr().slice(0, 8) + '01'

const loading = ref(false)
const activeTab = ref('records')
const categories = ref({ income: [], expense: [] })
const summary = ref({ income: 0, expense: 0, balance: 0, recordCount: 0, month: {} })
const records = ref([])
const total = ref({ income: 0, expense: 0, balance: 0 })
const trend = ref({ labels: [], income: [], expense: [] })
const scheduled = ref({ queryDays: 0, nextRunTime: null, items: [] })

const query = reactive({ range: [monthStartStr(), todayStr()], type: '' })

const shortcuts = [
  { text: '今天', value: () => [new Date(), new Date()] },
  { text: '近 7 天', value: () => [new Date(Date.now() - 6 * 864e5), new Date()] },
  { text: '近 30 天', value: () => [new Date(Date.now() - 29 * 864e5), new Date()] },
  {
    text: '本月',
    value: () => {
      const now = new Date()
      return [new Date(now.getFullYear(), now.getMonth(), 1), now]
    },
  },
  {
    text: '近一年',
    value: () => [new Date(Date.now() - 364 * 864e5), new Date()],
  },
  { text: '全部时间', value: () => ['', ''] },
]

const money = (value) => Number(value || 0).toFixed(2)

const rangeText = computed(() => {
  const [start, end] = query.range || []
  if (!start && !end) return '全部时间'
  return `${start || '最早'} ~ ${end || todayStr()}`
})

const buildParams = () => {
  const [start, end] = query.range || []
  return { start: start || undefined, end: end || undefined, type: query.type || undefined }
}

const loadRecords = async () => {
  loading.value = true
  try {
    const [recordData, trendData] = await Promise.all([getRecords(buildParams()), getTrend(buildParams())])
    records.value = recordData.items
    total.value = recordData
    trend.value = trendData
  } finally {
    loading.value = false
  }
}

const loadSummary = async () => {
  summary.value = await getSummary()
}

const loadScheduled = async () => {
  scheduled.value = await getScheduledReports()
}

const refreshAll = async () => {
  await Promise.all([loadSummary(), loadRecords(), loadScheduled()])
}

const resetQuery = async () => {
  query.range = [monthStartStr(), todayStr()]
  query.type = ''
  await loadRecords()
}

const removeRecord = async (row) => {
  await ElMessageBox.confirm(
    `确定删除 ${row.date} 的${row.type === 'income' ? '收入' : '支出'} ￥${row.amount.toFixed(2)}（${row.category}）吗？`,
    '删除确认',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
  )
  await deleteRecord(row.id)
  ElMessage.success('已删除')
  await refreshAll()
}

onMounted(async () => {
  categories.value = await getCategories()
  await refreshAll()
})
</script>

<style scoped>
.header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.app-title {
  margin: 0;
  font-size: 24px;
}

.app-sub {
  margin: 6px 0 0;
  color: #909399;
  font-size: 13px;
}

.schedule-tip {
  text-align: right;
}

.next-run {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}

.query-card {
  margin: 16px 0;
}

.range-alert {
  margin-bottom: 12px;
}
</style>

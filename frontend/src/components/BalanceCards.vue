<template>
  <el-row :gutter="16">
    <el-col :xs="24" :sm="12" :md="12">
      <el-card shadow="never" class="balance-card">
        <div class="label">当前总余额</div>
        <div class="balance-value" :class="summary.balance >= 0 ? 'text-income' : 'text-expense'">
          ￥{{ money(summary.balance) }}
        </div>
        <div class="sub">共 {{ summary.recordCount }} 条收支记录</div>
      </el-card>
    </el-col>
    <el-col :xs="12" :sm="6" :md="6">
      <el-card shadow="never" class="balance-card">
        <div class="label">累计收入</div>
        <div class="balance-value text-income">￥{{ money(summary.income) }}</div>
        <div class="sub">本月 ￥{{ money(summary.month?.income) }}</div>
      </el-card>
    </el-col>
    <el-col :xs="12" :sm="6" :md="6">
      <el-card shadow="never" class="balance-card">
        <div class="label">累计支出</div>
        <div class="balance-value text-expense">￥{{ money(summary.expense) }}</div>
        <div class="sub">本月 ￥{{ money(summary.month?.expense) }}</div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
defineProps({
  summary: {
    type: Object,
    default: () => ({ income: 0, expense: 0, balance: 0, recordCount: 0, month: {} }),
  },
})

const money = (value) => Number(value || 0).toFixed(2)
</script>

<style scoped>
.balance-card {
  margin-bottom: 16px;
}

.label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.sub {
  margin-top: 8px;
  font-size: 12px;
  color: #a8abb2;
}
</style>

<template>
  <el-table
    v-loading="loading"
    :data="records"
    :max-height="420"
    stripe
    empty-text="暂无收支记录"
  >
    <el-table-column prop="date" label="日期" width="118" />
    <el-table-column label="类型" width="92">
      <template #default="{ row }">
        <el-tag :type="row.type === 'income' ? 'success' : 'danger'" size="small" effect="light">
          {{ row.type === 'income' ? '收入' : '支出' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="category" label="类别" width="110" />
    <el-table-column label="金额" width="140" align="right">
      <template #default="{ row }">
        <span :class="row.type === 'income' ? 'text-income' : 'text-expense'">
          {{ row.type === 'income' ? '+' : '-' }}￥{{ row.amount.toFixed(2) }}
        </span>
      </template>
    </el-table-column>
    <el-table-column prop="note" label="备注" show-overflow-tooltip />
    <el-table-column prop="createdAt" label="记录时间" width="170" />
    <el-table-column label="操作" width="80" align="center">
      <template #default="{ row }">
        <el-button type="danger" link @click="emit('deleted', row)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
defineProps({
  records: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})
const emit = defineEmits(['deleted'])
</script>

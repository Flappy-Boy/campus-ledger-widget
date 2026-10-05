<template>
  <el-card shadow="never">
    <h3 class="section-title">
      <el-icon :color="isIncome ? '#67c23a' : '#f56c6c'">
        <component :is="isIncome ? Top : Bottom" />
      </el-icon>
      {{ isIncome ? '记录收入' : '记录支出' }}
    </h3>
    <el-form label-width="72px" @submit.prevent>
      <el-form-item label="金额">
        <el-input-number
          v-model="form.amount"
          :min="0.01"
          :max="9999999"
          :precision="2"
          :step="10"
          controls-position="right"
          placeholder="请输入金额"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item :label="isIncome ? '收入类型' : '支出类型'">
        <el-select v-model="form.category" placeholder="请选择类型" style="width: 100%">
          <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
      <el-form-item label="日期">
        <el-date-picker
          v-model="form.date"
          type="date"
          value-format="YYYY-MM-DD"
          :clearable="false"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.note" maxlength="60" show-word-limit placeholder="选填" />
      </el-form-item>
      <el-form-item>
        <el-button
          :type="isIncome ? 'success' : 'danger'"
          :icon="isIncome ? Plus : Minus"
          :loading="loading"
          style="width: 100%"
          @click="submit"
        >
          添加{{ isIncome ? '收入' : '支出' }}
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Bottom, Minus, Plus, Top } from '@element-plus/icons-vue'
import { createRecord } from '@/api'

const props = defineProps({
  type: { type: String, required: true },
  categories: { type: Array, default: () => [] },
})
const emit = defineEmits(['added'])

const isIncome = props.type === 'income'
const loading = ref(false)

const today = () => new Date().toISOString().slice(0, 10)

const form = reactive({ amount: null, category: '', date: today(), note: '' })

watch(
  () => props.categories,
  (list) => {
    if (!form.category && list.length) form.category = list[0]
  },
  { immediate: true },
)

const submit = async () => {
  if (!form.amount || form.amount <= 0) {
    ElMessage.warning('请输入正确的金额')
    return
  }
  if (!form.category) {
    ElMessage.warning('请选择类型')
    return
  }
  loading.value = true
  try {
    await createRecord({ ...form, type: props.type })
    ElMessage.success(`${isIncome ? '收入' : '支出'}添加成功`)
    form.amount = null
    form.note = ''
    emit('added')
  } finally {
    loading.value = false
  }
}
</script>

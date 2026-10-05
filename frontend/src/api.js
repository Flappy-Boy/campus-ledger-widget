import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: '/api', timeout: 10000 })

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.error || '请求失败，请检查后端服务是否已启动'
    ElMessage.error(message)
    return Promise.reject(error)
  },
)

export const getCategories = () => http.get('/categories')
export const getSummary = () => http.get('/summary')
export const getRecords = (params) => http.get('/records', { params })
export const createRecord = (payload) => http.post('/records', payload)
export const deleteRecord = (id) => http.delete(`/records/${id}`)
export const getTrend = (params) => http.get('/trend', { params })
export const getScheduledReports = () => http.get('/scheduled-reports')
export const runScheduledQuery = () => http.post('/scheduled-reports/run')

export default http

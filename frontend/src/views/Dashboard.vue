<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1 class="page-title">仪表盘</h1>
      <p class="page-subtitle">欢迎使用 ShopTalk AI 智能客服管理平台</p>
    </div>
    
    <!-- 数据概览卡片 -->
    <div class="stats-grid">
      <div
        v-for="stat in stats"
        :key="stat.key"
        class="stat-card tech-card hover-float"
      >
        <div class="stat-icon" :style="{ background: stat.color }">
          <el-icon><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-change" :class="stat.trend">
            <el-icon><component :is="stat.trend === 'up' ? 'TrendCharts' : 'Bottom'" /></el-icon>
            {{ stat.change }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-section">
      <div class="chart-row">
        <!-- 聊天量趋势 -->
        <div class="chart-card tech-card">
          <div class="chart-header">
            <h3>聊天量趋势</h3>
            <el-select v-model="chatTrendPeriod" size="small" style="width: 120px">
              <el-option label="今日" value="today" />
              <el-option label="本周" value="week" />
              <el-option label="本月" value="month" />
            </el-select>
          </div>
          <div class="chart-content">
            <v-chart :option="chatTrendOption" autoresize />
          </div>
        </div>
        
        <!-- 平台分布 -->
        <div class="chart-card tech-card">
          <div class="chart-header">
            <h3>平台消息分布</h3>
          </div>
          <div class="chart-content">
            <v-chart :option="platformDistributionOption" autoresize />
          </div>
        </div>
      </div>
      
      <div class="chart-row">
        <!-- 模型调用统计 -->
        <div class="chart-card tech-card">
          <div class="chart-header">
            <h3>AI模型调用统计</h3>
          </div>
          <div class="chart-content">
            <v-chart :option="modelUsageOption" autoresize />
          </div>
        </div>
        
        <!-- 情感分析 -->
        <div class="chart-card tech-card">
          <div class="chart-header">
            <h3>用户情感分析</h3>
          </div>
          <div class="chart-content">
            <v-chart :option="sentimentOption" autoresize />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 快速操作 -->
    <div class="quick-actions">
      <h3>快速操作</h3>
      <div class="actions-grid">
        <div
          v-for="action in quickActions"
          :key="action.key"
          class="action-card tech-card hover-float"
          @click="handleQuickAction(action.key)"
        >
          <div class="action-icon">
            <el-icon><component :is="action.icon" /></el-icon>
          </div>
          <div class="action-content">
            <div class="action-title">{{ action.title }}</div>
            <div class="action-desc">{{ action.description }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 最近活动 -->
    <div class="recent-activities">
      <h3>最近活动</h3>
      <div class="activity-list">
        <div
          v-for="activity in recentActivities"
          :key="activity.id"
          class="activity-item"
        >
          <div class="activity-avatar">
            <el-avatar :size="32" :src="activity.avatar">
              {{ activity.user.charAt(0) }}
            </el-avatar>
          </div>
          <div class="activity-content">
            <div class="activity-text">
              <strong>{{ activity.user }}</strong> {{ activity.action }}
            </div>
            <div class="activity-time">{{ formatTime(activity.time) }}</div>
          </div>
          <div class="activity-status" :class="activity.status">
            {{ getStatusText(activity.status) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import dayjs from 'dayjs'

const router = useRouter()

// 响应式数据
const chatTrendPeriod = ref('today')

// 统计数据
const stats = ref([
  {
    key: 'totalChats',
    label: '今日对话',
    value: '2,847',
    change: '+12.5%',
    trend: 'up',
    color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    icon: 'ChatRound'
  },
  {
    key: 'activeUsers',
    label: '活跃用户',
    value: '1,234',
    change: '+8.2%',
    trend: 'up',
    color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    icon: 'User'
  },
  {
    key: 'aiResolution',
    label: 'AI解决率',
    value: '87.3%',
    change: '+2.1%',
    trend: 'up',
    color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    icon: 'BrushFilled'
  },
  {
    key: 'avgResponse',
    label: '平均响应时间',
    value: '1.2s',
    change: '-0.3s',
    trend: 'down',
    color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    icon: 'Timer'
  }
])

// 快速操作
const quickActions = ref([
  {
    key: 'newChat',
    title: '开始新对话',
    description: '创建新的客服对话',
    icon: 'ChatRound'
  },
  {
    key: 'addKnowledge',
    title: '添加知识库',
    description: '添加新的知识库条目',
    icon: 'DocumentAdd'
  },
  {
    key: 'configModel',
    title: '配置模型',
    description: '设置AI模型参数',
    icon: 'Setting'
  },
  {
    key: 'viewAnalytics',
    title: '查看报表',
    description: '查看详细运营数据',
    icon: 'DataAnalysis'
  }
])

// 最近活动
const recentActivities = ref([
  {
    id: 1,
    user: '张三',
    action: '处理了一个客户咨询',
    time: new Date(Date.now() - 300000),
    status: 'success',
    avatar: ''
  },
  {
    id: 2,
    user: '李四',
    action: '更新了产品知识库',
    time: new Date(Date.now() - 600000),
    status: 'info',
    avatar: ''
  },
  {
    id: 3,
    user: '王五',
    action: '配置了新的AI模型',
    time: new Date(Date.now() - 900000),
    status: 'warning',
    avatar: ''
  }
])

// 图表配置
const chatTrendOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(42, 49, 66, 0.9)',
    borderColor: '#1890ff',
    textStyle: { color: '#fff' }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
    axisLine: { lineStyle: { color: '#404040' } },
    axisLabel: { color: '#8c8c8c' }
  },
  yAxis: {
    type: 'value',
    axisLine: { lineStyle: { color: '#404040' } },
    axisLabel: { color: '#8c8c8c' },
    splitLine: { lineStyle: { color: '#333333' } }
  },
  series: [{
    name: '对话量',
    type: 'line',
    data: [120, 200, 150, 800, 700, 600],
    smooth: true,
    lineStyle: { color: '#1890ff', width: 3 },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
          { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
        ]
      }
    }
  }]
}))

const platformDistributionOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(42, 49, 66, 0.9)',
    borderColor: '#1890ff',
    textStyle: { color: '#fff' }
  },
  legend: {
    orient: 'vertical',
    left: 'left',
    textStyle: { color: '#8c8c8c' }
  },
  series: [{
    name: '平台分布',
    type: 'pie',
    radius: '50%',
    data: [
      { value: 1048, name: '小红书' },
      { value: 735, name: '淘宝' },
      { value: 580, name: '京东' },
      { value: 484, name: 'PDD' },
      { value: 300, name: '其他' }
    ],
    emphasis: {
      itemStyle: {
        shadowBlur: 10,
        shadowOffsetX: 0,
        shadowColor: 'rgba(0, 0, 0, 0.5)'
      }
    }
  }]
}))

const modelUsageOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(42, 49, 66, 0.9)',
    borderColor: '#1890ff',
    textStyle: { color: '#fff' }
  },
  legend: {
    textStyle: { color: '#8c8c8c' }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: ['GPT-3.5', 'GPT-4', 'Claude-3', '通义千问', 'Llama2'],
    axisLine: { lineStyle: { color: '#404040' } },
    axisLabel: { color: '#8c8c8c' }
  },
  yAxis: {
    type: 'value',
    axisLine: { lineStyle: { color: '#404040' } },
    axisLabel: { color: '#8c8c8c' },
    splitLine: { lineStyle: { color: '#333333' } }
  },
  series: [{
    name: '调用次数',
    type: 'bar',
    data: [2400, 1398, 980, 1200, 800],
    itemStyle: {
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: '#667eea' },
          { offset: 1, color: '#764ba2' }
        ]
      }
    }
  }]
}))

const sentimentOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(42, 49, 66, 0.9)',
    borderColor: '#1890ff',
    textStyle: { color: '#fff' }
  },
  series: [{
    name: '情感分析',
    type: 'pie',
    radius: ['40%', '70%'],
    data: [
      { value: 65, name: '正面', itemStyle: { color: '#52c41a' } },
      { value: 25, name: '中性', itemStyle: { color: '#faad14' } },
      { value: 10, name: '负面', itemStyle: { color: '#ff4d4f' } }
    ],
    label: {
      show: true,
      position: 'outside',
      color: '#fff'
    }
  }]
}))

// 方法
const handleQuickAction = (actionKey: string) => {
  switch (actionKey) {
    case 'newChat':
      router.push('/chat')
      break
    case 'addKnowledge':
      router.push('/knowledge')
      break
    case 'configModel':
      router.push('/models')
      break
    case 'viewAnalytics':
      router.push('/analytics')
      break
  }
}

const formatTime = (time: Date) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

const getStatusText = (status: string) => {
  const statusMap = {
    success: '已完成',
    info: '处理中',
    warning: '待确认',
    error: '失败'
  }
  return statusMap[status] || '未知'
}

// 初始化
onMounted(() => {
  // 这里可以调用API获取真实数据
})
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 0;
}

.dashboard-header {
  margin-bottom: 32px;
  
  .page-title {
    font-size: 28px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 8px;
    background: $gradient-tech;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .page-subtitle {
    font-size: 16px;
    color: $text-secondary;
    margin: 0;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
  
  .stat-card {
    padding: 24px;
    display: flex;
    align-items: center;
    gap: 20px;
    animation: slideInUp 0.6s ease-out;
    
    .stat-icon {
      width: 60px;
      height: 60px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 24px;
    }
    
    .stat-content {
      flex: 1;
      
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: $text-primary;
        line-height: 1;
        margin-bottom: 4px;
      }
      
      .stat-label {
        font-size: 14px;
        color: $text-secondary;
        margin-bottom: 8px;
      }
      
      .stat-change {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        font-weight: 500;
        
        &.up {
          color: $success-color;
        }
        
        &.down {
          color: $error-color;
        }
      }
    }
  }
}

.charts-section {
  margin-bottom: 32px;
  
  .chart-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 24px;
    margin-bottom: 24px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .chart-card {
    padding: 24px;
    
    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      
      h3 {
        font-size: 18px;
        font-weight: 500;
        color: $text-primary;
        margin: 0;
      }
    }
    
    .chart-content {
      height: 300px;
    }
  }
}

.quick-actions {
  margin-bottom: 32px;
  
  h3 {
    font-size: 20px;
    font-weight: 500;
    color: $text-primary;
    margin-bottom: 16px;
  }
  
  .actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
    
    .action-card {
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        border-color: $primary-color;
        box-shadow: 0 8px 32px rgba(24, 144, 255, 0.2);
      }
      
      .action-icon {
        width: 48px;
        height: 48px;
        border-radius: 10px;
        background: $gradient-tech;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 20px;
      }
      
      .action-content {
        .action-title {
          font-size: 16px;
          font-weight: 500;
          color: $text-primary;
          margin-bottom: 4px;
        }
        
        .action-desc {
          font-size: 14px;
          color: $text-secondary;
        }
      }
    }
  }
}

.recent-activities {
  h3 {
    font-size: 20px;
    font-weight: 500;
    color: $text-primary;
    margin-bottom: 16px;
  }
  
  .activity-list {
    background: $bg-card;
    border: 1px solid $border-primary;
    border-radius: $border-radius-large;
    padding: 16px;
    
    .activity-item {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 12px 0;
      border-bottom: 1px solid $border-light;
      
      &:last-child {
        border-bottom: none;
      }
      
      .activity-avatar {
        flex-shrink: 0;
      }
      
      .activity-content {
        flex: 1;
        
        .activity-text {
          font-size: 14px;
          color: $text-primary;
          margin-bottom: 4px;
        }
        
        .activity-time {
          font-size: 12px;
          color: $text-tertiary;
        }
      }
      
      .activity-status {
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
        
        &.success {
          background: rgba(82, 196, 26, 0.1);
          color: $success-color;
        }
        
        &.info {
          background: rgba(24, 144, 255, 0.1);
          color: $info-color;
        }
        
        &.warning {
          background: rgba(250, 173, 20, 0.1);
          color: $warning-color;
        }
        
        &.error {
          background: rgba(255, 77, 79, 0.1);
          color: $error-color;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-row {
    grid-template-columns: 1fr;
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style> 
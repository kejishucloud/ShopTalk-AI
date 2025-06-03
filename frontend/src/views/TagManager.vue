<template>
  <div class="tag-manager">
    <div class="page-header">
      <h1>标签管理</h1>
      <p>管理系统标签，为用户和对话分类</p>
    </div>
    
    <!-- 操作栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        新建标签
      </el-button>
      
      <el-input
        v-model="searchQuery"
        placeholder="搜索标签..."
        style="width: 300px"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>
    
    <!-- 标签列表 -->
    <div class="tags-grid">
      <div
        v-for="tag in filteredTags"
        :key="tag.id"
        class="tag-card tech-card hover-float"
      >
        <div class="tag-color" :style="{ backgroundColor: tag.color }"></div>
        <div class="tag-content">
          <h3 class="tag-name">{{ tag.name }}</h3>
          <p class="tag-description">{{ tag.description || '暂无描述' }}</p>
          <div class="tag-stats">
            <span>使用次数: {{ tag.usageCount }}</span>
          </div>
        </div>
        <div class="tag-actions">
          <el-button text @click="editTag(tag)">
            <el-icon><Edit /></el-icon>
          </el-button>
          <el-button text type="danger" @click="deleteTag(tag)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 添加/编辑标签对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingTag ? '编辑标签' : '新建标签'"
      width="500px"
    >
      <el-form :model="tagForm" label-width="80px">
        <el-form-item label="标签名称">
          <el-input v-model="tagForm.name" placeholder="请输入标签名称" />
        </el-form-item>
        
        <el-form-item label="标签颜色">
          <el-color-picker v-model="tagForm.color" />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input
            v-model="tagForm.description"
            type="textarea"
            placeholder="请输入标签描述"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTag">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 响应式数据
const searchQuery = ref('')
const showAddDialog = ref(false)
const editingTag = ref(null)

// 表单数据
const tagForm = ref({
  name: '',
  color: '#1890ff',
  description: ''
})

// 模拟标签数据
const tags = ref([
  {
    id: 1,
    name: '客服咨询',
    color: '#1890ff',
    description: '客户服务相关咨询',
    usageCount: 128
  },
  {
    id: 2,
    name: '产品问题',
    color: '#52c41a',
    description: '产品功能和使用问题',
    usageCount: 89
  },
  {
    id: 3,
    name: '技术支持',
    color: '#722ed1',
    description: '技术相关问题',
    usageCount: 56
  },
  {
    id: 4,
    name: '订单问题',
    color: '#faad14',
    description: '订单相关问题',
    usageCount: 234
  }
])

// 计算属性
const filteredTags = computed(() => {
  if (!searchQuery.value) return tags.value
  return tags.value.filter(tag =>
    tag.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    tag.description.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// 方法
const editTag = (tag) => {
  editingTag.value = tag
  tagForm.value = { ...tag }
  showAddDialog.value = true
}

const deleteTag = async (tag) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除标签 "${tag.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = tags.value.findIndex(t => t.id === tag.id)
    if (index > -1) {
      tags.value.splice(index, 1)
      ElMessage.success('删除成功')
    }
  } catch {
    // 用户取消
  }
}

const saveTag = () => {
  if (!tagForm.value.name.trim()) {
    ElMessage.error('请输入标签名称')
    return
  }
  
  if (editingTag.value) {
    // 编辑
    const index = tags.value.findIndex(t => t.id === editingTag.value.id)
    if (index > -1) {
      tags.value[index] = { ...tags.value[index], ...tagForm.value }
    }
    ElMessage.success('更新成功')
  } else {
    // 新增
    const newTag = {
      id: Date.now(),
      ...tagForm.value,
      usageCount: 0
    }
    tags.value.unshift(newTag)
    ElMessage.success('创建成功')
  }
  
  showAddDialog.value = false
  editingTag.value = null
  tagForm.value = {
    name: '',
    color: '#1890ff',
    description: ''
  }
}
</script>

<style lang="scss" scoped>
.tag-manager {
  .page-header {
    margin-bottom: 32px;
    
    h1 {
      font-size: 28px;
      color: $text-primary;
      margin-bottom: 8px;
    }
    
    p {
      color: $text-secondary;
      margin: 0;
    }
  }
  
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding: 16px;
    background: $bg-card;
    border-radius: $border-radius-large;
  }
  
  .tags-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 24px;
    
    .tag-card {
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      position: relative;
      
      .tag-color {
        width: 12px;
        height: 60px;
        border-radius: 6px;
        flex-shrink: 0;
      }
      
      .tag-content {
        flex: 1;
        
        .tag-name {
          font-size: 16px;
          font-weight: 500;
          color: $text-primary;
          margin: 0 0 8px 0;
        }
        
        .tag-description {
          font-size: 14px;
          color: $text-secondary;
          margin: 0 0 12px 0;
          line-height: 1.4;
        }
        
        .tag-stats {
          font-size: 12px;
          color: $text-tertiary;
        }
      }
      
      .tag-actions {
        display: flex;
        gap: 8px;
        opacity: 0;
        transition: opacity 0.3s ease;
      }
      
      &:hover .tag-actions {
        opacity: 1;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .tag-manager {
    .toolbar {
      flex-direction: column;
      gap: 16px;
      align-items: stretch;
    }
    
    .tags-grid {
      grid-template-columns: 1fr;
    }
  }
}
</style> 
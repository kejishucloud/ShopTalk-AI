<template>
  <div class="chat-container">
    <!-- 会话列表 -->
    <div class="chat-sidebar" :class="{ 'is-collapsed': isSidebarCollapsed }">
      <div class="sidebar-header">
        <el-button type="primary" class="new-chat-btn" @click="createNewChat">
          <el-icon><Plus /></el-icon>
          新建对话
        </el-button>
        
        <el-button 
          text 
          circle 
          @click="toggleSidebar"
          class="collapse-sidebar-btn"
        >
          <el-icon><ArrowLeft v-if="!isSidebarCollapsed" /><ArrowRight v-else /></el-icon>
        </el-button>
      </div>
      
      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索对话..."
          prefix-icon="Search"
          clearable
        />
      </div>
      
      <!-- 筛选标签 -->
      <div class="filter-tags">
        <el-tag
          v-for="tag in filterTags"
          :key="tag"
          :type="selectedTags.includes(tag) ? 'primary' : 'info'"
          :effect="selectedTags.includes(tag) ? 'dark' : 'plain'"
          @click="toggleTag(tag)"
          class="filter-tag"
        >
          {{ tag }}
        </el-tag>
      </div>
      
      <!-- 会话列表 -->
      <div class="session-list">
        <div
          v-for="session in filteredSessions"
          :key="session.id"
          :class="['session-item', { active: currentSessionId === session.id }]"
          @click="switchSession(session.id)"
        >
          <div class="session-info">
            <div class="session-title">{{ session.title }}</div>
            <div class="session-preview">{{ session.lastMessage }}</div>
            <div class="session-time">{{ formatTime(session.updatedAt) }}</div>
          </div>
          <div class="session-actions">
            <el-dropdown @command="(cmd) => handleSessionAction(cmd, session.id)">
              <el-button text circle size="small">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">重命名</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 主聊天区域 -->
    <div class="chat-main">
      <div class="chat-header">
        <div class="chat-title">
          {{ currentSession?.title || '选择一个对话开始聊天' }}
        </div>
        
        <div class="chat-actions">
          <!-- 模式切换 -->
          <el-segmented
            v-model="chatMode"
            :options="chatModeOptions"
            size="small"
          />
          
          <!-- 设置按钮 -->
          <el-button text circle @click="showSettings = true">
            <el-icon><Setting /></el-icon>
          </el-button>
        </div>
      </div>
      
      <!-- 消息区域 -->
      <div ref="messageContainer" class="message-area">
        <div
          v-for="message in currentMessages"
          :key="message.id"
          :class="['message-item', message.sender === 'user' ? 'user-message' : 'ai-message']"
        >
          <div class="message-avatar">
            <el-avatar v-if="message.sender === 'user'" :src="userStore.userInfo?.avatar" size="small">
              {{ userStore.userInfo?.nickname?.charAt(0) || 'U' }}
            </el-avatar>
            <div v-else class="ai-avatar">
              <el-icon><Robot /></el-icon>
            </div>
          </div>
          
          <div class="message-content">
            <div class="message-header">
              <span class="message-sender">
                {{ message.sender === 'user' ? '我' : 'AI助手' }}
              </span>
              <span class="message-time">{{ formatTime(message.timestamp) }}</span>
            </div>
            
            <div class="message-body">
              <div v-if="message.type === 'text'" class="text-message">
                {{ message.content }}
              </div>
              
              <div v-else-if="message.type === 'image'" class="image-message">
                <el-image
                  :src="message.content"
                  :preview-src-list="[message.content]"
                  class="message-image"
                />
              </div>
              
              <div v-else-if="message.type === 'file'" class="file-message">
                <el-icon><Document /></el-icon>
                <span>{{ message.fileName }}</span>
                <el-button text type="primary" @click="downloadFile(message.content)">
                  下载
                </el-button>
              </div>
            </div>
            
            <!-- 消息操作 -->
            <div class="message-actions">
              <el-button text size="small" @click="copyMessage(message.content)">
                <el-icon><CopyDocument /></el-icon>
              </el-button>
              <el-button text size="small" @click="likeMessage(message.id)">
                <el-icon><Like /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
        
        <!-- 加载更多 -->
        <div v-if="hasMoreMessages" class="load-more">
          <el-button text @click="loadMoreMessages">加载更多历史消息</el-button>
        </div>
        
        <!-- 输入状态指示 -->
        <div v-if="isAiTyping" class="typing-indicator">
          <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          AI正在思考中...
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="input-area">
        <!-- 快捷话术 -->
        <div class="quick-replies" v-if="quickReplies.length > 0">
          <el-tag
            v-for="reply in quickReplies"
            :key="reply.id"
            @click="insertQuickReply(reply.content)"
            class="quick-reply-tag"
          >
            {{ reply.title }}
          </el-tag>
        </div>
        
        <!-- 输入框 -->
        <div class="input-container">
          <div class="input-tools">
            <!-- 文件上传 -->
            <el-upload
              ref="uploadRef"
              :show-file-list="false"
              :before-upload="beforeUpload"
              :http-request="customUpload"
              multiple
            >
              <el-button text circle>
                <el-icon><Paperclip /></el-icon>
              </el-button>
            </el-upload>
            
            <!-- 表情 -->
            <el-button text circle @click="showEmojiPicker = !showEmojiPicker">
              <el-icon><Smile /></el-icon>
            </el-button>
          </div>
          
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="输入消息..."
            resize="none"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.enter.shift.exact="addNewLine"
            class="message-input"
          />
          
          <div class="send-tools">
            <el-button
              type="primary"
              :loading="isSending"
              :disabled="!inputMessage.trim()"
              @click="sendMessage"
              class="send-btn"
            >
              发送
            </el-button>
          </div>
        </div>
        
        <!-- 上传的文件预览 -->
        <div v-if="uploadedFiles.length > 0" class="uploaded-files">
          <div
            v-for="(file, index) in uploadedFiles"
            :key="index"
            class="uploaded-file"
          >
            <el-icon><Document /></el-icon>
            <span>{{ file.name }}</span>
            <el-button text @click="removeUploadedFile(index)">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 设置抽屉 -->
    <el-drawer v-model="showSettings" title="聊天设置" direction="rtl" size="400px">
      <div class="chat-settings">
        <el-form label-position="top">
          <el-form-item label="选择模型">
            <el-select v-model="selectedModel" placeholder="请选择AI模型">
              <el-option
                v-for="model in availableModels"
                :key="model.id"
                :label="model.name"
                :value="model.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="温度控制">
            <el-slider v-model="temperature" :min="0" :max="1" :step="0.1" />
          </el-form-item>
          
          <el-form-item label="最大Token数">
            <el-input-number v-model="maxTokens" :min="100" :max="4000" />
          </el-form-item>
          
          <el-form-item label="上下文记忆">
            <el-switch v-model="enableContext" />
          </el-form-item>
        </el-form>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import dayjs from 'dayjs'

const userStore = useUserStore()

// 响应式数据
const isSidebarCollapsed = ref(false)
const searchQuery = ref('')
const selectedTags = ref<string[]>([])
const currentSessionId = ref<number | null>(null)
const chatMode = ref('knowledge')
const inputMessage = ref('')
const isSending = ref(false)
const isAiTyping = ref(false)
const showSettings = ref(false)
const showEmojiPicker = ref(false)
const uploadedFiles = ref<File[]>([])
const hasMoreMessages = ref(true)

// 消息容器引用
const messageContainer = ref<HTMLElement>()

// 聊天设置
const selectedModel = ref('gpt-3.5-turbo')
const temperature = ref(0.7)
const maxTokens = ref(2000)
const enableContext = ref(true)

// 模拟数据
const sessions = ref([
  {
    id: 1,
    title: '产品咨询对话',
    lastMessage: '请问有什么可以帮助您的吗？',
    updatedAt: new Date(),
    tags: ['客服', '产品']
  },
  {
    id: 2,
    title: '技术支持',
    lastMessage: '您的问题已经解决了',
    updatedAt: new Date(Date.now() - 3600000),
    tags: ['技术', '支持']
  }
])

const messages = ref([
  {
    id: 1,
    sessionId: 1,
    sender: 'user',
    type: 'text',
    content: '你好，我想了解一下这个产品的功能',
    timestamp: new Date(),
  },
  {
    id: 2,
    sessionId: 1,
    sender: 'ai',
    type: 'text',
    content: '您好！很高兴为您介绍我们的产品功能。我们的AI智能客服系统具有以下特点：\n\n1. 智能对话：支持自然语言理解和生成\n2. 多模态交互：支持文字、图片、文件等多种消息类型\n3. 知识库检索：快速匹配相关信息\n4. 情感分析：理解用户情绪并适当回应\n\n您还想了解哪些具体功能呢？',
    timestamp: new Date(Date.now() - 60000),
  }
])

const quickReplies = ref([
  { id: 1, title: '您好，有什么可以帮助您？', content: '您好，有什么可以帮助您？' },
  { id: 2, title: '请稍等，我来为您查询', content: '请稍等，我来为您查询' },
  { id: 3, title: '感谢您的咨询', content: '感谢您的咨询，祝您生活愉快！' }
])

const availableModels = ref([
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
  { id: 'gpt-4', name: 'GPT-4' },
  { id: 'claude-3', name: 'Claude 3' },
  { id: 'qwen-max', name: '通义千问 Max' }
])

// 计算属性
const filterTags = computed(() => {
  const tags = new Set<string>()
  sessions.value.forEach(session => {
    session.tags.forEach(tag => tags.add(tag))
  })
  return Array.from(tags)
})

const filteredSessions = computed(() => {
  return sessions.value.filter(session => {
    const matchesSearch = !searchQuery.value || 
      session.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      session.lastMessage.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    const matchesTags = selectedTags.value.length === 0 ||
      selectedTags.value.some(tag => session.tags.includes(tag))
    
    return matchesSearch && matchesTags
  })
})

const currentSession = computed(() => {
  return sessions.value.find(s => s.id === currentSessionId.value)
})

const currentMessages = computed(() => {
  return messages.value.filter(m => m.sessionId === currentSessionId.value)
})

const chatModeOptions = [
  { label: '知识库模式', value: 'knowledge' },
  { label: '大模型模式', value: 'llm' },
  { label: '混合模式', value: 'hybrid' }
]

// 方法
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

const toggleTag = (tag: string) => {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

const createNewChat = () => {
  const newSession = {
    id: Date.now(),
    title: `新对话 ${sessions.value.length + 1}`,
    lastMessage: '',
    updatedAt: new Date(),
    tags: []
  }
  sessions.value.unshift(newSession)
  switchSession(newSession.id)
}

const switchSession = (sessionId: number) => {
  currentSessionId.value = sessionId
  nextTick(() => {
    scrollToBottom()
  })
}

const handleSessionAction = async (command: string, sessionId: number) => {
  if (command === 'rename') {
    // 重命名对话
    const session = sessions.value.find(s => s.id === sessionId)
    if (session) {
      try {
        const { value } = await ElMessageBox.prompt('请输入新的对话标题', '重命名对话', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputValue: session.title
        })
        session.title = value
        ElMessage.success('重命名成功')
      } catch {
        // 用户取消
      }
    }
  } else if (command === 'delete') {
    // 删除对话
    try {
      await ElMessageBox.confirm('确定要删除这个对话吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      
      const index = sessions.value.findIndex(s => s.id === sessionId)
      if (index > -1) {
        sessions.value.splice(index, 1)
        if (currentSessionId.value === sessionId) {
          currentSessionId.value = sessions.value[0]?.id || null
        }
        ElMessage.success('删除成功')
      }
    } catch {
      // 用户取消
    }
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isSending.value) return
  
  const messageContent = inputMessage.value.trim()
  inputMessage.value = ''
  
  // 添加用户消息
  const userMessage = {
    id: Date.now(),
    sessionId: currentSessionId.value!,
    sender: 'user' as const,
    type: 'text' as const,
    content: messageContent,
    timestamp: new Date()
  }
  messages.value.push(userMessage)
  
  // 如果有上传的文件
  if (uploadedFiles.value.length > 0) {
    uploadedFiles.value.forEach((file, index) => {
      const fileMessage = {
        id: Date.now() + index + 1,
        sessionId: currentSessionId.value!,
        sender: 'user' as const,
        type: 'file' as const,
        content: URL.createObjectURL(file),
        fileName: file.name,
        timestamp: new Date()
      }
      messages.value.push(fileMessage)
    })
    uploadedFiles.value = []
  }
  
  scrollToBottom()
  
  // 模拟AI回复
  isSending.value = true
  isAiTyping.value = true
  
  try {
    // 这里应该调用实际的API
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    const aiMessage = {
      id: Date.now() + 1000,
      sessionId: currentSessionId.value!,
      sender: 'ai' as const,
      type: 'text' as const,
      content: '我理解您的问题。基于您的描述，我建议您可以尝试以下解决方案...',
      timestamp: new Date()
    }
    messages.value.push(aiMessage)
    
    // 更新会话最后消息
    const session = sessions.value.find(s => s.id === currentSessionId.value)
    if (session) {
      session.lastMessage = aiMessage.content
      session.updatedAt = new Date()
    }
    
    scrollToBottom()
  } catch (error) {
    ElMessage.error('发送失败，请重试')
  } finally {
    isSending.value = false
    isAiTyping.value = false
  }
}

const addNewLine = () => {
  inputMessage.value += '\n'
}

const insertQuickReply = (content: string) => {
  inputMessage.value = content
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight
    }
  })
}

const formatTime = (time: Date) => {
  return dayjs(time).format('MM-DD HH:mm')
}

const copyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

const likeMessage = (messageId: number) => {
  ElMessage.success('已点赞')
}

const downloadFile = (url: string) => {
  const link = document.createElement('a')
  link.href = url
  link.download = ''
  link.click()
}

const beforeUpload = (file: File) => {
  const isValidType = ['image/jpeg', 'image/png', 'application/pdf', 'application/msword'].includes(file.type)
  const isValidSize = file.size / 1024 / 1024 < 10 // 10MB
  
  if (!isValidType) {
    ElMessage.error('只支持图片、PDF、Word文档')
    return false
  }
  
  if (!isValidSize) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }
  
  return true
}

const customUpload = (options: any) => {
  uploadedFiles.value.push(options.file)
  return Promise.resolve()
}

const removeUploadedFile = (index: number) => {
  uploadedFiles.value.splice(index, 1)
}

const loadMoreMessages = () => {
  // 加载更多历史消息
  ElMessage.info('加载更多消息...')
}

// 监听会话变化
watch(currentSessionId, () => {
  nextTick(() => {
    scrollToBottom()
  })
})

// 初始化
onMounted(() => {
  if (sessions.value.length > 0) {
    currentSessionId.value = sessions.value[0].id
  }
})
</script>

<style lang="scss" scoped>
.chat-container {
  display: flex;
  height: 100%;
  background: $bg-primary;
  border-radius: $border-radius-large;
  overflow: hidden;
  box-shadow: $shadow-medium;
}

.chat-sidebar {
  width: 320px;
  background: $bg-secondary;
  border-right: 1px solid $border-primary;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  
  &.is-collapsed {
    width: 0;
    overflow: hidden;
  }
  
  .sidebar-header {
    padding: 16px;
    border-bottom: 1px solid $border-primary;
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .new-chat-btn {
      flex: 1;
      margin-right: 8px;
    }
  }
  
  .search-bar {
    padding: 16px;
    border-bottom: 1px solid $border-light;
  }
  
  .filter-tags {
    padding: 0 16px 16px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    
    .filter-tag {
      cursor: pointer;
      transition: all 0.3s ease;
    }
  }
  
  .session-list {
    flex: 1;
    overflow-y: auto;
    
    .session-item {
      padding: 16px;
      border-bottom: 1px solid $border-light;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      &:hover {
        background: rgba(255, 255, 255, 0.05);
      }
      
      &.active {
        background: rgba(24, 144, 255, 0.1);
        border-right: 3px solid $primary-color;
      }
      
      .session-info {
        flex: 1;
        min-width: 0;
        
        .session-title {
          font-size: 14px;
          font-weight: 500;
          color: $text-primary;
          margin-bottom: 4px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .session-preview {
          font-size: 12px;
          color: $text-secondary;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          margin-bottom: 4px;
        }
        
        .session-time {
          font-size: 11px;
          color: $text-tertiary;
        }
      }
      
      .session-actions {
        opacity: 0;
        transition: opacity 0.3s ease;
      }
      
      &:hover .session-actions {
        opacity: 1;
      }
    }
  }
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  
  .chat-header {
    height: 60px;
    padding: 0 24px;
    border-bottom: 1px solid $border-primary;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: $bg-secondary;
    
    .chat-title {
      font-size: 16px;
      font-weight: 500;
      color: $text-primary;
    }
    
    .chat-actions {
      display: flex;
      align-items: center;
      gap: 16px;
    }
  }
  
  .message-area {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    
    .message-item {
      display: flex;
      gap: 12px;
      margin-bottom: 24px;
      animation: slideInUp 0.3s ease-out;
      
      &.user-message {
        flex-direction: row-reverse;
        
        .message-content {
          background: $primary-color;
          color: white;
          margin-left: 60px;
        }
      }
      
      &.ai-message {
        .message-content {
          background: $bg-card;
          border: 1px solid $border-primary;
          margin-right: 60px;
        }
      }
      
      .message-avatar {
        .ai-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: $gradient-tech;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
        }
      }
      
      .message-content {
        max-width: 70%;
        border-radius: 12px;
        padding: 12px 16px;
        position: relative;
        
        .message-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
          
          .message-sender {
            font-size: 12px;
            font-weight: 500;
            opacity: 0.8;
          }
          
          .message-time {
            font-size: 11px;
            opacity: 0.6;
          }
        }
        
        .message-body {
          .text-message {
            white-space: pre-wrap;
            word-break: break-word;
            line-height: 1.5;
          }
          
          .image-message {
            .message-image {
              max-width: 200px;
              border-radius: 8px;
            }
          }
          
          .file-message {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
          }
        }
        
        .message-actions {
          display: flex;
          gap: 8px;
          margin-top: 8px;
          opacity: 0;
          transition: opacity 0.3s ease;
        }
        
        &:hover .message-actions {
          opacity: 1;
        }
      }
    }
    
    .load-more {
      text-align: center;
      margin-bottom: 16px;
    }
    
    .typing-indicator {
      display: flex;
      align-items: center;
      gap: 12px;
      color: $text-secondary;
      font-size: 14px;
      
      .typing-dots {
        display: flex;
        gap: 4px;
        
        span {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: $primary-color;
          animation: typing 1.4s infinite;
          
          &:nth-child(2) {
            animation-delay: 0.2s;
          }
          
          &:nth-child(3) {
            animation-delay: 0.4s;
          }
        }
      }
    }
  }
  
  .input-area {
    border-top: 1px solid $border-primary;
    background: $bg-secondary;
    padding: 16px 24px;
    
    .quick-replies {
      display: flex;
      gap: 8px;
      margin-bottom: 12px;
      flex-wrap: wrap;
      
      .quick-reply-tag {
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          background: $primary-color;
          color: white;
        }
      }
    }
    
    .input-container {
      display: flex;
      gap: 12px;
      align-items: flex-end;
      
      .input-tools {
        display: flex;
        gap: 8px;
      }
      
      .message-input {
        flex: 1;
        
        :deep(.el-textarea__inner) {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: $text-primary;
          border-radius: 8px;
          resize: none;
          
          &:focus {
            border-color: $primary-color;
            box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
          }
          
          &::placeholder {
            color: $text-placeholder;
          }
        }
      }
      
      .send-tools {
        display: flex;
        gap: 8px;
      }
    }
    
    .uploaded-files {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
      
      .uploaded-file {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        font-size: 12px;
      }
    }
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

.chat-settings {
  padding: 16px 0;
}

// 响应式设计
@media (max-width: 768px) {
  .chat-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100%;
    z-index: $z-modal;
    
    &.is-collapsed {
      transform: translateX(-100%);
    }
  }
  
  .chat-main {
    width: 100%;
  }
}
</style> 
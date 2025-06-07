<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '240px'" class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <img src="/logo.svg" alt="ShopTalk AI" v-if="!isCollapse" />
          <h1 v-if="!isCollapse" class="logo-text neon-text">ShopTalk AI</h1>
          <el-icon v-else class="logo-icon"><BrushFilled /></el-icon>
        </div>
      </div>
      
      <el-menu
        :default-active="$route.path"
        :collapse="isCollapse"
        :unique-opened="true"
        router
        class="sidebar-menu"
      >
        <el-menu-item
          v-for="route in menuRoutes"
          :key="route.path"
          :index="route.path"
          class="menu-item"
        >
          <el-icon><component :is="route.meta.icon" /></el-icon>
          <template #title>{{ route.meta.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <el-button
            text
            @click="toggleSidebar"
            class="collapse-btn"
          >
            <el-icon><Expand v-if="isCollapse" /><Fold v-else /></el-icon>
          </el-button>
          
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentRoute?.meta?.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 搜索框 -->
          <el-input
            v-model="searchQuery"
            placeholder="搜索功能..."
            prefix-icon="Search"
            class="search-input"
            clearable
          />
          
          <!-- 通知 -->
          <el-badge :value="12" class="notification-badge">
            <el-button text circle>
              <el-icon><Bell /></el-icon>
            </el-button>
          </el-badge>
          
          <!-- 用户菜单 -->
          <el-dropdown @command="handleUserCommand">
            <div class="user-info">
              <el-avatar :src="userStore.userInfo?.avatar" :size="32">
                {{ userStore.userInfo?.nickname?.charAt(0) || 'U' }}
              </el-avatar>
              <span class="username">{{ userStore.userInfo?.nickname || '用户' }}</span>
              <el-icon><CaretBottom /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主要内容 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)
const searchQuery = ref('')

// 当前路由信息
const currentRoute = computed(() => route.matched[route.matched.length - 1])

// 菜单路由
const menuRoutes = computed(() => {
  return router.options.routes
    .find(r => r.path === '/')
    ?.children?.filter(child => child.meta?.title) || []
})

// 切换侧边栏
const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}

// 处理用户菜单命令
const handleUserCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      // 系统设置功能
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        userStore.logout()
        router.push('/login')
      } catch {
        // 用户取消
      }
      break
  }
}

// 初始化用户信息
onMounted(() => {
  if (userStore.token && !userStore.userInfo) {
    userStore.fetchUserInfo()
  }
})
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
  display: flex;
  background: $bg-primary;
}

.sidebar {
  background: $bg-secondary;
  border-right: 1px solid $border-primary;
  transition: width 0.3s ease;
  overflow: hidden;
  
  .sidebar-header {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid $border-primary;
    
    .logo {
      display: flex;
      align-items: center;
      gap: 12px;
      
      img {
        width: 32px;
        height: 32px;
      }
      
      .logo-text {
        font-size: 18px;
        font-weight: bold;
        margin: 0;
      }
      
      .logo-icon {
        font-size: 24px;
        color: $primary-color;
      }
    }
  }
  
  .sidebar-menu {
    background: transparent;
    border: none;
    
    :deep(.el-menu-item) {
      color: $text-secondary;
      transition: all 0.3s ease;
      margin: 4px 8px;
      border-radius: 8px;
      
      &:hover {
        color: $text-primary;
        background: rgba(24, 144, 255, 0.1);
      }
      
      &.is-active {
        color: $primary-color;
        background: rgba(24, 144, 255, 0.2);
        border-right: 3px solid $primary-color;
      }
    }
    
    :deep(.el-menu-item-group__title) {
      color: $text-tertiary;
      font-size: 12px;
      padding: 8px 20px;
    }
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.header {
  background: $bg-secondary;
  border-bottom: 1px solid $border-primary;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 60px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 24px;
    
    .collapse-btn {
      color: $text-secondary;
      
      &:hover {
        color: $primary-color;
      }
    }
    
    .breadcrumb {
      :deep(.el-breadcrumb__item) {
        .el-breadcrumb__inner {
          color: $text-secondary;
          
          &:hover {
            color: $primary-color;
          }
        }
        
        &:last-child .el-breadcrumb__inner {
          color: $text-primary;
        }
      }
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .search-input {
      width: 240px;
      
      :deep(.el-input__wrapper) {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        
        &:hover {
          border-color: $primary-color;
        }
      }
      
      :deep(.el-input__inner) {
        color: $text-primary;
        
        &::placeholder {
          color: $text-placeholder;
        }
      }
    }
    
    .notification-badge {
      :deep(.el-button) {
        color: $text-secondary;
        
        &:hover {
          color: $primary-color;
        }
      }
    }
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 8px 12px;
      border-radius: 8px;
      transition: all 0.3s ease;
      
      &:hover {
        background: rgba(255, 255, 255, 0.05);
      }
      
      .username {
        color: $text-primary;
        font-size: 14px;
      }
      
      .el-icon {
        color: $text-secondary;
      }
    }
  }
}

.main-content {
  flex: 1;
  background: $bg-primary;
  overflow-y: auto;
  padding: 24px;
}

// 页面切换动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// 响应式设计
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: $z-sidebar;
    
    &.is-collapse {
      transform: translateX(-100%);
    }
  }
  
  .main-container {
    margin-left: 0;
  }
  
  .header {
    .search-input {
      display: none;
    }
  }
}
</style> 
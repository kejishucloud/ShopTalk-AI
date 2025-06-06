import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

// 懒加载组件
const Login = () => import('@/views/Login.vue')
const Layout = () => import('@/layouts/MainLayout.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const Chat = () => import('@/views/Chat.vue')
const Profile = () => import('@/views/Profile.vue')
const TagManager = () => import('@/views/TagManager.vue')
// TODO: Create these missing components
// const KeywordManager = () => import('@/views/KeywordManager.vue')
// const KnowledgeBase = () => import('@/views/KnowledgeBase.vue')
// const ModelManager = () => import('@/views/ModelManager.vue')
// const KnowledgeQuery = () => import('@/views/KnowledgeQuery.vue')
// const PlatformManager = () => import('@/views/PlatformManager.vue')
// const Analytics = () => import('@/views/Analytics.vue')
const SystemConfig = () => import('@/views/SystemConfig.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '仪表盘', icon: 'Odometer' }
      },
      {
        path: '/chat',
        name: 'Chat',
        component: Chat,
        meta: { title: '智能对话', icon: 'ChatRound' }
      },
      {
        path: '/profile',
        name: 'Profile',
        component: Profile,
        meta: { title: '个人中心', icon: 'User' }
      },
      {
        path: '/tags',
        name: 'TagManager',
        component: TagManager,
        meta: { title: '标签管理', icon: 'CollectionTag' }
      },
      // TODO: Uncomment these routes after creating the missing components
      // {
      //   path: '/keywords',
      //   name: 'KeywordManager',
      //   component: KeywordManager,
      //   meta: { title: '关键词管理', icon: 'Key' }
      // },
      // {
      //   path: '/knowledge',
      //   name: 'KnowledgeBase',
      //   component: KnowledgeBase,
      //   meta: { title: '知识库管理', icon: 'DocumentCopy' }
      // },
      // {
      //   path: '/models',
      //   name: 'ModelManager',
      //   component: ModelManager,
      //   meta: { title: '大模型管理', icon: 'BrushFilled' }
      // },
      // {
      //   path: '/knowledge-query',
      //   name: 'KnowledgeQuery',
      //   component: KnowledgeQuery,
      //   meta: { title: '知识库查询', icon: 'Search' }
      // },
      // {
      //   path: '/platforms',
      //   name: 'PlatformManager',
      //   component: PlatformManager,
      //   meta: { title: '平台接入', icon: 'Connection' }
      // },
      // {
      //   path: '/analytics',
      //   name: 'Analytics',
      //   component: Analytics,
      //   meta: { title: '运营监控', icon: 'DataAnalysis' }
      // },
      {
        path: '/system-config',
        name: 'SystemConfig',
        component: SystemConfig,
        meta: { title: '系统配置', icon: 'Setting' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.token) {
    next('/login')
  } else if (to.path === '/login' && userStore.token) {
    next('/')
  } else {
    next()
  }
})

export default router 
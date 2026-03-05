import { createRouter, createWebHistory } from 'vue-router'
import { isAuthed } from '@/services/auth'

import HomeView from '../views/HomeView.vue'
import ChatView from '../views/ChatView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView
    },
    { 
      path: '/login', 
      name: 'login', 
      component: LoginView 
    },
    { path: '/register', 
      name: 'register', 
      component: RegisterView 
    },
  ]
})


router.beforeEach((to) => {
  const publicPaths = ['/', '/login', '/register']

  if (!publicPaths.includes(to.path) && !isAuthed()) {
    return '/login'
  }
})


export default router


<template>
  <header class="topbar">
  <RouterLink class="topbar__brand" to="/">Voice Assistant</RouterLink>

  <div class="topbar__right">
    <template v-if="authed">
      <span class="topbar__email">{{ email }}</span>
      <button class="topbar__btn" @click="onLogout">Выйти</button>
    </template>
    <template v-else>
      <RouterLink class="topbar__link" to="/login">Войти</RouterLink>
      <RouterLink class="topbar__link" to="/register">Регистрация</RouterLink>
    </template>
  </div>
</header>

<RouterView />

</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { logout } from '@/services/auth'
import { authedEmail, authedToken } from '@/services/authStore'

const router = useRouter()
const route = useRoute()


const authed = computed(() => Boolean(authedToken.value))
const email = computed(() => authedEmail.value)

function onLogout() {
  logout()
  // если был на закрытой странице — вернём на логин, иначе можно на главную
  if (route.path === '/chat') router.push('/login')
  else router.push('/')
}
</script>

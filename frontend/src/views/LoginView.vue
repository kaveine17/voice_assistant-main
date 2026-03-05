<template>
  <div class="auth">
    <div class="auth__top">
      <RouterLink class="auth__back" to="/">← На главную</RouterLink>
    </div>

    <div class="auth__card">
      <h1 class="auth__title">Вход</h1>
      <p class="auth__subtitle">Введите почту и пароль</p>

      <form class="auth__form" @submit.prevent="onSubmit">
        <input
          v-model.trim="email"
          class="auth__input"
          type="email"
          placeholder="Email"
          autocomplete="email"
          required
        />

        <input
          v-model="password"
          class="auth__input"
          type="password"
          placeholder="Пароль"
          autocomplete="current-password"
          required
          minlength="6"
        />

        <p v-if="error" class="auth__error">{{ error }}</p>

        <button class="auth__button" type="submit" :disabled="loading">
          {{ loading ? 'Входим…' : 'Войти' }}
        </button>
      </form>

      <div class="auth__footer">
        Нет аккаунта?
        <RouterLink to="/register">Зарегистрироваться</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, isAuthed } from '@/services/auth'

const router = useRouter()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

// если уже есть токен — сразу в чат
if (isAuthed()) {
  router.replace('/chat')
}

async function onSubmit() {
  console.log('SUBMIT LOGIN', email.value, password.value)
  error.value = null
  loading.value = true
  try {
    await login(email.value, password.value)
    router.push('/chat')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Ошибка входа'
  } finally {
    loading.value = false
  }
}
</script>
<template>
  <div class="auth">
    <div class="auth__top">
      <RouterLink class="auth__back" to="/">← На главную</RouterLink>
    </div>

    <div class="auth__card">
      <h1 class="auth__title">Регистрация</h1>
      <p class="auth__subtitle">Создайте аккаунт</p>

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
          placeholder="Пароль (минимум 6 символов)"
          autocomplete="new-password"
          required
          minlength="6"
        />

        <input
          v-model="password2"
          class="auth__input"
          type="password"
          placeholder="Повторите пароль"
          autocomplete="new-password"
          required
          minlength="6"
        />

        <p v-if="error" class="auth__error">{{ error }}</p>

        <button class="auth__button" type="submit" :disabled="loading">
          {{ loading ? 'Создаём…' : 'Создать аккаунт' }}
        </button>
      </form>

      <div class="auth__footer">
        Уже есть аккаунт?
        <RouterLink to="/login">Войти</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { register, isAuthed } from '@/services/auth'

const router = useRouter()

const email = ref('')
const password = ref('')
const password2 = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

if (isAuthed()) {
  router.replace('/chat')
}

async function onSubmit() {
  error.value = null
  loading.value = true
  try {
    if (password.value !== password2.value) {
      throw new Error('Пароли не совпадают')
    }

    await register(email.value, password.value)
    router.push('/login')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Ошибка регистрации'
  } finally {
    loading.value = false
  }
}
</script>
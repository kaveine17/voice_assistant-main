<template>
  <div class="page">
    <div class="card">
      <div class="badge">Voice Assistant</div>

      <h1 class="title">Интеллектуальный персональный ассистент</h1>
      <p class="subtitle">
        Голосовое управление + чат. Сейчас собираем UI, дальше подключим STT API и ChatGPT API.
      </p>

      <div class="actions">
        <button class="btn btn--primary" @click="go('/chat')">Открыть чат</button>
        <button class="btn btn--ghost" @click="go('/login')">Войти</button>
        <button class="btn btn--ghost" @click="go('/register')">Регистрация</button>
      </div>

      <div class="meta">
        <span>Vue 3 + Vite</span>
        <span>FastAPI (позже)</span>
        <span>PostgreSQL</span>
        <span>STT + LLM</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
const go = (path: string) => router.push(path)
</script>
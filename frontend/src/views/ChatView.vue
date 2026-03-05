<template>
  <div class="page">
    <div class="card chat">
      <div class="chat__top">
        <div>
          <div class="badge">Диалог</div>
          <h1 class="title">Чат ассистента</h1>
          <p class="subtitle">Пока без бэка: ответы моковые. Дальше подключим STT и ChatGPT.</p>
        </div>

        <div class="chat__top-actions">
          <button class="btn btn--ghost" @click="goHome">На главную</button>
        </div>
      </div>

      <div class="chat__window" ref="windowRef">
        <div
          v-for="m in messages"
          :key="m.id"
          class="chat__msg"
          :class="m.role === 'user' ? 'chat__msg--user' : 'chat__msg--assistant'"
        >
          <div class="chat__bubble">
            <div class="chat__role">{{ m.role === 'user' ? 'Вы' : 'Ассистент' }}</div>
            <div class="chat__text">{{ m.text }}</div>
          </div>
        </div>
      </div>

      <div class="chat__composer">
        <button
          class="btn btn--ghost"
          @click="toggleRecording"
          :aria-pressed="recording"
          title="Запись голоса (пока UI-заглушка)"
        >
          {{ recording ? '■ Стоп' : '● Запись' }}
        </button>

        <input
          v-model="input"
          class="chat__input"
          type="text"
          placeholder="Напишите сообщение…"
          @keydown.enter.prevent="send"
        />

        <button class="btn btn--primary" @click="send" :disabled="!input.trim() || sending">
          {{ sending ? '…' : 'Отправить' }}
        </button>
      </div>

      <div class="chat__hint">
        Подсказка: позже кнопка “Запись” будет отправлять аудио на <code>/api/stt</code>, а текст — на <code>/api/chat</code>.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { chat, type ChatMessage } from '../services/chat'
type Role = 'user' | 'assistant'
type Msg = { id: string; role: Role; text: string }

const router = useRouter()

const input = ref('')
const sending = ref(false)
const recording = ref(false)
const windowRef = ref<HTMLDivElement | null>(null)

const messages = ref<Msg[]>([
  { id: crypto.randomUUID(), role: 'assistant', text: 'Привет! Я готов помочь. Напиши сообщение или нажми “Запись”.' },
])

function goHome() {
  router.push('/')
}

function toggleRecording() {
  // Пока только UI, без WebAudio.
  recording.value = !recording.value
  if (recording.value) {
    // имитация “распознанной речи” через 1.2 сек
    setTimeout(() => {
      if (!recording.value) return
      recording.value = false
      input.value = 'Привет! Это тест распознавания речи.'
    }, 1200)
  }
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return

  messages.value.push({ id: crypto.randomUUID(), role: 'user', text })
  input.value = ''
  sending.value = true
  await scrollToBottom()

  try {
    // Пока мок-ответ. Потом заменим на реальный fetch к backend.
    const payload: ChatMessage[] = [
  { role: 'system', content: 'Ты дружелюбный ассистент.' },
  ...messages.value.map((m): ChatMessage => ({
    role: m.role === 'user' ? 'user' : 'assistant',
    content: m.text,
  })),
]

const { reply } = await chat(payload, 0.7)

messages.value.push({
  id: crypto.randomUUID(),
  role: 'assistant',
  text: reply,
})
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

async function scrollToBottom() {
  await nextTick()
  const el = windowRef.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

onMounted(scrollToBottom)
</script>

<style scoped lang="scss">
@use "../assets/styles/variables" as v;

.chat {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__top {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: flex-start;
  }

  &__top-actions {
    display: flex;
    gap: 12px;
  }

  &__window {
    height: min(56vh, 520px);
    overflow: auto;
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 18px;
    background: rgba(255,255,255,0.75);
    padding: 14px;
  }

  &__msg {
    display: flex;
    margin: 10px 0;

    &--user { justify-content: flex-end; }
    &--assistant { justify-content: flex-start; }
  }

  &__bubble {
    width: min(560px, 92%);
    border-radius: 18px;
    padding: 12px 14px;
    border: 1px solid rgba(0,0,0,0.08);
    background: rgba(255,255,255,0.92);
  }

  &__msg--user .chat__bubble {
    background: rgba(99, 102, 241, 0.10);
    border-color: rgba(99, 102, 241, 0.25);
  }

  &__role {
    font-size: 12px;
    color: v.$muted;
    margin-bottom: 6px;
  }

  &__text {
    white-space: pre-wrap;
    line-height: 1.45;
    color: v.$text;
  }

  &__composer {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 12px;
    align-items: center;
  }

  &__input {
    width: 100%;
    padding: 12px 14px;
    border-radius: 14px;
    border: 1px solid rgba(0, 0, 0, 0.16);
    background: rgba(255, 255, 255, 0.95);
    font-size: 14px;
    outline: none;
    transition: 0.15s ease;
  }

  &__input:focus {
    border-color: rgba(99, 102, 241, 0.9);
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.18);
  }

  &__hint {
    font-size: 12px;
    color: v.$muted;

    code {
      padding: 2px 6px;
      border-radius: 10px;
      border: 1px solid rgba(0,0,0,0.08);
      background: rgba(255,255,255,0.8);
    }
  }
}
</style>
<template>
  <div class="chat-page" :class="{ 'chat-page--sidebar-open': sidebarOpen }">
    <div class="chat-sidebar-overlay" aria-hidden="true" @click="sidebarOpen = false" />

    <aside class="chat-sidebar">
      <div class="chat-sidebar__top">
        <button class="chat-sidebar__close" type="button" aria-label="Закрыть меню" @click="sidebarOpen = false">
          ×
        </button>
        <button class="btn btn--primary chat-sidebar__new" @click="createNewConversation">
          + Новый чат
        </button>
      </div>

      <div class="chat-sidebar__list">
        <div
          v-for="conversation in conversations"
          :key="conversation.id"
          class="chat-sidebar__item"
          :class="{ 'chat-sidebar__item--active': conversation.id === activeConversationId }"
          role="button"
          tabindex="0"
          @click="selectConversation(conversation.id); sidebarOpen = false"
          @keydown.enter.space.prevent="selectConversation(conversation.id); sidebarOpen = false"
        >
          <div class="chat-sidebar__item-content">
            <div class="chat-sidebar__title">{{ conversation.title }}</div>
            <div class="chat-sidebar__date">{{ formatDate(conversation.created_at) }}</div>
          </div>
          <button
            type="button"
            class="chat-sidebar__item-delete"
            aria-label="Удалить чат"
            :disabled="deletingId === conversation.id"
            @click.stop="deleteConversation(conversation.id)"
          >
            {{ deletingId === conversation.id ? '…' : '×' }}
          </button>
        </div>

        <div v-if="!conversations.length" class="chat-sidebar__empty">
          Пока нет чатов
        </div>
      </div>
    </aside>

    <section class="chat-main">
      <div class="chat-main__header">
        <button
          class="chat-main__menu-btn"
          type="button"
          aria-label="Открыть список чатов"
          @click="sidebarOpen = true"
        >
          ☰
        </button>
        <div>
          <h1 class="chat-main__title">
            {{ activeConversationTitle || 'Чат ассистента' }}
          </h1>
          <p class="chat-main__subtitle">
            История сохраняется отдельно для каждого чата
          </p>
        </div>
      </div>

      <div ref="messagesContainer" class="chat-main__messages">
        <template v-if="messages.length">
          <div
            v-for="message in messages"
            :key="message.id"
            class="chat-message"
            :class="{
              'chat-message--user': message.role === 'user',
              'chat-message--assistant': message.role === 'assistant'
            }"
          >
            <div class="chat-message__bubble">
              <div class="chat-message__role">
                {{ message.role === 'user' ? 'Вы' : 'Ассистент' }}
              </div>
              <div class="chat-message__content">
                {{ message.content }}
              </div>
            </div>
          </div>
        </template>

        <div v-else class="chat-main__empty">
          Выберите чат или создайте новый, чтобы начать разговор
        </div>

        <div v-if="sending" class="chat-message chat-message--assistant">
          <div class="chat-message__bubble">
            <div class="chat-message__role">Ассистент</div>
            <div class="chat-message__content">Печатает...</div>
          </div>
        </div>
      </div>

      <div class="chat-main__composer">
        <div class="chat-main__input-row">
          <textarea
            v-model="input"
            class="chat-main__input"
            placeholder="Введите сообщение..."
            rows="3"
            @keydown.enter.prevent="handleEnter"
          />
          <button
            type="button"
            class="chat-main__voice-btn"
            :class="{ 'chat-main__voice-btn--recording': isRecording }"
            :disabled="!activeConversationId || sending"
            :title="isRecording ? 'Остановить запись' : 'Голосовой ввод'"
            aria-label="Голосовой ввод"
            @click="toggleVoiceInput"
          >
            <svg class="chat-main__voice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3Z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" x2="12" y1="19" y2="22"/>
            </svg>
          </button>
          <button
            class="btn btn--primary chat-main__send-btn"
            :disabled="!canSend"
            @click="sendMessage"
          >
            {{ sending ? 'Отправка...' : 'Отправить' }}
          </button>
        </div>
        <p v-if="voiceError" class="chat-main__voice-error">{{ voiceError }}</p>

        <p v-if="error" class="chat-main__error">
          {{ error }}
        </p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">

import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'

const API = 'http://127.0.0.1:8000/api'

const SpeechRecognitionAPI =
  typeof window !== 'undefined' &&
  ((window as Window & { SpeechRecognition?: new () => SpeechRecognition; webkitSpeechRecognition?: new () => SpeechRecognition }).SpeechRecognition ||
    (window as Window & { webkitSpeechRecognition?: new () => SpeechRecognition }).webkitSpeechRecognition)

type Conversation = {
  id: number
  title: string
  created_at: string
}

type Message = {
  id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

const conversations = ref<Conversation[]>([])
const messages = ref<Message[]>([])
const activeConversationId = ref<number | null>(null)
const input = ref('')
const loading = ref(false)
const sending = ref(false)
const error = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const sidebarOpen = ref(false)
const deletingId = ref<number | null>(null)
const isRecording = ref(false)
const voiceError = ref('')
let recognition: SpeechRecognition | null = null



const activeConversationTitle = computed(() => {
  return conversations.value.find(c => c.id === activeConversationId.value)?.title ?? ''
})

const canSend = computed(() => {
  return Boolean(input.value.trim()) && Boolean(activeConversationId.value) && !sending.value
})

function authHeaders() {
  return {
    Authorization: `Bearer ${getToken()}`,
    'Content-Type': 'application/json',
  }
}
function getToken () {
  return localStorage.getItem('va_token')
}

async function fetchConversations() {
  loading.value = true
  error.value = ''

  try {
    const res = await fetch(`${API}/conversations`, {
      headers: {
        Authorization: `Bearer ${getToken()}`,
      },
    })

    const data = await res.json()

    if (!res.ok) {
      throw new Error(data?.detail ?? 'Не удалось загрузить чаты')
    }

    conversations.value = data

    if (data.length && !activeConversationId.value) {
      activeConversationId.value = data[0].id
      await fetchMessages(data[0].id)
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Ошибка загрузки чатов'
  } finally {
    loading.value = false
  }
}

async function createNewConversation() {
  error.value = ''

  try {
    const res = await fetch(`${API}/conversations`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ title: 'Новый чат' }),
    })

    const data = await res.json()

    if (!res.ok) {
      throw new Error(data?.detail ?? 'Не удалось создать чат')
    }

    conversations.value.unshift(data)
    activeConversationId.value = data.id
    messages.value = []
    input.value = ''
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Ошибка создания чата'
  }
}

async function fetchMessages(conversationId: number) {
  error.value = ''

  try {
    const res = await fetch(`${API}/conversations/${conversationId}/messages`, {
      headers: {
        Authorization: `Bearer ${getToken()}`,
      },
    })

    const data = await res.json()

    if (!res.ok) {
      throw new Error(data?.detail ?? 'Не удалось загрузить сообщения')
    }

    messages.value = data
    await scrollToBottom()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Ошибка загрузки сообщений'
  }
}

async function selectConversation(conversationId: number) {
  if (activeConversationId.value === conversationId) return

  activeConversationId.value = conversationId
  await fetchMessages(conversationId)
}

async function deleteConversation(conversationId: number) {
  error.value = ''
  deletingId.value = conversationId
  try {
    const res = await fetch(`${API}/conversations/${conversationId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data?.detail ?? 'Не удалось удалить чат')
    }
    const wasActive = activeConversationId.value === conversationId
    conversations.value = conversations.value.filter((c) => c.id !== conversationId)
    if (wasActive) {
      activeConversationId.value = conversations.value[0]?.id ?? null
      if (activeConversationId.value) {
        await fetchMessages(activeConversationId.value)
      } else {
        messages.value = []
      }
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Ошибка удаления чата'
  } finally {
    deletingId.value = null
  }
}

async function sendMessage() {
  if (!canSend.value || !activeConversationId.value) return

  const content = input.value.trim()
  if (!content) return

  error.value = ''
  sending.value = true

  // Оптимистичное отображение: сразу показываем сообщение пользователя
  const tempUserMessage: Message = {
    id: -Date.now(),
    conversation_id: activeConversationId.value,
    role: 'user',
    content,
    created_at: new Date().toISOString(),
  }
  messages.value.push(tempUserMessage)
  input.value = ''
  await scrollToBottom()

  try {
    const res = await fetch(`${API}/conversations/${activeConversationId.value}/send`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ content }),
    })

    const data = await res.json()

    if (!res.ok) {
      throw new Error(data?.detail ?? 'Не удалось отправить сообщение')
    }

    await fetchMessages(activeConversationId.value)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Ошибка отправки сообщения'
    // Убираем оптимистичное сообщение при ошибке
    messages.value = messages.value.filter((m) => m.id !== tempUserMessage.id)
  } finally {
    sending.value = false
  }
}

function handleEnter(event: KeyboardEvent) {
  if (event.shiftKey) return
  sendMessage()
}

function toggleVoiceInput() {
  if (!SpeechRecognitionAPI) {
    voiceError.value = 'Голосовой ввод не поддерживается в этом браузере (Chrome, Edge)'
    return
  }
  voiceError.value = ''
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

function startRecording() {
  if (!SpeechRecognitionAPI || !activeConversationId.value) return
  recognition = new (SpeechRecognitionAPI as new () => SpeechRecognition)()
  recognition.continuous = true
  recognition.interimResults = true
  recognition.lang = 'ru-RU'
  recognition.onresult = (event: SpeechRecognitionEvent) => {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        const transcript = event.results[i][0].transcript
        if (transcript) {
          input.value = (input.value + (input.value ? ' ' : '') + transcript).trim()
        }
      }
    }
  }
  recognition.onerror = (e: SpeechRecognitionErrorEvent) => {
    if (e.error !== 'aborted' && e.error !== 'no-speech') {
      voiceError.value =
        e.error === 'not-allowed'
          ? 'Доступ к микрофону запрещён'
          : e.error === 'network'
            ? 'Нет связи с сервисом распознавания. Проверьте интернет и попробуйте снова.'
            : e.error === 'service-not-allowed'
              ? 'Сервис распознавания речи недоступен (проверьте настройки браузера).'
              : `Ошибка: ${e.error}`
    }
    stopRecording()
  }
  recognition.onend = () => {
    if (isRecording.value) {
      isRecording.value = false
    }
  }
  isRecording.value = true
  recognition.start()
}

function stopRecording() {
  if (recognition) {
    try {
      recognition.stop()
    } catch {
      /* ignore */
    }
    recognition = null
  }
  isRecording.value = false
}

onUnmounted(() => {
  stopRecording()
})

function formatDate(value: string) {
  const date = new Date(value)
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  })
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

onMounted(async () => {
  await fetchConversations()
})
</script>
<style src="../assets/styles/pages/chat.scss" lang="scss"></style>

<template>
  <div class="chat-page">
    <aside class="chat-sidebar">
      <div class="chat-sidebar__top">
        <button class="btn btn--primary chat-sidebar__new" @click="createNewConversation">
          + Новый чат
        </button>
      </div>

      <div class="chat-sidebar__list">
        <button
          v-for="conversation in conversations"
          :key="conversation.id"
          class="chat-sidebar__item"
          :class="{ 'chat-sidebar__item--active': conversation.id === activeConversationId }"
          @click="selectConversation(conversation.id)"
        >
          <div class="chat-sidebar__title">{{ conversation.title }}</div>
          <div class="chat-sidebar__date">{{ formatDate(conversation.created_at) }}</div>
        </button>

        <div v-if="!conversations.length" class="chat-sidebar__empty">
          Пока нет чатов
        </div>
      </div>
    </aside>

    <section class="chat-main">
      <div class="chat-main__header">
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
        <textarea
          v-model="input"
          class="chat-main__input"
          placeholder="Введите сообщение..."
          rows="3"
          @keydown.enter.prevent="handleEnter"
        />

        <div class="chat-main__actions">
          <button
            class="btn btn--primary"
            :disabled="!canSend"
            @click="sendMessage"
          >
            {{ sending ? 'Отправка...' : 'Отправить' }}
          </button>
        </div>

        <p v-if="error" class="chat-main__error">
          {{ error }}
        </p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">

import { computed, nextTick, onMounted, ref } from 'vue'

const API = 'http://127.0.0.1:8000/api'

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

const token = localStorage.getItem('va_token')

const activeConversationTitle = computed(() => {
  return conversations.value.find(c => c.id === activeConversationId.value)?.title ?? ''
})

const canSend = computed(() => {
  return Boolean(input.value.trim()) && Boolean(activeConversationId.value) && !sending.value
})

function authHeaders() {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}

async function fetchConversations() {
  loading.value = true
  error.value = ''

  try {
    const res = await fetch(`${API}/conversations`, {
      headers: {
        Authorization: `Bearer ${token}`,
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
        Authorization: `Bearer ${token}`,
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

async function sendMessage() {
  if (!canSend.value || !activeConversationId.value) return

  const content = input.value.trim()
  if (!content) return

  error.value = ''
  sending.value = true

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

    input.value = ''
    await fetchMessages(activeConversationId.value)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Ошибка отправки сообщения'
  } finally {
    sending.value = false
  }
}

function handleEnter(event: KeyboardEvent) {
  if (event.shiftKey) return
  sendMessage()
}

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

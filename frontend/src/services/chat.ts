import { getToken } from './auth'

const API = 'http://127.0.0.1:8000'

export type Role = 'system' | 'user' | 'assistant'
export type ChatMessage = { role: Role; content: string }

export async function chat(messages: ChatMessage[], temperature = 0.7) {
  const token = getToken()

  const res = await fetch(`${API}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ messages, temperature }),
  })

  const data = await safeJson(res)
  if (!res.ok) throw new Error(data?.detail ?? 'Ошибка запроса к /api/chat')
  return data as { reply: string }
}

async function safeJson(res: Response) {
  try {
    return await res.json()
  } catch {
    return null
  }
}
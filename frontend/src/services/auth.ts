
// frontend/src/services/auth.ts
import { syncAuthFromStorage } from './authStore'
const API = 'http://127.0.0.1:8000'

const TOKEN_KEY = 'va_token'
const EMAIL_KEY = 'va_email'

export function isAuthed() {
  return Boolean(localStorage.getItem(TOKEN_KEY))
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getAuthedEmail() {
  return localStorage.getItem(EMAIL_KEY)
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(EMAIL_KEY)
  syncAuthFromStorage()
}

export async function register(email: string, password: string) {
  const res = await fetch(`${API}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })

  if (!res.ok) {
    const data = await safeJson(res)
    throw new Error(data?.detail ?? 'Ошибка регистрации')
  }
}

export async function login(email: string, password: string) {
  // ВАЖНО: backend /auth/login сейчас принимает form-data (OAuth2)
  const body = new URLSearchParams()
  body.set('username', email)
  body.set('password', password)

  const res = await fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })

  const data = await safeJson(res)
  if (!res.ok) throw new Error(data?.detail ?? 'Ошибка входа')

  localStorage.setItem(TOKEN_KEY, data.access_token)
  localStorage.setItem(EMAIL_KEY, email.toLowerCase())
  syncAuthFromStorage()
}

export async function me() {
  const token = getToken()
  const res = await fetch(`${API}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  const data = await safeJson(res)
  if (!res.ok) throw new Error(data?.detail ?? 'Не авторизован')
  return data
}

async function safeJson(res: Response) {
  try {
    return await res.json()
  } catch {
    return null
  }
}
import { ref } from 'vue'

const TOKEN_KEY = 'va_token'
const EMAIL_KEY = 'va_email'

export const authedEmail = ref<string | null>(localStorage.getItem(EMAIL_KEY))
export const authedToken = ref<string | null>(localStorage.getItem(TOKEN_KEY))

export function syncAuthFromStorage() {
  authedEmail.value = localStorage.getItem(EMAIL_KEY)
  authedToken.value = localStorage.getItem(TOKEN_KEY)
}
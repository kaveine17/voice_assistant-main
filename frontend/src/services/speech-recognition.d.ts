declare global {
  interface SpeechRecognitionAlternative {
    transcript: string
    confidence: number
  }

  interface SpeechRecognitionResult {
    readonly isFinal: boolean
    readonly length: number
    item(index: number): SpeechRecognitionAlternative
    [index: number]: SpeechRecognitionAlternative
  }

  interface SpeechRecognitionResultList {
    readonly length: number
    item(index: number): SpeechRecognitionResult
    [index: number]: SpeechRecognitionResult
  }

  interface SpeechRecognitionEvent extends Event {
    readonly resultIndex: number
    readonly results: SpeechRecognitionResultList
  }

  interface SpeechRecognitionErrorEvent extends Event {
    readonly error:
      | 'aborted'
      | 'audio-capture'
      | 'bad-grammar'
      | 'language-not-supported'
      | 'network'
      | 'no-speech'
      | 'not-allowed'
      | 'service-not-allowed'
    readonly message: string
  }

  interface SpeechRecognition extends EventTarget {
    continuous: boolean
    interimResults: boolean
    lang: string

    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null
    onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null
    onend: ((this: SpeechRecognition, ev: Event) => void) | null

    start(): void
    stop(): void
    abort(): void
  }

  interface Window {
    SpeechRecognition?: {
      new (): SpeechRecognition
    }
    webkitSpeechRecognition?: {
      new (): SpeechRecognition
    }
  }
}

export {}
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Send, Loader2 } from 'lucide-react'
import { api } from '../api/client.ts'

interface Message {
  role: string
  content: string
}

interface Provider {
  name: string
  models: string[]
}

export default function PlaygroundPage() {
  const [provider, setProvider] = useState('openai')
  const [model, setModel] = useState('gpt-4o')
  const [messages, setMessages] = useState<Message[]>([{ role: 'user', content: '' }])
  const [temperature, setTemperature] = useState(0.7)
  const [maxTokens, setMaxTokens] = useState(1024)
  const [stream, setStream] = useState(true)
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState('')
  const [error, setError] = useState('')

  const { data: modelsData } = useQuery({
    queryKey: ['models'],
    queryFn: () => api.playground.models(),
  })

  const providers: Provider[] = modelsData?.providers || []

  function handleProviderChange(p: string) {
    setProvider(p)
    const prov = providers.find((x) => x.name === p)
    if (prov) setModel(prov.models[0])
  }

  async function handleSend() {
    setLoading(true)
    setResponse('')
    setError('')

    const validMessages = messages.filter((m) => m.content.trim())
    if (validMessages.length === 0) {
      setLoading(false)
      return
    }

    try {
      if (stream) {
        const res = await fetch('/api/v1/playground/completion', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            provider,
            model,
            messages: validMessages,
            temperature,
            max_tokens: maxTokens,
            stream: true,
          }),
        })
        const reader = res.body?.getReader()
        const decoder = new TextDecoder()
        if (!reader) return

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const chunk = decoder.decode(value, { stream: true })
          for (const line of chunk.split('\n')) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              if (data === '[DONE]') continue
              try {
                const parsed = JSON.parse(data)
                if (parsed.type === 'token' && parsed.content) {
                  setResponse((prev) => prev + parsed.content)
                }
              } catch {
                // ignore malformed
              }
            }
          }
        }
      } else {
        const data = await api.playground.completion({
          provider,
          model,
          messages: validMessages,
          temperature,
          max_tokens: maxTokens,
          stream: false,
        })
        setResponse(data.choices?.[0]?.message?.content || JSON.stringify(data))
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-4 max-w-5xl">
      <h1 className="text-xl font-semibold text-text">Playground</h1>

      <div className="flex gap-3">
        <select
          value={provider}
          onChange={(e) => handleProviderChange(e.target.value)}
          className="px-3 py-1.5 bg-surface border border-border rounded-md text-sm text-text focus:outline-none focus:border-accent"
        >
          {providers.map((p) => (
            <option key={p.name} value={p.name}>
              {p.name}
            </option>
          ))}
        </select>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="px-3 py-1.5 bg-surface border border-border rounded-md text-sm text-text focus:outline-none focus:border-accent"
        >
          {providers
            .find((p) => p.name === provider)
            ?.models.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
        </select>
      </div>

      <div className="bg-surface border border-border rounded-lg p-4 space-y-3">
        {messages.map((msg, idx) => (
          <div key={idx} className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-text-muted uppercase">{msg.role}</span>
              {messages.length > 1 && (
                <button
                  onClick={() => setMessages((m) => m.filter((_, i) => i !== idx))}
                  className="text-xs text-text-muted hover:text-error"
                >
                  remove
                </button>
              )}
            </div>
            <textarea
              value={msg.content}
              onChange={(e) => {
                const next = [...messages]
                next[idx].content = e.target.value
                setMessages(next)
              }}
              rows={3}
              className="w-full bg-bg border border-border rounded-md p-2.5 text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent resize-none"
              placeholder={`Enter ${msg.role} message...`}
            />
          </div>
        ))}
        <button
          onClick={() => setMessages((m) => [...m, { role: 'user', content: '' }])}
          className="text-xs text-accent hover:text-accent-light"
        >
          + Add message
        </button>
      </div>

      <div className="flex items-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-text-secondary">Temperature</span>
          <input
            type="range"
            min={0}
            max={2}
            step={0.1}
            value={temperature}
            onChange={(e) => setTemperature(Number(e.target.value))}
            className="w-24 accent-accent"
          />
          <span className="text-text-muted w-8">{temperature}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-text-secondary">Max tokens</span>
          <input
            type="number"
            value={maxTokens}
            onChange={(e) => setMaxTokens(Number(e.target.value))}
            className="w-20 px-2 py-1 bg-surface border border-border rounded-md text-text text-sm focus:outline-none focus:border-accent"
          />
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={stream}
            onChange={(e) => setStream(e.target.checked)}
            className="accent-accent"
          />
          <span className="text-text-secondary">Stream</span>
        </label>
        <button
          onClick={handleSend}
          disabled={loading}
          className="ml-auto inline-flex items-center gap-1.5 px-4 py-1.5 bg-accent hover:bg-accent-hover text-white rounded-md text-sm font-medium transition-colors disabled:opacity-50"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          Send
        </button>
      </div>

      {error && (
        <div className="bg-error/5 border border-error/20 rounded-lg p-3 text-sm text-error">{error}</div>
      )}

      {(response || loading) && (
        <div className="bg-surface border border-border rounded-lg p-4 space-y-2">
          <div className="text-xs font-medium text-text-secondary uppercase">Response</div>
          <div className="text-sm text-text whitespace-pre-wrap leading-relaxed">{response}</div>
        </div>
      )}
    </div>
  )
}

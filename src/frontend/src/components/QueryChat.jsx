import { useEffect, useRef, useState } from 'react'
import { postQuery, proofVideoUrl } from '../api/queryApi.js'
import './QueryChat.css'

// If the question already names a date some way the backend understands
// ("2026-07-06", "yesterday", "last 3 days", "today"), leave it alone --
// explicit start/end params would otherwise override that phrase instead
// of complementing it. Only inject a day when there's nothing to go on,
// so a question typed while looking at an older video defaults to that
// video's day instead of "today".
const DATE_PHRASE_RE = /\b\d{4}-\d{2}-\d{2}\b|\byesterday\b|\b(?:last|past)\s+\d+\s+days?\b|\btoday\b/i

function withDateHint(question, dateHint) {
  if (!dateHint || DATE_PHRASE_RE.test(question)) return question
  return `${question} on ${dateHint}`
}

function proofHeading(proof) {
  const segments = proof?.segments || []
  if (!segments.length) return null
  const dayCount = new Set(segments.map((segment) => segment.date)).size
  const clipWord = segments.length === 1 ? 'clip' : 'clips'
  const dayWord = dayCount === 1 ? 'day' : 'days'
  return `${segments.length} ${clipWord} across ${dayCount} ${dayWord}`
}

function segmentCaption(segment) {
  return `${segment.date} · ${segment.clip_start_timestamp}–${segment.clip_end_timestamp}`
}

export default function QueryChat({ dateHint, placeholder }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [includeProof, setIncludeProof] = useState(false)
  const listRef = useRef(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isSending])

  async function handleSubmit(e) {
    e.preventDefault()
    const question = input.trim()
    if (!question || isSending) return

    setMessages((current) => [...current, { role: 'user', text: question }])
    setInput('')
    setIsSending(true)
    try {
      const response = await postQuery(withDateHint(question, dateHint), { includeProof })
      setMessages((current) => [
        ...current,
        { role: 'assistant', text: response.answer, proof: includeProof ? response.proof : null },
      ])
    } catch (err) {
      setMessages((current) => [
        ...current,
        { role: 'assistant', text: err.message, isError: true },
      ])
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="query-chat">
      <div className="query-chat__messages" ref={listRef}>
        {messages.length === 0 && (
          <p className="query-chat__hint">
            Ask about your pets' activity, e.g. "Did my cat play in the last 3 days?"
          </p>
        )}
        {messages.map((message, index) => (
          <div key={index}>
            <div
              className={`query-chat__message query-chat__message--${message.role}${
                message.isError ? ' query-chat__message--error' : ''
              }`}
            >
              {message.text}
            </div>
            {message.proof?.segments?.length > 0 && (
              <div className="query-chat__proof-group">
                <p className="query-chat__proof-heading">{proofHeading(message.proof)}</p>
                {message.proof.segments.map((segment) => (
                  <div className="query-chat__proof" key={segment.segment}>
                    <video
                      className="query-chat__proof-video"
                      src={proofVideoUrl(segment.video_path)}
                      controls
                    />
                    <p className="query-chat__proof-caption">{segmentCaption(segment)}</p>
                  </div>
                ))}
                {message.proof.status === 'partial' && (
                  <p className="query-chat__proof-note">
                    Some matches had no available clip{message.proof.error ? `: ${message.proof.error}` : '.'}
                  </p>
                )}
              </div>
            )}
            {message.proof &&
              !message.proof.segments?.length &&
              message.proof.status !== 'not_requested' && (
                <p className="query-chat__proof-note">
                  Evidence clip unavailable{message.proof.error ? `: ${message.proof.error}` : '.'}
                </p>
              )}
          </div>
        ))}
        {isSending && (
          <div className="query-chat__message query-chat__message--assistant query-chat__message--pending">
            Thinking…
          </div>
        )}
      </div>
      <label className="query-chat__proof-toggle">
        <input
          type="checkbox"
          checked={includeProof}
          onChange={(e) => setIncludeProof(e.target.checked)}
        />
        Include evidence clip with the answer
      </label>
      <form className="query-chat__form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder || 'Ask a question…'}
          disabled={isSending}
        />
        <button className="btn btn--primary" type="submit" disabled={isSending || !input.trim()}>
          Ask
        </button>
      </form>
    </div>
  )
}

import { useState } from 'react'
import QueryCatIcon from './QueryCatIcon.jsx'
import QueryChat from './QueryChat.jsx'
import './QueryWidget.css'

export default function QueryWidget() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="query-widget">
      {isOpen && (
        <div className="query-widget__panel">
          <div className="query-widget__panel-header">
            <span>Ask about your pets</span>
            <button
              className="query-widget__panel-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close"
            >
              &times;
            </button>
          </div>
          <QueryChat />
        </div>
      )}
      <button
        className="query-widget__button"
        onClick={() => setIsOpen((open) => !open)}
        aria-label="Ask about your pet's activity"
        title="Ask about your pet's activity"
      >
        <QueryCatIcon size={40} />
      </button>
    </div>
  )
}

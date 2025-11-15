'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Send } from 'lucide-react'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  showSuggestions?: boolean
}

export default function ChatInput({ onSendMessage, disabled, showSuggestions = true }: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [input])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSendMessage(input)
      setInput('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto px-4 py-6">
      <form onSubmit={handleSubmit} className="relative">
        <div className="flex items-end gap-2 bg-card border border-border rounded-md focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20 transition-all px-4 py-2.5">
          {/* Text Input */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask HACK-RUC Chat..."
            disabled={disabled}
            rows={1}
            className="flex-1 resize-none bg-transparent text-sm focus:outline-none max-h-32 overflow-y-auto placeholder:text-muted-foreground"
            style={{ minHeight: '24px' }}
          />

          {/* Send Button */}
          <Button
            type="submit"
            disabled={!input.trim() || disabled}
            size="icon"
            className="h-8 w-8 flex-shrink-0"
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </form>
      {showSuggestions && (
        <p className="text-xs text-muted-foreground mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      )}
    </div>
  )
}

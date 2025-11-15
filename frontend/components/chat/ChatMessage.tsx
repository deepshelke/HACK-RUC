'use client'

import { Message } from '@/lib/types/chat'
import { format } from 'date-fns'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { User, Sparkles } from 'lucide-react'

interface ChatMessageProps {
  message: Message
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={`flex items-start space-x-3 ${
        isUser ? 'flex-row-reverse space-x-reverse' : ''
      }`}
    >
      <Avatar className="h-8 w-8">
        <AvatarFallback className={isUser ? 'bg-primary text-primary-foreground' : 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'}>
          {isUser ? (
            <User className="h-4 w-4" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
        </AvatarFallback>
      </Avatar>
      <div
        className={`flex-1 max-w-[85%] ${
          isUser ? 'flex flex-col items-end' : ''
        }`}
      >
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-primary text-primary-foreground rounded-tr-sm'
              : 'bg-muted text-foreground rounded-tl-sm'
          }`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
            {message.content}
          </p>
        </div>
        <span className="text-xs text-muted-foreground mt-1 px-1">
          {message.timestamp && !isNaN(new Date(message.timestamp).getTime())
            ? format(new Date(message.timestamp), 'HH:mm')
            : 'Now'}
        </span>
      </div>
    </div>
  )
}


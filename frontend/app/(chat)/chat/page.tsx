'use client'

import { useState, useRef, useEffect } from 'react'
import { useChat } from '@/lib/contexts/ChatContext'
import { useAuth } from '@/lib/contexts/AuthContext'
import ChatMessage from '@/components/chat/ChatMessage'
import ChatInput from '@/components/chat/ChatInput'
import ChatSidebar from '@/components/chat/ChatSidebar'
import ChatSidebarSheet from '@/components/chat/ChatSidebarSheet'
import ChatHeader from '@/components/chat/ChatHeader'
import { Sparkles } from 'lucide-react'

export default function ChatPage() {
  const { currentChat, messages, sendMessage, isSending, createChat, isLoading } = useChat()
  const { user } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!currentChat && !isLoading) {
      createChat().catch(console.error)
    }
  }, [currentChat, isLoading, createChat])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Permanent Sidebar - Desktop */}
      <div className={`hidden md:flex ${sidebarCollapsed ? 'w-16' : 'md:w-64 lg:w-72'} flex-col border-r bg-muted/30 transition-all duration-300`}>
        <ChatSidebar 
          collapsed={sidebarCollapsed} 
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)} 
        />
      </div>

      {/* Mobile Sidebar Sheet */}
      <ChatSidebarSheet open={sidebarOpen} onOpenChange={setSidebarOpen} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <ChatHeader onMenuClick={() => setSidebarOpen(true)} />
        
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full px-4">
              {/* Personalized Greeting */}
              <div className="mb-8 text-center">
                <h1 className="text-4xl font-semibold mb-2 bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
                  Hello, {user?.name?.split(' ')[0] || 'there'}
                </h1>
                <p className="text-muted-foreground text-lg">
                  How can I help you today?
                </p>
              </div>

              {/* Input Field */}
              <div className="w-full max-w-3xl">
                <ChatInput onSendMessage={sendMessage} disabled={isSending} showSuggestions={false} />
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto px-4 py-8">
              <div className="space-y-6">
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}
                {isSending && (
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex space-x-1 pt-2">
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>
          )}
        </div>

        {/* Input at bottom - only show when there are messages */}
        {messages.length > 0 && (
          <div className="border-t bg-background">
            <ChatInput onSendMessage={sendMessage} disabled={isSending} showSuggestions={false} />
          </div>
        )}
      </div>
    </div>
  )
}

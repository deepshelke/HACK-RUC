'use client'

import { useState } from 'react'
import { useChat } from '@/lib/contexts/ChatContext'
import { useAuth } from '@/lib/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { 
  Menu, 
  Plus, 
  Square, 
  Copy, 
  MessageSquare, 
  Trash2, 
  Settings,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'

interface ChatSidebarProps {
  collapsed?: boolean
  onToggleCollapse?: () => void
}

export default function ChatSidebar({ collapsed = false, onToggleCollapse }: ChatSidebarProps) {
  const { chats, currentChat, createChat, selectChat, deleteChat, isLoading } = useChat()
  const { user } = useAuth()
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleCreateChat = async () => {
    try {
      await createChat()
    } catch (error) {
      console.error('Failed to create chat:', error)
    }
  }

  const handleSelectChat = async (chatId: string) => {
    try {
      await selectChat(chatId)
    } catch (error) {
      console.error('Failed to select chat:', error)
    }
  }

  const handleDeleteChat = async (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation()
    if (!confirm('Are you sure you want to delete this chat?')) return

    try {
      setDeletingId(chatId)
      await deleteChat(chatId)
    } catch (error) {
      console.error('Failed to delete chat:', error)
    } finally {
      setDeletingId(null)
    }
  }

  if (collapsed) {
    return (
      <div className="flex flex-col h-full bg-background border-r items-center py-3">
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-9 w-9 mb-2"
          onClick={onToggleCollapse}
        >
          <ChevronRight className="h-5 w-5" />
        </Button>
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-9 w-9 mb-4"
          onClick={handleCreateChat}
        >
          <Plus className="h-5 w-5" />
        </Button>
        <Separator className="mb-4" />
        <ScrollArea className="flex-1 w-full">
          <div className="flex flex-col items-center gap-2 px-2">
            {chats.map((chat) => (
              <Button
                key={chat.id}
                variant={currentChat?.id === chat.id ? "secondary" : "ghost"}
                size="icon"
                className="h-9 w-9"
                onClick={() => handleSelectChat(chat.id)}
                title={chat.title}
              >
                <MessageSquare className="h-4 w-4" />
              </Button>
            ))}
          </div>
        </ScrollArea>
        <Separator className="mb-4" />
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-9 w-9"
          title="Settings and help"
        >
          <Settings className="h-5 w-5" />
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Top Icons */}
      <div className="flex items-center justify-between p-3 border-b">
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-9 w-9"
          onClick={onToggleCollapse}
        >
          <ChevronLeft className="h-5 w-5" />
        </Button>
      </div>

      {/* New Chat Button */}
      <div className="p-3 border-b">
        <Button 
          onClick={handleCreateChat} 
          className="w-full justify-start gap-2 h-10"
          variant="ghost"
        >
          <div className="relative">
            <Square className="h-4 w-4" />
            <Copy className="h-3 w-3 absolute -top-0.5 -right-0.5" />
          </div>
          <span>New chat</span>
        </Button>
      </div>

      {/* Recent Chats */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="p-3 border-b">
          <h2 className="text-xs font-semibold text-muted-foreground px-2">Recent</h2>
        </div>
        <ScrollArea className="flex-1">
          {isLoading && chats.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground text-sm">
              Loading chats...
            </div>
          ) : chats.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No chats yet</p>
            </div>
          ) : (
            <div className="p-2">
              {chats.map((chat) => (
                <div
                  key={chat.id}
                  onClick={() => handleSelectChat(chat.id)}
                  className={`
                    group relative p-2.5 rounded-lg cursor-pointer transition-colors mb-1
                    ${currentChat?.id === chat.id
                      ? 'bg-muted'
                      : 'hover:bg-muted/50'
                    }
                  `}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-sm truncate leading-tight">
                        {chat.title}
                      </h3>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="opacity-0 group-hover:opacity-100 h-6 w-6 flex-shrink-0"
                      onClick={(e) => handleDeleteChat(e, chat.id)}
                      disabled={deletingId === chat.id}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* Settings at Bottom */}
      <div className="border-t p-3">
        <Button 
          variant="ghost" 
          className="w-full justify-start gap-2 h-9 text-sm"
        >
          <Settings className="h-4 w-4" />
          <span>Settings and help</span>
        </Button>
      </div>
    </div>
  )
}

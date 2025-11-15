'use client'

import { Button } from '@/components/ui/button'
import { Menu } from 'lucide-react'
import UserAvatarMenu from './UserAvatarMenu'

interface ChatHeaderProps {
  onMenuClick?: () => void
}

export default function ChatHeader({ onMenuClick }: ChatHeaderProps) {
  return (
    <header className="border-b border-border bg-card px-4 md:px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuClick}
            className="md:hidden"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <h1 className="text-base font-semibold">HACK-RUC Chat</h1>
        </div>
        <div className="flex items-center gap-3">
          <UserAvatarMenu />
        </div>
      </div>
    </header>
  )
}

'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Menu, LogOut, LogIn } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

interface ChatHeaderProps {
  onMenuClick?: () => void
}

export default function ChatHeader({ onMenuClick }: ChatHeaderProps) {
  const router = useRouter()
  const { user, logout, isAuthenticated } = useAuth()

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const handleLogin = () => {
    router.push('/login')
  }

  return (
    <header className="border-b bg-background px-4 md:px-6 py-3">
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
          <h1 className="text-lg font-semibold">HACK-RUC Chat</h1>
        </div>
        <div className="flex items-center gap-3">
          {isAuthenticated && (
            <span className="text-xs font-medium px-2 py-1 rounded bg-primary/10 text-primary">
              PRO
            </span>
          )}
          {isAuthenticated ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-red-500 text-white">
                      {user?.name.charAt(0).toUpperCase() || 'U'}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button variant="outline" size="sm" onClick={handleLogin}>
              <LogIn className="mr-2 h-4 w-4" />
              Sign in
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}

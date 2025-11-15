'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/contexts/AuthContext'
import { useTheme } from '@/lib/contexts/ThemeContext'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { LogOut, LogIn, Moon, Sun, User } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export default function UserAvatarMenu() {
  const router = useRouter()
  const { user, logout, isAuthenticated } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [open, setOpen] = useState(false)

  const handleLogout = async () => {
    try {
      await logout()
      setOpen(false)
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const handleLogin = () => {
    router.push('/login')
    setOpen(false)
  }

  const handleThemeToggle = () => {
    toggleTheme()
  }

  // Get user's nickname or first name
  const nickname = user?.name?.split(' ')[0] || user?.name || 'Guest'

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <div 
        className="relative"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
      >
        <DropdownMenuTrigger asChild>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 rounded-full hover:opacity-80 transition-opacity"
          >
            <Avatar className="h-8 w-8 border border-border">
              <AvatarFallback className="bg-primary text-primary-foreground">
                {isAuthenticated && user?.name
                  ? user.name.charAt(0).toUpperCase()
                  : <User className="h-4 w-4" />}
              </AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent 
          align="end" 
          className="w-56"
        >
          {isAuthenticated && (
            <>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{nickname}</p>
                  {user?.email && (
                    <p className="text-xs leading-none text-muted-foreground">
                      {user.email}
                    </p>
                  )}
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
            </>
          )}
          <DropdownMenuItem onClick={handleThemeToggle}>
            {theme === 'dark' ? (
              <>
                <Sun className="mr-2 h-4 w-4" />
                <span>Light mode</span>
              </>
            ) : (
              <>
                <Moon className="mr-2 h-4 w-4" />
                <span>Dark mode</span>
              </>
            )}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          {isAuthenticated ? (
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              <span>Sign out</span>
            </DropdownMenuItem>
          ) : (
            <DropdownMenuItem onClick={handleLogin}>
              <LogIn className="mr-2 h-4 w-4" />
              <span>Sign in</span>
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </div>
    </DropdownMenu>
  )
}

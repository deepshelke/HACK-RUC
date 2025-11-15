'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { X } from 'lucide-react'

interface AuthPromptProps {
  onClose?: () => void
  message?: string
}

export default function AuthPrompt({ onClose, message }: AuthPromptProps) {
  const router = useRouter()
  const { isAuthenticated } = useAuth()

  if (isAuthenticated) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Sign in required</CardTitle>
            {onClose && (
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
          <CardDescription>
            {message || 'This feature requires authentication. Please sign in to continue.'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col space-y-2">
            <Button onClick={() => router.push('/login')} className="w-full">
              Sign in
            </Button>
            <Button 
              variant="outline" 
              onClick={() => router.push('/signup')} 
              className="w-full"
            >
              Create account
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


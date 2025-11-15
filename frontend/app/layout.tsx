import type { Metadata } from 'next'
import { AuthProvider } from '@/lib/contexts/AuthContext'
import { ChatProvider } from '@/lib/contexts/ChatContext'
import { ThemeProvider } from '@/lib/contexts/ThemeContext'
import './globals.css'

export const metadata: Metadata = {
  title: 'HACK-RUC Chat',
  description: 'Chat interface inspired by Gemini',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" data-theme="caffeine" className="dark">
      <body className="antialiased">
        <ThemeProvider>
          <AuthProvider>
            <ChatProvider>
              {children}
            </ChatProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}

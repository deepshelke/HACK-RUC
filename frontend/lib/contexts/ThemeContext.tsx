'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

export type ThemeName = 'caffeine' | 'neo-brutalism'
export type ThemeMode = 'light' | 'dark'

interface ThemeContextType {
  themeName: ThemeName
  themeMode: ThemeMode
  setTheme: (name: ThemeName, mode: ThemeMode) => void
  toggleMode: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [themeName, setThemeName] = useState<ThemeName>('caffeine')
  const [themeMode, setThemeMode] = useState<ThemeMode>('dark')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Check for saved theme preference or default to caffeine dark
    if (typeof window !== 'undefined') {
      const savedThemeName = localStorage.getItem('themeName') as ThemeName | null
      const savedThemeMode = localStorage.getItem('themeMode') as ThemeMode | null
      
      const name = savedThemeName || 'caffeine'
      const mode = savedThemeMode || 'dark'
      
      setThemeName(name)
      setThemeMode(mode)
      applyTheme(name, mode)
    }
  }, [])

  const applyTheme = (name: ThemeName, mode: ThemeMode) => {
    if (typeof window === 'undefined') return
    const html = document.documentElement
    html.setAttribute('data-theme', name)
    if (mode === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  const setTheme = (name: ThemeName, mode: ThemeMode) => {
    setThemeName(name)
    setThemeMode(mode)
    if (typeof window !== 'undefined') {
      localStorage.setItem('themeName', name)
      localStorage.setItem('themeMode', mode)
    }
    applyTheme(name, mode)
  }

  const toggleMode = () => {
    const newMode = themeMode === 'dark' ? 'light' : 'dark'
    setTheme(themeName, newMode)
  }

  // Always provide the context, even before mounting
  return (
    <ThemeContext.Provider value={{ themeName, themeMode, setTheme, toggleMode }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

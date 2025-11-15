'use client'

import Image from 'next/image'
import { cn } from '@/lib/utils/cn'
import { useState } from 'react'

interface LogoProps {
  className?: string
  width?: number
  height?: number
  showText?: boolean
}

export default function Logo({ className, width = 24, height = 24, showText = false }: LogoProps) {
  const [imageError, setImageError] = useState(false)

  // If image fails to load, show fallback
  if (imageError) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <div 
          className="rounded-md bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm"
          style={{ width, height }}
        >
          F
        </div>
        {showText && (
          <span className="font-semibold text-base">Fairly</span>
        )}
      </div>
    )
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Image
        src="/logo.png"
        alt="Fairly Logo"
        width={width}
        height={height}
        className="object-contain"
        priority
        onError={() => setImageError(true)}
      />
      {showText && (
        <span className="font-semibold text-base">Fairly</span>
      )}
    </div>
  )
}


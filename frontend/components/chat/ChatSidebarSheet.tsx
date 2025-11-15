'use client'

import ChatSidebar from './ChatSidebar'
import { Sheet, SheetContent } from '@/components/ui/sheet'

interface ChatSidebarSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function ChatSidebarSheet({ open, onOpenChange }: ChatSidebarSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange} side="left">
      <SheetContent className="w-64 lg:w-72 p-0">
        <ChatSidebar collapsed={false} onToggleCollapse={() => onOpenChange(false)} />
      </SheetContent>
    </Sheet>
  )
}


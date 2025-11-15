import * as React from "react"
import { cn } from "@/lib/utils/cn"

interface DropdownMenuContextType {
  open: boolean
  setOpen: (open: boolean) => void
}

const DropdownMenuContext = React.createContext<DropdownMenuContextType>({
  open: false,
  setOpen: () => {},
})

const DropdownMenu = ({ 
  children, 
  open: controlledOpen,
  onOpenChange 
}: { 
  children: React.ReactNode
  open?: boolean
  onOpenChange?: (open: boolean) => void
}) => {
  const [internalOpen, setInternalOpen] = React.useState(false)
  const open = controlledOpen !== undefined ? controlledOpen : internalOpen
  const setOpen = (newOpen: boolean) => {
    if (controlledOpen === undefined) {
      setInternalOpen(newOpen)
    }
    onOpenChange?.(newOpen)
  }

  return (
    <DropdownMenuContext.Provider value={{ open, setOpen }}>
      <div className="relative">{children}</div>
    </DropdownMenuContext.Provider>
  )
}

const DropdownMenuTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { asChild?: boolean }
>(({ asChild, children, ...props }, ref) => {
  const { open, setOpen } = React.useContext(DropdownMenuContext)

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, {
      ...props,
      onClick: (e: React.MouseEvent) => {
        setOpen(!open)
        props.onClick?.(e)
      },
    } as any)
  }

  return (
    <button
      ref={ref}
      onClick={() => setOpen(!open)}
      {...props}
    >
      {children}
    </button>
  )
})
DropdownMenuTrigger.displayName = "DropdownMenuTrigger"

const DropdownMenuContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { align?: "start" | "end" }
>(({ className, align = "end", children, ...props }, ref) => {
  const { open, setOpen } = React.useContext(DropdownMenuContext)

  if (!open) return null

  return (
    <>
      <div
        className="fixed inset-0 z-40"
        onClick={() => setOpen(false)}
      />
      <div
        ref={ref}
        className={cn(
          "absolute z-50 min-w-[8rem] overflow-visible rounded-md border bg-popover p-1 text-popover-foreground shadow-md",
          align === "end" ? "right-0 top-full mt-1" : "left-0 top-full mt-1",
          className
        )}
        onClick={(e) => e.stopPropagation()}
        onMouseLeave={(e) => {
          // Don't close if mouse is moving to submenu
          const target = e.relatedTarget as HTMLElement
          if (target?.closest('[data-submenu]')) {
            return
          }
        }}
        {...props}
      >
        {children}
      </div>
    </>
  )
})
DropdownMenuContent.displayName = "DropdownMenuContent"

const DropdownMenuItem = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
  const { setOpen } = React.useContext(DropdownMenuContext)

  return (
    <div
      ref={ref}
      className={cn(
        "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        className
      )}
      onClick={() => setOpen(false)}
      {...props}
    />
  )
})
DropdownMenuItem.displayName = "DropdownMenuItem"

const DropdownMenuLabel = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("px-2 py-1.5 text-sm font-semibold", className)}
    {...props}
  />
))
DropdownMenuLabel.displayName = "DropdownMenuLabel"

const DropdownMenuSeparator = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("-mx-1 my-1 h-px bg-muted", className)}
    {...props}
  />
))
DropdownMenuSeparator.displayName = "DropdownMenuSeparator"

const DropdownMenuSub = ({ children }: { children: React.ReactNode }) => {
  const [subOpen, setSubOpen] = React.useState(false)
  const { open: parentOpen } = React.useContext(DropdownMenuContext)
  
  return (
    <div 
      className="relative"
      onMouseEnter={() => {
        if (parentOpen) {
          setSubOpen(true)
        }
      }}
      onMouseLeave={() => setSubOpen(false)}
    >
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, { subOpen, setSubOpen, parentOpen } as any)
        }
        return child
      })}
    </div>
  )
}

const DropdownMenuSubTrigger = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { subOpen?: boolean; setSubOpen?: (open: boolean) => void; parentOpen?: boolean }
>(({ className, subOpen, setSubOpen, parentOpen, children, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground",
        className
      )}
      onMouseEnter={() => {
        if (parentOpen) {
          setSubOpen?.(true)
        }
      }}
      onClick={(e) => {
        e.stopPropagation()
        if (parentOpen) {
          setSubOpen?.(!subOpen)
        }
      }}
      {...props}
    >
      {children}
      <svg
        className="ml-auto h-4 w-4"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="m9 18 6-6-6-6" />
      </svg>
    </div>
  )
})
DropdownMenuSubTrigger.displayName = "DropdownMenuSubTrigger"

const DropdownMenuSubContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { subOpen?: boolean; setSubOpen?: (open: boolean) => void; align?: "start" | "end" }
>(({ className, subOpen, setSubOpen, align = "end", children, ...props }, ref) => {
  if (!subOpen) return null

  // For right-aligned menus, show submenu on the left side
  const positionClass = align === "end" 
    ? "right-full top-0 mr-1" 
    : "left-full top-0 ml-1"

  return (
    <div
      ref={ref}
      data-submenu
      className={cn(
        "absolute z-[100] min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-lg",
        positionClass,
        className
      )}
      style={{ position: 'absolute' }}
      onMouseEnter={() => setSubOpen?.(true)}
      onMouseLeave={() => setSubOpen?.(false)}
      onClick={(e) => e.stopPropagation()}
      {...props}
    >
      {children}
    </div>
  )
})
DropdownMenuSubContent.displayName = "DropdownMenuSubContent"

export { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuSub, DropdownMenuSubTrigger, DropdownMenuSubContent }


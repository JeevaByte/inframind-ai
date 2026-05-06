"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { LayoutGrid, Upload, FileText, Settings, ChevronDown } from "lucide-react"
import { useState } from "react"
import { cn } from "@/lib/utils"

const navItems = [
  { label: "Overview", href: "/dashboard", icon: LayoutGrid },
  { label: "Upload", href: "/upload", icon: Upload },
  { label: "Results", href: "/dashboard", icon: FileText },
  { label: "Settings", href: "/dashboard", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        "hidden md:flex h-screen flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950 transition-all duration-300",
        isCollapsed ? "w-20" : "w-64"
      )}
    >
      <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-800">
        {!isCollapsed && (
          <span className="font-bold text-slate-900 dark:text-white">
            Dashboard
          </span>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded"
          aria-label="Toggle sidebar"
          aria-expanded={!isCollapsed}
        >
          <ChevronDown className={cn("h-4 w-4 transition-transform", isCollapsed && "rotate-90")} />
        </button>
      </div>

      <nav className="flex-1 space-y-2 p-4">
        {navItems.map(({ label, href, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-4 py-2 rounded-lg transition-colors",
              pathname === href
                ? "bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400"
                : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
            )}
            title={isCollapsed ? label : undefined}
          >
            <Icon className="h-5 w-5 flex-shrink-0" />
            {!isCollapsed && <span className="text-sm font-medium">{label}</span>}
          </Link>
        ))}
      </nav>

      <div className="border-t border-slate-200 dark:border-slate-800 p-4">
        <div className={cn(
          "text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2",
          isCollapsed && "justify-center"
        )}>
          <div className="h-2 w-2 rounded-full bg-green-500" />
          {!isCollapsed && <span>Online</span>}
        </div>
      </div>
    </aside>
  )
}

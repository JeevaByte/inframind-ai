"use client"

import Link from "next/link"
import { Menu, X } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/ui/theme-toggle"

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <nav className="sticky top-0 z-40 border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600">
              <span className="text-sm font-bold text-white">IA</span>
            </div>
            <span className="text-lg font-bold text-slate-900 dark:text-white">
              InfraMind AI
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <Link href="/dashboard" className="text-sm text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
              Dashboard
            </Link>
            <Link href="/upload" className="text-sm text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
              Upload
            </Link>
            <Link href="#features" className="text-sm text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
              Features
            </Link>
          </div>

          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Button className="hidden md:flex">Sign In</Button>
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="md:hidden"
              aria-label="Toggle navigation menu"
              aria-expanded={isOpen}
            >
              {isOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>

        {isOpen && (
          <div className="md:hidden border-t border-slate-200 dark:border-slate-800 py-4 space-y-2">
            <Link href="/dashboard" className="block text-sm text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
              Dashboard
            </Link>
            <Link href="/upload" className="block text-sm text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
              Upload
            </Link>
            <Link href="#features" className="block text-sm text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
              Features
            </Link>
            <Button className="w-full">Sign In</Button>
          </div>
        )}
      </div>
    </nav>
  )
}

"use client"

import Link from "next/link"
import { Menu, X } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/ui/theme-toggle"

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <nav className="sticky top-0 z-40 border-b border-border/80 bg-background/90 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-cyan-400">
              <span className="text-sm font-bold text-white">IL</span>
            </div>
            <span className="text-lg font-bold text-foreground">
              infralint
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <Link href="/dashboard" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              Dashboard
            </Link>
            <Link href="/upload" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              Upload
            </Link>
            <Link href="/#features" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
              Features
            </Link>
          </div>

          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Button asChild variant="ghost" className="hidden md:flex">
              <Link href="/signin">Sign In</Link>
            </Button>
            <Button asChild className="hidden rounded-full md:flex">
              <Link href="/register">Create Account</Link>
            </Button>
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
          <div className="space-y-3 border-t border-border/80 py-4 md:hidden">
            <Link href="/dashboard" className="block text-sm text-muted-foreground transition-colors hover:text-foreground">
              Dashboard
            </Link>
            <Link href="/upload" className="block text-sm text-muted-foreground transition-colors hover:text-foreground">
              Upload
            </Link>
            <Link href="/#features" className="block text-sm text-muted-foreground transition-colors hover:text-foreground">
              Features
            </Link>
            <Button asChild variant="outline" className="w-full">
              <Link href="/signin">Sign In</Link>
            </Button>
            <Button asChild className="w-full">
              <Link href="/register">Create Account</Link>
            </Button>
          </div>
        )}
      </div>
    </nav>
  )
}

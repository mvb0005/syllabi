import type { ReactNode } from 'react'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <span className="text-lg font-semibold tracking-tight">
            📚 Syllabi LMS
          </span>
          <nav className="flex gap-4 text-sm text-muted-foreground">
            <a href="/" className="hover:text-foreground">
              Dashboard
            </a>
            <a href="/courses" className="hover:text-foreground">
              Courses
            </a>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
    </div>
  )
}

import type { ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'

interface AppShellProps {
  children: ReactNode
}

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive
    ? 'text-foreground underline underline-offset-4'
    : 'text-muted-foreground hover:text-foreground'

/**
 * Journal-style running head: site name in small caps on the left,
 * section links on the right, separated from the page by a hairline rule.
 */
export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-foreground/70 bg-background">
        <div className="mx-auto flex max-w-3xl items-baseline justify-between px-4 py-2.5">
          <Link
            to="/"
            className="text-sm tracking-[0.18em] uppercase !text-foreground !no-underline"
          >
            Syllabi · A Journal of Coursework
          </Link>
          <nav className="flex gap-5 text-sm italic">
            <NavLink to="/" end className={navLinkClass}>
              Front matter
            </NavLink>
            <NavLink to="/courses" className={navLinkClass}>
              Courses
            </NavLink>
          </nav>
        </div>
      </header>
      <main>{children}</main>
    </div>
  )
}

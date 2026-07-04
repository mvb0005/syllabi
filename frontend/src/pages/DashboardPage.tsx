import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  getHealth,
  listCourses,
  type CoursePublic,
  type HealthResponse,
} from '@/api/client'

/**
 * The journal's front matter: masthead statement, colophon-style status
 * line, and a pointer to the table of contents.
 */
export function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)
  const [courses, setCourses] = useState<CoursePublic[] | null>(null)

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err: unknown) =>
        setHealthError(err instanceof Error ? err.message : 'Unknown error'),
      )
    listCourses()
      .then(setCourses)
      .catch(() => setCourses(null))
  }, [])

  return (
    <article className="sheet">
      <header className="mb-9 text-center">
        <h1 className="mb-4 text-2xl font-bold leading-tight">Syllabi</h1>
        <p className="text-sm italic">A Journal of Coursework</p>
        <p className="mt-3 text-sm text-muted-foreground">
          AI-generated courses · automated grading pipelines
        </p>
      </header>

      <section className="mx-9 mb-8">
        <p className="mb-1.5 text-center text-sm font-bold">Abstract</p>
        <p className="text-justify text-sm leading-normal">
          Instructors define curricula; the platform generates full course
          materials, starter codebases, and grading pipelines. Deterministic
          test suites grade what can be executed; language-model rubrics grade
          what must be read. Each course is typeset and published here as a
          self-contained scholarly document.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-lg font-bold">
          <span className="mr-4">1</span>In this issue
        </h2>
        {courses && courses.length > 0 ? (
          <ol className="ml-6 list-decimal space-y-1.5">
            {courses.map((course) => (
              <li key={course.id}>
                <Link to={`/courses/${course.id}`}>{course.title}</Link>
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-sm italic text-muted-foreground">
            No courses published yet — see the{' '}
            <Link to="/courses">catalogue</Link> for updates.
          </p>
        )}
      </section>

      <hr className="mx-auto mt-10 w-1/3 border-t border-foreground" />
      <footer className="mt-3 text-center text-sm text-muted-foreground">
        Colophon: backend{' '}
        {health ? (
          <span>reports “{health.status}”</span>
        ) : healthError ? (
          <span>unreachable ({healthError})</span>
        ) : (
          <span>being consulted…</span>
        )}
        . Typeset in the browser with KaTeX.
      </footer>
    </article>
  )
}

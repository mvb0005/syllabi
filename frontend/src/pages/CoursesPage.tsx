import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listCourses, type CoursePublic } from '@/api/client'

/**
 * Course catalogue rendered as a journal's table of contents:
 * each course is an entry with a linked title and a one-paragraph summary.
 */
export function CoursesPage() {
  const [courses, setCourses] = useState<CoursePublic[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listCourses()
      .then(setCourses)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : 'Unknown error'),
      )
  }, [])

  return (
    <article className="sheet">
      <header className="mb-9 text-center">
        <h1 className="text-2xl font-bold leading-tight">Courses</h1>
        <p className="mt-2 text-sm italic text-muted-foreground">
          Table of contents · {courses ? courses.length : '—'} entries
        </p>
      </header>

      {error && (
        <p className="text-center text-sm text-destructive">
          The catalogue could not be retrieved: {error}
        </p>
      )}
      {!error && courses === null && (
        <p className="text-center text-sm italic text-muted-foreground">
          Retrieving the catalogue…
        </p>
      )}
      {courses !== null && courses.length === 0 && (
        <p className="text-center text-sm italic text-muted-foreground">
          The catalogue is empty. Courses appear here once published.
        </p>
      )}

      <ol className="list-none space-y-7 p-0">
        {courses?.map((course, i) => (
          <li key={course.id}>
            <div className="flex items-baseline gap-3">
              <span className="text-sm tabular-nums">{i + 1}.</span>
              <div>
                <Link
                  to={`/courses/${course.id}`}
                  className="font-bold leading-snug"
                >
                  {course.title}
                </Link>
                {!course.is_published && (
                  <span className="ml-2 text-xs uppercase tracking-widest text-muted-foreground">
                    unpublished draft
                  </span>
                )}
                <p className="mt-1 text-justify text-sm leading-relaxed text-foreground/90">
                  {course.description}
                </p>
              </div>
            </div>
          </li>
        ))}
      </ol>
    </article>
  )
}

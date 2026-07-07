import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  getCourse,
  listCourseAssignments,
  listCourseExcerpts,
  listModules,
  type AssignmentPublic,
  type CoursePublic,
  type ModulePublic,
  type SourceExcerptPublic,
  type SourcePublic,
} from '@/api/client'
import { Citation } from '@/components/CourseBlocks'

interface ModuleSection {
  module: ModulePublic
  assignments: AssignmentPublic[]
  excerpts: SourceExcerptPublic[]
}

/**
 * A course's front matter: centered title block, the description as the
 * abstract, a linked table of contents (one page per phase), and the
 * course-wide References section.
 */
export function CoursePage() {
  const { courseId } = useParams<{ courseId: string }>()
  const [course, setCourse] = useState<CoursePublic | null>(null)
  const [sections, setSections] = useState<ModuleSection[] | null>(null)
  const [references, setReferences] = useState<SourcePublic[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!courseId) return
    Promise.all([
      getCourse(courseId),
      listModules(courseId),
      listCourseAssignments(courseId),
      listCourseExcerpts(courseId),
    ])
      .then(([courseData, modules, assignments, excerpts]) => {
        setCourse(courseData)
        setSections(
          modules.map((module) => ({
            module,
            assignments: assignments.filter((a) => a.module_id === module.id),
            excerpts: excerpts.filter((e) => e.module_id === module.id),
          })),
        )
        // Number sources by first appearance across the course.
        const seen = new Map<string, SourcePublic>()
        for (const excerpt of excerpts) {
          if (!seen.has(excerpt.source_id)) {
            seen.set(excerpt.source_id, excerpt.source)
          }
        }
        setReferences([...seen.values()])
      })
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : 'Unknown error'),
      )
  }, [courseId])

  if (error) {
    return (
      <article className="sheet">
        <p className="text-center text-sm text-destructive">
          This course could not be retrieved: {error}
        </p>
        <p className="mt-4 text-center text-sm">
          <Link to="/courses">Return to the catalogue</Link>
        </p>
      </article>
    )
  }

  if (!course || !sections) {
    return (
      <article className="sheet">
        <p className="text-center text-sm italic text-muted-foreground">
          Typesetting…
        </p>
      </article>
    )
  }

  const describe = ({ assignments, excerpts }: ModuleSection) => {
    const parts = [
      assignments.length > 0 &&
        `${assignments.length} exercise${assignments.length > 1 ? 's' : ''}`,
      excerpts.length > 0 &&
        `${excerpts.length} reading${excerpts.length > 1 ? 's' : ''}`,
    ].filter(Boolean)
    return parts.join(', ')
  }

  return (
    <article className="sheet">
      <header className="mb-9 text-center">
        <h1 className="mb-4 text-2xl font-bold leading-tight">
          {course.title}
        </h1>
        {!course.is_published && (
          <p className="text-xs uppercase tracking-widest text-muted-foreground">
            unpublished draft
          </p>
        )}
      </header>

      <section className="mx-9 mb-8">
        <p className="mb-1.5 text-center text-sm font-bold">Abstract</p>
        <p className="text-justify text-sm leading-normal">
          {course.description}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="mb-3 mt-8 text-lg font-bold">Contents</h2>
        <ol className="ml-2 list-none space-y-2 p-0">
          {sections.map((section, i) => (
            <li key={section.module.id} className="flex gap-4">
              <span className="shrink-0 tabular-nums">{i + 1}</span>
              <span>
                <Link to={`/courses/${courseId}/modules/${section.module.id}`}>
                  {section.module.title}
                </Link>
                {describe(section) && (
                  <span className="ml-3 text-sm text-muted-foreground">
                    {describe(section)}
                  </span>
                )}
              </span>
            </li>
          ))}
        </ol>
      </section>

      {references.length > 0 && (
        <section id="references" className="mb-8">
          <h2 className="mb-2 mt-8 text-lg font-bold">References</h2>
          <ol className="ml-6 list-none space-y-1.5 p-0 text-sm">
            {references.map((source, i) => (
              <li key={source.id} className="flex gap-3">
                <span className="shrink-0 tabular-nums">[{i + 1}]</span>
                <span>
                  <Citation source={source} />
                </span>
              </li>
            ))}
          </ol>
        </section>
      )}

      <hr className="mx-auto mt-10 w-1/3 border-t border-foreground" />
      <footer className="mt-3 text-center text-sm text-muted-foreground">
        Typeset in the browser with KaTeX.{' '}
        <Link to="/courses">Return to the catalogue.</Link>
      </footer>
    </article>
  )
}

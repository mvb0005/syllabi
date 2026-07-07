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
import { Citation, ExcerptBlock, ExerciseBlock } from '@/components/CourseBlocks'
import { Markdown } from '@/components/Markdown'

/**
 * One phase of a course on its own page: the distilled lesson first, then
 * its exercises, with the supporting readings and references at the bottom
 * — evidence after the teaching, per the course's content philosophy.
 */
export function ModulePage() {
  const { courseId, moduleId } = useParams<{ courseId: string; moduleId: string }>()
  const [course, setCourse] = useState<CoursePublic | null>(null)
  const [modules, setModules] = useState<ModulePublic[] | null>(null)
  const [assignments, setAssignments] = useState<AssignmentPublic[]>([])
  const [excerpts, setExcerpts] = useState<SourceExcerptPublic[]>([])
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
      .then(([courseData, moduleList, assignmentList, excerptList]) => {
        setCourse(courseData)
        setModules(moduleList)
        setAssignments(assignmentList)
        setExcerpts(excerptList)
        // Number sources by first appearance across the whole course so a
        // citation like [1] means the same thing on every page.
        const seen = new Map<string, SourcePublic>()
        for (const excerpt of excerptList) {
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
          This phase could not be retrieved: {error}
        </p>
        <p className="mt-4 text-center text-sm">
          <Link to={`/courses/${courseId}`}>Return to the course.</Link>
        </p>
      </article>
    )
  }

  if (!course || !modules) {
    return (
      <article className="sheet">
        <p className="text-center text-sm italic text-muted-foreground">
          Typesetting…
        </p>
      </article>
    )
  }

  const index = modules.findIndex((m) => m.id === moduleId)
  const module = index >= 0 ? modules[index] : null
  if (!module) {
    return (
      <article className="sheet">
        <p className="text-center text-sm text-destructive">
          This phase does not exist.{' '}
          <Link to={`/courses/${courseId}`}>Return to the course.</Link>
        </p>
      </article>
    )
  }

  const moduleAssignments = assignments.filter((a) => a.module_id === module.id)
  const moduleExcerpts = excerpts.filter((e) => e.module_id === module.id)
  const refNumberOf = (sourceId: string) =>
    references.findIndex((s) => s.id === sourceId) + 1
  const citedHere = references.filter((s) =>
    moduleExcerpts.some((e) => e.source_id === s.id),
  )
  const prev = index > 0 ? modules[index - 1] : null
  const next = index < modules.length - 1 ? modules[index + 1] : null

  return (
    <article className="sheet">
      <header className="mb-8">
        <p className="mb-3 text-center text-sm text-muted-foreground">
          <Link to={`/courses/${courseId}`}>{course.title}</Link>
        </p>
        <h1 className="text-center text-xl font-bold leading-tight">
          <span className="mr-3">{index + 1}</span>
          {module.title}
        </h1>
      </header>

      <Markdown>{module.content_md}</Markdown>

      {moduleAssignments.map((assignment, exerciseIndex) => (
        <ExerciseBlock
          key={assignment.id}
          assignment={assignment}
          label={`${index + 1}.${exerciseIndex + 1}`}
        />
      ))}

      {moduleExcerpts.length > 0 && (
        <section className="mt-10">
          <h2 className="mb-1 text-lg font-bold">Readings</h2>
          <p className="mb-3 text-sm text-muted-foreground">
            The textbook passages this phase's claims rest on — for going
            deeper, not required in order to proceed.
          </p>
          {moduleExcerpts.map((excerpt) => (
            <ExcerptBlock
              key={excerpt.id}
              excerpt={excerpt}
              refNumber={refNumberOf(excerpt.source_id)}
            />
          ))}
        </section>
      )}

      {citedHere.length > 0 && (
        <section id="references" className="mt-8">
          <h2 className="mb-2 text-lg font-bold">References</h2>
          <ol className="ml-6 list-none space-y-1.5 p-0 text-sm">
            {citedHere.map((source) => (
              <li key={source.id} className="flex gap-3">
                <span className="shrink-0 tabular-nums">
                  [{refNumberOf(source.id)}]
                </span>
                <span>
                  <Citation source={source} />
                </span>
              </li>
            ))}
          </ol>
        </section>
      )}

      <nav className="mt-10 flex justify-between text-sm">
        <span>
          {prev && (
            <Link to={`/courses/${courseId}/modules/${prev.id}`}>
              ‹ {prev.title}
            </Link>
          )}
        </span>
        <span>
          {next && (
            <Link to={`/courses/${courseId}/modules/${next.id}`}>
              {next.title} ›
            </Link>
          )}
        </span>
      </nav>

      <hr className="mx-auto mt-10 w-1/3 border-t border-foreground" />
      <footer className="mt-3 text-center text-sm text-muted-foreground">
        <Link to={`/courses/${courseId}`}>Return to the course overview.</Link>
      </footer>
    </article>
  )
}

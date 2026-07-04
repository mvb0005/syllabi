import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  getCourse,
  listCourseAssignments,
  listModules,
  type AssignmentPublic,
  type CoursePublic,
  type GradingType,
  type ModulePublic,
} from '@/api/client'
import { Markdown } from '@/components/Markdown'

const gradingLabel: Record<GradingType, string> = {
  deterministic: 'graded deterministically by test suite',
  llm_rubric: 'graded against a rubric',
  hybrid: 'graded by test suite and rubric',
}

interface ModuleWithAssignments {
  module: ModulePublic
  assignments: AssignmentPublic[]
}

/**
 * A course rendered as a scholarly paper: centered title block, the course
 * description as the abstract, modules as numbered sections of typeset
 * markdown, and assignments as exercise environments within each section.
 */
export function CoursePage() {
  const { courseId } = useParams<{ courseId: string }>()
  const [course, setCourse] = useState<CoursePublic | null>(null)
  const [sections, setSections] = useState<ModuleWithAssignments[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!courseId) return
    Promise.all([
      getCourse(courseId),
      listModules(courseId),
      listCourseAssignments(courseId),
    ])
      .then(([courseData, modules, assignments]) => {
        setCourse(courseData)
        setSections(
          modules.map((module) => ({
            module,
            assignments: assignments.filter((a) => a.module_id === module.id),
          })),
        )
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

      {sections.map(({ module, assignments }, sectionIndex) => (
        <section key={module.id} className="mb-8">
          <h2 className="mb-2 mt-8 text-lg font-bold">
            <span className="mr-4">{sectionIndex + 1}</span>
            {module.title}
          </h2>
          <Markdown>{module.content_md}</Markdown>

          {assignments.map((assignment, exerciseIndex) => (
            <div key={assignment.id} className="mt-5">
              <p className="mb-1">
                <span className="font-bold">
                  Exercise {sectionIndex + 1}.{exerciseIndex + 1}
                </span>{' '}
                <span className="italic">({assignment.title}).</span>{' '}
                <span className="text-sm text-muted-foreground">
                  {assignment.max_score} points,{' '}
                  {gradingLabel[assignment.grading_type]}.
                </span>
              </p>
              <Markdown>{assignment.description_md}</Markdown>
            </div>
          ))}
        </section>
      ))}

      <hr className="mx-auto mt-10 w-1/3 border-t border-foreground" />
      <footer className="mt-3 text-center text-sm text-muted-foreground">
        Typeset in the browser with KaTeX.{' '}
        <Link to="/courses">Return to the catalogue.</Link>
      </footer>
    </article>
  )
}

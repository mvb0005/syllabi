import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  getCourse,
  listCourseAssignments,
  listCourseExcerpts,
  listModules,
  type AssignmentPublic,
  type CoursePublic,
  type GradingType,
  type ModulePublic,
  type SourceExcerptPublic,
  type SourcePublic,
} from '@/api/client'
import { Markdown } from '@/components/Markdown'

const gradingLabel: Record<GradingType, string> = {
  deterministic: 'graded deterministically by test suite',
  llm_rubric: 'graded against a rubric',
  hybrid: 'graded by test suite and rubric',
}

interface ModuleSection {
  module: ModulePublic
  assignments: AssignmentPublic[]
  excerpts: SourceExcerptPublic[]
}

/** Bibliography entry: "J. G. Proakis and M. Salehi, *Digital Communications*, 5th ed. McGraw-Hill, 2008." */
function Citation({ source }: { source: SourcePublic }) {
  // Normalize a possibly period-terminated edition ("5th ed.") so the
  // sentence break before the publisher never doubles up ("ed..").
  const edition = source.edition.replace(/\.+$/, '')
  const tail = [source.publisher, source.year !== null ? String(source.year) : null]
    .filter(Boolean)
    .join(', ')
  return (
    <>
      {source.authors}, <em>{source.title}</em>
      {edition && `, ${edition}`}.{tail && ` ${tail}.`}
    </>
  )
}

interface ExcerptBlockProps {
  excerpt: SourceExcerptPublic
  refNumber: number
}

/** A cited reading: topic label, optional context, the excerpt, attribution. */
function ExcerptBlock({ excerpt, refNumber }: ExcerptBlockProps) {
  const pages =
    excerpt.page_start === excerpt.page_end
      ? `p. ${excerpt.page_start}`
      : `pp. ${excerpt.page_start}–${excerpt.page_end}`
  return (
    <div className="my-5">
      <p className="mb-1">
        <span className="text-sm font-bold uppercase tracking-widest">
          Reading
        </span>{' '}
        <span className="italic">({excerpt.topic}).</span>{' '}
        <a href="#references" className="text-sm">
          [{refNumber}, {pages}]
        </a>
      </p>
      {excerpt.context_md && <Markdown>{excerpt.context_md}</Markdown>}
      <blockquote className="my-2 border-l border-foreground/60 pl-4 text-[0.94rem] leading-normal">
        <p className="whitespace-pre-wrap text-justify">
          {excerpt.content_text}
        </p>
      </blockquote>
      <p className="text-right text-sm text-muted-foreground">
        — {excerpt.source.authors}, <em>{excerpt.source.title}</em>, {pages}.
      </p>
    </div>
  )
}

/**
 * A course rendered as a scholarly paper: centered title block, the course
 * description as the abstract, modules as numbered sections of typeset
 * markdown with cited source readings, assignments as exercise
 * environments, and a numbered References section for every cited source.
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

  const refNumberOf = (sourceId: string) =>
    references.findIndex((s) => s.id === sourceId) + 1

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

      {sections.map(({ module, assignments, excerpts }, sectionIndex) => (
        <section key={module.id} className="mb-8">
          <h2 className="mb-2 mt-8 text-lg font-bold">
            <span className="mr-4">{sectionIndex + 1}</span>
            {module.title}
          </h2>
          <Markdown>{module.content_md}</Markdown>

          {excerpts.map((excerpt) => (
            <ExcerptBlock
              key={excerpt.id}
              excerpt={excerpt}
              refNumber={refNumberOf(excerpt.source_id)}
            />
          ))}

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

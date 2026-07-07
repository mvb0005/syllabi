import type {
  AssignmentPublic,
  GradingType,
  SourceExcerptPublic,
  SourcePublic,
} from '@/api/client'
import { excerptPdfUrl } from '@/api/client'
import { CodeMilestone } from '@/components/CodeMilestone'
import { Markdown } from '@/components/Markdown'
import { PdfExcerpt } from '@/components/PdfExcerpt'

const gradingLabel: Record<GradingType, string> = {
  deterministic: 'graded deterministically by test suite',
  llm_rubric: 'graded against a rubric',
  hybrid: 'graded by test suite and rubric',
}

/** Bibliography entry: "J. G. Proakis and M. Salehi, *Digital Communications*, 5th ed. McGraw-Hill, 2008." */
export function Citation({ source }: { source: SourcePublic }) {
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
export function ExcerptBlock({ excerpt, refNumber }: ExcerptBlockProps) {
  // Cite the book's own printed page numbers, which is what a reader sees
  // on the page images and what locates the passage in a physical copy.
  const printedStart = excerpt.page_start - excerpt.source.page_offset
  const printedEnd = excerpt.page_end - excerpt.source.page_offset
  const pages =
    printedStart === printedEnd
      ? `p. ${printedStart}`
      : `pp. ${printedStart}–${printedEnd}`
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
      {excerpt.source.kind === 'pdf' ? (
        <figure className="my-2 border-l border-foreground/60 pl-4">
          <PdfExcerpt
            url={excerptPdfUrl(excerpt.id)}
            firstSourcePage={printedStart}
          />
        </figure>
      ) : (
        <blockquote className="my-2 border-l border-foreground/60 pl-4 text-[0.94rem] leading-normal">
          <p className="whitespace-pre-wrap text-justify">
            {excerpt.content_text}
          </p>
        </blockquote>
      )}
      <p className="text-right text-sm text-muted-foreground">
        — {excerpt.source.authors}, <em>{excerpt.source.title}</em>, {pages}.
      </p>
    </div>
  )
}

interface ExerciseBlockProps {
  assignment: AssignmentPublic
  /** Rendered exercise label, e.g. "1.2". */
  label: string
}

/** An exercise environment: header line, typeset brief, optional editor. */
export function ExerciseBlock({ assignment, label }: ExerciseBlockProps) {
  return (
    <div className="mt-5">
      <p className="mb-1">
        <span className="font-bold">Exercise {label}</span>{' '}
        <span className="italic">({assignment.title}).</span>{' '}
        <span className="text-sm text-muted-foreground">
          {assignment.max_score} points, {gradingLabel[assignment.grading_type]}.
        </span>
      </p>
      <Markdown>{assignment.description_md}</Markdown>
      {assignment.starter_code && (
        <CodeMilestone
          starterCode={assignment.starter_code}
          assignmentId={assignment.id}
        />
      )}
    </div>
  )
}

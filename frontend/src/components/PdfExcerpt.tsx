import { useEffect, useRef, useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

interface PdfExcerptProps {
  /** URL of the excerpt's sliced PDF (already scoped to the cited pages). */
  url: string
  /** Source page number of the slice's first page, for true page labels. */
  firstSourcePage: number
}

/**
 * Paged reader for an excerpt's PDF slice, rendered by PDF.js with a text
 * layer (selectable, vector-crisp). One page at a time with prev/next
 * controls, labeled with the source's own page numbers.
 */
export function PdfExcerpt({ url, firstSourcePage }: PdfExcerptProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState<number>()
  const [numPages, setNumPages] = useState<number>()
  const [pageNumber, setPageNumber] = useState(1)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const observer = new ResizeObserver(([entry]) => {
      setWidth(entry.contentRect.width)
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const nav = numPages !== undefined && numPages > 1 && (
    <nav className="flex items-baseline justify-between text-sm text-muted-foreground">
      <button
        type="button"
        onClick={() => setPageNumber((p) => p - 1)}
        disabled={pageNumber <= 1}
        className="cursor-pointer disabled:cursor-default disabled:opacity-30"
      >
        ‹ Previous
      </button>
      <span>
        Page {pageNumber} of {numPages} (p. {firstSourcePage + pageNumber - 1})
      </span>
      <button
        type="button"
        onClick={() => setPageNumber((p) => p + 1)}
        disabled={pageNumber >= numPages}
        className="cursor-pointer disabled:cursor-default disabled:opacity-30"
      >
        Next ›
      </button>
    </nav>
  )

  return (
    <div ref={containerRef}>
      <Document
        file={url}
        onLoadSuccess={({ numPages: n }) => {
          setNumPages(n)
          setPageNumber(1)
        }}
        loading={
          <p className="text-sm text-muted-foreground">Loading reading…</p>
        }
        error={
          <p className="text-sm text-muted-foreground">
            Could not load the reading.{' '}
            <a href={url} className="underline">
              Open the PDF directly.
            </a>
          </p>
        }
      >
        {nav}
        <Page
          pageNumber={pageNumber}
          width={width}
          className="my-2 border border-foreground/20"
        />
        {nav}
      </Document>
    </div>
  )
}

import { isValidElement, type ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import { VISUALS } from '@/components/visuals'

interface MarkdownProps {
  children: string
  className?: string
}

/**
 * remark-math only treats $$…$$ as display math when the fences sit on
 * their own lines; a single-line `$$x$$` falls back to inline math. Promote
 * single-line double-dollar spans to fenced display blocks so equations
 * center and render in display style, as authors expect.
 */
function promoteDisplayMath(source: string): string {
  return source.replace(/\$\$([^$]+)\$\$/g, (_m, tex: string) => `\n\n$$\n${tex}\n$$\n\n`)
}

/**
 * Typeset markdown: GitHub-flavored markdown with TeX math ($…$ / $$…$$)
 * rendered by KaTeX, styled by the `.prose-paper` rules in index.css.
 */
export function Markdown({ children, className }: MarkdownProps) {
  return (
    <div className={className ? `prose-paper ${className}` : 'prose-paper'}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          // ```visual fenced blocks embed a registered interactive
          // component. Intercept at the <pre> wrapper so the visual is not
          // boxed in code-listing styling (mono font, gray band,
          // non-wrapping white-space that clips its labels). Anything
          // unrecognized falls through as a plain listing.
          pre(props) {
            const { children, ...rest } = props
            const child = isValidElement<{ className?: string; children?: ReactNode }>(
              children,
            )
              ? children
              : null
            if (child && /language-visual/.test(child.props.className ?? '')) {
              try {
                const spec = JSON.parse(String(child.props.children)) as { name: string }
                const Visual = VISUALS[spec.name]
                if (Visual) return <Visual />
              } catch {
                // fall through to plain rendering
              }
            }
            return <pre {...rest}>{children}</pre>
          },
        }}
      >
        {promoteDisplayMath(children)}
      </ReactMarkdown>
    </div>
  )
}

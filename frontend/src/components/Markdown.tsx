import ReactMarkdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'

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
      >
        {promoteDisplayMath(children)}
      </ReactMarkdown>
    </div>
  )
}

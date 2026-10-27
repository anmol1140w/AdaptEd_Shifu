import type { ReactNode } from 'react'

function formatMath(source: string) {
  const subscriptDigits: Record<string, string> = { '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉', '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎' }
  const superscriptDigits: Record<string, string> = { '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '+': '⁺', '-': '⁻', '(': '⁽', ')': '⁾' }
  const toUnicode = (value: string, mapping: Record<string, string>) => [...value].map((char) => mapping[char] ?? char).join('')

  return source
    .replace(/\\\\/g, '\\')
    .replace(/\\(?:text|mathrm|operatorname)\{([^{}]*)\}/g, '$1')
    .replace(/\\(?:dfrac|tfrac|frac)\{([^{}]*)\}\{([^{}]*)\}/g, '($1) / ($2)')
    .replace(/\\(?:left|right)\s*/g, '')
    .replace(/\\(?:,|;|:|!|quad|qquad)\s*/g, ' ')
    .replace(/\\Delta\b/g, 'Δ').replace(/\\delta\b/g, 'δ')
    .replace(/\\sigma\b/g, 'σ').replace(/\\theta\b/g, 'θ').replace(/\\pi\b/g, 'π')
    .replace(/\\mu\b/g, 'μ').replace(/\\rho\b/g, 'ρ').replace(/\\omega\b/g, 'ω')
    .replace(/\\times\b/g, '×').replace(/\\cdot\b/g, '·').replace(/\\pm\b/g, '±')
    .replace(/\\approx\b/g, '≈').replace(/\\neq\b/g, '≠').replace(/\\leq\b/g, '≤').replace(/\\geq\b/g, '≥')
    .replace(/\\infty\b/g, '∞').replace(/\\perp\b/g, '⊥').replace(/\\parallel\b/g, '∥')
    .replace(/_\{([^{}]+)\}/g, (_, value: string) => toUnicode(value, subscriptDigits))
    .replace(/\^\{([^{}]+)\}/g, (_, value: string) => toUnicode(value, superscriptDigits))
    .replace(/\^([0-9+-])/g, (_, value: string) => toUnicode(value, superscriptDigits))
    .replace(/\\/g, '')
    .replace(/[{}]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function inlineContent(text: string, keyPrefix: string): ReactNode[] {
  const tokens = text.split(/(\*\*[^*]+\*\*|\$[^$\n]+\$)/g).filter(Boolean)
  return tokens.map((token, index) => {
    const key = `${keyPrefix}-${index}`
    if (token.startsWith('**') && token.endsWith('**')) return <strong key={key}>{token.slice(2, -2)}</strong>
    if (token.startsWith('$') && token.endsWith('$')) return <span className="tutor-inline-formula" key={key}>{formatMath(token.slice(1, -1))}</span>
    return token
  })
}

function proseBlocks(text: string, keyPrefix: string) {
  const paragraphs = text.split(/\n\s*\n/).map((paragraph) => paragraph.trim()).filter(Boolean)
  return paragraphs.map((paragraph, paragraphIndex) => {
    const markers = [...paragraph.matchAll(/(?:^|\s)(\d+)\.\s+/g)]
    if (markers.length < 2) {
      return <p className="tutor-response-paragraph" key={`${keyPrefix}-p-${paragraphIndex}`}>{inlineContent(paragraph, `${keyPrefix}-${paragraphIndex}`)}</p>
    }

    const first = markers[0]
    const listStart = (first.index ?? 0) + first[0].length - first[1].length - 2
    const intro = paragraph.slice(0, Math.max(0, listStart)).trim()
    const items = markers.map((marker, index) => {
      const start = (marker.index ?? 0) + marker[0].length
      const end = index + 1 < markers.length ? markers[index + 1].index ?? paragraph.length : paragraph.length
      return paragraph.slice(start, end).trim()
    })
    return <div className="tutor-response-list-block" key={`${keyPrefix}-list-${paragraphIndex}`}>
      {intro && <p className="tutor-response-paragraph">{inlineContent(intro, `${keyPrefix}-intro-${paragraphIndex}`)}</p>}
      <ol>{items.map((item, itemIndex) => <li key={`${keyPrefix}-li-${itemIndex}`}>{inlineContent(item, `${keyPrefix}-item-${paragraphIndex}-${itemIndex}`)}</li>)}</ol>
    </div>
  })
}

export function TutorAnswerText({ text }: { text: string }) {
  const normalized = text.replace(/\\\(/g, '$').replace(/\\\)/g, '$')
  const blocks = normalized.split(/(\$\$[\s\S]*?\$\$)/g).filter(Boolean)
  return <div className="tutor-response-text">{blocks.map((block, index) => {
    if (block.startsWith('$$') && block.endsWith('$$')) {
      return <div className="tutor-display-formula" key={`formula-${index}`}>{formatMath(block.slice(2, -2))}</div>
    }
    return proseBlocks(block, `response-${index}`)
  })}</div>
}

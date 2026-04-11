// frontend/src/utils/markdown-renderer.ts
import DOMPurify from 'dompurify'

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function highlightCode(code: string, language: string): string {
  if (!language || language === 'text') return escapeHtml(code)

  const keywords: Record<string, string[]> = {
    javascript: ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return', 'class', 'import', 'export', 'try', 'catch', 'finally'],
    typescript: ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return', 'class', 'interface', 'type', 'import', 'export'],
    python: ['def', 'class', 'if', 'else', 'for', 'while', 'import', 'from', 'return', 'True', 'False', 'None', 'try', 'except'],
    java: ['public', 'class', 'static', 'void', 'main', 'String', 'int', 'boolean', 'if', 'else', 'for', 'while', 'return'],
    html: ['<!DOCTYPE', '<html', '<head', '<body', '<div', '<span', '<p', '<h1', '<h2', '<a', '<img'],
    css: ['.', '#', '{', '}', ':', ';', 'color', 'background', 'margin', 'padding', 'font'],
  }

  let highlighted = escapeHtml(code)
  const langKeywords = keywords[language] || keywords.javascript
  if (langKeywords) {
    langKeywords.forEach(keyword => {
      const regex = new RegExp(`\\b(${keyword})\\b`, 'g')
      highlighted = highlighted.replace(regex, '<span class="hljs-keyword">$1</span>')
    })
  }
  highlighted = highlighted.replace(/(["'])(.*?)\1/g, '<span class="hljs-string">$1$2$1</span>')
  if (['javascript', 'typescript', 'python', 'java'].includes(language)) {
    highlighted = highlighted.replace(/\/\/.*$/gm, '<span class="hljs-comment">$&</span>')
    highlighted = highlighted.replace(/\/\*[\s\S]*?\*\//g, '<span class="hljs-comment">$&</span>')
  }
  return highlighted
}

function fixTitleSpacing(markdown: string): string {
  if (!markdown) return markdown
  return markdown.replace(/^(#{1,6}\s+.*?)(\n{2,})/gm, (_, title) => title + '\n')
}

function fixListNumbering(markdown: string): string {
  if (!markdown) return markdown
  const lines = markdown.split('\n')
  const result: string[] = []
  let inOrderedList = false
  let currentNumber = 1
  let tempList: string[] = []

  for (const line of lines) {
    const orderedMatch = line.match(/^(\s*)(\d+)\.\s+(.*)/)
    if (orderedMatch) {
      const [, indent, , content] = orderedMatch
      if (!inOrderedList) {
        inOrderedList = true
        currentNumber = 1
      }
      tempList.push(`${indent}${currentNumber}. ${content}`)
      currentNumber++
    } else {
      if (inOrderedList) {
        result.push(...tempList)
        tempList = []
        inOrderedList = false
      }
      result.push(line)
    }
  }
  if (inOrderedList) result.push(...tempList)
  return result.join('\n')
}

function parseTable(lines: string[], startIdx: number): { html: string; endIdx: number } | null {
  if (startIdx + 2 >= lines.length) return null
  const headerLine = lines[startIdx]?.trim()
  const separatorLine = lines[startIdx + 1]?.trim()
  if (!headerLine || !separatorLine) return null
  if (!/^\|?[\s:-]+\|[\s|:-]+\|?$/.test(separatorLine)) return null

  const parseRow = (line: string): string[] => {
    const trimmed = line.replace(/^\|/, '').replace(/\|$/, '')
    return trimmed.split('|').map(cell => cell.trim())
  }

  const headers = parseRow(headerLine)
  if (headers.length === 0) return null

  const aligns: ('left' | 'center' | 'right' | null)[] = []
  const sepCells = parseRow(separatorLine)
  for (let i = 0; i < headers.length; i++) {
    const cell = sepCells[i] || ''
    if (cell.startsWith(':') && cell.endsWith(':')) aligns.push('center')
    else if (cell.endsWith(':')) aligns.push('right')
    else if (cell.startsWith(':')) aligns.push('left')
    else aligns.push(null)
  }

  const rows: string[][] = []
  let idx = startIdx + 2
  while (idx < lines.length) {
    const line = lines[idx]?.trim()
    if (!line || !line.includes('|')) break
    if (/^\|?[\s:-]+\|[\s|:-]+\|?$/.test(line)) break
    rows.push(parseRow(line))
    idx++
  }

  let html = '<div class="markdown-table-wrapper"><table><thead>\n<tr>\n'
  headers.forEach((header, i) => {
    const align = aligns[i] ? ` align="${aligns[i]}"` : ''
    html += `<th${align}>${escapeHtml(header)}</th>\n`
  })
  html += '</tr>\n</thead><tbody>\n'
  rows.forEach(row => {
    html += '<tr>\n'
    headers.forEach((_, i) => {
      const cell = row[i] || ''
      const align = aligns[i] ? ` align="${aligns[i]}"` : ''
      html += `<td${align}>${escapeHtml(cell)}</td>\n`
    })
    html += '</tr>\n'
  })
  html += '</tbody></table></div>\n'
  return { html, endIdx: idx - 1 }
}

function processBlockquotes(markdown: string): string {
  const lines = markdown.split('\n')
  const result: string[] = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i] || ''
    if (line.startsWith('>')) {
      let quoteContent = ''
      while (i < lines.length && (lines[i] || '').startsWith('>')) {
        const content = (lines[i] || '').replace(/^>\s?/, '')
        quoteContent += (quoteContent ? '\n' : '') + content
        i++
      }
      result.push(`<blockquote>${quoteContent.replace(/\n/g, '<br>')}</blockquote>`)
    } else {
      result.push(line)
      i++
    }
  }
  return result.join('\n')
}

function markdownToHtml(markdown: string): string {
  if (!markdown) return ''

  let processed = fixTitleSpacing(markdown)
  processed = fixListNumbering(processed)

  // 存储代码块 HTML，占位符使用特殊不可见字符（不会出现在普通文本中）
  const codeBlocks: string[] = []
  // 先提取所有代码块，并用占位符替换
  processed = processed.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    const language = lang || 'text'
    const highlighted = highlightCode(code, language)
    const html = `<div class="markdown-code-block">
      <div class="code-header">
        <span class="code-language">${escapeHtml(language)}</span>
        <button class="copy-code-btn" data-code="${encodeURIComponent(code)}">复制</button>
      </div>
      <pre><code class="hljs language-${escapeHtml(language)}">${highlighted}</code></pre>
    </div>`
    const placeholder = `\x00CODE_BLOCK_${codeBlocks.length}\x00` // 使用空字符占位
    codeBlocks.push(html)
    return `\n${placeholder}\n`
  })

  // 处理多行引用
  processed = processBlockquotes(processed)

  // 处理表格
  const lines = processed.split('\n')
  const newLines: string[] = []
  let idx = 0
  while (idx < lines.length) {
    const tableResult = parseTable(lines, idx)
    if (tableResult) {
      newLines.push(tableResult.html)
      idx = tableResult.endIdx + 1
    } else {
      newLines.push(lines[idx] || '')
      idx++
    }
  }
  processed = newLines.join('\n')

  // 行内代码
  processed = processed.replace(/`([^`]+)`/g, (_, code) => `<code class="markdown-inline-code">${escapeHtml(code)}</code>`)

  // 标题
  processed = processed
    .replace(/^###### (.*)$/gm, '<h6>$1</h6>')
    .replace(/^##### (.*)$/gm, '<h5>$1</h5>')
    .replace(/^#### (.*)$/gm, '<h4>$1</h4>')
    .replace(/^### (.*)$/gm, '<h3>$1</h3>')
    .replace(/^## (.*)$/gm, '<h2>$1</h2>')
    .replace(/^# (.*)$/gm, '<h1>$1</h1>')

  // 粗体/斜体/删除线
  processed = processed.replace(/\*\*(.*?)\*\*/g, (_, content) => `<strong>${escapeHtml(content)}</strong>`)
  processed = processed.replace(/__(.*?)__/g, (_, content) => `<strong>${escapeHtml(content)}</strong>`)
  processed = processed.replace(/\*(.*?)\*/g, (_, content) => `<em>${escapeHtml(content)}</em>`)
  processed = processed.replace(/_(.*?)_/g, (_, content) => `<em>${escapeHtml(content)}</em>`)
  processed = processed.replace(/~~(.*?)~~/g, (_, content) => `<del>${escapeHtml(content)}</del>`)

  // 链接与图片
  processed = processed.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, text, url) => {
    return `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(text)}</a>`
  })
  processed = processed.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, alt, src) => {
    return `<img src="${escapeHtml(src)}" alt="${escapeHtml(alt)}" />`
  })

  // 水平线
  processed = processed.replace(/^\s*(---|\*\*\*|___)\s*$/gm, '<hr>')

  // 列表处理
  const listLines = processed.split('\n')
  const listResult: string[] = []
  let inList = false
  let listType: 'ul' | 'ol' | null = null

  for (const line of listLines) {
    const orderedMatch = line.match(/^(\s*)(\d+)\.\s+(.*)/)
    const unorderedMatch = line.match(/^(\s*)([-*+])\s+(.*)/)

    if (orderedMatch) {
      const content = orderedMatch[3] || ''
      if (!inList) {
        if (listResult.length && listResult[listResult.length - 1] !== '') listResult.push('')
        listResult.push('<ol>')
        inList = true
        listType = 'ol'
      }
      listResult.push(`<li>${content}</li>`)
    } else if (unorderedMatch) {
      const content = unorderedMatch[3] || ''
      if (!inList) {
        if (listResult.length && listResult[listResult.length - 1] !== '') listResult.push('')
        listResult.push('<ul>')
        inList = true
        listType = 'ul'
      }
      listResult.push(`<li>${content}</li>`)
    } else {
      if (inList) {
        listResult.push(listType === 'ol' ? '</ol>' : '</ul>')
        inList = false
        listType = null
      }
      listResult.push(line)
    }
  }
  if (inList) {
    listResult.push(listType === 'ol' ? '</ol>' : '</ul>')
  }
  processed = listResult.join('\n')

  // 段落包裹：按空行分割，跳过包含占位符的块和已是块级元素的块
  const blocks = processed.split(/\n{2,}/)
  const wrappedBlocks = blocks.map(block => {
    const trimmed = block.trim()
    if (!trimmed) return ''
    // 如果块包含占位符（不可见字符），直接返回原块（保留占位符）
    if (trimmed.includes('\x00CODE_BLOCK_')) return trimmed
    // 如果块以块级 HTML 标签开头，不包裹
    if (/^<\/?(h\d|ul|ol|li|blockquote|pre|table|thead|tbody|tr|th|td|hr|div|p)/i.test(trimmed)) return trimmed
    // 否则包裹 <p>
    return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`
  })
  processed = wrappedBlocks.join('\n\n')

  // 最后替换占位符为真正的代码块 HTML
  for (let i = 0; i < codeBlocks.length; i++) {
    const placeholder = `\x00CODE_BLOCK_${i}\x00`
    // 使用 split + join 确保替换所有出现
    processed = processed.split(placeholder).join(codeBlocks[i] ?? '')
  }

  return processed
}

/**
 * 将 Markdown 转换为 HTML，代码块直接输出，不使用占位符
 */
export function renderMarkdown(markdown: string): string {
  if (!markdown) return ''

  try {
    // 1. 预处理：修复标题间距和列表编号
    let processed = fixTitleSpacing(markdown)
    processed = fixListNumbering(processed)

    // 2. 按行处理，构建 HTML 片段数组
    const lines = processed.split('\n')
    const result: string[] = []
    let i = 0
    const totalLines = lines.length

    while (i < totalLines) {
      const line = lines[i] || ''

      // 2.1 代码块检测
      if (line.startsWith('```')) {
        const lang = line.slice(3).trim()
        let codeContent = ''
        i++ // 跳过开始标记
        while (i < totalLines && !(lines[i] || '').startsWith('```')) {
          codeContent += (codeContent ? '\n' : '') + (lines[i] || '')
          i++
        }
        i++ // 跳过结束标记
        const highlighted = highlightCode(codeContent, lang)
        const codeHtml = `<div class="markdown-code-block">
          <div class="code-header">
            <span class="code-language">${escapeHtml(lang || 'text')}</span>
            <button class="copy-code-btn" data-code="${encodeURIComponent(codeContent)}">复制</button>
          </div>
          <pre><code class="hljs language-${escapeHtml(lang || 'text')}">${highlighted}</code></pre>
        </div>`
        result.push(codeHtml)
        continue
      }

      // 2.2 表格检测（多行）
      const tableResult = parseTable(lines, i)
      if (tableResult) {
        result.push(tableResult.html)
        i = tableResult.endIdx + 1
        continue
      }

      // 2.3 引用块（多行）
      if (line.startsWith('>')) {
        const quoteLines: string[] = []
        while (i < totalLines && (lines[i] || '').startsWith('>')) {
          quoteLines.push((lines[i] || '').replace(/^>\s?/, ''))
          i++
        }
        const quoteHtml = `<blockquote>${quoteLines.join('<br>')}</blockquote>`
        result.push(quoteHtml)
        continue
      }

      // 2.4 标题
      const headerMatch = line.match(/^(#{1,6})\s+(.*)/)
      if (headerMatch) {
        const level = headerMatch[1]!.length
        const content = headerMatch[2] ?? ''
        result.push(`<h${level}>${escapeHtml(content)}</h${level}>`)
        i++
        continue
      }

      // 2.5 水平线
      if (/^\s*(---|\*\*\*|___)\s*$/.test(line)) {
        result.push('<hr>')
        i++
        continue
      }

      // 2.6 列表（有序/无序）
      const orderedMatch = line.match(/^(\s*)(\d+)\.\s+(.*)/)
      const unorderedMatch = line.match(/^(\s*)([-*+])\s+(.*)/)
      if (orderedMatch || unorderedMatch) {
        const listItems: string[] = []
        const listType: 'ol' | 'ul' = orderedMatch ? 'ol' : 'ul'
        const indentLevel = 0
        while (i < totalLines) {
          const currentLine = lines[i] || ''
          const currOrdered = currentLine.match(/^(\s*)(\d+)\.\s+(.*)/)
          const currUnordered = currentLine.match(/^(\s*)([-*+])\s+(.*)/)
          if ((listType === 'ol' && currOrdered) || (listType === 'ul' && currUnordered)) {
            const content = (listType === 'ol' ? currOrdered![3] : currUnordered![3]) || ''
            listItems.push(`<li>${escapeHtml(content)}</li>`)
            i++
          } else {
            break
          }
        }
        result.push(`<${listType}>${listItems.join('')}</${listType}>`)
        continue
      }

      // 2.7 普通段落（可能是空行分隔的连续文本）
      // 收集直到下一个空行或块级元素
      const paragraphLines: string[] = []
      while (i < totalLines) {
        const cur = lines[i] || ''
        // 遇到空行或块级标记则停止
        if (cur.trim() === '' || cur.startsWith('#') || cur.startsWith('```') || cur.startsWith('>') || cur.match(/^\s*(\d+\.|[-*+])\s+/)) {
          break
        }
        paragraphLines.push(cur)
        i++
      }
      if (paragraphLines.length > 0) {
        const paraText = paragraphLines.join(' ')
        // 内联样式处理：粗体、斜体、行内代码、链接等
        let inlineHtml = escapeHtml(paraText)
        inlineHtml = inlineHtml.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        inlineHtml = inlineHtml.replace(/__(.*?)__/g, '<strong>$1</strong>')
        inlineHtml = inlineHtml.replace(/\*(.*?)\*/g, '<em>$1</em>')
        inlineHtml = inlineHtml.replace(/_(.*?)_/g, '<em>$1</em>')
        inlineHtml = inlineHtml.replace(/~~(.*?)~~/g, '<del>$1</del>')
        inlineHtml = inlineHtml.replace(/`([^`]+)`/g, '<code class="markdown-inline-code">$1</code>')
        inlineHtml = inlineHtml.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
        inlineHtml = inlineHtml.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">')
        result.push(`<p>${inlineHtml}</p>`)
        continue
      }

      // 其他情况（空行等）直接跳过
      i++
    }

    const rawHtml = result.join('\n')
    // XSS 净化
    const cleanHtml = DOMPurify.sanitize(rawHtml, {
      ALLOWED_TAGS: [
        'h1','h2','h3','h4','h5','h6','p','br','hr','strong','em','u','del',
        'blockquote','code','pre','ul','ol','li','table','thead','tbody','tr','th','td',
        'a','img','div','span','button'
      ],
      ALLOWED_ATTR: ['class','href','target','src','alt','title','data-code','rel','align']
    })
    return cleanHtml
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    return escapeHtml(markdown)
  }
}

export function initCodeCopyButtons(container: HTMLElement | Document = document): void {
  const buttons = container.querySelectorAll('.copy-code-btn')
  buttons.forEach(button => {
    const newButton = button.cloneNode(true) as HTMLElement
    button.parentNode?.replaceChild(newButton, button)

    newButton.addEventListener('click', async (e) => {
      e.preventDefault()
      e.stopPropagation()
      const target = e.currentTarget as HTMLElement
      const encoded = target.getAttribute('data-code')
      if (!encoded) return
      let code: string
      try {
        code = decodeURIComponent(encoded)
      } catch {
        console.error('解码失败')
        return
      }
      try {
        await navigator.clipboard.writeText(code)
        const originalText = target.textContent || '复制'
        target.textContent = '已复制!'
        target.classList.add('copied')
        setTimeout(() => {
          target.textContent = originalText
          target.classList.remove('copied')
        }, 2000)
      } catch (err) {
        console.error('复制失败:', err)
        const originalText = target.textContent || '复制'
        target.textContent = '复制失败'
        target.classList.add('error')
        setTimeout(() => {
          target.textContent = originalText
          target.classList.remove('error')
        }, 2000)
      }
    })
  })
}

export function renderStreamingMarkdown(partialMarkdown: string): string {
  if (!partialMarkdown) return ''
  try {
    const delimiters = (partialMarkdown.match(/```/g) || []).length
    if (delimiters % 2 !== 0) {
      const lastIndex = partialMarkdown.lastIndexOf('```')
      if (lastIndex !== -1) {
        const before = partialMarkdown.substring(0, lastIndex)
        const after = partialMarkdown.substring(lastIndex)
        const escapedAfter = after.replace(/</g, '&lt;').replace(/>/g, '&gt;')
        return renderMarkdown(before) + escapedAfter
      }
    }
    return renderMarkdown(partialMarkdown)
  } catch (error) {
    console.warn('流式渲染失败', error)
    return escapeHtml(partialMarkdown)
  }
}
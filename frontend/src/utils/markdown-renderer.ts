// frontend/src/utils/markdown-renderer.ts
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

// ============================================
// 创建和配置 markdown-it 实例
// ============================================

// 创建 markdown-it 实例，针对紧凑显示进行优化
const md = new MarkdownIt({
  html: false,         // 禁止 HTML 标签
  xhtmlOut: false,     // 不使用 XHTML
  breaks: false,       // 关闭：不将 \n 自动转换为 <br> - 这是导致多余换行的原因！
  langPrefix: 'language-',
  linkify: true,       // 自动链接
  typographer: false,  // 关闭排版替换
  quotes: '""\'\'',
})

// 自定义段落渲染，实现更紧凑的布局
md.renderer.rules.paragraph_open = () => '<p>'
md.renderer.rules.paragraph_close = () => '</p>'

// 自定义代码块渲染
md.renderer.rules.fence = function(tokens, idx, options, env, self) {
  const token = tokens[idx]
  if (!token) return ''
  
  const info = token.info ? md.utils.unescapeAll(token.info).trim() : ''
  const lang = info.split(/\s+/g)[0] || ''
  const code = token.content
  
  // 使用 highlight.js 进行代码高亮
  let highlighted = code
  if (lang && hljs.getLanguage(lang)) {
    try {
      highlighted = hljs.highlight(code, { language: lang }).value
    } catch (err) {
      console.warn('代码高亮失败:', err)
      highlighted = md.utils.escapeHtml(code)
    }
  } else {
    highlighted = md.utils.escapeHtml(code)
  }
  
  return `
    <div class="markdown-code-block">
      <div class="code-header">
        <span class="code-language">${md.utils.escapeHtml(lang || 'text')}</span>
        <button class="copy-code-btn" data-code="${encodeURIComponent(code)}">复制</button>
      </div>
      <pre><code class="hljs language-${md.utils.escapeHtml(lang || 'text')}">${highlighted}</code></pre>
    </div>
  `
}

// 自定义列表项渲染，移除额外间距
md.renderer.rules.list_item_open = () => '<li>'
md.renderer.rules.list_item_close = () => '</li>'

// 自定义标题渲染
md.renderer.rules.heading_open = (tokens, idx) => {
  const token = tokens[idx]
  if (!token) return ''
  return `<h${token.markup.length}>`
}
md.renderer.rules.heading_close = (tokens, idx) => {
  const token = tokens[idx]
  if (!token) return ''
  return `</h${token.markup.length}>`
}

// ============================================
// 紧凑渲染函数
// ============================================

export function renderMarkdown(markdown: string): string {
  if (!markdown) return ''
  
  try {
    // 预处理：清理多余的空行
    const cleanedMarkdown = markdown
      .replace(/\n{3,}/g, '\n\n')  // 将3个以上空行替换为2个
      .trim()
    
    // 使用 markdown-it 渲染
    const html = md.render(cleanedMarkdown)
    
    // 后处理：移除多余的换行和空格
    const compactHtml = html
      .replace(/\n\s*\n/g, '\n')  // 移除连续的空行
      .replace(/>\s+</g, '><')    // 移除标签间的多余空格
      .trim()
    
    // 使用 DOMPurify 进行安全过滤
    const cleanHtml = DOMPurify.sanitize(compactHtml, {
      ALLOWED_TAGS: [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
        'p', 'br', 'hr', 
        'strong', 'b', 'em', 'i', 'u', 'del', 's', 'strike',
        'blockquote', 
        'code', 'pre', 
        'ul', 'ol', 'li', 
        'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
        'a', 'img', 
        'div', 'span', 'button'
      ],
      ALLOWED_ATTR: [
        'class', 'href', 'target', 'src', 'alt', 'title', 
        'data-code', 'rel', 'align', 'width', 'height', 'colspan', 'rowspan'
      ],
      ADD_ATTR: ['target', 'rel']
    })
    
    return cleanHtml
    
  } catch (error) {
    console.error('Markdown 渲染失败:', error)
    return escapeHtml(markdown)
  }
}

// 流式渲染版本，保持紧凑
export function renderStreamingMarkdown(partialMarkdown: string): string {
  if (!partialMarkdown) return ''
  
  try {
    // 检查是否有未闭合的代码块
    const codeBlockDelimiters = (partialMarkdown.match(/```/g) || []).length
    
    if (codeBlockDelimiters % 2 === 1) {
      // 有未闭合的代码块
      const lastCodeBlockStart = partialMarkdown.lastIndexOf('```')
      
      if (lastCodeBlockStart !== -1) {
        // 分割已完成部分和未完成部分
        const completed = partialMarkdown.substring(0, lastCodeBlockStart)
        const unfinished = partialMarkdown.substring(lastCodeBlockStart)
        
        // 渲染已完成部分
        const renderedCompleted = renderMarkdown(completed)
        
        // 对未完成部分进行简单转义
        const escapedUnfinished = escapeHtml(unfinished)
        
        return renderedCompleted + `<div class="incomplete-code-block">${escapedUnfinished}</div>`
      }
    }
    
    return renderMarkdown(partialMarkdown)
    
  } catch (error) {
    console.warn('流式渲染失败:', error)
    return escapeHtml(partialMarkdown)
  }
}

// ============================================
// 辅助函数
// ============================================

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// 保持其他函数不变
export function initCodeCopyButtons(container: HTMLElement | Document = document): void {
  const buttons = container.querySelectorAll('.copy-code-btn')
  
  buttons.forEach(button => {
    const newButton = button.cloneNode(true) as HTMLElement
    button.parentNode?.replaceChild(newButton, button)
    
    newButton.addEventListener('click', async (e) => {
      e.preventDefault()
      e.stopPropagation()
      
      const target = e.currentTarget as HTMLElement
      const encodedCode = target.getAttribute('data-code')
      
      if (!encodedCode) return
      
      let code: string
      try {
        code = decodeURIComponent(encodedCode)
      } catch {
        console.error('解码失败')
        target.textContent = '解码失败'
        target.classList.add('error')
        setTimeout(() => {
          target.textContent = '复制'
          target.classList.remove('error')
        }, 2000)
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

export function cleanupCodeCopyButtons(container: HTMLElement): void {
  const copyButtons = container.querySelectorAll('.copy-code-btn')
  copyButtons.forEach(button => {
    button.remove()
  })
}
export function parseMarkdown(text) {
  if (!text) return ''
  let html = text
    // Escape HTML for safety (basic)
    .replace(/</g, '&lt;').replace(/>/g, '&gt;')

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
  // Italic
  html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>')

  // Images ![alt](url)
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/gim, '<img src="$2" alt="$1" style="max-width:100%; border-radius: 8px; margin: 8px 0;" />')
  
  // Links [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank" style="color: #60a5fa; text-decoration: underline;">$1</a>')

  // Blockquotes
  html = html.replace(/^> (.*$)/gim, '<blockquote style="border-left: 3px solid #60a5fa; padding-left: 10px; color: #9ca3af; margin: 10px 0;">$1</blockquote>')

  // Code inline
  html = html.replace(/`(.*?)`/gim, '<code style="background: rgba(0,0,0,0.2); padding: 2px 4px; border-radius: 4px; font-family: monospace; font-size: 0.9em;">$1</code>')

  // Newlines into <br> inside paragraphs, but better to wrap in paragraphs
  html = html.split(/\n\n+/).map(p => {
    // don't wrap headers or blockquotes in p
    if (p.startsWith('<h') || p.startsWith('<blockquote') || p.startsWith('<img')) return p
    return '<p style="margin-bottom: 12px; line-height: 1.6;">' + p.replace(/\n/g, '<br />') + '</p>'
  }).join('')

  // Bullet Lists
  html = html.replace(/^\s*\- (.*$)/gim, '<li style="margin-left: 20px;">$1</li>')
  // wrap subsequent <li>s in <ul>
  html = html.replace(/(<li.*<\/li>)/gms, '<ul style="margin-bottom: 12px;">$1</ul>')
  // cleanup multiple uls
  html = html.replace(/<\/ul>\s*<ul[^>]*>/g, '')

  return html
}

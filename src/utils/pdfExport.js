import { jsPDF } from 'jspdf'
import { getAllPlaybooks, formatFileSize } from './playbookStore'

export function exportTicketPDF(ticket) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const W = 210, M = 20, CW = W - M * 2

  // ─── Header ───────────────────────────────────────────────
  doc.setFillColor(15, 23, 42) // Lighter dark blue
  doc.rect(0, 0, W, 32, 'F')
  doc.setTextColor(248, 250, 252)
  doc.setFontSize(18)
  doc.setFont('helvetica', 'bold')
  doc.text('Incident Report', M, 14)
  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(148, 163, 184)
  doc.text(`${ticket.id}  ·  Generated ${new Date().toLocaleString('id-ID')}`, M, 22)

  // Severity badge (top right)
  const sevColors = {
    critical: [239, 68, 68],
    high: [249, 115, 22],
    medium: [234, 179, 8],
    low: [34, 197, 94]
  }
  const sc = sevColors[ticket.severity?.toLowerCase()] || [148, 163, 184]
  doc.setFillColor(...sc)
  doc.roundedRect(W - M - 26, 10, 26, 8, 1.5, 1.5, 'F')
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(8)
  doc.setFont('helvetica', 'bold')
  doc.text(ticket.severity?.toUpperCase() || 'UNKNOWN', W - M - 13, 15.5, { align: 'center' })

  let y = 42

  // ─── Status row ───────────────────────────────────────────
  const statusColors = {
    open: [234, 179, 8],
    in_progress: [59, 130, 246],
    solved: [34, 197, 94],
    closed: [100, 116, 139],
    false_positive: [249, 115, 22]
  }
  const stc = statusColors[ticket.status] || [100, 116, 139]
  doc.setFillColor(...stc)
  doc.roundedRect(M, y, 30, 7, 1, 1, 'F')
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(7)
  doc.setFont('helvetica', 'bold')
  doc.text((ticket.status || '').replace('_', ' ').toUpperCase(), M + 15, y + 4.8, { align: 'center' })

  doc.setTextColor(100, 116, 139)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.text(`Created: ${new Date(ticket.createdAt).toLocaleString('id-ID')}`, M + 36, y + 4.8)
  doc.text(`Updated: ${new Date(ticket.updatedAt).toLocaleString('id-ID')}`, M + 95, y + 4.8)

  y += 12

  // Subtle separator line
  doc.setDrawColor(226, 232, 240)
  doc.setLineWidth(0.5)
  doc.line(M, y, W - M, y)
  y += 10

  // ─── Section helper ───────────────────────────────────────
  function section(title, rows) {
    if (y > 260) { doc.addPage(); y = 20 }
    
    // Title
    doc.setTextColor(30, 41, 59)
    doc.setFontSize(11)
    doc.setFont('helvetica', 'bold')
    doc.text(title.toUpperCase(), M, y)
    y += 2
    
    // Short underline accent
    doc.setDrawColor(59, 130, 246)
    doc.setLineWidth(1)
    doc.line(M, y, M + 12, y)
    y += 8

    rows.forEach(([label, value]) => {
      if (y > 270) { doc.addPage(); y = 20 }
      
      doc.setFontSize(9)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(100, 116, 139)
      doc.text(label, M, y)
      
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(15, 23, 42)
      const lines = doc.splitTextToSize(String(value || '-'), CW - 35)
      doc.text(lines, M + 35, y)
      
      y += lines.length * 5 + 3
    })
    y += 8
  }

  // ─── Alert Information ────────────────────────────────────
  section('Alert Information', [
    ['Agent', `${ticket.agentName || '-'} (${ticket.agentIp || '-'})`],
    ['Alert Time', new Date(ticket.alertTimestamp || ticket.createdAt).toLocaleString('id-ID')],
    ['Rule ID', ticket.ruleId || '-'],
    ['Rule Level', String(ticket.ruleLevel || '-')],
    ['Description', ticket.ruleDescription || '-'],
    ['CVE ID', ticket.cveId || '-'],
    ['Package', ticket.packageName ? `${ticket.packageName} v${ticket.packageVersion || ''}` : '-'],
    ['Assignee', ticket.assignee || 'Unassigned'],
    ['Tags', ticket.tags?.length ? ticket.tags.join(', ') : '-'],
  ])

  // ─── Analysis ─────────────────────────────────────────────
  section('Incident Analysis', [
    ['Description', ticket.description || '-'],
    ['Root Cause', ticket.rootCause || '-'],
    ['Solution', ticket.solution || '-'],
    ['Notes', ticket.notes || '-'],
  ])

  // ─── Playbook Progress ────────────────────────────────────
  if (ticket.playbook) {
    const { playbookName, completedSteps, totalSteps, steps } = ticket.playbook
    const pb = getAllPlaybooks().find(p => p.id === ticket.playbook.playbookId)
    const pct = totalSteps ? Math.round((completedSteps / totalSteps) * 100) : 0

    section(`Playbook: ${playbookName}`, [
      ['Progress', `${completedSteps}/${totalSteps} steps (${pct}%)`],
      ['Status', pct === 100 ? 'COMPLETED' : 'IN PROGRESS'],
      ['Attached', new Date(ticket.playbook.attachedAt).toLocaleString('id-ID')],
    ])

    if (pb) {
      pb.steps.sort((a, b) => a.order - b.order).forEach(step => {
        const prog = steps[step.id]
        if (y > 260) { doc.addPage(); y = 20 }
        const status = prog?.checked ? '[✓]' : '[ ]'
        doc.setFontSize(8)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(prog?.checked ? 34 : 80, prog?.checked ? 197 : 80, prog?.checked ? 94 : 80)
        doc.text(`${status} ${step.order}. ${step.title}`, M, y)
        y += 5
        if (prog?.note) {
          doc.setFont('helvetica', 'italic')
          doc.setTextColor(100, 100, 100)
          const noteLines = doc.splitTextToSize(`Note: ${prog.note}`, CW - 10)
          doc.text(noteLines, M + 8, y)
          y += noteLines.length * 4 + 2
        }
      })
      y += 4
    }
  }

  // ─── Evidence List ────────────────────────────────────────
  if (ticket.evidence?.length) {
    section('Evidence Collected', ticket.evidence.map((ev, i) => [
      `#${i + 1} ${ev.fileName}`,
      `${formatFileSize(ev.fileSize)} · ${new Date(ev.uploadedAt).toLocaleString('id-ID')} · ${ev.description || 'No description'}`
    ]))
    // Note: images not embedded in PDF to keep file size manageable
    doc.setFontSize(7)
    doc.setTextColor(150, 150, 150)
    if (y > 280) { doc.addPage(); y = 20 }
    doc.text('* File evidence tidak diembed dalam PDF. Download dari aplikasi untuk akses file.', M, y)
    y += 6
  }

  // ─── Activity Timeline ────────────────────────────────────
  if (ticket.history?.length) {
    section('Activity Timeline', ticket.history.map(h => [
      new Date(h.timestamp).toLocaleString('id-ID'),
      h.detail
    ]))
  }

  // ─── Footer ───────────────────────────────────────────────
  const pageCount = doc.internal.getNumberOfPages()
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i)
    doc.setFontSize(7)
    doc.setTextColor(150, 150, 150)
    doc.text(`PatchOps — Confidential · Page ${i} of ${pageCount}`, W / 2, 290, { align: 'center' })
    doc.text(`Ticket ID: ${ticket.id}`, M, 290)
  }

  doc.save(`${ticket.id}_report.pdf`)
}

export function exportBulkPDF(tickets) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })

  tickets.forEach((ticket, idx) => {
    if (idx > 0) doc.addPage()

    let y = 20

    // Title
    doc.setFontSize(12)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(20, 20, 20)
    doc.text(`${ticket.id}`, 20, y)
    y += 6

    doc.setFontSize(9)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(60, 60, 60)
    const descLines = doc.splitTextToSize(ticket.ruleDescription || '-', 170)
    doc.text(descLines, 20, y)
    y += descLines.length * 4.5 + 4

    doc.setFontSize(8)
    doc.text(`Agent: ${ticket.agentName || '-'} (${ticket.agentIp || '-'})`, 20, y); y += 5
    doc.text(`Status: ${(ticket.status || '').replace('_', ' ').toUpperCase()} | Severity: ${ticket.severity || '-'}`, 20, y); y += 5
    doc.text(`Created: ${new Date(ticket.createdAt).toLocaleString('id-ID')}`, 20, y); y += 5
    doc.text(`CVE: ${ticket.cveId || '-'} | Package: ${ticket.packageName || '-'}`, 20, y); y += 5
    doc.text(`Assignee: ${ticket.assignee || 'Unassigned'}`, 20, y); y += 8

    // Playbook progress summary
    if (ticket.playbook) {
      doc.setFont('helvetica', 'bold')
      const pct = ticket.playbook.totalSteps ? Math.round((ticket.playbook.completedSteps / ticket.playbook.totalSteps) * 100) : 0
      doc.text(`Playbook: ${ticket.playbook.playbookName} (${pct}%)`, 20, y); y += 5
      doc.setFont('helvetica', 'normal')
    }

    if (ticket.solution) {
      doc.setFont('helvetica', 'bold')
      doc.text('Solution:', 20, y); y += 5
      doc.setFont('helvetica', 'normal')
      const lines = doc.splitTextToSize(ticket.solution, 170)
      doc.text(lines, 20, y)
      y += lines.length * 4.5
    }

    // Divider line
    doc.setDrawColor(200, 200, 200)
    doc.line(20, 280, 190, 280)
    doc.setFontSize(7)
    doc.setTextColor(150, 150, 150)
    doc.text(`PatchOps · Page ${idx + 1}/${tickets.length}`, 105, 285, { align: 'center' })
  })

  doc.save(`tickets_bulk_${new Date().toISOString().slice(0, 10)}.pdf`)
}

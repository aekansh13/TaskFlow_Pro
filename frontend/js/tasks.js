/**
 * tasks.js — Browser feature helpers for TaskFlow Pro dashboard.
 * Exports:
 *   initDueNotifications(tasks) — fires Web Notifications for tasks due within 24h
 *   exportToPDF(tasks)          — generates and downloads a jsPDF task report
 *
 * Both functions are non-breaking: if any browser API is unavailable the rest
 * of the app continues to work normally.
 */

// ---------------------------------------------------------------------------
// FEATURE 1: Browser due-date notifications
// ---------------------------------------------------------------------------

/**
 * Request notification permission (if not already decided) then fire a
 * Notification for every incomplete task that's due within the next 24 hours.
 * Duplicate notifications for the same task are suppressed via the `tag` option.
 *
 * @param {Array} tasks - Array of task objects from the API
 */
export async function initDueNotifications(tasks) {
  // Bail out silently if Web Notifications are not supported
  if (!('Notification' in window)) return;

  try {
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') return;

    const now  = new Date();
    const in24 = new Date(now.getTime() + 24 * 60 * 60 * 1000);

    const dueSoon = tasks.filter(task => {
      if (!task.due_date || task.status === 'done') return false;
      const due = new Date(task.due_date);
      return due >= now && due <= in24;
    });

    for (const task of dueSoon) {
      const dueDate = new Date(task.due_date);
      const formattedDate = dueDate.toLocaleString(undefined, {
        weekday: 'short',
        month:   'short',
        day:     'numeric',
        hour:    '2-digit',
        minute:  '2-digit',
      });

      new Notification('TaskFlow Pro — Task Due Soon', {
        body: `${task.title} is due by ${formattedDate}`,
        icon: '/favicon.ico',
        tag:  task.id,    // prevents duplicate notifications for the same task
      });
    }
  } catch (_) {
    // Silently ignore any permission or notification errors
  }
}

// ---------------------------------------------------------------------------
// FEATURE 2: PDF export (jsPDF loaded from CDN on dashboard.html)
// ---------------------------------------------------------------------------

/**
 * Generate a PDF report of the provided tasks and trigger a browser download.
 * Requires jsPDF to be loaded globally (via CDN script tag on the page).
 *
 * @param {Array}  tasks     - Array of task objects from the API
 * @param {string} userName  - Display name for the PDF header
 */
export function exportToPDF(tasks, userName = '') {
  try {
    // jsPDF is loaded from CDN as a global
    if (typeof window.jspdf === 'undefined' && typeof window.jsPDF === 'undefined') {
      alert('PDF export library is not loaded. Please refresh the page and try again.');
      return;
    }

    const { jsPDF } = window.jspdf || window;
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

    const PAGE_W  = 210;
    const PAGE_H  = 297;
    const MARGIN  = 16;
    const CONTENT_W = PAGE_W - MARGIN * 2;
    const LINE_H    = 8;

    let y            = MARGIN;
    let pageNum      = 1;
    const totalPages = _estimatePageCount(doc, tasks, MARGIN, LINE_H, PAGE_H);

    // ---------- Header ----------
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(18);
    doc.setTextColor(26, 86, 219);          // brand blue
    doc.text('TaskFlow Pro — My Tasks', MARGIN, y);
    y += 7;

    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(107, 114, 128);        // muted
    const headerRight = userName
      ? `${userName}  |  ${_fmtDate(new Date())}`
      : _fmtDate(new Date());
    doc.text(headerRight, PAGE_W - MARGIN, y, { align: 'right' });
    y += 4;

    // Horizontal rule
    doc.setDrawColor(229, 231, 235);
    doc.setLineWidth(0.5);
    doc.line(MARGIN, y, PAGE_W - MARGIN, y);
    y += 7;

    // ---------- Tasks ----------
    for (const task of tasks) {
      // Check if we need a new page (leave 20 mm for footer)
      if (y > PAGE_H - 20 - MARGIN) {
        _addFooter(doc, pageNum, totalPages, MARGIN, PAGE_H);
        doc.addPage();
        pageNum++;
        y = MARGIN + 5;
      }

      const isDone  = task.status === 'done';
      const dueText = task.due_date
        ? _fmtDate(new Date(task.due_date))
        : 'No due date';
      const pomText = task.pomodoro_count > 0
        ? `Pomodoro x${task.pomodoro_count}`
        : '';

      // Title
      doc.setFont('helvetica', isDone ? 'normal' : 'bold');
      doc.setFontSize(10);
      doc.setTextColor(isDone ? 107 : 17, isDone ? 114 : 24, isDone ? 128 : 39);

      const titleLines = doc.splitTextToSize(task.title, CONTENT_W - 40);
      doc.text(titleLines, MARGIN, y);

      // Strikethrough for completed tasks
      if (isDone) {
        const titleWidth = doc.getTextWidth(task.title.slice(0, 50));
        doc.setDrawColor(107, 114, 128);
        doc.setLineWidth(0.3);
        doc.line(MARGIN, y - 0.5, MARGIN + Math.min(titleWidth, CONTENT_W - 40), y - 0.5);
      }

      y += LINE_H * titleLines.length;

      // Meta line: priority | status | due | pomodoro
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(8);
      doc.setTextColor(107, 114, 128);

      const priority = (task.priority || 'medium').toUpperCase();
      const status   = (task.status   || 'todo').replace('_', ' ').toUpperCase();
      const meta     = [priority, status, dueText, pomText].filter(Boolean).join('   |   ');
      doc.text(meta, MARGIN, y);
      y += LINE_H * 0.7;

      // Subtask line
      if (task.subtasks?.length) {
        const done  = task.subtasks.filter(s => s.done).length;
        const total = task.subtasks.length;
        doc.setFontSize(7.5);
        doc.text(`Subtasks: ${done}/${total} completed`, MARGIN, y);
        y += LINE_H * 0.6;
      }

      // Light separator
      doc.setDrawColor(243, 244, 246);
      doc.setLineWidth(0.3);
      doc.line(MARGIN, y, PAGE_W - MARGIN, y);
      y += 4;
    }

    // Footer for last page
    _addFooter(doc, pageNum, totalPages, MARGIN, PAGE_H);

    // Download
    doc.save('taskflow-tasks.pdf');

  } catch (err) {
    console.error('PDF export failed:', err);
    alert('PDF export failed. Please try again.');
  }
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function _fmtDate(date) {
  return date.toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

function _addFooter(doc, pageNum, totalPages, margin, pageH) {
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(156, 163, 175);
  doc.text(
    `Page ${pageNum} of ${totalPages}`,
    210 - margin,
    pageH - 8,
    { align: 'right' },
  );
}

function _estimatePageCount(doc, tasks, margin, lineH, pageH) {
  // Rough estimate: 3–4 lines per task on average
  const contentH = pageH - margin * 2 - 20;
  const linesPerPage = Math.floor(contentH / (lineH * 1.8));
  const estimatedLines = tasks.reduce((acc, t) => {
    return acc + 2 + (t.subtasks?.length ? 1 : 0);
  }, 0);
  return Math.max(1, Math.ceil(estimatedLines / linesPerPage));
}

import { useState } from 'react';
import './Widgets.css';

// Days in the month that have "tasks" — this would ideally come from the API,
// but we highlight a few meaningful dates based on today as a demo.
// In a future iteration, wire to /api/tasks/today to mark real task days.
function CalendarWidget() {
  const now = new Date();
  const month = now.toLocaleString('default', { month: 'long' }).toUpperCase();
  const year = now.getFullYear();
  const today = now.getDate();
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1).getDay();
  const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();

  // Simulate task-bearing days: always mark today, and a few nearby days
  const taskDays = new Set([today, today + 2, today + 5, today - 3].filter(d => d >= 1 && d <= daysInMonth));

  const days = [];
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let i = 1; i <= daysInMonth; i++) days.push(i);

  return (
    <div className="widget glass-card glow-border">
      <div className="widget-header">
        <span className="pixel-text widget-label">📅 CALENDAR</span>
        <span className="cal-year-label">{year}</span>
      </div>
      <div className="cal-month">{month}</div>
      <div className="cal-grid">
        {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((d, i) => (
          <span key={i} className="cal-dayname">{d}</span>
        ))}
        {days.map((d, i) => (
          <span
            key={i}
            className={`cal-day ${d === today ? 'cal-today' : ''} ${d === null ? 'cal-empty' : ''} ${d && taskDays.has(d) && d !== today ? 'cal-has-task' : ''}`}
          >
            {d}
            {d && taskDays.has(d) && <span className="cal-dot" />}
          </span>
        ))}
      </div>
    </div>
  );
}

export default CalendarWidget;

import './Widgets.css';

function TasksWidget() {
  // Placeholder tasks — will be populated from API later
  const tasks = [
    { title: 'No tasks yet', done: false },
  ];

  const completion = 0;

  return (
    <div className="widget glass-card glow-border">
      <div className="widget-header">
        <span className="pixel-text widget-label">✅ TASKS</span>
      </div>
      <div className="tasks-list">
        {tasks.map((t, i) => (
          <div key={i} className={`task-item ${t.done ? 'done' : ''}`}>
            <span className="task-check pixel-text">{t.done ? '■' : '□'}</span>
            <span className="task-title">{t.title}</span>
          </div>
        ))}
      </div>
      <div className="xp-bar-container">
        <div className="xp-bar-label">
          <span className="pixel-text" style={{ fontSize: '0.4rem' }}>PROGRESS</span>
          <span className="pixel-text" style={{ fontSize: '0.4rem' }}>{completion}%</span>
        </div>
        <div className="xp-bar">
          <div className="xp-fill" style={{ width: `${completion}%` }} />
        </div>
      </div>
    </div>
  );
}

export default TasksWidget;

import './Sidebar.css';
import { playClickSound } from '../utils/sound';
import UserCard from './UserCard';

function Sidebar({ user, sessionsCount, sessions, activeSessionId, onSelectSession, onNewChat, onDeleteChat }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="pixel-text sidebar-label">SAVE SLOTS</span>
        <button className="btn-pixel btn-green new-game-btn" onClick={() => { playClickSound(); onNewChat(); }}>+ NEW</button>
      </div>
      <div className="sidebar-list">
        {sessions.map((s, i) => (
          <div
            key={s.id}
            className={`sidebar-slot ${s.id === activeSessionId ? 'active' : ''}`}
            onClick={() => { playClickSound(); onSelectSession(s.id); }}
          >
            <span className="slot-number pixel-text">
              {String(i + 1).padStart(2, '0')}
            </span>
            <div className="slot-info">
              <span className="slot-title">{s.title || 'New Chat'}</span>
              <button
                className="sidebar-delete"
                title="Delete Session"
                onClick={(e) => {
                  e.stopPropagation();
                  playClickSound();
                  onDeleteChat(s.id);
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"></path>
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
      <div className="sidebar-footer">
        <UserCard user={user} sessionsCount={sessionsCount} />
      </div>
    </aside>
  );
}

export default Sidebar;

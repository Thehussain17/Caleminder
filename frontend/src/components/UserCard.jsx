import './Widgets.css';

function UserCard({ user, sessionsCount }) {
  return (
    <div className="widget glass-card glow-border user-card">
      <div className="widget-header">
        <span className="pixel-text widget-label">👤 PLAYER</span>
      </div>
      <div className="user-card-body">
        {user?.picture && (
          <img src={user.picture} alt="" className="user-card-avatar" referrerPolicy="no-referrer" />
        )}
        <div className="user-card-info">
          <span className="user-card-name">{user?.name || 'Player 1'}</span>
          <span className="user-card-stat pixel-text">LVL {Math.min(sessionsCount + 1, 99)}</span>
        </div>
      </div>
      <div className="user-card-stats">
        <div className="stat-row">
          <span className="stat-label">Sessions</span>
          <span className="stat-value pixel-text">{sessionsCount}</span>
        </div>
      </div>
      <div style={{ marginTop: '0.75rem', textAlign: 'center' }}>
        <a
          href="https://buymeacoffee.com"         target="_blank"
          rel="noreferrer"
          className="btn-pixel"
          style={{ display: 'inline-block', width: '100%', textDecoration: 'none', fontSize: '0.5rem', padding: '0.4rem' }}
        >
          ☕ BUY Hussain A COFFEE
        </a>
      </div>
    </div>
  );
}

export default UserCard;

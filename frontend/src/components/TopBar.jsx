import './TopBar.css';
import { playClickSound } from '../utils/sound';

function TopBar({ user, sessionTitle, onLogout }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <span className="topbar-logo">◈</span>
        <span className="pixel-text topbar-brand">CALEMINDER</span>
      </div>
      <div className="topbar-center">
        <span className="topbar-session-title">{sessionTitle || 'New Chat'}</span>
      </div>
      <div className="topbar-right">
        {user?.picture && (
          <img src={user.picture} alt="" className="topbar-avatar" referrerPolicy="no-referrer" />
        )}
        <button className="topbar-exit pixel-text" onClick={() => { playClickSound(); onLogout(); }}>⏻ EXIT</button>
      </div>
    </header>
  );
}

export default TopBar;

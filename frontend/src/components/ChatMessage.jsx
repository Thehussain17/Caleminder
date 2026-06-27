import './ChatMessage.css';
import { useEffect } from 'react';
import { playResponseSound } from '../utils/sound';

// Detect if this is a system/limit message (starts with GAME OVER or ⏳)
function isSystemMessage(text) {
  if (!text) return false;
  return text.startsWith('**GAME OVER') || text.startsWith('⏳ **Slow') || text.startsWith('Sorry,');
}

function ChatMessage({ role, text, userAvatar }) {
  const isUser = role === 'user';
  const isSystem = !isUser && isSystemMessage(text);

  // Play a subtle chime when AI responds
  useEffect(() => {
    if (!isUser && !isSystem) {
      playResponseSound();
    }
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  if (isSystem) {
    return (
      <div className="msg msg-system">
        <div className="msg-system-icon">⚙</div>
        <div className="msg-bubble msg-system-bubble">
          <div className="msg-text" dangerouslySetInnerHTML={{ __html: formatText(text) }} />
        </div>
      </div>
    );
  }

  return (
    <div className={`msg ${isUser ? 'msg-user' : 'msg-ai'}`}>
      <div className="msg-avatar">
        {isUser && userAvatar ? (
          <img src={userAvatar} alt="U" className="msg-avatar-img" referrerPolicy="no-referrer" />
        ) : (
          <span className="pixel-text">{isUser ? 'U' : '✦'}</span>
        )}
      </div>
      <div className="msg-bubble">
        <div className="msg-text" dangerouslySetInnerHTML={{ __html: formatText(text) }} />
      </div>
    </div>
  );
}

function formatText(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/`(.*?)`/g, '<code>$1</code>');
}

export default ChatMessage;

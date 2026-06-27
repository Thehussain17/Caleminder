import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getSessions, createSession, getChat, sendMessage, logout, deleteSession } from '../api/client';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import ChatMessage from '../components/ChatMessage';
import InputBar from '../components/InputBar';
import CalendarWidget from '../components/CalendarWidget';
import TasksWidget from '../components/TasksWidget';
import UserCard from '../components/UserCard';
import DriveWidget from '../components/DriveWidget';
import { playClickSound } from '../utils/sound';
import './ChatPage.css';

function ChatPage({ user, setAuth }) {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const [sessions, setSessions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentSession, setCurrentSession] = useState(null);
  const chatEndRef = useRef(null);

  // Load sessions
  useEffect(() => {
    loadSessions();
  }, []);

  // Load chat when session changes
  useEffect(() => {
    if (sessionId) {
      loadChat(sessionId);
    }
  }, [sessionId]);

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function loadSessions() {
    try {
      const data = await getSessions();
      setSessions(data);
      // Auto-navigate to first session or create one
      if (!sessionId && data.length > 0) {
        navigate(`/chat/${data[0].id}`, { replace: true });
      } else if (!sessionId && data.length === 0) {
        handleNewChat();
      }
    } catch (e) {
      if (e.message === 'UNAUTHORIZED') {
        setAuth({ authenticated: false });
      }
    }
  }

  async function loadChat(sid) {
    try {
      const data = await getChat(sid);
      setMessages(data.messages || []);
      setCurrentSession(data.session);
    } catch (e) {
      console.error('Failed to load chat:', e);
    }
  }

  async function handleNewChat() {
    playClickSound();
    try {
      const data = await createSession();
      await loadSessions();
      navigate(`/chat/${data.session_id}`);
    } catch (e) {
      console.error('Failed to create session:', e);
    }
  }

  async function handleDeleteChat(id) {
    try {
      await deleteSession(id);
      await loadSessions();
      if (sessionId === id) navigate('/');
    } catch (e) {
      console.error('Failed to delete session:', e);
    }
  }

  async function handleSend(text, imageFile) {
    if (!sessionId || (!text.trim() && !imageFile)) return;

    playClickSound();
    // Optimistic UI update
    setMessages(prev => [...prev, { role: 'user', text: text }]);
    setLoading(true);

    try {
      const data = await sendMessage(sessionId, text, imageFile);
      setMessages(prev => [...prev, { role: 'model', text: data.response }]);
      loadSessions(); // refresh titles
    } catch (e) {
      setMessages(prev => [...prev, { role: 'model', text: '⚠ Something went wrong. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleLogout() {
    try {
      await logout();
    } catch (e) {
      console.error('Logout API failed:', e);
    }
    setAuth({ authenticated: false });
    navigate('/login');
  }

  function handleDriveQuickAction(prompt) {
    playClickSound();
    handleSend(prompt, null);
  }

  return (
    <div className="chat-page">
      {/* Left Sidebar */}
      <Sidebar
        user={user}
        sessionsCount={sessions.length}
        sessions={sessions}
        activeSessionId={sessionId}
        onSelectSession={(id) => navigate(`/chat/${id}`)}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
      />

      {/* Center Chat */}
      <main className="chat-main">
        <TopBar user={user} sessionTitle={currentSession?.title} onLogout={handleLogout} />
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty">
              <span className="pixel-text neon-text" style={{ fontSize: '0.6rem' }}>AWAITING COMMAND...</span>
              <p>Send a message to begin</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <ChatMessage key={i} role={msg.role} text={msg.text} userAvatar={user?.picture} />
          ))}
          {loading && (
            <div className="chat-typing">
              <span className="pixel-text" style={{ fontSize: '0.55rem', color: 'var(--accent-neon)' }}>
                PROCESSING<span className="cursor-blink"></span>
              </span>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
        <InputBar onSend={handleSend} disabled={loading} />
      </main>

      {/* Right Widgets */}
      <aside className="widget-panel">
        <a
          href="https://mail.google.com/mail/?view=cm&fs=1&to=thehussain17@gmail.com&su=Caleminder%20Feedback&body=hey%20hussain%20I%20used%20Caleminder%2C%20and%20these%20are%20the%20reasons%20why%20I%20find%20this%20stupid%3A%0D%0A"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-pixel btn-green"
          style={{ fontSize: '0.45rem', padding: '0.6rem', marginBottom: '1rem', width: '100%', display: 'block', textAlign: 'center' }}
          onClick={playClickSound}
        >
          TELL ME WHY IS THIS STUPID
        </a>
        <CalendarWidget />
        <TasksWidget />
        <DriveWidget onQuickAction={handleDriveQuickAction} />
      </aside>
    </div>
  );
}

export default ChatPage;

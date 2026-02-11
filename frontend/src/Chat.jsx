import React, { useState, useEffect, useRef } from 'react';
import { Send, Paperclip, Loader2, Bot, User, Plus, MessageSquare, LogOut, Settings } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';

const Chat = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [user, setUser] = useState({ name: '', picture: '' });
  const messagesEndRef = useRef(null);

  // Fetch sessions and user info on mount
  useEffect(() => {
    fetchSessions();
    // In a real app, user info might come from a dedicated /me endpoint
    // Here we might get it from the chat page context or sessions.
    // For now, let's assume sessions endpoint could return user info or we separate it.
    // Let's create a quick /me endpoint in backend or parse it from first load.
    // Actually, we can just use the sessions for the sidebar.
  }, []);

  // Fetch chat history when sessionId changes
  useEffect(() => {
    if (sessionId) {
      fetchHistory(sessionId);
    }
  }, [sessionId]);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history, loading]);

  const fetchSessions = async () => {
    try {
      const res = await fetch('/api/sessions');
      if (res.status === 401) {
        navigate('/');
        return;
      }
      const data = await res.json();
      setSessions(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchHistory = async (id) => {
    try {
      const res = await fetch(`/api/chat/${id}`);
      if (res.status === 404) return;

      const data = await res.json();
      setHistory(data.history || []);
      setUser(data.user || { name: 'User', picture: null });
    } catch (e) {
      console.error(e);
    }
  };

  const createNewChat = async () => {
    try {
      const res = await fetch('/api/new_chat', { method: 'POST' });
      const data = await res.json();
      if (data.session_id) {
        navigate(`/chat/${data.session_id}`);
        fetchSessions();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if ((!input.trim() && !file) || loading) return;

    const currentInput = input;
    const currentFile = file;

    // Optimistic Update
    const optimisticMsg = {
        role: 'user',
        parts: [
            { text: currentInput },
            ...(currentFile ? [{ file_data: true, text: `Attached: ${currentFile.name}` }] : [])
        ]
    };

    setHistory(prev => [...prev, optimisticMsg]);
    setInput('');
    setFile(null);
    setLoading(true);

    const formData = new FormData();
    formData.append('message', currentInput);
    if (currentFile) formData.append('image', currentFile);

    try {
      const res = await fetch(`/api/chat/${sessionId}`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      const aiMsg = {
          role: 'model',
          parts: [{ text: data.response }]
      };

      setHistory(prev => [...prev, aiMsg]);
      if (history.length === 0) fetchSessions();
    } catch (e) {
      console.error(e);
      setHistory(prev => [...prev, { role: 'model', parts: [{ text: 'Error: Could not connect to server.' }] }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-white overflow-hidden font-sans text-gray-900">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col flex-shrink-0">
        <div className="p-4">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold">C</div>
            <h1 className="font-bold text-lg text-gray-800">Caleminder AI</h1>
          </div>
          <button onClick={createNewChat} className="w-full bg-gray-900 hover:bg-gray-800 text-white rounded-lg py-2.5 px-4 flex items-center justify-center gap-2 transition-colors shadow-sm font-medium text-sm cursor-pointer">
            <Plus size={16} /> New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {sessions.map(session => (
            <Link
              key={session.id}
              to={`/chat/${session.id}`}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm truncate transition-colors ${sessionId === session.id ? 'bg-indigo-50 text-indigo-600 font-medium' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              <MessageSquare size={14} />
              <span className="truncate">{session.title || 'Untitled Chat'}</span>
            </Link>
          ))}
        </div>

        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center gap-3">
             {user.picture ? (
                 <img src={user.picture} alt="Profile" className="w-8 h-8 rounded-full" />
             ) : (
                 <div className="w-8 h-8 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold">
                     {user.name ? user.name[0] : <User size={16}/>}
                 </div>
             )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{user.name || 'User'}</p>
              <p className="text-xs text-gray-500 truncate">Free Plan</p>
            </div>
            <a href="/api/logout" className="text-gray-400 hover:text-gray-600">
              <LogOut size={16} />
            </a>
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col relative">
        <div className="h-14 border-b border-gray-100 flex items-center justify-between px-6 bg-white">
             <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-md">
                <Bot size={16} className="text-indigo-500"/>
                <span className="text-xs font-semibold text-gray-700">Gemini 2.5 Flash</span>
            </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 pb-32 space-y-6">
            {history.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                    <Bot size={48} className="mb-4 text-indigo-100"/>
                    <p>Start a new conversation with Caleminder AI</p>
                </div>
            )}

            {history.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start gap-4 max-w-3xl'}`}>
                    {msg.role !== 'user' && (
                        <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center flex-shrink-0 text-indigo-600 mt-1">
                             <Bot size={16} />
                        </div>
                    )}

                    <div className={`
                        ${msg.role === 'user'
                            ? 'bg-indigo-600 text-white rounded-2xl rounded-tr-sm py-3 px-4 max-w-2xl shadow-sm text-sm'
                            : 'bg-white border border-gray-100 rounded-2xl rounded-tl-sm py-3 px-4 shadow-sm text-sm text-gray-800 leading-relaxed w-full'}
                    `}>
                        {msg.parts?.map((part, pIdx) => (
                            <div key={pIdx}>
                                {part.text && <p className="whitespace-pre-wrap">{part.text}</p>}
                                {part.file_data && (
                                    <p className="text-xs opacity-75 mt-1 border-t border-indigo-400/30 pt-1">
                                        [File Attached]
                                    </p>
                                )}
                                {part.function_call && (
                                     <div className="text-xs bg-gray-50 border border-gray-200 p-2 rounded mt-2 font-mono text-gray-500">
                                        Running: {part.function_call.name}...
                                    </div>
                                )}
                                {part.function_response && (
                                     <div className="text-xs text-green-600 mt-1 mb-2">
                                        ✓ Completed: {part.function_response.name}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            ))}

            {loading && (
                 <div className="flex gap-4 max-w-3xl">
                    <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center flex-shrink-0 text-indigo-600 animate-pulse">
                        <Bot size={16} />
                    </div>
                    <div className="text-sm text-gray-400 py-2">Caleminder AI is thinking...</div>
                </div>
            )}
            <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="absolute bottom-0 left-0 w-full bg-white/90 backdrop-blur-sm p-4 border-t border-gray-100">
             <div className="max-w-4xl mx-auto relative">
                {file && (
                    <div className="absolute bottom-full mb-2 left-0 bg-gray-100 p-2 rounded-lg border border-gray-200 flex items-center gap-2">
                        <span className="text-xs text-gray-600 truncate max-w-xs">{file.name}</span>
                        <button onClick={() => setFile(null)} className="text-red-500 hover:text-red-700">×</button>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl shadow-lg flex items-center p-2 gap-2 focus-within:ring-2 focus-within:ring-indigo-100 transition-shadow">
                    <label className="p-2 text-gray-400 hover:text-gray-600 cursor-pointer rounded-lg hover:bg-gray-50 transition-colors">
                        <Paperclip size={20} />
                        <input type="file" className="hidden" accept="image/*" onChange={(e) => setFile(e.target.files[0])} />
                    </label>

                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask anything..."
                        className="flex-1 bg-transparent border-none focus:ring-0 text-sm py-2 px-1 placeholder-gray-400 text-gray-800 outline-none"
                    />

                    <button
                        type="submit"
                        disabled={loading || (!input.trim() && !file)}
                        className="bg-gray-900 text-white rounded-lg p-2 hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                       {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                    </button>
                </form>
                <p className="text-center text-[10px] text-gray-400 mt-2">Caleminder AI can make mistakes. Consider checking important information.</p>
             </div>
        </div>
      </main>
    </div>
  );
};

export default Chat;

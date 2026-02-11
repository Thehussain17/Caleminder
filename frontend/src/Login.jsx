import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Check if already logged in
    fetch('/api/sessions')
      .then(res => {
        if (res.ok) {
          return res.json();
        }
        throw new Error('Not logged in');
      })
      .then(sessions => {
        // Redirect to most recent session or create new
        if (sessions.length > 0) {
            navigate(`/chat/${sessions[0].id}`);
        } else {
            fetch('/api/new_chat', { method: 'POST' })
                .then(r => r.json())
                .then(data => navigate(`/chat/${data.session_id}`));
        }
      })
      .catch(() => {
        // Not logged in, stay here
      });
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 p-4 font-sans text-gray-900">
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8 max-w-md w-full text-center">
        {/* Branding Logo */}
        <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center text-white font-bold text-3xl mx-auto mb-6 shadow-md">
          C
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">Welcome to Caleminder AI</h1>
        <p className="text-gray-500 mb-8">Your intelligent workspace companion.</p>

        {/* Google Sign-In Button */}
        <a
          href="/api/auth/google"
          className="flex items-center justify-center gap-3 w-full bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 font-medium py-3 px-4 rounded-xl transition-colors shadow-sm"
        >
          {/* Google Logo SVG - fixed size and alignment */}
          <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
            <svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" className="w-full h-full block">
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path>
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path>
              <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path>
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path>
            </svg>
          </div>
          <span>Sign in with Google</span>
        </a>

        <p className="text-xs text-gray-400 mt-6">By continuing, you agree to our Terms of Service and Privacy Policy.</p>
      </div>
    </div>
  );
};

export default Login;

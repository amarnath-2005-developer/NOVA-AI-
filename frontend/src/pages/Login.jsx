import React, { useState, useEffect } from 'react';
import './Login.css';

const LoginPage = ({ onNavigate = () => { } }) => {
  const [authMode, setAuthMode] = useState('login'); // 'login', 'register', 'profiles'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [newProfileName, setNewProfileName] = useState('');
  const [profiles, setProfiles] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const savedEmail = localStorage.getItem('nova_account_email');
    const savedProfiles = localStorage.getItem('nova_account_profiles');
    if (savedEmail && savedProfiles) {
      setEmail(savedEmail);
      setProfiles(JSON.parse(savedProfiles));
      setAuthMode('profiles');
    }
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');

      setProfiles(data.profiles);
      localStorage.setItem('nova_account_email', data.email);
      localStorage.setItem('nova_account_profiles', JSON.stringify(data.profiles));
      setAuthMode('profiles');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    if (!newProfileName) {
      setError('Please provide a default profile name.');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, first_profile: newProfileName })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Registration failed');

      setProfiles(data.profiles);
      localStorage.setItem('nova_account_email', email);
      localStorage.setItem('nova_account_profiles', JSON.stringify(data.profiles));
      setAuthMode('profiles');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddProfile = async () => {
    if (!newProfileName) return;
    const addedProfileName = newProfileName; // Store locally before state clears
    setError('');
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/auth/profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, profile_name: addedProfileName })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to add profile');

      setProfiles(data.profiles);
      localStorage.setItem('nova_account_profiles', JSON.stringify(data.profiles));
      setNewProfileName('');

      // Inline auto-select logic to customize the greeting for new users
      try {
        fetch('http://127.0.0.1:8000/api/v1/command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: `switch user to ${addedProfileName} confirm` })
        });
      } catch (e) { }

      localStorage.setItem('nova_active_user', addedProfileName);
      onNavigate('home');

      import('../lib/tts').then(({ tts }) => {
        tts.speak(`Welcome, ${addedProfileName}. Systems initialized.`);
      });


    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('nova_account_email');
    localStorage.removeItem('nova_account_profiles');
    setAuthMode('login');
    setEmail('');
    setPassword('');
  };

  const selectProfile = (profileId) => {
    // Notify backend to switch active context without blocking UI
    try {
      fetch('http://127.0.0.1:8000/api/v1/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: `switch user to ${profileId} confirm` })
      });
    } catch (e) { }

    localStorage.setItem('nova_active_user', profileId);
    onNavigate('home');

    // Announce the profile switch
    import('../lib/tts').then(({ tts }) => {
      tts.speak(`Welcome back, ${profileId}. Systems online.`);
    });
  };

  if (authMode === 'profiles') {
    return (
      <div id="main" className="main-container">
        <div className="netflix-profile-container">
          <h1 className="netflix-title">Who is accessing NOVA?</h1>

          <div className="netflix-profiles">
            {profiles.map(p => (
              <div
                key={p}
                onClick={() => selectProfile(p)}
                className="netflix-profile-card"
              >
                <div className="netflix-avatar">
                  <span>{p.charAt(0).toUpperCase()}</span>
                </div>
                <span className="netflix-name">{p}</span>
              </div>
            ))}

            {profiles.length < 3 && (
              <div className="netflix-profile-card add-profile-card">
                <div className="netflix-avatar add-avatar" onClick={handleAddProfile} style={{ cursor: 'pointer' }}>
                  <span>+</span>
                </div>
                <input
                  type="text"
                  placeholder="New Profile"
                  className="netflix-add-input"
                  value={newProfileName}
                  onChange={e => setNewProfileName(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleAddProfile();
                  }}
                />
              </div>
            )}
          </div>
          {error && <p className="netflix-error">{error}</p>}

          <button
            className="netflix-signout-btn"
            onClick={handleLogout}
          >
            Sign Out
          </button>
        </div>
      </div>
    );
  }

  return (
    <div id="main" className="main-container">
      <div className="box relative">
        <h2 className="font-serif italic text-3xl mb-8">{authMode === 'login' ? 'Login' : 'Register'}</h2>
        <form onSubmit={authMode === 'login' ? handleLogin : handleRegister}>
          <div className="input-box">
            <input
              id="user-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <label>Email Address</label>
          </div>
          <div className="input-box">
            <input
              id="user-pass"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <label>Password</label>
          </div>

          {authMode === 'register' && (
            <div className="input-box">
              <input
                id="user-profile"
                type="text"
                required
                value={newProfileName}
                onChange={(e) => setNewProfileName(e.target.value)}
              />
              <label>Default Profile Name</label>
            </div>
          )}

          {error && <p style={{ color: '#ff4444', fontSize: '12px', marginBottom: '10px' }}>{error}</p>}

          <input id="submit" type="submit" value={loading ? "Processing..." : "Submit"} disabled={loading} />
        </form>
        {authMode === 'login' ? (
          <p className="mt-4 text-xs text-cyan-400/50">Need an account? <span className="text-cyan-400 cursor-pointer hover:underline" onClick={() => { setAuthMode('register'); setError(''); }}>Register</span></p>
        ) : (
          <p className="mt-4 text-xs text-cyan-400/50">Already have an account? <span className="text-cyan-400 cursor-pointer hover:underline" onClick={() => { setAuthMode('login'); setError(''); }}>Login</span></p>
        )}
      </div>
    </div>
  );
};

export default LoginPage;

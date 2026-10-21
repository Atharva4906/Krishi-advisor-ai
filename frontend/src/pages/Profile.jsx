import { useEffect, useState } from 'react';
import { api } from '../api';

const emptyProfile = { name: '', phone: '', village: '', district: '', lang: 'mr' };
const districts = ['Pune', 'Nashik', 'Ahmednagar', 'Solapur', 'Kolhapur', 'Satara', 'Sangli', 'Aurangabad', 'Latur', 'Osmanabad', 'Nanded', 'Jalgaon', 'Amravati', 'Nagpur'];

export default function Profile() {
  const [profile, setProfile] = useState(emptyProfile);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    api('/api/profile')
      .then((data) => setProfile(data))
      .catch((err) => setError(`${err.message}. Login through Flask first.`));
  }, []);

  const update = (event) => setProfile({ ...profile, [event.target.name]: event.target.value });

  async function submit(event) {
    event.preventDefault();
    setMessage('');
    setError('');
    try {
      const updated = await api('/api/profile', {
        method: 'PUT',
        body: JSON.stringify(profile),
      });
      setProfile(updated);
      setMessage('प्रोफाइल अपडेट झाली / Profile updated successfully.');
    } catch (err) {
      setError(err.message);
    }
  }

  const getInitials = () => {
    return profile.name ? profile.name.charAt(0).toUpperCase() : '👤';
  };

  const location = [profile.village, profile.district].filter(Boolean).join(', ');

  return (
    <section className="fp">
      <style>{css}</style>

      {/* Identity header */}
      <header className="fp-head">
        <div className="fp-rows" aria-hidden="true" />
        <div className="fp-head-body">
          <div className="fp-avatar">{getInitials()}</div>
          <div className="fp-id">
            <p className="fp-role">Farmer Profile</p>
            <h1 className="fp-name">{profile.name || 'नवीन शेतकरी'}</h1>
            <ul className="fp-meta">
              <li>
                <span aria-hidden="true">📞</span>
                {profile.phone ? `+91 ${profile.phone}` : 'नंबर उपलब्ध नाही'}
              </li>
              {location && (
                <li>
                  <span aria-hidden="true">📍</span>
                  {location}
                </li>
              )}
            </ul>
          </div>
        </div>
      </header>

      {/* Notifications */}
      {error && (
        <div className="fp-note fp-note-error" role="alert">
          {error}
        </div>
      )}
      {message && (
        <div className="fp-note fp-note-ok" role="status">
          {message}
        </div>
      )}

      {/* Edit form */}
      <form onSubmit={submit} className="fp-form">
        <div className="fp-form-title">
          <h2>माहिती अपडेट करा</h2>
          <span>Edit Details</span>
        </div>

        <div className="fp-field">
          <label htmlFor="fp-name">
            पूर्ण नाव <small>Full Name</small>
          </label>
          <input
            id="fp-name"
            name="name"
            value={profile.name || ''}
            onChange={update}
            required
            autoComplete="name"
          />
        </div>

        <div className="fp-grid">
          <div className="fp-field">
            <label htmlFor="fp-village">
              गाव <small>Village</small>
            </label>
            <input
              id="fp-village"
              name="village"
              value={profile.village || ''}
              onChange={update}
            />
          </div>
          <div className="fp-field">
            <label htmlFor="fp-district">
              जिल्हा <small>District</small>
            </label>
            <select
              id="fp-district"
              name="district"
              value={profile.district || ''}
              onChange={update}
            >
              <option value="">निवडा / Select</option>
              {districts.map((district) => (
                <option key={district} value={district}>
                  {district}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="fp-field">
          <span className="fp-label" id="fp-lang-label">
            पसंतीची भाषा <small>Language</small>
          </span>
          <div className="fp-seg" role="radiogroup" aria-labelledby="fp-lang-label">
            {[
              { value: 'mr', label: 'मराठी', sub: 'Marathi' },
              { value: 'en', label: 'English', sub: 'इंग्रजी' },
            ].map((opt) => {
              const active = (profile.lang || 'mr') === opt.value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  role="radio"
                  aria-checked={active}
                  className={active ? 'is-active' : ''}
                  onClick={() => update({ target: { name: 'lang', value: opt.value } })}
                >
                  <strong>{opt.label}</strong>
                  <span>{opt.sub}</span>
                </button>
              );
            })}
          </div>
        </div>

        <button type="submit" className="fp-save">
          बदल जतन करा / Save Changes
        </button>
      </form>
    </section>
  );
}

const css = `
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Noto+Sans:wght@400;500;600;700&display=swap');

.fp {
  --g900: #1b5e20;
  --g700: #2e7d32;
  --g300: #81c784;
  --g100: #e8f5e9;
  --ink: #14201a;
  --muted: #5b6b61;
  --line: #dfe7e1;
  --bg: #f4f8f5;
  max-width: 680px;
  margin: 0 auto;
  padding: 16px 16px 40px;
  font-family: 'Noto Sans', 'Noto Sans Devanagari', system-ui, -apple-system, sans-serif;
  color: var(--ink);
  background: var(--bg);
  box-sizing: border-box;
}
.fp *, .fp *::before, .fp *::after { box-sizing: border-box; }

/* Header */
.fp-head {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 20px;
  overflow: hidden;
  margin-bottom: 16px;
}
.fp-rows {
  height: 88px;
  background:
    repeating-linear-gradient(
      100deg,
      var(--g700) 0 14px,
      #388e3c 14px 18px,
      var(--g300) 18px 32px,
      #66bb6a 32px 36px
    );
  border-bottom: 6px solid var(--g900);
}
.fp-head-body {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  padding: 0 20px 20px;
  margin-top: -40px;
}
.fp-avatar {
  flex: none;
  width: 88px;
  height: 88px;
  border-radius: 24px;
  background: var(--g100);
  color: var(--g700);
  border: 4px solid #fff;
  display: grid;
  place-items: center;
  font-size: 36px;
  font-weight: 700;
}
.fp-id { min-width: 0; padding-bottom: 2px; }
.fp-role {
  margin: 0 0 2px;
  font-size: 13px;
  font-weight: 600;
  color: var(--g700);
}
.fp-name {
  margin: 0 0 10px;
  font-size: 26px;
  line-height: 1.25;
  font-weight: 700;
  overflow-wrap: anywhere;
}
.fp-meta {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.fp-meta li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--g100);
  color: var(--g900);
  font-size: 14px;
  font-weight: 500;
}

/* Notifications */
.fp-note {
  padding: 14px 16px;
  border-radius: 12px;
  margin-bottom: 16px;
  font-size: 15px;
  line-height: 1.5;
}
.fp-note-error { background: #fde8e8; color: #9b1c1c; border-left: 4px solid #c81e1e; }
.fp-note-ok { background: var(--g100); color: var(--g900); border-left: 4px solid var(--g900); }

/* Form */
.fp-form {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 24px 20px;
}
.fp-form-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 16px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--line);
}
.fp-form-title h2 { margin: 0; font-size: 20px; font-weight: 700; }
.fp-form-title span { font-size: 14px; color: var(--muted); }

.fp-field { margin-bottom: 20px; }
.fp-field label, .fp-label {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 15px;
  font-weight: 600;
}
.fp-field small { font-size: 13px; font-weight: 400; color: var(--muted); }
.fp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.fp input, .fp select {
  width: 100%;
  min-height: 52px;
  padding: 12px 14px;
  font: inherit;
  font-size: 16px;
  color: var(--ink);
  background: #fff;
  border: 1.5px solid #cfd9d2;
  border-radius: 12px;
  outline: none;
  transition: border-color .15s, box-shadow .15s;
}
.fp select {
  appearance: none;
  padding-right: 40px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='9' viewBox='0 0 14 9'%3E%3Cpath d='M1 1l6 6 6-6' fill='none' stroke='%232e7d32' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
}
.fp input:focus, .fp select:focus {
  border-color: var(--g700);
  box-shadow: 0 0 0 4px rgba(46,125,50,.15);
}

/* Language toggle */
.fp-seg {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 4px;
  background: var(--g100);
  border-radius: 14px;
}
.fp-seg button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-height: 56px;
  padding: 8px;
  font: inherit;
  color: var(--g900);
  background: transparent;
  border: 0;
  border-radius: 10px;
  cursor: pointer;
  transition: background-color .15s, color .15s;
}
.fp-seg button strong { font-size: 16px; font-weight: 600; }
.fp-seg button span { font-size: 12px; opacity: .75; }
.fp-seg button.is-active { background: var(--g700); color: #fff; }
.fp-seg button:focus-visible { outline: 3px solid var(--g900); outline-offset: 2px; }

/* Save */
.fp-save {
  width: 100%;
  min-height: 56px;
  margin-top: 8px;
  padding: 14px;
  font: inherit;
  font-size: 17px;
  font-weight: 600;
  color: #fff;
  background: var(--g700);
  border: 0;
  border-radius: 14px;
  cursor: pointer;
  transition: background-color .15s;
}
.fp-save:hover { background: var(--g900); }
.fp-save:active { transform: translateY(1px); }
.fp-save:focus-visible { outline: 3px solid var(--g900); outline-offset: 3px; }

@media (max-width: 480px) {
  .fp-head-body { flex-direction: column; align-items: flex-start; margin-top: -44px; }
  .fp-name { font-size: 23px; }
  .fp-grid { grid-template-columns: 1fr; gap: 0; }
  .fp-form-title { flex-direction: column; gap: 2px; }
}
`;
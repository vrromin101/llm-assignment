const express = require('express');
const session = require('express-session');
const bcrypt = require('bcryptjs');
const Database = require('better-sqlite3');

const db = new Database('users.db');
db.exec(`CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
)`);

const app = express();
app.use(express.json());
app.use(session({ secret: 'change-this-secret', resave: false, saveUninitialized: false }));
app.use(express.static('public'));

app.post('/api/register', (req, res) => {
  const { name, email, password } = req.body;
  if (!name || !email || !password || password.length < 6)
    return res.status(400).json({ error: 'All fields required; password min 6 chars' });
  try {
    const hash = bcrypt.hashSync(password, 10);
    db.prepare('INSERT INTO users (name,email,password) VALUES (?,?,?)')
      .run(name, email.toLowerCase(), hash);
    res.json({ message: 'Registered successfully. Please login.' });
  } catch (e) {
    res.status(409).json({ error: 'Email already registered' });
  }
});

app.post('/api/login', (req, res) => {
  const { email, password } = req.body;
  const user = db.prepare('SELECT * FROM users WHERE email=?').get((email || '').toLowerCase());
  if (!user || !bcrypt.compareSync(password || '', user.password))
    return res.status(401).json({ error: 'Invalid email or password' });
  req.session.user = { id: user.id, name: user.name, email: user.email };
  res.json({ message: 'Login successful', user: req.session.user });
});

app.get('/api/me', (req, res) =>
  req.session.user ? res.json(req.session.user) : res.status(401).json({ error: 'Not logged in' }));

app.post('/api/logout', (req, res) => req.session.destroy(() => res.json({ message: 'Logged out' })));

app.listen(3000, () => console.log('Running at http://localhost:3000'));

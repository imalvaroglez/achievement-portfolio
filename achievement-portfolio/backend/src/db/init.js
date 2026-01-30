import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

const schema = `
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME
);

CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  color TEXT DEFAULT '#3b82f6',
  icon TEXT,
  sort_order INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS achievements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  category_id INTEGER,
  date_achieved DATE,
  difficulty TEXT CHECK(difficulty IN ('easy', 'medium', 'hard', 'expert')),
  status TEXT DEFAULT 'completed' CHECK(status IN ('pending', 'in_progress', 'completed')),
  skills TEXT,
  image_url TEXT,
  notes TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS milestones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  achievement_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  completed_at DATETIME,
  sort_order INTEGER DEFAULT 0,
  FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_achievements_category ON achievements(category_id);
CREATE INDEX IF NOT EXISTS idx_achievements_status ON achievements(status);
CREATE INDEX IF NOT EXISTS idx_achievements_date ON achievements(date_achieved);
`;

export async function initDatabase(dbPath) {
  const db = await open({
    filename: dbPath,
    driver: sqlite3.Database
  });

  await db.exec('PRAGMA journal_mode = WAL;');
  await db.exec('PRAGMA foreign_keys = ON;');
  await db.exec('PRAGMA optimize;');

  await db.exec(schema);

  const categoryCount = await db.get('SELECT COUNT(*) as count FROM categories');
  if (categoryCount.count === 0) {
    const defaultCategories = [
      { name: 'Career', description: 'Professional achievements', color: '#3b82f6', icon: 'briefcase' },
      { name: 'Education', description: 'Learning and certifications', color: '#10b981', icon: 'graduation-cap' },
      { name: 'Personal', description: 'Personal growth milestones', color: '#f59e0b', icon: 'user' },
      { name: 'Skills', description: 'Technical and soft skills', color: '#8b5cf6', icon: 'code' },
      { name: 'Projects', description: 'Completed projects', color: '#ef4444', icon: 'folder' },
    ];

    for (const cat of defaultCategories) {
      await db.run(
        'INSERT INTO categories (name, description, color, icon) VALUES (?, ?, ?, ?)',
        [cat.name, cat.description, cat.color, cat.icon]
      );
    }
    console.log('✅ Created default categories');
  }

  console.log('✅ Database initialized');
  return db;
}

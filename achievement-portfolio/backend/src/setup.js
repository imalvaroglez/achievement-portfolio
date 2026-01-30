#!/usr/bin/env node
/**
 * Setup script for Achievement Portfolio
 * Creates initial admin user and configures environment
 */

import bcrypt from 'bcryptjs';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import dotenv from 'dotenv';
import { readFile, writeFile } from 'fs/promises';
import { existsSync } from 'fs';
import readline from 'readline';

dotenv.config();

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(query) {
  return new Promise((resolve) => {
    rl.question(query, resolve);
  });
}

async function setup() {
  console.log('🎯 Achievement Portfolio Setup\n');

  // Check if .env exists
  if (!existsSync('.env')) {
    console.log('⚙️  Creating .env file...\n');
    const jwtSecret = await question('Enter JWT secret (or press Enter to generate): ');
    const adminUsername = await question('Enter admin username (default: admin): ');
    const adminPassword = await question('Enter admin password: ');

    const envContent = `DATABASE_PATH=/app/data/portfolio.db
PORT=3000
NODE_ENV=production
JWT_SECRET=${jwtSecret || require('crypto').randomBytes(32).toString('hex')}
ADMIN_USERNAME=${adminUsername || 'admin'}
ADMIN_PASSWORD=${adminPassword || 'admin123'}
FRONTEND_URL=http://localhost:5173
`;

    await writeFile('.env', envContent);
    console.log('✅ .env file created\n');
  } else {
    console.log('✅ .env file already exists\n');
  }

  // Connect to database
  const dbPath = process.env.DATABASE_PATH || './data/portfolio.db';
  console.log(`📊 Connecting to database: ${dbPath}`);

  const db = await open({
    filename: dbPath,
    driver: sqlite3.Database
  });

  console.log('✅ Database connected\n');

  // Create tables if they don't exist
  console.log('🔨 Creating tables...');
  await db.exec(`
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
  `);
  console.log('✅ Tables created\n');

  // Seed categories if empty
  const categoryCount = await db.get('SELECT COUNT(*) as count FROM categories');
  if (categoryCount.count === 0) {
    console.log('📁 Seeding default categories...');
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
    console.log('✅ Default categories seeded\n');
  } else {
    console.log('✅ Categories already exist\n');
  }

  // Create admin user if doesn't exist
  const adminUsername = process.env.ADMIN_USERNAME || 'admin';
  const adminPassword = process.env.ADMIN_PASSWORD || 'admin123';

  const existingUser = await db.get('SELECT id FROM users WHERE username = ?', [adminUsername]);

  if (!existingUser) {
    console.log('👤 Creating admin user...');
    const passwordHash = await bcrypt.hash(adminPassword, 10);
    await db.run(
      'INSERT INTO users (username, password_hash) VALUES (?, ?)',
      [adminUsername, passwordHash]
    );
    console.log(`✅ Admin user created: ${adminUsername}\n`);
  } else {
    console.log(`✅ Admin user already exists: ${adminUsername}\n`);
  }

  await db.close();

  console.log('🎉 Setup complete!\n');
  console.log('Next steps:');
  console.log('1. Start the application: podman-compose -f podman/podman-compose.yml up -d');
  console.log('2. Access the frontend: http://localhost:5173');
  console.log('3. Login with your admin credentials\n');

  rl.close();
}

setup().catch(console.error);

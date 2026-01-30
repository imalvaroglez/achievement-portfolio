import { Router } from 'express';

const router = Router();

router.get('/', async (req, res) => {
  try {
    const db = req.app.get('db');
    const { status, category_id, difficulty, search, limit = 50, offset = 0 } = req.query;

    let query = `
      SELECT
        a.*,
        c.name as category_name,
        c.color as category_color,
        c.icon as category_icon
      FROM achievements a
      LEFT JOIN categories c ON a.category_id = c.id
      WHERE 1=1
    `;
    const params = [];

    if (status) {
      query += ' AND a.status = ?';
      params.push(status);
    }

    if (category_id) {
      query += ' AND a.category_id = ?';
      params.push(category_id);
    }

    if (difficulty) {
      query += ' AND a.difficulty = ?';
      params.push(difficulty);
    }

    if (search) {
      query += ' AND (a.title LIKE ? OR a.description LIKE ?)';
      params.push(`%${search}%`, `%${search}%`);
    }

    query += ' ORDER BY a.date_achieved DESC, a.created_at DESC';
    query += ' LIMIT ? OFFSET ?';
    params.push(parseInt(limit), parseInt(offset));

    const achievements = await db.all(query, params);

    res.json({ achievements });
  } catch (error) {
    console.error('Get achievements error:', error);
    res.status(500).json({ error: 'Failed to fetch achievements' });
  }
});

router.get('/:id', async (req, res) => {
  try {
    const db = req.app.get('db');
    const achievement = await db.get(
      `SELECT
        a.*,
        c.name as category_name,
        c.color as category_color,
        c.icon as category_icon
      FROM achievements a
      LEFT JOIN categories c ON a.category_id = c.id
      WHERE a.id = ?`,
      [req.params.id]
    );

    if (!achievement) {
      return res.status(404).json({ error: 'Achievement not found' });
    }

    const milestones = await db.all(
      'SELECT * FROM milestones WHERE achievement_id = ? ORDER BY sort_order',
      [req.params.id]
    );

    res.json({ achievement, milestones });
  } catch (error) {
    console.error('Get achievement error:', error);
    res.status(500).json({ error: 'Failed to fetch achievement' });
  }
});

router.post('/', async (req, res) => {
  try {
    const {
      title,
      description,
      category_id,
      date_achieved,
      difficulty,
      status,
      skills,
      image_url,
      notes
    } = req.body;

    if (!title) {
      return res.status(400).json({ error: 'Title is required' });
    }

    const db = req.app.get('db');

    const result = await db.run(
      `INSERT INTO achievements
        (title, description, category_id, date_achieved, difficulty, status, skills, image_url, notes)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [title, description, category_id, date_achieved, difficulty, status || 'completed', skills, image_url, notes]
    );

    const achievement = await db.get('SELECT * FROM achievements WHERE id = ?', [result.lastID]);

    res.status(201).json({ achievement });
  } catch (error) {
    console.error('Create achievement error:', error);
    res.status(500).json({ error: 'Failed to create achievement' });
  }
});

router.put('/:id', async (req, res) => {
  try {
    const {
      title,
      description,
      category_id,
      date_achieved,
      difficulty,
      status,
      skills,
      image_url,
      notes
    } = req.body;

    if (!title) {
      return res.status(400).json({ error: 'Title is required' });
    }

    const db = req.app.get('db');

    await db.run(
      `UPDATE achievements
       SET title = ?, description = ?, category_id = ?, date_achieved = ?, difficulty = ?,
           status = ?, skills = ?, image_url = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
       WHERE id = ?`,
      [title, description, category_id, date_achieved, difficulty, status, skills, image_url, notes, req.params.id]
    );

    const achievement = await db.get('SELECT * FROM achievements WHERE id = ?', [req.params.id]);

    if (!achievement) {
      return res.status(404).json({ error: 'Achievement not found' });
    }

    res.json({ achievement });
  } catch (error) {
    console.error('Update achievement error:', error);
    res.status(500).json({ error: 'Failed to update achievement' });
  }
});

router.delete('/:id', async (req, res) => {
  try {
    const db = req.app.get('db');
    const result = await db.run('DELETE FROM achievements WHERE id = ?', [req.params.id]);

    if (result.changes === 0) {
      return res.status(404).json({ error: 'Achievement not found' });
    }

    res.json({ message: 'Achievement deleted' });
  } catch (error) {
    console.error('Delete achievement error:', error);
    res.status(500).json({ error: 'Failed to delete achievement' });
  }
});

router.post('/:id/milestones', async (req, res) => {
  try {
    const { title, description, completed_at } = req.body;

    if (!title) {
      return res.status(400).json({ error: 'Title is required' });
    }

    const db = req.app.get('db');

    const result = await db.run(
      'INSERT INTO milestones (achievement_id, title, description, completed_at) VALUES (?, ?, ?, ?)',
      [req.params.id, title, description, completed_at]
    );

    const milestone = await db.get('SELECT * FROM milestones WHERE id = ?', [result.lastID]);

    res.status(201).json({ milestone });
  } catch (error) {
    console.error('Create milestone error:', error);
    res.status(500).json({ error: 'Failed to create milestone' });
  }
});

router.put('/:id/milestones/:milestoneId', async (req, res) => {
  try {
    const { title, description, completed_at } = req.body;

    const db = req.app.get('db');

    await db.run(
      'UPDATE milestones SET title = ?, description = ?, completed_at = ? WHERE id = ? AND achievement_id = ?',
      [title, description, completed_at, req.params.milestoneId, req.params.id]
    );

    const milestone = await db.get('SELECT * FROM milestones WHERE id = ?', [req.params.milestoneId]);

    if (!milestone) {
      return res.status(404).json({ error: 'Milestone not found' });
    }

    res.json({ milestone });
  } catch (error) {
    console.error('Update milestone error:', error);
    res.status(500).json({ error: 'Failed to update milestone' });
  }
});

router.delete('/:id/milestones/:milestoneId', async (req, res) => {
  try {
    const db = req.app.get('db');
    const result = await db.run(
      'DELETE FROM milestones WHERE id = ? AND achievement_id = ?',
      [req.params.milestoneId, req.params.id]
    );

    if (result.changes === 0) {
      return res.status(404).json({ error: 'Milestone not found' });
    }

    res.json({ message: 'Milestone deleted' });
  } catch (error) {
    console.error('Delete milestone error:', error);
    res.status(500).json({ error: 'Failed to delete milestone' });
  }
});

export default router;

import { Router } from 'express';

const router = Router();

router.get('/', async (req, res) => {
  try {
    const db = req.app.get('db');

    const categories = await db.all(
      'SELECT * FROM categories ORDER BY sort_order ASC, name ASC'
    );

    for (const category of categories) {
      const count = await db.get(
        'SELECT COUNT(*) as count FROM achievements WHERE category_id = ?',
        [category.id]
      );
      category.achievement_count = count.count;
    }

    res.json({ categories });
  } catch (error) {
    console.error('Get categories error:', error);
    res.status(500).json({ error: 'Failed to fetch categories' });
  }
});

router.get('/:id', async (req, res) => {
  try {
    const db = req.app.get('db');

    const category = await db.get(
      'SELECT * FROM categories WHERE id = ?',
      [req.params.id]
    );

    if (!category) {
      return res.status(404).json({ error: 'Category not found' });
    }

    const achievements = await db.all(
      'SELECT * FROM achievements WHERE category_id = ? ORDER BY date_achieved DESC',
      [req.params.id]
    );

    res.json({ category, achievements });
  } catch (error) {
    console.error('Get category error:', error);
    res.status(500).json({ error: 'Failed to fetch category' });
  }
});

router.post('/', async (req, res) => {
  try {
    const { name, description, color, icon } = req.body;

    if (!name) {
      return res.status(400).json({ error: 'Name is required' });
    }

    const db = req.app.get('db');

    const result = await db.run(
      'INSERT INTO categories (name, description, color, icon) VALUES (?, ?, ?, ?)',
      [name, description, color || '#3b82f6', icon]
    );

    const category = await db.get('SELECT * FROM categories WHERE id = ?', [result.lastID]);

    res.status(201).json({ category });
  } catch (error) {
    console.error('Create category error:', error);
    res.status(500).json({ error: 'Failed to create category' });
  }
});

router.put('/:id', async (req, res) => {
  try {
    const { name, description, color, icon, sort_order } = req.body;

    if (!name) {
      return res.status(400).json({ error: 'Name is required' });
    }

    const db = req.app.get('db');

    await db.run(
      'UPDATE categories SET name = ?, description = ?, color = ?, icon = ?, sort_order = ? WHERE id = ?',
      [name, description, color, icon, sort_order || 0, req.params.id]
    );

    const category = await db.get('SELECT * FROM categories WHERE id = ?', [req.params.id]);

    if (!category) {
      return res.status(404).json({ error: 'Category not found' });
    }

    res.json({ category });
  } catch (error) {
    console.error('Update category error:', error);
    res.status(500).json({ error: 'Failed to update category' });
  }
});

router.delete('/:id', async (req, res) => {
  try {
    const db = req.app.get('db');

    const count = await db.get(
      'SELECT COUNT(*) as count FROM achievements WHERE category_id = ?',
      [req.params.id]
    );

    if (count.count > 0) {
      return res.status(400).json({ error: 'Cannot delete category with achievements' });
    }

    const result = await db.run('DELETE FROM categories WHERE id = ?', [req.params.id]);

    if (result.changes === 0) {
      return res.status(404).json({ error: 'Category not found' });
    }

    res.json({ message: 'Category deleted' });
  } catch (error) {
    console.error('Delete category error:', error);
    res.status(500).json({ error: 'Failed to delete category' });
  }
});

export default router;

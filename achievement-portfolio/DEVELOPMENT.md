# Achievement Portfolio - Development Guide

This document provides additional details for developers working on the Achievement Portfolio project.

## Development Setup

### Prerequisites
- Node.js v18+
- Podman (optional, for container testing)

### Local Development Without Containers

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your settings
npm install
npm run dev
# Backend runs on http://localhost:3000

# Frontend (new terminal)
cd frontend
cp .env.example .env
# Edit VITE_API_URL if needed
npm install
npm run dev
# Frontend runs on http://localhost:5173
```

## Project Architecture

### Backend (Express.js)
- **server.js**: Main entry point, middleware setup, route registration
- **db/init.js**: SQLite database initialization and schema
- **middleware/auth.js**: JWT authentication middleware
- **routes/auth.js**: Authentication endpoints
- **routes/achievements.js**: Achievement CRUD operations
- **routes/categories.js**: Category CRUD operations

### Frontend (React + Vite)
- **App.jsx**: Main routing and layout
- **contexts/AuthContext.jsx**: Authentication state management
- **utils/api.js**: Axios instance with auth interceptors
- **components/Navbar.jsx**: Navigation component
- **pages/**: Page components

## Database Schema

### Users
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME
);
```

### Categories
```sql
CREATE TABLE categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  color TEXT DEFAULT '#3b82f6',
  icon TEXT,
  sort_order INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Achievements
```sql
CREATE TABLE achievements (
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
```

### Milestones
```sql
CREATE TABLE milestones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  achievement_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  completed_at DATETIME,
  sort_order INTEGER DEFAULT 0,
  FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
);
```

## API Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message"
}
```

## Adding New Features

### Adding a New API Endpoint

1. Create route function in `backend/src/routes/`
2. Register in `backend/src/server.js`
3. Add authentication middleware if needed
4. Add frontend API call in `frontend/src/utils/api.js`
5. Create React component/page

### Adding a New Page

1. Create component in `frontend/src/pages/`
2. Add route in `frontend/src/App.jsx`
3. Update navigation in `frontend/src/components/Navbar.jsx`

## Testing

### Manual Testing Checklist

- [ ] User registration
- [ ] User login
- [ ] Create category
- [ ] Create achievement
- [ ] Add milestone
- [ ] Update achievement status
- [ ] Delete achievement
- [ ] Delete category (empty only)
- [ ] Logout
- [ ] Protected route redirect

### API Testing with curl

```bash
# Login
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Get achievements (requires token)
curl http://localhost:3000/api/achievements \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Create achievement
curl -X POST http://localhost:3000/api/achievements \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "Learn React",
    "description": "Completed React course",
    "category_id": 1,
    "difficulty": "medium",
    "status": "completed"
  }'
```

## Deployment Considerations

### Security
- Change all default secrets
- Use HTTPS in production
- Implement rate limiting (already included)
- Consider adding CSRF protection
- Regular security updates for dependencies

### Performance
- SQLite is suitable for single-user applications
- Consider implementing database indexing for large datasets
- Implement pagination for achievement lists
- Cache static assets (already configured in nginx)

### Backups
- Regular backups of the `data/` directory
- Consider automated backup scripts
- Test restore procedures regularly

## Troubleshooting Development Issues

### Frontend build fails
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Backend fails to start
```bash
cd backend
rm -rf node_modules package-lock.json
npm install
```

### Database locked errors
```bash
# Ensure only one process is accessing the database
# Check for running Node processes
ps aux | grep node
```

### CORS errors
```bash
# Verify FRONTEND_URL in backend .env matches frontend URL
# Check VITE_API_URL in frontend .env matches backend URL
```

## Code Style

### JavaScript/React
- Use ES6+ syntax
- Functional components with hooks
- Named exports for components
- PropTypes or TypeScript for type safety (optional)

### Backend
- Async/await for database operations
- Proper error handling
- Environment variables for configuration
- Clean separation of concerns

## Future Enhancements

Ideas for future improvements:
- [ ] Image upload support
- [ ] Export achievements to PDF
- [ ] Dark mode support
- [ ] Achievement sharing (public links)
- [ ] Timeline view of achievements
- [ ] Statistics and analytics dashboard
- [ ] Multiple user support
- [ ] Email notifications for milestone reminders
- [ ] Import/export functionality
- [ ] Tags system for achievements

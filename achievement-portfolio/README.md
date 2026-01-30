# Achievement Portfolio

A personal achievement portfolio application, containerized with Podman. Track and showcase your accomplishments across categories like career, education, skills, and personal growth.

## 🌟 Features

- **Achievement Tracking**: Log and categorize your personal and professional accomplishments
- **Milestone Progress**: Break down achievements into smaller, trackable milestones
- **Category Organization**: Organize achievements by custom categories with color coding
- **Difficulty Levels**: Mark achievements by difficulty (easy, medium, hard, expert)
- **Status Tracking**: Track progress (pending, in-progress, completed)
- **Secure Authentication**: JWT-based authentication with encrypted passwords
- **Privacy First**: All data stored locally in SQLite - no external dependencies

## 🛠️ Tech Stack

- **Backend**: Node.js + Express.js
- **Frontend**: React + Vite + Tailwind CSS
- **Database**: SQLite (embedded, no separate database container needed)
- **Containerization**: Podman
- **Orchestration**: Podman Compose

## 🔒 Security Notes

⚠️ **This application contains personal information.**

- All data is stored locally in the SQLite database
- No external API calls to third-party services
- Environment variables must be configured before running
- **Change default credentials on first run!**

## 📋 Prerequisites

- **Podman** (v3.0+): [Installation Guide](https://podman.io/getting-started/installation)
- **Podman Compose**: `pip install podman-compose` or `pip3 install podman-compose`
- **Node.js v18+**: For local development only

## 🚀 Quick Start

### Option 1: Using the Setup Script (Recommended)

```bash
# Clone the repository
git clone https://github.com/imalvaroglez/achievement-portfolio.git
cd achievement-portfolio

# Run the setup script
./setup.sh
```

The script will:
1. Check for Podman and podman-compose
2. Guide you through environment configuration
3. Create admin credentials
4. Build and start all containers

### Option 2: Manual Setup

#### 1. Configure Environment

Create `.env` file in `backend/`:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your values:

```env
# Database
DATABASE_PATH=/app/data/portfolio.db

# Server
PORT=3000
NODE_ENV=production

# Authentication (CHANGE THESE!)
JWT_SECRET=generate-a-secure-random-string-32-chars-or-more
ADMIN_USERNAME=your-username
ADMIN_PASSWORD=your-secure-password

# CORS
FRONTEND_URL=http://localhost:5173
```

Generate a secure JWT secret:
```bash
openssl rand -hex 32
```

#### 2. Build and Start

```bash
# Build and start all containers
podman-compose -f podman/podman-compose.yml up -d --build

# View logs
podman-compose -f podman/podman-compose.yml logs -f

# Check container status
podman ps
```

## 🌐 Access

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:3000/api
- **Health Check**: http://localhost:3000/api/health

## 📖 Usage

### First Login

1. Open http://localhost:5173
2. Use your admin credentials to log in
3. Default categories will be created automatically:
   - 📁 Career
   - 🎓 Education
   - 👤 Personal
   - 💻 Skills
   - 📂 Projects

### Adding Achievements

1. Click "New Achievement" on the dashboard
2. Fill in the details:
   - Title and description
   - Category
   - Date achieved
   - Difficulty level
   - Skills (comma-separated)
   - Notes

3. Add milestones to track progress
4. Save and view in your dashboard

### Managing Categories

1. Navigate to "Categories" from the navbar
2. Create new categories with custom colors and icons
3. Edit or delete categories (empty only)

## 🔧 Development

### Local Development

```bash
# Backend
cd backend
npm install
npm run dev

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Project Structure

```
achievement-portfolio/
├── backend/
│   ├── src/
│   │   ├── routes/        # API routes
│   │   ├── middleware/    # Auth middleware
│   │   ├── db/           # Database initialization
│   │   └── server.js     # Entry point
│   ├── Containerfile     # Podman image definition
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── pages/        # React pages
│   │   ├── components/   # Reusable components
│   │   ├── contexts/     # React contexts (Auth)
│   │   └── utils/        # API utilities
│   ├── Containerfile     # Podman image definition
│   └── package.json
├── podman/
│   └── podman-compose.yml
├── data/                 # Persistent database volume
└── setup.sh             # Quick start script
```

## 🗄️ Data Persistence

Database files are persisted in the `data/` directory via Podman volumes. This means:

- Data survives container restarts
- Backups are as simple as copying the `data/` directory
- No separate database server required

### Backup Your Data

```bash
# Stop containers
podman-compose -f podman/podman-compose.yml down

# Backup data directory
tar -czf achievement-portfolio-backup-$(date +%Y%m%d).tar.gz data/

# Start containers
podman-compose -f podman/podman-compose.yml up -d
```

### Restore Data

```bash
# Stop containers
podman-compose -f podman/podman-compose.yml down

# Extract backup
tar -xzf achievement-portfolio-backup-YYYYMMDD.tar.gz

# Start containers
podman-compose -f podman/podman-compose.yml up -d
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Register new user
- `GET /api/auth/me` - Get current user

### Achievements
- `GET /api/achievements` - List all achievements
- `GET /api/achievements/:id` - Get single achievement
- `POST /api/achievements` - Create achievement
- `PUT /api/achievements/:id` - Update achievement
- `DELETE /api/achievements/:id` - Delete achievement
- `POST /api/achievements/:id/milestones` - Add milestone
- `PUT /api/achievements/:id/milestones/:milestoneId` - Update milestone
- `DELETE /api/achievements/:id/milestones/:milestoneId` - Delete milestone

### Categories
- `GET /api/categories` - List all categories
- `GET /api/categories/:id` - Get single category with achievements
- `POST /api/categories` - Create category
- `PUT /api/categories/:id` - Update category
- `DELETE /api/categories/:id` - Delete category (empty only)

## 🛑 Stopping the Application

```bash
# Stop containers
podman-compose -f podman/podman-compose.yml down

# Stop and remove volumes (deletes all data!)
podman-compose -f podman/podman-compose.yml down -v
```

## 🐛 Troubleshooting

### Container won't start

Check logs:
```bash
podman-compose -f podman/podman-compose.yml logs backend
podman-compose -f podman/podman-compose.yml logs frontend
```

### Port already in use

Change ports in `podman/podman-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "3001:3000"  # Change 3000 to 3001
  frontend:
    ports:
      - "5174:80"    # Change 5173 to 5174
```

### Database errors

Ensure the data directory exists:
```bash
mkdir -p data
```

### Login issues

Reset admin password:
```bash
# Enter backend container
podman exec -it achievement-portfolio-backend sh

# Run setup script
node src/setup.js
```

## 📝 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_PATH` | SQLite database file path | `/app/data/portfolio.db` | No |
| `PORT` | Backend server port | `3000` | No |
| `NODE_ENV` | Environment mode | `production` | No |
| `JWT_SECRET` | Secret for JWT tokens | **CHANGE THIS!** | Yes |
| `ADMIN_USERNAME` | Admin username | `admin` | Yes |
| `ADMIN_PASSWORD` | Admin password | **CHANGE THIS!** | Yes |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:5173` | No |
| `VITE_API_URL` | Backend API URL | `http://localhost:3000` | No |

## 📄 License

MIT

## 🤝 Contributing

This is a personal project, but feel free to fork and customize!

## 📧 Support

For issues or questions, please open an issue on GitHub.

---

Built with ❤️ using Podman and modern web technologies.

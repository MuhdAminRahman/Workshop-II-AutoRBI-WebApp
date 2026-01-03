# Workshop-II-AutoRBI-WebApp

RBI (Risk-Based Inspection) Data Extraction & Reporting Platform

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (locally or via Render)
- Git

### Setup Backend
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Initialize database
alembic upgrade head

# Run server
uvicorn app.main:app --reload
```

Backend runs at: `http://localhost:8000`

### Setup Frontend
```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Run development server
npm run dev
```

Frontend runs at: `http://localhost:5173`

## Project Structure

- **backend/**: FastAPI application
  - `app/`: Main application code (models, services, routes)
  - `migrations/`: Alembic database migrations
  - `tests/`: Unit & integration tests
  - `requirements.txt`: Python dependencies

- **frontend/**: React/TypeScript application
  - `src/`: React components, hooks, services
  - `public/`: Static assets
  - `package.json`: Node dependencies

## Features

### MVP (2-Week Sprint)
- ✅ User authentication (login/register)
- ✅ Data extraction from PDFs using Claude AI
- ✅ Real-time progress tracking (WebSocket)
- ✅ Excel template management & auto-fill
- ✅ PowerPoint report generation
- ✅ Analytics dashboard with health scores
- ✅ File versioning & download

### Future Features (v1.1+)
- [ ] User management UI
- [ ] Advanced filtering & search
- [ ] Email notifications
- [ ] API documentation (Swagger)
- [ ] Mobile app

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **Auth**: JWT tokens
- **LLM**: Claude API (Anthropic)
- **Real-time**: WebSocket
- **File Storage**: Cloudinary
- **Deployment**: Render

### Frontend
- **Framework**: React 18 + TypeScript
- **Router**: React Router v6
- **State**: Zustand + TanStack Query
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Deployment**: Render

## Development

See [DEVELOPMENT.md](./DEVELOPMENT.md) for detailed development guide.

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Code Style

- **Python**: PEP 8 (enforced with black, flake8)
- **JavaScript/TypeScript**: ESLint + Prettier
- **Commit Messages**: Conventional Commits

## Deployment

See [SETUP.md](./SETUP.md) for production deployment guide.

### Quick Deploy to Render
```bash
# Backend
1. Create web service on Render
2. Connect GitHub repository
3. Set environment variables
4. Deploy

# Frontend
1. Create static site on Render
2. Connect GitHub repository
3. Build command: npm run build
4. Publish directory: dist
5. Deploy
```

## Environment Variables

See `.env.example` files in both `backend/` and `frontend/` directories.

**Important**: Never commit actual `.env` files. Use `.env.example` as template.

## API Documentation

When backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

See [API Contract](./DEVELOPMENT.md#api-contract) for detailed endpoint documentation.

## Contributing

1. Create a branch for your feature: `git checkout -b feature/feature-name`
2. Make changes and commit: `git commit -m "feat: add feature"`
3. Push to branch: `git push origin feature/feature-name`
4. Create Pull Request

### Branch Naming
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Production hotfixes
- `docs/` - Documentation only

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running
- Verify `.env` DATABASE_URL is correct
- Run `alembic upgrade head`

### Frontend shows blank page
- Check browser console for errors
- Verify VITE_API_URL in `.env.local`
- Clear node_modules: `rm -rf node_modules && npm install`

### WebSocket connection fails
- Check backend WebSocket URL in frontend `.env.local`
- Verify backend is running on expected port
- Check CORS settings in backend `main.py`

## Support

For issues or questions:
1. Check existing GitHub issues
2. Create new issue with: steps to reproduce, expected behavior, actual behavior
3. Include version numbers and environment details

## License

MIT License - See LICENSE file for details

## Team

- **Developer**: You
- **Start Date**: January 2024
- **Timeline**: 2-week MVP sprint

## Timeline

| Week | Focus |
|------|-------|
| Week 1 | Backend: Auth, DB, Core Services, Extraction, WebSocket |
| Week 2 | Frontend: Auth, Dashboard, Extraction Wizard, Reports, Analytics |
| Week 3 | Deployment, Testing, Bug Fixes, Documentation |

## Roadmap

### MVP (Current)
- Basic extraction workflow
- Simple analytics
- File versioning

### v1.1 (Month 2)
- Advanced filtering
- User management
- Email notifications

### v1.2 (Month 3)
- Mobile app
- API integrations
- Performance optimization

---

**Last Updated**: January 2024
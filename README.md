# ClockIt - Professional Time Tracker

[![CI](https://github.com/JollyGreenFrogs/clockit/actions/workflows/ci.yml/badge.svg)](https://github.com/JollyGreenFrogs/clockit/actions/workflows/ci.yml)

A modern, cloud-ready time tracking application built with FastAPI and React. Track time spent on projects and generate invoices.

## ✨ Features

- ⏱️ **Time Tracking**: Start/pause timers with automatic single-timer management
- 📋 **Task Management**: Organize tasks with categories and descriptions
- 💰 **Multi-Currency Support**: Invoice generation with 100+ currencies
- 📄 **Invoice Generation**: Professional invoices with export tracking
- 🏗️ **Cloud-Ready**: Docker and Kubernetes deployment support
- 🛡️ **Production Ready**: Health checks, structured logging, and security best practices
- 💾 **Flexible Storage**: File-based (development) or PostgreSQL (production)

## 🛡️ Security Notice

**Important:** A comprehensive security audit has been completed. Before deploying to production, please review:

- 📋 [Security Audit README](SECURITY_AUDIT_README.md) - Start here
- 🚀 [Quick Start Security Guide](SECURITY_QUICK_START.md) - Fix critical issues in 1 hour
- 👔 [Executive Summary](SECURITY_EXECUTIVE_SUMMARY.md) - For stakeholders

**Current Security Score:** 5.6/10 (MODERATE RISK)  
**Status:** Not production-ready without critical fixes

See [SECURITY_AUDIT_SUMMARY.txt](SECURITY_AUDIT_SUMMARY.txt) for a quick overview.

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd clockit

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

Access the application at http://localhost:8000

### Docker Development

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or build and run manually
docker build -t clockit .
docker run -p 8000:8000 clockit
```

### Production Deployment

For production deployment to cloud platforms, see [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive guides covering:
- Kubernetes clusters
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances
- Docker Swarm

## 📁 Project Structure

```
clockit/
├── src/                    # Application source code
│   ├── business/          # Business logic managers
│   ├── config.py          # Configuration management
│   ├── main.py           # FastAPI application
│   └── ...
├── k8s/                   # Kubernetes deployment manifests
├── tests/                 # Test suite
├── Dockerfile            # Multi-stage container build
├── docker-compose.yml    # Development environment
├── DEPLOYMENT.md         # Cloud deployment guide
└── .env.example          # Environment configuration template
```

## ⚙️ Configuration

The application uses environment-based configuration. Copy `.env.example` to `.env` and customize:

```bash
# Application settings
ENVIRONMENT=development
DATABASE_TYPE=file
CLOCKIT_DATA_DIR=./clockit_data

# For production with PostgreSQL
DATABASE_TYPE=postgres
POSTGRES_HOST=your-db-host
POSTGRES_PASSWORD=your-password
SECRET_KEY=your-secret-key
```

## 🔌 API Endpoints

### Core Operations
- `GET /` - Web interface
- `GET /health` - Health check for monitoring
- `GET /tasks` - List all tasks
- `POST /tasks` - Create new task
- `POST /tasks/{id}/time` - Add time entry

### Invoice & Reporting
- `GET /invoice/preview` - Preview invoice
- `POST /invoice/generate` - Generate and export invoice
- `GET /categories` - Get task categories
- `GET /rates` - Get billing rates

### System
- `GET /system/data-location` - Data storage info
- `POST /system/shutdown` - Graceful shutdown

## 🧪 Testing

### Quick Start

```bash
# Setup environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/
```

### Detailed Testing Guide

For comprehensive testing instructions including:
- Environment setup
- Running specific tests
- Troubleshooting common issues
- Frontend testing
- CI/CD information

See **[TESTING.md](TESTING.md)** for the complete guide.

### CI/CD Pipeline
- ✅ **Backend testing**: pytest with Python 3.12
- ✅ **Frontend testing**: Vitest + Playwright E2E
- ✅ **Code quality**: black, isort, flake8, ESLint
- ✅ **Multi-browser testing**: Chromium, Firefox, WebKit
- ✅ **WSL compatible**: All tests run in headless mode

## 🏗️ Cloud Deployment

ClockIt is designed for cloud deployment with:

- **Docker containerization** with multi-stage builds
- **Kubernetes manifests** with scaling and monitoring
- **Health checks** for container orchestration
- **Environment-based configuration** for different deployment stages
- **Database abstraction** supporting both file and PostgreSQL storage
- **Security best practices** with non-root containers and secret management

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For deployment issues and questions:
1. Check the health endpoint: `/health`
2. Review application logs
3. Consult [DEPLOYMENT.md](DEPLOYMENT.md) for troubleshooting
4. Open an issue on GitHub

Or use uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

2. Open your web browser and navigate to:
   - Main application: http://localhost:8000
   - API documentation: http://localhost:8000/docs
   - Alternative API docs: http://localhost:8000/redoc

## Usage

### Web Interface

- Open http://localhost:8000 in your browser
- Create new tasks by entering a name and optional description
- Click "Start" to begin timing a task
- Click "Pause" to stop the current timer
- View total time spent on each task
- Delete tasks when no longer needed
- **Add Tasks**: Use the "Add Task" button to create new tasks
### API Endpoints

- `POST /tasks` - Create a new task
- `GET /tasks` - List all tasks with current status
- `GET /tasks/{task_id}` - Get specific task details
- `POST /tasks/{task_id}/start` - Start timer for a task
- `POST /tasks/{task_id}/pause` - Pause timer for a task
- `DELETE /tasks/{task_id}` - Delete a task
- `GET /tasks/{task_id}/report` - Get detailed time report for a task

### Example API Usage

Create a task:
```bash
curl -X POST "http://localhost:8000/tasks" \
     -H "Content-Type: application/json" \
     -d '{"name": "Fix login bug", "description": "Resolve authentication issue"}'
```

Start timer:
```bash
curl -X POST "http://localhost:8000/tasks/{task_id}/start"
```

Pause timer:
```bash
curl -X POST "http://localhost:8000/tasks/{task_id}/pause"
```

## Features Explained

### Timer Management
- Only one timer can run at a time
- Starting a new timer automatically pauses any currently running timer
- Time is tracked in sessions and accumulated for total time

### 2-Hour Alert
- When a timer runs continuously for 2 hours, an alert is printed to the console
- In a production environment, this could be enhanced to send email/push notifications

### Data Persistence
- All task data is saved to `tasks_data.json`
- Data persists between application restarts
- Time entries are stored as separate sessions

### Time Format
- All times are displayed in HH:MM format
- Seconds are tracked internally for accuracy but not displayed

## File Structure

```
clockit/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── tasks_data.json     # Auto-generated data file (after first use)
```

## Customization

You can easily modify the application:
- Change the alert time by modifying the sleep duration in `schedule_alert()`
- Add new fields to tasks by updating the `TaskCreate` and `TaskResponse` models
- Integrate with a database by replacing the JSON file storage
- Add authentication for multi-user support
- Enhance the UI with a modern frontend framework

## Notes

- The application runs on port 8000 by default
- Data is stored locally in JSON format
- The web interface auto-refreshes every 30 seconds to show updated times
- All times are stored in the server's local timezone

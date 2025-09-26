# ClockIt - Time Tracker

A simple time tracking application built with FastAPI that allows you to track time spent on projects, tasks, features, and issues.

## Features

- ✅ Create tasks/features/issues with names and descriptions
- ⏱️ Start and pause timers for different tasks
- 🔄 Only one timer can run at a time (automatically pauses others)
- ⏰ 2-hour alert reminder when a timer has been running continuously
- 📊 View total time spent in HH:MM format
- 💾 Persistent data storage (JSON file)
- 🗑️ Delete tasks when no longer needed
- 📈 Detailed time reports for each task
- 📥 **NEW**: Import tasks from Microsoft Planner
- 🔄 **NEW**: Sync with Microsoft 365 Planner tasks

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the FastAPI server:
```bash
python main.py
```

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
- **Import from MS Planner**: Click "📥 Import from MS Planner" to sync tasks
- **Setup Planner**: Use "🔧 Setup Config" to configure Microsoft Planner integration

### Microsoft Planner Integration

ClockIt can import tasks directly from Microsoft Planner:

1. **Setup**: Click "🔧 Setup Config" in the web interface
2. **Configure**: Follow the setup guide in `PLANNER_SETUP.md`
3. **Import**: Click "📥 Import from MS Planner" to sync your tasks
4. **Track**: Start timing any imported task just like manually created ones

For detailed setup instructions, see [PLANNER_SETUP.md](PLANNER_SETUP.md).

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

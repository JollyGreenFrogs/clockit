import { useState, useEffect } from 'react'

function EnhancedStopwatch({ onTimeUpdate, tasks, onSaveToTask }) {
  const [time, setTime] = useState(0)
  const [isRunning, setIsRunning] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [startTime, setStartTime] = useState(null)
  const [breakMinutes, setBreakMinutes] = useState(0)
  const [showBreakSection, setShowBreakSection] = useState(false)
  const [selectedTask, setSelectedTask] = useState('')
  const [taskForTiming, setTaskForTiming] = useState('')

  useEffect(() => {
    let interval = null
    if (isRunning && !isPaused) {
      interval = setInterval(() => {
        setTime(Date.now() - startTime)
      }, 10)
    }
    return () => clearInterval(interval)
  }, [isRunning, isPaused, startTime])

  useEffect(() => {
    if (onTimeUpdate) {
      // Calculate time with break deduction
      const breakTime = breakMinutes * 60 * 1000
      const finalTime = Math.max(0, time - breakTime)
      onTimeUpdate(finalTime)
    }
  }, [time, breakMinutes, onTimeUpdate])

  const startTimer = () => {
    if (isPaused) {
      // Resume from pause
      setStartTime(Date.now() - time)
      setIsPaused(false)
    } else {
      // Fresh start
      setStartTime(Date.now())
      setTime(0)
      setBreakMinutes(0)
      setShowBreakSection(false)
    }
    setIsRunning(true)
  }

  const pauseTimer = () => {
    setIsPaused(true)
  }

  const stopTimer = () => {
    setIsRunning(false)
    setIsPaused(false)
    setShowBreakSection(true)
  }

  const resetTimer = () => {
    setTime(0)
    setIsRunning(false)
    setIsPaused(false)
    setStartTime(null)
    setBreakMinutes(0)
    setShowBreakSection(false)
    setTaskForTiming('')
  }

  const saveTimeToSelectedTask = () => {
    if (!selectedTask || !time) return
    
    const breakTime = breakMinutes * 60 * 1000
    const finalTime = Math.max(0, time - breakTime)
    
    if (onSaveToTask) {
      onSaveToTask(selectedTask, finalTime)
      resetTimer()
    }
  }

  const formatTime = (time) => {
    const hours = Math.floor(time / 3600000)
    const minutes = Math.floor((time % 3600000) / 60000)
    const seconds = Math.floor((time % 60000) / 1000)

    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  }

  const getDisplayClass = () => {
    if (isRunning && !isPaused) return 'timer-display running'
    if (isPaused) return 'timer-display paused'
    return 'timer-display'
  }

  const getFinalTime = () => {
    const breakTime = breakMinutes * 60 * 1000
    return Math.max(0, time - breakTime)
  }

  const taskList = Object.keys(tasks || {})

  return (
    <div className="stopwatch-widget">
      {/* Task Selection for Timing */}
      {!isRunning && !isPaused && taskList.length > 0 && (
        <div className="task-selection-section">
          <div className="form-row">
            <label>Working on:</label>
            <select 
              value={taskForTiming}
              onChange={(e) => setTaskForTiming(e.target.value)}
            >
              <option value="">Select task (optional)</option>
              {taskList.map(taskName => (
                <option key={taskName} value={taskName}>{taskName}</option>
              ))}
            </select>
          </div>
          {taskForTiming && (
            <div className="selected-task-info">
              📋 Timing: <strong>{taskForTiming}</strong>
            </div>
          )}
        </div>
      )}

      {/* Timer Display */}
      <div className="stopwatch-display">
        <div className={getDisplayClass()}>
          {formatTime(time)}
        </div>
        {taskForTiming && (isRunning || isPaused) && (
          <div className="timing-task-display">
            📋 Working on: <strong>{taskForTiming}</strong>
          </div>
        )}
        {breakMinutes > 0 && (
          <div style={{ fontSize: '0.9em', color: '#6c757d', marginBottom: '10px' }}>
            Break: {breakMinutes} min • Final: {formatTime(getFinalTime())}
          </div>
        )}
        <div className="timer-controls">
          {!isRunning ? (
            <button onClick={startTimer} className="btn btn-success">
              ▶️ Start
            </button>
          ) : !isPaused ? (
            <button onClick={pauseTimer} className="btn btn-warning">
              ⏸️ Pause
            </button>
          ) : (
            <button onClick={startTimer} className="btn btn-success">
              ▶️ Resume
            </button>
          )}
          <button 
            onClick={stopTimer} 
            disabled={!isRunning && !isPaused} 
            className="btn btn-danger"
          >
            ⏹️ Stop
          </button>
          <button onClick={resetTimer} className="btn btn-secondary">
            🔄 Reset
          </button>
        </div>
      </div>

      {/* Break Time Section */}
      {showBreakSection && (
        <div className="break-section">
          <div className="form-row">
            <label>Break time to subtract (minutes):</label>
            <input
              type="number"
              value={breakMinutes}
              onChange={(e) => setBreakMinutes(parseInt(e.target.value) || 0)}
              min="0"
              placeholder="e.g., 15"
            />
          </div>
          <div style={{ fontSize: '0.9em', color: '#6c757d', marginTop: '10px' }}>
            Total time: {formatTime(time)} → Final time: {formatTime(getFinalTime())}
          </div>
        </div>
      )}

      {/* Save Time to Task */}
      {(time > 0 && !isRunning) && (
        <div className="save-time-section">
          <h4>Save Time to Task</h4>
          <div className="save-time">
            <select 
              value={selectedTask}
              onChange={(e) => setSelectedTask(e.target.value)}
            >
              <option value="">Select task to save time to</option>
              {taskList.map(taskName => (
                <option key={taskName} value={taskName}>{taskName}</option>
              ))}
            </select>
            <button 
              onClick={saveTimeToSelectedTask} 
              disabled={!selectedTask} 
              className="btn btn-success"
            >
              💾 Save Time ({formatTime(getFinalTime())})
            </button>
          </div>
          {taskForTiming && taskForTiming !== selectedTask && (
            <button 
              onClick={() => setSelectedTask(taskForTiming)}
              className="btn btn-secondary"
              style={{ marginTop: '10px' }}
            >
              💾 Save to "{taskForTiming}" (timed task)
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default EnhancedStopwatch
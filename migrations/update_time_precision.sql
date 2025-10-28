-- Migration to update time precision in database
-- Convert Float columns to DECIMAL(10,6) for 1-second precision

-- Update tasks table
ALTER TABLE tasks 
ALTER COLUMN time_spent TYPE DECIMAL(10,6);

-- Update time_entries table  
ALTER TABLE time_entries
ALTER COLUMN duration TYPE DECIMAL(10,6);

-- Update any existing data to ensure proper precision
UPDATE tasks SET time_spent = ROUND(time_spent::DECIMAL, 6) WHERE time_spent IS NOT NULL;
UPDATE time_entries SET duration = ROUND(duration::DECIMAL, 6) WHERE duration IS NOT NULL;
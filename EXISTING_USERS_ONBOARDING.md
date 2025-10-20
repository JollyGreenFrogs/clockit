# Existing Users Onboarding Guide

## Overview

The ClockIt application now requires all users to complete an onboarding process to set up mandatory task categories. This ensures proper invoice generation with categorized tasks.

## How Existing Users Are Handled

### Database Migration

When you upgrade to this version, a database migration automatically:

1. **Adds onboarding fields** to existing user records:
   - `onboarding_completed`: Set to `FALSE` by default for existing users
   - `default_category`: Set to `NULL` by default

2. **Preserves existing data**: All existing tasks, time entries, and user data remain unchanged

### User Experience for Existing Users

#### On Next Login:
1. **Automatic redirect**: Users will be redirected to the onboarding page instead of the dashboard
2. **Onboarding prompt**: A friendly interface explains the new category system
3. **Category setup**: Users must:
   - Set a default category for new tasks
   - Create one or more categories for organizing their work

#### During Transition Period:
- **Task creation still works** if users provide a category manually
- **API validation prevents** tasks without categories
- **Frontend shows onboarding prompt** until completed

## API Endpoints for Existing Users

### Check Onboarding Status
```bash
GET /onboarding/status
# Response for existing users (before onboarding):
{
  "onboarding_completed": false,
  "default_category": null,
  "needs_onboarding": true
}
```

### Complete Onboarding
```bash
POST /onboarding/complete
{
  "default_category": "Development",
  "categories": ["Development", "Testing", "Documentation", "Admin"]
}
# Response:
{
  "message": "Onboarding completed successfully",
  "default_category": "Development",
  "categories_created": 4
}
```

### Task Creation Validation
```bash
# ❌ This will fail (no category):
POST /tasks
{
  "name": "My Task",
  "description": "Task description"
}
# Response: 422 Validation Error - Field required: category

# ✅ This will work (with category):
POST /tasks
{
  "name": "My Task", 
  "description": "Task description",
  "category": "Development"
}
```

## Migration Process

### Automatic Migration
Run the migration script to add onboarding fields:

```bash
cd scripts/
python migrate_onboarding.py
```

### Manual Database Updates (if needed)
```sql
-- Add onboarding fields to users table
ALTER TABLE users ADD COLUMN onboarding_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN default_category VARCHAR(100) NULL;
```

## Benefits for Existing Users

1. **Better Organization**: Categories help organize tasks for cleaner invoices
2. **Improved Invoicing**: Invoice generation groups tasks by category automatically
3. **Default Settings**: Set preferred category once, use for all new tasks
4. **Backward Compatibility**: Existing tasks continue to work normally

## Support

If existing users experience any issues:

1. **Check onboarding status**: Use the `/onboarding/status` endpoint
2. **Complete onboarding**: Use the frontend onboarding flow
3. **Manual category assignment**: Tasks can be created with manual category specification
4. **Database verification**: Ensure migration completed successfully

## Example User Flow

```
1. Existing user logs in
   ↓
2. System checks: onboarding_completed = false
   ↓
3. Redirect to onboarding page
   ↓
4. User sets default category: "Development"
   ↓ 
5. User creates categories: ["Development", "Testing", "Admin"]
   ↓
6. Onboarding completed
   ↓
7. User redirected to dashboard
   ↓
8. All new tasks use "Development" as default category
   ↓
9. Invoice generation works with proper categorization
```

This ensures a smooth transition for existing users while maintaining data integrity and improving the overall user experience.
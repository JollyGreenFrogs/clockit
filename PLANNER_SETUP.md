# Microsoft Planner Integration Setup Guide

This guide will help you set up Microsoft Planner integration with ClockIt to automatically import your Planner tasks.

## Prerequisites

- Microsoft 365 account with access to Microsoft Planner
- Azure AD admin permissions (or someone who can help with app registration)
- Access to Azure Portal (https://portal.azure.com)

## Step 1: Register Application in Azure AD

1. **Go to Azure Portal**
   - Navigate to https://portal.azure.com
   - Sign in with your Microsoft 365 admin account

2. **Register a New Application**
   - Go to "Azure Active Directory" > "App registrations"
   - Click "New registration"
   - Fill in the following:
     - **Name**: `ClockIt Time Tracker`
     - **Supported account types**: `Accounts in this organizational directory only`
     - **Redirect URI**: Leave blank for now
   - Click "Register"

3. **Note Your Application Details**
   - After registration, note down:
     - **Application (client) ID**
     - **Directory (tenant) ID**

## Step 2: Create Client Secret

1. **Generate Secret**
   - In your app registration, go to "Certificates & secrets"
   - Click "New client secret"
   - Add a description: `ClockIt Integration`
   - Choose expiration: `24 months` (recommended)
   - Click "Add"

2. **Copy the Secret Value**
   - **IMPORTANT**: Copy the secret value immediately and store it securely
   - You won't be able to see it again after you navigate away

## Step 3: Configure API Permissions

1. **Add Microsoft Graph Permissions**
   - Go to "API permissions"
   - Click "Add a permission"
   - Select "Microsoft Graph"
   - Choose "Application permissions"
   - Add the following permissions:
     - `Tasks.Read` - Read tasks in all task lists
     - `Group.Read.All` - Read all groups (needed for Planner access)

2. **Grant Admin Consent**
   - Click "Grant admin consent for [Your Organization]"
   - Confirm the consent

## Step 4: Configure ClockIt

### Option 1: Using Configuration File (Recommended)

1. **Run Setup Command**
   - In ClockIt web interface, click "🔧 Setup Config"
   - This creates `planner_config_sample.json`

2. **Create Configuration File**
   - Copy `planner_config_sample.json` to `planner_config.json`
   - Update the values:
   ```json
   {
     "tenant_id": "your-tenant-id-from-step-1",
     "client_id": "your-client-id-from-step-1",
     "client_secret": "your-client-secret-from-step-2"
   }
   ```

### Option 2: Using Environment Variables

Set the following environment variables:
```bash
export MS_TENANT_ID="your-tenant-id"
export MS_CLIENT_ID="your-client-id"
export MS_CLIENT_SECRET="your-client-secret"
```

## Step 5: Test the Integration

1. **Check Configuration**
   - In ClockIt, click "⚙️ Check Config"
   - Verify all items show ✅

2. **Import Tasks**
   - Click "📥 Import from MS Planner"
   - If successful, you'll see your Planner tasks imported
   - Each task will include:
     - Plan name
     - Bucket name
     - Progress percentage
     - Due date (if set)

## How It Works

### What Gets Imported
- ✅ Active tasks (not 100% complete)
- ✅ Task title and description
- ✅ Plan and bucket information
- ✅ Progress and due date
- ❌ Completed tasks are skipped
- ❌ Duplicate imports are prevented

### Task Format
Imported tasks will have descriptions like:
```
Plan: Marketing Campaign
Bucket: Content Creation
Description: Create blog post about new features
Progress: 25%
Due: 2025-08-01
```

### Sync Behavior
- Import only brings in new tasks
- Existing tasks (already imported) are skipped
- No automatic sync - manual import each time
- Original Planner tasks are not modified

## Troubleshooting

### Common Issues

**Authentication Failed**
- Verify tenant ID, client ID, and client secret
- Ensure admin consent was granted
- Check that the app registration is in the correct tenant

**No Tasks Imported**
- Verify you have active (incomplete) tasks in Planner
- Check that the user has access to the plans
- Ensure API permissions are correctly configured

**Permission Errors**
- Verify `Tasks.Read` and `Group.Read.All` permissions are granted
- Ensure admin consent was provided
- Check that permissions are "Application permissions" not "Delegated"

### API Endpoints

You can also use the API directly:

```bash
# Check configuration
curl http://localhost:8000/planner/config

# Setup sample config
curl -X POST http://localhost:8000/planner/setup

# Sync tasks
curl -X POST http://localhost:8000/planner/sync
```

## Security Considerations

- Store credentials securely (use environment variables in production)
- Regularly rotate client secrets
- Limit API permissions to minimum required
- Monitor app usage in Azure AD logs

## Advanced Usage

### Filtering Tasks
Currently imports all incomplete tasks. To customize:
1. Modify `ms_planner_integration.py`
2. Adjust the filter logic in `get_plan_tasks()`
3. Add custom filtering criteria

### Automatic Sync
To enable automatic sync:
1. Set up a scheduled task or cron job
2. Call the `/planner/sync` endpoint periodically
3. Consider rate limiting and error handling

### Multiple Tenants
For multi-tenant scenarios:
1. Register the app as multi-tenant
2. Implement user-specific authentication flow
3. Store credentials per user/tenant

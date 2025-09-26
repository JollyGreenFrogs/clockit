"""
Microsoft Planner Integration for ClockIt
This module handles authentication and task retrieval from Microsoft Planner via Microsoft Graph API
"""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

@dataclass
class PlannerTask:
    id: str
    title: str
    description: str
    plan_id: str
    plan_title: str
    bucket_name: str
    priority: int
    percent_complete: int
    created_date: datetime
    due_date: Optional[datetime] = None

class MSPlannerClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://graph.microsoft.com/v1.0"
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Microsoft Graph using client credentials flow
        This requires app registration in Azure AD with appropriate permissions
        """
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'client_id': self.client_id,
            'scope': 'https://graph.microsoft.com/.default',
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Authentication failed: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    async def get_all_group_plans(self) -> List[Dict]:
        """Get all plans from all groups (for application permissions)"""
        if not self.access_token:
            raise Exception("Not authenticated. Call authenticate() first.")

        # Get all groups
        groups_url = f"{self.base_url}/groups"
        try:
            groups_response = requests.get(groups_url, headers=self._get_headers())
            groups_response.raise_for_status()
            groups_data = groups_response.json()
            plans = []
            for group in groups_data.get('value', []):
                group_id = group['id']
                # Get plans for this group
                plans_url = f"{self.base_url}/groups/{group_id}/planner/plans"
                plans_response = requests.get(plans_url, headers=self._get_headers())
                if plans_response.status_code == 200:
                    plans_data = plans_response.json()
                    for plan in plans_data.get('value', []):
                        plan['group_id'] = group_id
                        plans.append(plan)
            return plans
        except requests.exceptions.RequestException as e:
            print(f"Failed to get group plans: {e}")
            return []
    
    async def get_plan_tasks(self, plan_id: str) -> List[PlannerTask]:
        """Get all tasks from a specific plan"""
        if not self.access_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        # Get tasks
        tasks_url = f"{self.base_url}/planner/plans/{plan_id}/tasks"
        buckets_url = f"{self.base_url}/planner/plans/{plan_id}/buckets"
        plan_url = f"{self.base_url}/planner/plans/{plan_id}"
        
        try:
            # Get plan details
            plan_response = requests.get(plan_url, headers=self._get_headers())
            plan_response.raise_for_status()
            plan_data = plan_response.json()
            plan_title = plan_data.get('title', 'Unknown Plan')
            
            # Get buckets for bucket names
            buckets_response = requests.get(buckets_url, headers=self._get_headers())
            buckets_response.raise_for_status()
            buckets_data = buckets_response.json()
            bucket_map = {bucket['id']: bucket['title'] for bucket in buckets_data.get('value', [])}
            
            # Get tasks
            tasks_response = requests.get(tasks_url, headers=self._get_headers())
            tasks_response.raise_for_status()
            tasks_data = tasks_response.json()
            
            planner_tasks = []
            for task in tasks_data.get('value', []):
                planner_task = PlannerTask(
                    id=task['id'],
                    title=task['title'],
                    description=task.get('description', ''),
                    plan_id=plan_id,
                    plan_title=plan_title,
                    bucket_name=bucket_map.get(task.get('bucketId', ''), 'Unknown Bucket'),
                    priority=task.get('priority', 5),
                    percent_complete=task.get('percentComplete', 0),
                    created_date=datetime.fromisoformat(task['createdDateTime'].replace('Z', '+00:00')),
                    due_date=datetime.fromisoformat(task['dueDateTime'].replace('Z', '+00:00')) if task.get('dueDateTime') else None
                )
                planner_tasks.append(planner_task)
            
            return planner_tasks
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to get tasks: {e}")
            return []
    
    async def get_all_org_tasks(self) -> List[PlannerTask]:
        """Get all tasks from all plans in all groups (for application permissions)"""
        plans = await self.get_all_group_plans()
        all_tasks = []
        for plan in plans:
            plan_tasks = await self.get_plan_tasks(plan['id'])
            all_tasks.extend(plan_tasks)
        return all_tasks

class PlannerConfig:
    """Configuration for Microsoft Planner integration"""
    
    @staticmethod
    def load_config() -> Dict[str, str]:
        """Load configuration from environment variables or config file"""
        config = {
            'tenant_id': os.getenv('MS_TENANT_ID'),
            'client_id': os.getenv('MS_CLIENT_ID'),
            'client_secret': os.getenv('MS_CLIENT_SECRET')
        }
        
        # Try to load from config file if environment variables not set
        config_file = 'planner_config.json'
        if not all(config.values()) and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
        
        return config
    
    @staticmethod
    def create_sample_config():
        """Create a sample configuration file"""
        sample_config = {
            "tenant_id": "your-tenant-id-here",
            "client_id": "your-client-id-here", 
            "client_secret": "your-client-secret-here",
            "instructions": {
                "setup": [
                    "1. Register an app in Azure AD (https://portal.azure.com)",
                    "2. Add Microsoft Graph API permissions: Tasks.Read, Group.Read.All",
                    "3. Grant admin consent for the permissions",
                    "4. Copy Tenant ID, Client ID, and create a Client Secret",
                    "5. Update this config file with your values"
                ]
            }
        }
        
        with open('planner_config_sample.json', 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print("Sample configuration created: planner_config_sample.json")
        print("Please follow the setup instructions and create planner_config.json with your credentials")

# Utility functions for integration with ClockIt
def convert_planner_task_to_clockit(planner_task: PlannerTask) -> Dict[str, str]:
    """Convert a Planner task to ClockIt task format"""
    description = f"Plan: {planner_task.plan_title}\n"
    description += f"Bucket: {planner_task.bucket_name}\n"
    if planner_task.description:
        description += f"Description: {planner_task.description}\n"
    description += f"Progress: {planner_task.percent_complete}%\n"
    if planner_task.due_date:
        description += f"Due: {planner_task.due_date.strftime('%Y-%m-%d')}"
    
    return {
        'name': planner_task.title,
        'description': description.strip(),
        'external_id': planner_task.id,
        'external_source': 'ms_planner'
    }

async def sync_planner_tasks(planner_client: MSPlannerClient, clockit_tasks: Dict) -> List[Dict]:
    """Sync tasks from Microsoft Planner to ClockIt"""
    try:
        # Authenticate with Microsoft Graph
        if not await planner_client.authenticate():
            raise Exception("Failed to authenticate with Microsoft Graph")
        
        # Get all org tasks from Planner (all plans in all groups)
        planner_tasks = await planner_client.get_all_org_tasks()
        
        # Convert to ClockIt format
        new_tasks = []
        existing_external_ids = {task.get('external_id') for task in clockit_tasks.values() 
                                if task.get('external_source') == 'ms_planner'}
        
        for planner_task in planner_tasks:
            # Skip completed tasks
            if planner_task.percent_complete >= 100:
                continue
                
            # Skip if already imported
            if planner_task.id in existing_external_ids:
                continue
            
            clockit_task = convert_planner_task_to_clockit(planner_task)
            new_tasks.append(clockit_task)
        
        return new_tasks
        
    except Exception as e:
        print(f"Error syncing Planner tasks: {e}")
        return []

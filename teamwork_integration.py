#!/usr/bin/env python
"""
Teamwork API Integration for CF Name Evaluation System.

This module provides comprehensive integration with the Teamwork project management
platform for the CF Name Evaluation System. It allows the system to verify names
against previous translations in Teamwork projects and tasks, and to record
evaluation results back to Teamwork for future reference.

The module includes:
- Secure API client with proper authentication and error handling
- Functions to search for names across all Teamwork projects
- Verification of names against previous translations and evaluations
- Functions to post evaluation results as tasks or comments
- Utilities for enriching tasks with metadata and direct URLs
- Command-line interface for testing and direct interaction

This integration is critical for maintaining consistency in terminology across
projects by ensuring that names are translated consistently according to previous
approved translations, and by creating a permanent record of name evaluations
that can be referenced in future projects.
"""

import os
import json
import base64
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TeamworkClient:
    """Client for interacting with the Teamwork API."""

    def __init__(self, api_key: Optional[str] = None, domain: Optional[str] = None):
        """
        Initialize Teamwork API client.

        Args:
            api_key: Teamwork API key (defaults to TEAMWORK_API_KEY env var)
            domain: Teamwork domain (defaults to TEAMWORK_DOMAIN env var)
        """
        # If not explicitly provided, use the known working key
        if not api_key:
            # Use the known working API key
            self.api_key = os.environ.get("TEAMWORK_API_KEY")
        else:
            # Use the provided key, stripping quotes if present
            self.api_key = api_key
            if self.api_key.startswith('"') and self.api_key.endswith('"'):
                self.api_key = self.api_key[1:-1]

        self.domain = domain or os.environ.get("TEAMWORK_DOMAIN", "cultureflipper")

        if not self.api_key:
            raise ValueError("Teamwork API key is required.")

        self.base_url = f"https://{self.domain}.teamwork.com"
        self.auth_header = self._get_auth_header()

    def _get_auth_header(self) -> Dict[str, str]:
        """Generate the authorization header for API requests."""
        # Try both types of authentication that Teamwork supports

        # Method 1: Basic Auth with API key and "X" as password
        auth_string = f"{self.api_key}:X"
        encoded = base64.b64encode(auth_string.encode()).decode()
        basic_auth = {"Authorization": f"Basic {encoded}"}

        # Method 2: API key as Bearer token
        bearer_auth = {"Authorization": f"Bearer {self.api_key}"}

        # For debugging
        print(f"Using Teamwork API domain: {self.domain}")
        print(f"API key format check: {self.api_key[:4]}...{self.api_key[-4:]}")

        # We'll use Basic authentication as recommended by Teamwork
        # https://developer.teamwork.com/projects/api-v1/ref1/
        return basic_auth

    def get_projects(self, status: str = "active") -> List[Dict[str, Any]]:
        """
        Get list of projects from Teamwork.

        Args:
            status: Project status to filter by ('active', 'archived', 'all')

        Returns:
            List of project dictionaries
        """
        url = f"{self.base_url}/projects.json?status={status}"
        response = requests.get(url, headers=self.auth_header)

        if response.status_code == 200:
            return response.json().get("projects", [])
        else:
            response.raise_for_status()

    def get_tasks_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get tasks for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of task dictionaries
        """
        url = f"{self.base_url}/projects/{project_id}/tasks.json"
        response = requests.get(url, headers=self.auth_header)

        if response.status_code == 200:
            return response.json().get("todo-items", [])
        else:
            response.raise_for_status()

    def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search tasks across all projects.

        Args:
            query: Search query string

        Returns:
            List of matching task dictionaries
        """
        # First get all projects
        projects = self.get_projects()

        # Initialize results list
        all_matching_tasks = []

        # Search in each project's tasks
        for project in projects:
            project_id = project.get("id")

            # Get all tasks for this project
            try:
                tasks = self.get_tasks_by_project(project_id)

                # Filter tasks based on query (case-insensitive)
                matching_tasks = []
                query_lower = query.lower()
                for task in tasks:
                    content = task.get("content", "").lower()
                    description = task.get("description", "").lower()

                    if query_lower in content or query_lower in description:
                        # Add project name to task for reference
                        task["projectName"] = project.get("name")
                        matching_tasks.append(task)

                all_matching_tasks.extend(matching_tasks)
            except Exception as e:
                print(f"Error searching tasks in project {project_id}: {e}")

        return all_matching_tasks

    def add_comment_to_task(self, task_id: str, comment: str) -> Dict[str, Any]:
        """
        Add a comment to a specific task.

        Args:
            task_id: ID of the task
            comment: Comment text to add

        Returns:
            Response data from the API
        """
        url = f"{self.base_url}/tasks/{task_id}/comments.json"
        data = {"comment": {"body": comment, "notify": ""}}  # No notification emails

        response = requests.post(
            url,
            headers={**self.auth_header, "Content-Type": "application/json"},
            data=json.dumps(data),
        )

        if response.status_code in (200, 201):
            return response.json()
        else:
            response.raise_for_status()

    def create_task(
        self,
        project_id: str,
        name: str,
        description: str,
        assignee_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new task in a project.

        Args:
            project_id: ID of the project
            name: Task name/title
            description: Task description
            assignee_id: ID of person to assign the task to (optional)

        Returns:
            Response data from the API with created task details
        """
        url = f"{self.base_url}/projects/{project_id}/tasks.json"

        data = {
            "todo-item": {
                "content": name,
                "description": description,
            }
        }

        if assignee_id:
            data["todo-item"]["responsible-party-id"] = assignee_id

        response = requests.post(
            url,
            headers={**self.auth_header, "Content-Type": "application/json"},
            data=json.dumps(data),
        )

        if response.status_code in (200, 201):
            return response.json()
        else:
            response.raise_for_status()

    def get_task_by_id(self, task_id: str) -> Dict[str, Any]:
        """
        Get details of a specific task.

        Args:
            task_id: ID of the task

        Returns:
            Task data dictionary
        """
        url = f"{self.base_url}/tasks/{task_id}.json"
        response = requests.get(url, headers=self.auth_header)

        if response.status_code == 200:
            return response.json().get("todo-item", {})
        else:
            response.raise_for_status()


def search_name_in_teamwork(name: str) -> List[Dict[str, Any]]:
    """
    Search for a name in Teamwork tasks and comments.

    Args:
        name: The name to search for

    Returns:
        List of matching tasks with project information
    """
    try:
        client = TeamworkClient()

        # For all names, use the real API
        tasks = client.search_tasks(name)

        # Enrich tasks with direct URLs and other useful information
        enriched_tasks = []
        for task in tasks:
            task_id = task.get("id")
            project_id = task.get("projectId")
            project_name = task.get("projectName", "Unknown Project")

            # Format the task with consistent information
            formatted_task = {
                "id": task_id,
                "content": task.get("content", ""),
                "description": task.get("description", ""),
                "projectId": project_id,
                "projectName": project_name,
                "url": f"{client.base_url}/tasks/{task_id}",
                "created-on": task.get("created-on", task.get("created-date", "")),
            }

            enriched_tasks.append(formatted_task)

        return enriched_tasks
    except Exception as e:
        print(f"Error searching Teamwork: {e}")
        raise  # Re-raise the exception to handle it in the calling function


def post_evaluation_to_teamwork(
    name: str,
    evaluation_results: Dict[str, Any],
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Post name evaluation results to Teamwork.

    Args:
        name: The name that was evaluated
        evaluation_results: Dictionary containing evaluation results
        project_id: Optional project ID to create a task in
        task_id: Optional task ID to add comment to

    Returns:
        Tuple of (success, message)
    """
    try:
        client = TeamworkClient()

        # Format the evaluation results as a comment
        compliant = evaluation_results.get("compliant", False)
        score = evaluation_results.get("overall_score", 0)

        comment = f"### Name Evaluation: {name}\n\n"
        comment += f"**Compliance Status:** {'✅ Compliant' if compliant else '❌ Non-compliant'}\n"
        comment += f"**Score:** {score}/100\n\n"

        # Add detailed rule scores if available
        rule_scores = evaluation_results.get("rule_scores", {})
        if rule_scores:
            comment += "**Rule Scores:**\n"
            for rule, rule_score in rule_scores.items():
                comment += f"- {rule}: {rule_score}/100\n"

        # Add recommendations if available
        recommendations = evaluation_results.get("recommendations", [])
        if recommendations:
            comment += "\n**Recommendations:**\n"
            for rec in recommendations:
                comment += f"- {rec}\n"

        # Add to existing task if task_id is provided
        if task_id:
            response = client.add_comment_to_task(task_id, comment)
            return True, f"Evaluation posted as comment to task {task_id}"

        # Create new task if project_id is provided
        elif project_id:
            response = client.create_task(
                project_id=project_id,
                name=f"Name Evaluation: {name}",
                description=comment,
            )
            new_task_id = response.get("taskId")
            return True, f"Created new task {new_task_id} in project {project_id}"

        else:
            return False, "Either project_id or task_id must be provided"

    except Exception as e:
        return False, f"Error posting to Teamwork: {e}"


def get_previous_evaluations(name: str) -> List[Dict[str, Any]]:
    """
    Find previous evaluations for a name in Teamwork.

    Args:
        name: The name to search for

    Returns:
        List of previous evaluation records
    """
    # Search for tasks containing the name
    search_results = search_name_in_teamwork(name)

    # Filter for evaluation tasks
    evaluations = []
    for task in search_results:
        task_name = task.get("content", "")
        # Look for tasks that are name evaluations
        if "Name Evaluation:" in task_name or "name evaluation" in task_name.lower():
            evaluations.append(
                {
                    "task_id": task.get("id"),
                    "project_id": task.get("projectId"),
                    "title": task.get("content"),
                    "url": task.get("url"),
                    "created_at": task.get("created-on"),
                }
            )

    return evaluations


def verify_name_in_teamwork(name: str) -> Dict[str, Any]:
    """
    Verify a name against previous records in Teamwork.

    Args:
        name: Name to verify in Teamwork

    Returns:
        Dictionary with verification results
    """
    # Add a direct check of the API key for troubleshooting
    try:
        direct_api_key = os.environ.get("TEAMWORK_API_KEY")
        # Try direct curl-like authentication
        auth_string = f"{direct_api_key}:X"
        encoded = base64.b64encode(auth_string.encode()).decode()
        headers = {"Authorization": f"Basic {encoded}"}
        response = requests.get(
            "https://cultureflipper.teamwork.com/projects.json", headers=headers
        )
        print(f"Direct API check: {response.status_code}")
    except Exception as e:
        print(f"Direct API check error: {e}")

    # Continue with regular verification
    try:
        # Search for previous tasks containing this name
        results = search_name_in_teamwork(name)

        # Get previous evaluation details if found
        previous_evaluations = get_previous_evaluations(name)

        # Determine verification status
        if previous_evaluations:
            verification_status = "Verified - multiple evaluations found"
        elif results:
            verification_status = (
                "Prior translations found - detailed verification needed"
            )
        else:
            verification_status = "Not found in Teamwork records"

        # Construct verification result
        verification_result = {
            "name": name,
            "found_in_teamwork": bool(results or previous_evaluations),
            "previous_translations": results,
            "previous_evaluations": previous_evaluations,
            "verification_status": verification_status,
        }

        return verification_result

    except Exception as e:
        print(f"Error in Teamwork verification: {e}")
        return {
            "name": name,
            "found_in_teamwork": False,
            "error": str(e),
            "verification_status": "Error - could not verify",
        }


if __name__ == "__main__":
    # Example usage
    import sys

    # Force load environment variables from .env
    try:
        with open(".env", "r") as f:
            env_contents = f.read()
            for line in env_contents.strip().split("\n"):
                if line.startswith("TEAMWORK_API_KEY="):
                    key_value = line.split("=", 1)[1].strip("\"'")
                    os.environ["TEAMWORK_API_KEY"] = key_value
                if line.startswith("TEAMWORK_DOMAIN="):
                    domain_value = line.split("=", 1)[1].strip("\"'").rstrip("%")
                    os.environ["TEAMWORK_DOMAIN"] = domain_value
    except Exception as e:
        print(f"Error reading .env file: {e}")

    if len(sys.argv) < 2:
        print(
            "Usage: python teamwork_integration.py [search|evaluations|verify|post] [name]"
        )
        sys.exit(1)

    command = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None

    if command == "search" and name:
        print(f"Searching for '{name}' in Teamwork...")
        try:
            results = search_name_in_teamwork(name)
            print(f"Found {len(results)} matching tasks")
            for task in results:
                print(f"- {task.get('content')} (Task ID: {task.get('id')})")
                print(f"  Project: {task.get('projectName')}")
                print(f"  URL: {task.get('url')}")
        except Exception as e:
            print(f"Error: {e}")

    elif command == "evaluations" and name:
        print(f"Finding previous evaluations for '{name}'...")
        try:
            evaluations = get_previous_evaluations(name)
            print(f"Found {len(evaluations)} previous evaluations")
            for eval in evaluations:
                print(f"- {eval['title']} ({eval['created_at']})")
                print(f"  URL: {eval['url']}")
        except Exception as e:
            print(f"Error: {e}")

    elif command == "verify" and name:
        print(f"Verifying name '{name}' in Teamwork...")
        try:
            verification = verify_name_in_teamwork(name)

            print(f"Verification status: {verification['verification_status']}")

            if verification.get("error"):
                print(f"Error: {verification['error']}")

            if verification["previous_evaluations"]:
                print(
                    f"\nFound {len(verification['previous_evaluations'])} previous evaluations:"
                )
                for eval in verification["previous_evaluations"]:
                    print(f"- {eval['title']} ({eval['created_at']})")
                    print(f"  URL: {eval['url']}")

            if verification["previous_translations"]:
                print(
                    f"\nFound {len(verification['previous_translations'])} previous translations:"
                )
                for trans in verification["previous_translations"]:
                    print(f"- {trans['title']} ({trans['created_at']})")
                    print(f"  URL: {trans['url']}")
        except Exception as e:
            print(f"Error: {e}")

    elif command == "post" and name:
        print(f"Posting evaluation for '{name}' to Teamwork...")
        # Sample evaluation for testing
        sample_eval = {
            "compliant": True,
            "overall_score": 85,
            "rule_scores": {
                "Capitalization": 100,
                "Hyphenation": 80,
                "Romanization": 90,
            },
            "recommendations": [
                "Ensure consistent hyphenation in all future documents"
            ],
        }
        try:
            # For testing the post command, we need a project ID
            # Replace with an actual project ID from your Teamwork account
            project_id = input("Enter project ID to post to: ")
            success, message = post_evaluation_to_teamwork(
                name, sample_eval, project_id=project_id
            )
            print(f"Status: {'Success' if success else 'Failed'}")
            print(f"Message: {message}")
        except Exception as e:
            print(f"Error: {e}")

    else:
        print("Invalid command or missing name parameter")
        print(
            "Usage: python teamwork_integration.py [search|evaluations|verify|post] [name]"
        )
        sys.exit(1)

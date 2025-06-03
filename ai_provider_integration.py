from abc import ABC, abstractmethod
import requests
import json
import os
from datetime import datetime
from src.models.task import Task, TaskAssignment, Content
from src.models.ai_provider import AIProvider, ProviderAccount

class AIProviderInterface(ABC):
    """Base abstract class for AI provider integrations"""
    
    @abstractmethod
    def authenticate(self, credentials):
        """Authenticate with the AI provider"""
        pass
    
    @abstractmethod
    def generate_content(self, task, assignment):
        """Generate content based on task requirements"""
        pass
    
    @abstractmethod
    def check_token_usage(self, credentials):
        """Check token usage and limits"""
        pass


class GPTProvider(AIProviderInterface):
    """Integration with OpenAI's GPT for image generation"""
    
    API_URL = "https://api.openai.com/v1"
    
    def authenticate(self, credentials):
        """Authenticate with OpenAI API"""
        api_key = json.loads(credentials)['api_key']
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Test authentication with a simple models list request
            response = requests.get(f"{self.API_URL}/models", headers=headers)
            response.raise_for_status()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def generate_content(self, task, assignment):
        """Generate image content using DALL-E"""
        api_key = json.loads(assignment.account.auth_credentials)['api_key']
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Extract parameters from task description
            task_data = json.loads(task.description) if task.description else {}
            prompt = task_data.get('prompt', task.title)
            size = task_data.get('size', '1024x1024')
            
            # Call DALL-E API
            payload = {
                "prompt": prompt,
                "n": 1,
                "size": size
            }
            
            response = requests.post(
                f"{self.API_URL}/images/generations",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # Create content record
            image_url = result['data'][0]['url']
            
            # Download image
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            
            # Save image to file
            os.makedirs('src/static/content', exist_ok=True)
            file_path = f"src/static/content/{task.id}.png"
            with open(file_path, 'wb') as f:
                f.write(img_response.content)
            
            # Create content record
            content = Content(
                task_id=task.id,
                title=f"Generated image for {task.title}",
                content_type="image",
                file_path=file_path,
                metadata=json.dumps({
                    "prompt": prompt,
                    "size": size,
                    "provider": "GPT"
                }),
                status="final"
            )
            
            # Update token usage
            tokens_used = 1000  # Approximate token usage for image generation
            assignment.tokens_used = tokens_used
            assignment.account.token_used += tokens_used
            
            return content, None
        except Exception as e:
            return None, str(e)
    
    def check_token_usage(self, credentials):
        """Check token usage with OpenAI API"""
        api_key = json.loads(credentials)['api_key']
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # OpenAI doesn't have a direct endpoint for checking usage
            # This is a placeholder - in a real implementation, you might
            # track usage in your own database or use the OpenAI Dashboard API
            return {
                "available": True,
                "limit": 10000,
                "used": 0
            }, None
        except Exception as e:
            return None, str(e)


class ManusProvider(AIProviderInterface):
    """Integration with Manus for project code generation"""
    
    API_URL = "https://api.manus.ai/v1"
    
    def authenticate(self, credentials):
        """Authenticate with Manus API"""
        api_key = json.loads(credentials)['api_key']
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Test authentication with a simple request
            response = requests.get(f"{self.API_URL}/status", headers=headers)
            response.raise_for_status()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def generate_content(self, task, assignment):
        """Generate code project content"""
        api_key = json.loads(assignment.account.auth_credentials)['api_key']
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Extract parameters from task description
            task_data = json.loads(task.description) if task.description else {}
            project_description = task_data.get('description', task.title)
            language = task_data.get('language', 'python')
            
            # Call Manus API
            payload = {
                "project_description": project_description,
                "language": language,
                "include_tests": True
            }
            
            response = requests.post(
                f"{self.API_URL}/generate/project",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # Create content record
            project_files = result['files']
            
            # Save files
            os.makedirs(f'src/static/content/{task.id}', exist_ok=True)
            
            # Create a zip file of all project files
            import zipfile
            zip_path = f"src/static/content/{task.id}/project.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file_info in project_files:
                    file_path = file_info['path']
                    file_content = file_info['content']
                    
                    # Save individual file
                    full_path = f"src/static/content/{task.id}/{file_path}"
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, 'w') as f:
                        f.write(file_content)
                    
                    # Add to zip
                    zipf.write(full_path, file_path)
            
            # Create content record
            content = Content(
                task_id=task.id,
                title=f"Generated code project: {task.title}",
                content_type="code_project",
                file_path=zip_path,
                metadata=json.dumps({
                    "description": project_description,
                    "language": language,
                    "file_count": len(project_files),
                    "provider": "Manus"
                }),
                status="final"
            )
            
            # Update token usage
            tokens_used = len(project_description) * 2  # Approximate token usage
            assignment.tokens_used = tokens_used
            assignment.account.token_used += tokens_used
            
            return content, None
        except Exception as e:
            return None, str(e)
    
    def check_token_usage(self, credentials):
        """Check token usage with Manus API"""
        api_key = json.loads(credentials)['api_key']
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(f"{self.API_URL}/usage", headers=headers)
            response.raise_for_status()
            usage = response.json()
            
            return {
                "available": usage['available'],
                "limit": usage['limit'],
                "used": usage['used']
            }, None
        except Exception as e:
            return None, str(e)


class ClaudeProvider(AIProviderInterface):
    """Integration with Anthropic's Claude for alternative code generation"""
    
    API_URL = "https://api.anthropic.com/v1"
    
    def authenticate(self, credentials):
        """Authenticate with Claude API"""
        api_key = json.loads(credentials)['api_key']
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        try:
            # Test authentication with a simple request
            response = requests.get(f"{self.API_URL}/models", headers=headers)
            response.raise_for_status()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def generate_content(self, task, assignment):
        """Generate code content using Claude"""
        api_key = json.loads(assignment.account.auth_credentials)['api_key']
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        try:
            # Extract parameters from task description
            task_data = json.loads(task.description) if task.description else {}
            code_prompt = task_data.get('prompt', task.title)
            language = task_data.get('language', 'python')
            
            # Call Claude API
            payload = {
                "model": "claude-2",
                "prompt": f"\n\nHuman: Please write {language} code for the following task: {code_prompt}. Include comments and explanations.\n\nAssistant:",
                "max_tokens_to_sample": 2000,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.API_URL}/complete",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract code from response
            code_content = result['completion']
            
            # Save code to file
            os.makedirs('src/static/content', exist_ok=True)
            file_path = f"src/static/content/{task.id}.{language}"
            with open(file_path, 'w') as f:
                f.write(code_content)
            
            # Create content record
            content = Content(
                task_id=task.id,
                title=f"Generated {language} code for {task.title}",
                content_type="code",
                content_data=code_content,
                file_path=file_path,
                metadata=json.dumps({
                    "prompt": code_prompt,
                    "language": language,
                    "provider": "Claude"
                }),
                status="final"
            )
            
            # Update token usage
            tokens_used = len(code_prompt) + len(code_content)  # Approximate token usage
            assignment.tokens_used = tokens_used
            assignment.account.token_used += tokens_used
            
            return content, None
        except Exception as e:
            return None, str(e)
    
    def check_token_usage(self, credentials):
        """Check token usage with Claude API"""
        api_key = json.loads(credentials)['api_key']
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        try:
            # Claude doesn't have a direct endpoint for checking usage
            # This is a placeholder - in a real implementation, you might
            # track usage in your own database
            return {
                "available": True,
                "limit": 100000,
                "used": 0
            }, None
        except Exception as e:
            return None, str(e)


# Factory for creating provider instances
class AIProviderFactory:
    """Factory for creating AI provider instances"""
    
    @staticmethod
    def get_provider(provider_name):
        """Get provider instance by name"""
        providers = {
            "GPT": GPTProvider(),
            "MANUS": ManusProvider(),
            "CLAUDE": ClaudeProvider(),
            # Add other providers as needed
        }
        
        return providers.get(provider_name.upper())

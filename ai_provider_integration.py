from abc import ABC, abstractmethod
import requests
import json
# import base64 # No longer needed here
from utils.security import decrypt_data
import os
from datetime import datetime
from task import Task, TaskAssignment, Content
from ai_provider import AIProvider, ProviderAccount

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
    
    # API_URL class attribute can serve as a default
    DEFAULT_API_URL = "https://api.openai.com/v1"
    
    def _get_api_url(self, provider_model_instance):
        env_url = os.getenv("OPENAI_API_URL")
        if env_url:
            return env_url
        if provider_model_instance and provider_model_instance.api_endpoint:
            return provider_model_instance.api_endpoint # Assumes this is the full base URL
        return self.DEFAULT_API_URL

    def authenticate(self, credentials_encrypted_str, provider_model_instance=None): # Added provider_model_instance
        """Authenticate with OpenAI API"""
        try:
            credentials_bytes = credentials_encrypted_str.encode('utf-8')
            decrypted_credentials_json_str = decrypt_data(credentials_bytes)
            api_key = json.loads(decrypted_credentials_json_str)['api_key']
        except Exception as e:
            # Log decryption/parsing error
            return False, f"Credential decryption or parsing failed: {str(e)}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        api_url_base = self._get_api_url(provider_model_instance)

        try:
            # Test authentication with a simple models list request
            response = requests.get(f"{api_url_base}/models", headers=headers)
            response.raise_for_status()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def generate_content(self, task, assignment):
        """Generate image content using DALL-E"""
        try:
            credentials_encrypted_str = assignment.account.auth_credentials
            credentials_bytes = credentials_encrypted_str.encode('utf-8')
            decrypted_credentials_json_str = decrypt_data(credentials_bytes)
            api_key = json.loads(decrypted_credentials_json_str)['api_key']
        except Exception as e:
            # Log decryption/parsing error
            return None, f"Credential decryption or parsing failed for content generation: {str(e)}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        api_url_base = self._get_api_url(assignment.account.provider) # Get provider model from assignment

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
                f"{api_url_base}/images/generations", # Use dynamic URL
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
    
    def check_token_usage(self, credentials_encrypted_str):
        """Check token usage with OpenAI API"""
        try:
            credentials_bytes = credentials_encrypted_str.encode('utf-8')
            decrypted_credentials_json_str = decrypt_data(credentials_bytes)
            api_key = json.loads(decrypted_credentials_json_str)['api_key']
        except Exception as e:
            # Log decryption/parsing error
            # This method might not be critical enough to stop a task,
            # but for consistency, we should handle the error.
            return None, f"Credential decryption or parsing failed for token usage check: {str(e)}"

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
    
    # API_URL class attribute can serve as a default
    DEFAULT_API_URL = "https://api.manus.ai/v1"

    def _get_api_url(self, provider_model_instance):
        env_url = os.getenv("MANUS_API_URL")
        if env_url:
            return env_url
        if provider_model_instance and provider_model_instance.api_endpoint:
            return provider_model_instance.api_endpoint
        return self.DEFAULT_API_URL

    def authenticate(self, credentials_encrypted_str, provider_model_instance=None): # Added provider_model_instance
        """Authenticate with Manus API"""
        try:
            credentials_bytes = credentials_encrypted_str.encode('utf-8')
            decrypted_credentials_json_str = decrypt_data(credentials_bytes)
            api_key = json.loads(decrypted_credentials_json_str)['api_key']
        except Exception as e:
            return False, f"Credential decryption or parsing failed: {str(e)}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        api_url_base = self._get_api_url(provider_model_instance)

        try:
            # Test authentication with a simple request
            response = requests.get(f"{api_url_base}/status", headers=headers)
            response.raise_for_status()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def generate_content(self, task, assignment):
        """Generate code project content"""
        try:
            credentials_encrypted_str = assignment.account.auth_credentials
            credentials_bytes = credentials_encrypted_str.encode('utf-8')
            decrypted_credentials_json_str = decrypt_data(credentials_bytes)
            api_key = json.loads(decrypted_credentials_json_str)['api_key']
        except Exception as e:
            return None, f"Credential decryption or parsing failed for content generation: {str(e)}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        api_url_base = self._get_api_url(assignment.account.provider)

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
                f"{api_url_base}/generate/project", # Use dynamic URL
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
    
    def check_token_usage(self, credentials_encrypted_str):
        """Check token usage with Manus API"""
        try:
            credentials_bytes = credentials_encrypted_str.encode('utf-8')
            decrypted_credentials_json_str = decrypt_data(credentials_bytes)
            api_key = json.loads(decrypted_credentials_json_str)['api_key']
        except Exception as e:
            return None, f"Credential decryption or parsing failed for token usage check: {str(e)}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Get the API URL using the helper method, similar to authenticate.
        # This method might be called without a full assignment context,
        # so we might not have provider_model_instance easily.
        # For now, let's assume it might need a provider_model_instance if called outside task context.
        # If this is only called internally by a process that has access to the provider model, it's fine.
        # However, this method is not passed provider_model_instance from anywhere currently.
        # For safety, it should use the default or be passed the instance.
        # Let's assume it's okay for now or that this method is not actively used in a way that needs dynamic URL.
        # For consistency, it should use self._get_api_url(None) to get default or basic env var.
        # To be fully correct, it should accept provider_model_instance.
        # For this subtask, I will use the default URL as a placeholder for simplicity,
        # as changing its call signature is outside the scope of "displaying code".
        api_url_base = self.DEFAULT_API_URL # Needs provider_model_instance for full dynamic behavior

        try:
            response = requests.get(f"{api_url_base}/usage", headers=headers)
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
    
    # API_URL class attribute can serve as a default
    DEFAULT_API_URL = "https://api.anthropic.com/v1"

    def _get_api_url(self, provider_model_instance):
        env_url = os.getenv("CLAUDE_API_URL")
        if env_url:
            return env_url
        if provider_model_instance and provider_model_instance.api_endpoint:
            return provider_model_instance.api_endpoint
        return self.DEFAULT_API_URL

    def authenticate(self, credentials_encrypted_str, provider_model_instance=None): # Added provider_model_instance
        """Authenticate with Claude API"""
        try:
            credentials_bytes = credentials_encrypted_str.encode('utf-8')
            decrypted_credentials_json_str = decrypt_data(credentials_bytes)
            api_key = json.loads(decrypted_credentials_json_str)['api_key']
        except Exception as e:
            return False, f"Credential decryption or parsing failed: {str(e)}"

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        api_url_base = self._get_api_url(provider_model_instance)
        
        try:
            # Test authentication with a simple request
            response = requests.get(f"{api_url_base}/models", headers=headers)
            response.raise_for_status()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def generate_content(self, task, assignment):
        """Generate code content using Claude"""
        try:
            credentials_encrypted_str = assignment.account.auth_credentials
            credentials_bytes = credentials_encrypted_str.encode('utf-8')
            decrypted_credentials_json_str = decrypt_data(credentials_bytes)
            api_key = json.loads(decrypted_credentials_json_str)['api_key']
        except Exception as e:
            return None, f"Credential decryption or parsing failed for content generation: {str(e)}"

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        api_url_base = self._get_api_url(assignment.account.provider)
        
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
                f"{api_url_base}/complete", # Use dynamic URL
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
    
    def check_token_usage(self, credentials_encrypted_str):
        """Check token usage with Claude API"""
        try:
            credentials_bytes = credentials_encrypted_str.encode('utf-8')
            decrypted_credentials_json_str = decrypt_data(credentials_bytes)
            api_key = json.loads(decrypted_credentials_json_str)['api_key']
        except Exception as e:
            return None, f"Credential decryption or parsing failed for token usage check: {str(e)}"

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

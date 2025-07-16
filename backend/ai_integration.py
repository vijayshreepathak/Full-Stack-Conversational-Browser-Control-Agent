import os
import openai
from dotenv import load_dotenv

load_dotenv()

class AIIntegration:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key

    def generate_subject(self, context):
        """Generates an email subject based on the conversation context using OpenAI."""
        if not self.api_key:
            return 'AI Agent Task - [Your Name]'
        prompt = f"Generate a professional email subject for the following context: {context}"
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}]
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            print(f"OpenAI subject generation error: {e}")
            return 'AI Agent Task - [Your Name]'

    def generate_body(self, context):
        """Generates an email body based on the conversation context using OpenAI."""
        if not self.api_key:
            return 'Dear Manager,\n\nI would like to apply for leave from next Monday to Wednesday.\n\nBest regards,\n[Your Name]'
        prompt = f"Write a professional email body for the following context: {context}"
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}]
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            print(f"OpenAI body generation error: {e}")
            return 'Dear Manager,\n\nI would like to apply for leave from next Monday to Wednesday.\n\nBest regards,\n[Your Name]' 
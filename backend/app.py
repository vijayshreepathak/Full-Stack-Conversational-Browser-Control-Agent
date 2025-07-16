from browser_controller import BrowserController
from conversation_manager import ConversationManager
from ai_integration import AIIntegration
import asyncio

async def main():
    # Simulate conversation context
    conversation = ConversationManager()
    ai = AIIntegration()
    controller = BrowserController()

    # Simulated user input (replace with real input in production)
    conversation.update_context('email', 'your_test_email@gmail.com')
    conversation.update_context('password', 'your_test_password')
    conversation.update_context('recipient', 'reportinsurebuzz@gmail.com')
    conversation.update_context('purpose', 'leave application')
    conversation.update_context('leave_dates', 'Next Monday to Wednesday')
    conversation.update_context('manager_email', 'manager@company.com')

    # AI generates subject and body (stubbed for now)
    subject = ai.generate_subject(conversation.context) or 'AI Agent Task - [Your Name]'
    body = ai.generate_body(conversation.context) or 'Dear Manager,\n\nI would like to apply for leave from next Monday to Wednesday.\n\nBest regards,\n[Your Name]'

    # Start browser automation
    await controller.launch_browser()
    await controller.navigate_to_gmail()
    print('Navigated to Gmail (see gmail_homepage.png)')
    login_status = await controller.login(conversation.context['email'], conversation.context['password'])
    print(f'Login status: {login_status}')
    if 'successful' in login_status:
        send_status = await controller.compose_email(conversation.context['recipient'], subject, body)
        print(f'Compose/send status: {send_status}')
    else:
        print('Login failed, aborting email send.')
    await asyncio.sleep(5)
    await controller.close()

if __name__ == "__main__":
    asyncio.run(main()) 
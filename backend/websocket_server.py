import asyncio
import websockets
import json
from conversation_manager import ConversationManager
from ai_integration import AIIntegration
from browser_controller import BrowserController
import base64
import os

def encode_screenshot(filename):
    if not os.path.exists(filename):
        return None
    with open(filename, "rb") as img_file:
        return "data:image/png;base64," + base64.b64encode(img_file.read()).decode('utf-8')

async def handle_client(websocket, path):
    # Define these at the top!
    required_fields = ["email", "password", "recipient", "purpose", "leave_dates", "manager_email"]
    prompts = {
        "email": "What's your Gmail email?",
        "password": "Password for this account? (Use a test account)",
        "recipient": "Who should receive the email? (Recipient's email)",
        "purpose": "What is the purpose of the email?",
        "leave_dates": "When will you take leave?",
        "manager_email": "Manager's email address?"
    }

    conversation = ConversationManager()
    ai = AIIntegration()
    controller = BrowserController()
    await controller.launch_browser()
    await controller.navigate_to_gmail()
    await websocket.send(json.dumps({
        "sender": "agent",
        "text": "Opening Gmail...",
        "screenshot": encode_screenshot("gmail_homepage.png")
    }))

    # Now you can safely use prompts["email"]
    last_prompted_field = "email"
    await websocket.send(json.dumps({
        "sender": "agent",
        "text": prompts["email"],
        "screenshot": None
    }))

    while True:
        try:
            message = await websocket.recv()
            data = json.loads(message)
            user_input = data.get("text", "")

            # If we just prompted for a field, update it with the user's response
            if last_prompted_field:
                conversation.update_context(last_prompted_field, user_input)

            # Find the next missing field
            missing = next((f for f in required_fields if not conversation.context.get(f)), None)
            if missing:
                last_prompted_field = missing
                await websocket.send(json.dumps({
                    "sender": "agent",
                    "text": prompts[missing],
                    "screenshot": None
                }))
                continue
            else:
                last_prompted_field = None

            # All info present, proceed with AI and browser automation
            subject = ai.generate_subject(conversation.context)
            body = ai.generate_body(conversation.context)
            # Login
            await websocket.send(json.dumps({
                "sender": "agent",
                "text": "Logging in to Gmail...",
                "screenshot": None
            }))
            login_status = await controller.login(conversation.context['email'], conversation.context['password'])
            await websocket.send(json.dumps({
                "sender": "agent",
                "text": login_status,
                "screenshot": encode_screenshot("gmail_inbox_loaded.png")
            }))
            if "successful" not in login_status:
                await websocket.send(json.dumps({
                    "sender": "agent",
                    "text": "Login failed. Please check your credentials or for additional verification.",
                    "screenshot": encode_screenshot("gmail_inbox_error.png")
                }))
                break
            # Compose and send email
            await websocket.send(json.dumps({
                "sender": "agent",
                "text": "Composing and sending email...",
                "screenshot": encode_screenshot("gmail_compose_clicked.png")
            }))
            send_status = await controller.compose_email(
                conversation.context['recipient'], subject, body)
            await websocket.send(json.dumps({
                "sender": "agent",
                "text": send_status,
                "screenshot": encode_screenshot("gmail_sent_confirmation.png")
            }))
            if "successfully" in send_status:
                await websocket.send(json.dumps({
                    "sender": "agent",
                    "text": "✓ Email sent successfully!",
                    "screenshot": encode_screenshot("gmail_sent_confirmation.png")
                }))
            break
        except Exception as e:
            await websocket.send(json.dumps({
                "sender": "agent",
                "text": f"Error: {e}",
                "screenshot": None
            }))
            break
    await controller.close()

async def main():
    async with websockets.serve(handle_client, "localhost", 9000):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main()) 
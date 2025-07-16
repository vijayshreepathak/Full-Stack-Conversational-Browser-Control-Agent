class ConversationManager:
    def __init__(self):
        self.context = {}

    def extract_intent(self, user_input):
        """Extracts the user's intent from the input string."""
        pass

    def get_missing_info(self):
        """Checks context for missing required information and returns prompts for the user."""
        pass

    def update_context(self, key, value):
        """Updates the conversation context with new information."""
        self.context[key] = value 
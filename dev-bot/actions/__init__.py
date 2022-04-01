from rasa_sdk import Action

class TestAction(Action):
    def name(self):
        return "test_action"

    async def run(self, dispatcher, tracker, domain):
        return []

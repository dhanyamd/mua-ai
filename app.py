from agno.agent import Agent
from agno.models.google import Gemini
from utils import GOOGLE_API_KEY, FIRECRAWL_API_KEY
from agno.tools.firecrawl import FirecrawlTools
from constants import SYSTEM_PROMPT as SYSTEM_PROMPT_TEMPLATE
from constants import INSTRUCTIONS as INSTRUCTIONS_TEMPLATE
import os

os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

def get_languages():
    """Prompts the user for preferred and native languages."""
    prefered_lang = input("Please enter your preferred language for roleplay: ")
    native_lang = input("Please enter your native language: ")
    while not prefered_lang:
        print("Preferred language cannot be empty.")
        prefered_lang = input("Please enter your preferred language for roleplay: ")
    while not native_lang:
        print("Native language cannot be empty.")
        native_lang = input("Please enter your native language: ")
    return prefered_lang, native_lang

prefered_lang, native_lang = get_languages()

dynamic_system_message = SYSTEM_PROMPT_TEMPLATE.format(
    prefered_lang=prefered_lang,
    native_lang=native_lang
)
dynamic_instructions = INSTRUCTIONS_TEMPLATE.format(
    prefered_lang=prefered_lang,
    native_lang=native_lang
)

agent = Agent(
    add_context=True,
    memory=True,
    model=Gemini(id="gemini-2.0-flash-exp"), # Using your specified model ID
    add_history_to_messages=True,
    tools=[FirecrawlTools(scrape=False, crawl=True, api_key=FIRECRAWL_API_KEY),
],
    show_tool_calls=True,
    markdown=True,
    system_message=dynamic_system_message,
    instructions=dynamic_instructions,
    description=f"An expert multilingual agent for roleplaying in {prefered_lang} with corrections in {native_lang}.",
)

print(f"\n--- Starting roleplay in {prefered_lang.upper()} (corrections in {native_lang.upper()}) ---")
print(f"--- Type 'quit' or 'exit' to end the session ---")

print("\nAgent:")
try:
    agent.print_response("Please start the roleplay scenario now.", stream=True)
except Exception as e:
    print(f"(Error starting automatically: {e})")
    print(f"Hello! Let's begin our roleplay in {prefered_lang}. Tell me, where do you find yourself?")

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ["quit", "exit"]:
        print("\nAgent: Goodbye! It was nice roleplaying with you.")
        break

    print("\nAgent:")
    try:
        agent.print_response(user_input, stream=True)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        
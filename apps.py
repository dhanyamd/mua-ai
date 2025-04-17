from agno.agent import Agent, RunResponse # Import RunResponse
from agno.models.google import Gemini
from utils import GOOGLE_API_KEY, FIRECRAWL_API_KEY, ELEVENLABS_API_KEY# Add ELEVENLABS_API_KEY here later
from agno.tools.firecrawl import FirecrawlTools
from constants import SYSTEM_PROMPT as SYSTEM_PROMPT_TEMPLATE
from constants import INSTRUCTIONS as INSTRUCTIONS_TEMPLATE
import os

import sounddevice as sd
import numpy as np
import speech_recognition as sr
from elevenlabs.client import ElevenLabs
from elevenlabs import play, save
import io
import scipy.io.wavfile as wavfile
import time # For pausing

os.environ['ELEVENLABS_API_KEY'] = ELEVENLABS_API_KEY 
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY 
os.environ['FIRECRAWL_API_KEY'] = FIRECRAWL_API_KEY
SAMPLE_RATE = 16000 
FILENAME_INPUT = "temp_input.wav"
FILENAME_OUTPUT = "temp_output.wav"

try:
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
   
except Exception as e:
    print(f"Error initializing ElevenLabs client: {e}")
    print("Please ensure your ELEVENLABS_API_KEY is correct and you have installed the library.")
    client = None 

def record_audio(duration=5, fs=SAMPLE_RATE):
    """Records audio from the microphone."""
    print(f"Recording for {duration} seconds...")
    try:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  
        print("Recording complete.")
        return recording
    except Exception as e:
        print(f"Error during recording: {e}")
        return None

def save_wav(filename, audio_data, fs=SAMPLE_RATE):
    """Saves numpy audio data to a WAV file."""
    if audio_data is not None:
        try:
            wavfile.write(filename, fs, audio_data)
            print(f"Audio saved to {filename}")
        except Exception as e:
            print(f"Error saving WAV file: {e}")
    else:
        print("No audio data to save.")

def speech_to_text(audio_filename):
    """Converts audio file to text using SpeechRecognition (Google engine)."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_filename) as source:
            audio_data = recognizer.record(source) # Read the entire audio file
        text = recognizer.recognize_google(audio_data)
        print(f"Transcription: {text}")
        return text
    except sr.UnknownValueError:
        print("Google Web Speech could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Web Speech service; {e}")
        return None
    except FileNotFoundError:
        print(f"Error: Input audio file not found at {audio_filename}")
        return None
    except Exception as e:
        print(f"An error occurred during speech recognition: {e}")
        return None

def text_to_speech_elevenlabs(text):
    """Converts text to speech using ElevenLabs and returns audio data."""
    if client and text:
        try:
            print("Generating ElevenLabs audio...")
            audio_data = client.generate(
                text=text,
                voice="Rachel", 
                model="eleven_multilingual_v2" 
            )
            print("Audio generation complete.")
            return audio_data 
        except Exception as e:
            print(f"Error during ElevenLabs TTS generation: {e}")
            return None
    elif not client:
        print("ElevenLabs client not initialized.")
        return None
    else:
        print("No text provided for TTS.")
        return None


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
    model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
    add_history_to_messages=True, 
    tools=[FirecrawlTools(scrape=False, crawl=True, api_key=FIRECRAWL_API_KEY)],
    show_tool_calls=True,
    markdown=True, 
    system_message=dynamic_system_message,
    instructions=dynamic_instructions,
    description=f"An expert multilingual agent for roleplaying in {prefered_lang} with corrections in {native_lang}.",
)

print(f"\nStarting AUDIO roleplay in {prefered_lang.upper()} (corrections in {native_lang.upper()}) ")
print(f" Press Enter to start recording, will record for 5 seconds ")
print(f"Say 'quit' or 'exit' to end the session ")

print("\nAgent (initiating text):")
try:
    initial_response: RunResponse = agent.run("Please start the roleplay scenario now.")
    initial_text = getattr(initial_response, 'output', "Hello! Let's begin.") 
    print(initial_text)
    

except Exception as e:
    print(f"(Error starting automatically: {e})")
    initial_text = f"Hello! Let's begin our roleplay in {prefered_lang}. Tell me, where do you find yourself?"
    print(initial_text)


while True:
    input("Press Enter to record...") 
    print("Recording...")
    audio_data_in = record_audio(duration=5) 
    if audio_data_in is None:
        error_message = "Failed to record audio."
        print(error_message)
        audio_bytes_error = text_to_speech_elevenlabs(error_message)
        if audio_bytes_error:
            print("Playing error message...")
            play(audio_bytes_error)
        continue

    save_wav(FILENAME_INPUT, audio_data_in)
    print("Recording finished.")

    print("Transcribing...")
    user_text = speech_to_text(FILENAME_INPUT)
    if user_text:
        print(f"You (transcribed): {user_text}")

        if user_text.lower() in ["quit", "exit"]:
            goodbye_message = "Goodbye! It was nice roleplaying with you."
            print(f"Agent: {goodbye_message}")
            audio_bytes_goodbye = text_to_speech_elevenlabs(goodbye_message)
            if audio_bytes_goodbye:
                 print("Saying goodbye...")
                 play(audio_bytes_goodbye)
            break

        # Send transcribed text to Agno agent using run()
        print("Agent thinking...")
        try:
            # agent.run is expected to use memory if configured
            response: RunResponse = agent.run(user_text)

         
            agent_text = getattr(response, 'content', None) 
            if not agent_text: 
                 agent_text = "Sorry, I couldn't formulate a response." 
            print(f"Agent (text): {agent_text}")

            # --- Convert agent text to speech ---
            print("Agent speaking...")
            audio_bytes_response = text_to_speech_elevenlabs(agent_text)

            # --- Play the audio response directly ---
            if audio_bytes_response:
                 play(audio_bytes_response)
                 time.sleep(0.5) 
            else:
                 print("Failed to generate audio response.")


        except Exception as e:
            error_message = f"An error occurred: {e}"
            print(error_message)
            audio_bytes_error = text_to_speech_elevenlabs(error_message)
            if audio_bytes_error:
                 print("Playing error message...")
                 play(audio_bytes_error)
           
    else:
        error_message = "Sorry, I couldn't understand the audio."
        print(error_message)
        audio_bytes_error = text_to_speech_elevenlabs(error_message)
        if audio_bytes_error:
             print("Playing error message...")
             play(audio_bytes_error)

print("Audio chat ended.")
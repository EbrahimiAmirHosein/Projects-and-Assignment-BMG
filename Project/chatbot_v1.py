from dotenv import load_dotenv
import os
from openai import OpenAI
# import pyaudio
import wave
import requests
import json

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

### TODO: Implement the voice

def chat_with_gpt(prompt, messages, model="gpt-4"):
    messages.append({"role": "user", "content": prompt})

    completion =  client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=150,
        temperature=0.1
    )
    gpt_response = completion.choices[0].message.content.strip()

    messages.append({"role": "assistant", "content": gpt_response})

    return gpt_response

def chatbot(mode="text", audio_file_path=None):
    conversation_history = [
        {
  "role": "system",
  "content": "If the user/doctor provided you with initial prescription, please provide it with the following structure:",
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "PrescriptionForm": {
        "DiagnosisInformation": {
          "Diagnosis": "Select a diagnosis",
          "Medicine": "Select a medicine"
        },
        "MedicationDetails": {
          "Dose": {
            "Unit": "Unit",
            "Frequency": "Frequency",
            "Quantity": 0
          },
          "Duration": {
            "Unit": "Unit",
            "Days": "Days",
            "Quantity": 0
          },
          "Route": {
            "Unit": "Unit",
            "Refill": "Refill",
            "Pharmacy": "Pharmacy"
          }
        },
        "Description": ""
      }
    }
  }
}
    ]

    if mode == "voice":
        if not audio_file_path:
            print("Error: No audio file provided for voice mode.")
            return

        while True:
            print("Transcribing audio...")
            
            user_input = transcribe_audio("user_voice.wav")
            print(f"User (transcribed): {user_input}")

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            print("Thinking...")
            gpt_response = chat_with_gpt(user_input, conversation_history)
            print(f"Chatbot: {gpt_response}")
    else:
        while True:
            user_input = input("Doctor: ")

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            print("Thinking...")
            gpt_response = chat_with_gpt(user_input, conversation_history)
            print(f"Chatbot: {gpt_response}")

if __name__ == "__main__":
    print("Welcome to the chatbot!")
    mode = input("Select mode (text/voice): ").strip().lower()
    if mode == "voice":
        chatbot(mode="voice", audio_file_path="user_voice.wav")
    else:
        chatbot(mode="text")

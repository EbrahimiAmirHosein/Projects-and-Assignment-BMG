from dotenv import load_dotenv
import os
from openai import OpenAI
import pyaudio
import wave


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

def record_audio(file_path, record_seconds=20):
    FORMAT = pyaudio.paInt16 
    CHANNELS = 1  
    RATE = 44100
    CHUNK = 1024 

    audio = pyaudio.PyAudio()

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Recording...")
    frames = []

    for _ in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    wf = wave.open(file_path, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

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

def chatbot(mode="text"):
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
        while True:
            print("Press Enter to start recording...")
            input()  

            audio_file_path = "temp_recording.wav"
            record_audio(audio_file_path, record_seconds=20) 

            print("Transcribing audio...")
            user_input = transcribe_audio(audio_file_path)
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
    chatbot(mode=mode)
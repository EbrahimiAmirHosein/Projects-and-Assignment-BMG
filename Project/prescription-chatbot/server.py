from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from openai import OpenAI
import json
import pyaudio
import wave

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes




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

# Function to transcribe audio
def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

# Function to chat with GPT
def chat_with_gpt(prompt, messages, model="gpt-4"):
    messages.append({"role": "user", "content": prompt})

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=5000,
        temperature=0
    )
    gpt_response = completion.choices[0].message.content.strip()

    messages.append({"role": "assistant", "content": gpt_response})

    return gpt_response

conversation_history = [
    {
        "role": "system",
        "content": "You are a helpful assistant that generates prescriptions. Always return the prescription in the following JSON format: (Warn doctor in Description if you suspect any drug conflicts). If any information is missing, use 'None' as the value for that field."
                   "{ "
                   "\"Prescriptions\": [ "
                   "{ "
                   "\"DiagnosisInformation\": { \"Diagnosis\": \"<diagnosis>\", \"Medicine\": \"<medicine>\" }, "
                   "\"MedicationDetails\": { "
                   "\"Dose\": \"<dose>\", "
                   "\"DoseUnit\": \"<dose unit>\", "
                   "\"DoseRoute\": \"<dose route>\", "
                   "\"Frequency\": \"<frequency>\", "
                   "\"FrequencyDuration\": \"<frequency duration>\", "
                   "\"FrequencyUnit\": \"<frequency unit>\", "
                   "\"Quantity\": \"<quantity>\", "
                   "\"QuantityUnit\": \"<quantity unit>\", "
                   "\"Refill\": \"<refill>\", "
                   "\"Pharmacy\": \"<pharmacy>\" "
                   "}, "
                   "\"Description\": \"<description>\" "
                   "} ], "
                   "}"
    }
]

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('text')
    if not user_input:
        return jsonify({"error": "No text provided"}), 400

    try:
        # Define a system message to instruct OpenAI to return structured JSON
        system_message = {
            "role": "system",
            "content": "You are a helpful assistant that generates prescriptions. Always return the prescription in the following JSON format: (Warn doctor in Description if you suspect any drug conflicts). If any information is missing, use 'None' as the value for that field."
                       "{ "
                       "\"Prescriptions\": [ "
                       "{ "
                       "\"DiagnosisInformation\": { \"Diagnosis\": \"<diagnosis>\", \"Medicine\": \"<medicine>\" }, "
                       "\"MedicationDetails\": { "
                       "\"Dose\": \"<dose>\", "
                       "\"DoseUnit\": \"<dose unit>\", "
                       "\"DoseRoute\": \"<dose route>\", "
                       "\"Frequency\": \"<frequency>\", "
                       "\"FrequencyDuration\": \"<frequency duration>\", "
                       "\"FrequencyUnit\": \"<frequency unit>\", "
                       "\"Quantity\": \"<quantity>\", "
                       "\"QuantityUnit\": \"<quantity unit>\", "
                       "\"Refill\": \"<refill>\", "
                       "\"Pharmacy\": \"<pharmacy>\" "
                       "}, "
                       "\"Description\": \"<description>\" "
                       "} ], "
                       "}"
        }

        # Send the user input to OpenAI
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[system_message, {"role": "user", "content": user_input}],
            max_tokens=500,  # Increased token limit
            temperature=0.1
        )

        # Extract the response from OpenAI
        gpt_response = completion.choices[0].message.content.strip()
        print("OpenAI Response:", gpt_response)  # Log the OpenAI response

        # Fix malformed JSON (e.g., replace hyphens in numeric fields with strings)
        gpt_response = gpt_response.replace('1-2', '"1-2"')  # Example fix for "1-2"

        # Check if the response is a complete JSON object
        if not gpt_response.strip().endswith("}"):
            print("OpenAI response is incomplete. Returning default response.")
            return jsonify({
                "response": {
                    "Prescriptions": [
                        {
                            "DiagnosisInformation": {"Diagnosis": None, "Medicine": None},
                            "MedicationDetails": {
                                "Dose": None,
                                "DoseUnit": None,
                                "DoseRoute": None,
                                "Frequency": None,
                                "FrequencyDuration": None,
                                "FrequencyUnit": None,
                                "Quantity": None,
                                "QuantityUnit": None,
                                "Refill": None,
                                "Pharmacy": None
                            },
                            "Description": "Please try again with proper prescription content."
                        }
                    ]
                }
            })

        # Parse the response into a JSON object
        try:
            prescription = json.loads(gpt_response)

            # Ensure all fields are present, filling in 'None' for missing fields
            for p in prescription.get("Prescriptions", []):
                p.setdefault("DiagnosisInformation", {"Diagnosis": None, "Medicine": None})
                p.setdefault("MedicationDetails", {
                    "Dose": None,
                    "DoseUnit": None,
                    "DoseRoute": None,
                    "Frequency": None,
                    "FrequencyDuration": None,
                    "FrequencyUnit": None,
                    "Quantity": None,
                    "QuantityUnit": None,
                    "Refill": None,
                    "Pharmacy": None
                })
                p.setdefault("Description", None)

            return jsonify({"response": prescription})
        except json.JSONDecodeError as e:
            print("Failed to parse OpenAI response as JSON. Returning default response.")
            return jsonify({
                "response": {
                    "Prescriptions": [
                        {
                            "DiagnosisInformation": {"Diagnosis": None, "Medicine": None},
                            "MedicationDetails": {
                                "Dose": None,
                                "DoseUnit": None,
                                "DoseRoute": None,
                                "Frequency": None,
                                "FrequencyDuration": None,
                                "FrequencyUnit": None,
                                "Quantity": None,
                                "QuantityUnit": None,
                                "Refill": None,
                                "Pharmacy": None
                            },
                            "Description": "Please try again with proper prescription content."
                        }
                    ]
                }
            })

    except Exception as e:
        print("Error in /chat endpoint. Returning default response.")
        return jsonify({
            "response": {
                "Prescriptions": [
                    {
                        "DiagnosisInformation": {"Diagnosis": None, "Medicine": None},
                        "MedicationDetails": {
                            "Dose": None,
                            "DoseUnit": None,
                            "DoseRoute": None,
                            "Frequency": None,
                            "FrequencyDuration": None,
                            "FrequencyUnit": None,
                            "Quantity": None,
                            "QuantityUnit": None,
                            "Refill": None,
                            "Pharmacy": None
                        },
                        "Description": "Please try again with proper prescription content."
                    }
                ]
            }
        })


@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Save the uploaded file temporarily
        file_path = "temp_recording.wav"
        file.save(file_path)

        # Transcribe the audio
        user_input = transcribe_audio(file_path)
        print("Transcribed Text:", user_input)

        # Define the system message (same as in /chat)
        system_message = {
            "role": "system",
            "content": "You are a helpful assistant that generates prescriptions. Always return the prescription in the following JSON format: (Warn doctor in Description if you suspect any drug conflicts). If any information is missing, use 'None' as the value for that field."
                       "{ "
                       "\"Prescriptions\": [ "
                       "{ "
                       "\"DiagnosisInformation\": { \"Diagnosis\": \"<diagnosis>\", \"Medicine\": \"<medicine>\" }, "
                       "\"MedicationDetails\": { "
                       "\"Dose\": \"<dose>\", "
                       "\"DoseUnit\": \"<dose unit>\", "
                       "\"DoseRoute\": \"<dose route>\", "
                       "\"Frequency\": \"<frequency>\", "
                       "\"FrequencyDuration\": \"<frequency duration>\", "
                       "\"FrequencyUnit\": \"<frequency unit>\", "
                       "\"Quantity\": \"<quantity>\", "
                       "\"QuantityUnit\": \"<quantity unit>\", "
                       "\"Refill\": \"<refill>\", "
                       "\"Pharmacy\": \"<pharmacy>\" "
                       "}, "
                       "\"Description\": \"<description>\" "
                       "} ], "
                       "}"
        }

        # Send the transcribed text to OpenAI
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[system_message, {"role": "user", "content": user_input}],
            max_tokens=500,
            temperature=0.1
        )

        # Extract the response from OpenAI
        gpt_response = completion.choices[0].message.content.strip()
        print("OpenAI Response:", gpt_response)

        # Fix malformed JSON (e.g., replace hyphens in numeric fields with strings)
        # gpt_response = gpt_response.replace('1-2', '"1-2"')

        # Check if the response is a complete JSON object
        if not gpt_response.strip().endswith("}"):
            
            print("OpenAI response is incomplete**********. Returning default response.")
            return jsonify({
                "response": {
                    "Prescriptions": [
                        {
                            "DiagnosisInformation": {"Diagnosis": None, "Medicine": None},
                            "MedicationDetails": {
                                "Dose": None,
                                "DoseUnit": None,
                                "DoseRoute": None,
                                "Frequency": None,
                                "FrequencyDuration": None,
                                "FrequencyUnit": None,
                                "Quantity": None,
                                "QuantityUnit": None,
                                "Refill": None,
                                "Pharmacy": None
                            },
                            "Description": "Please try again with proper prescription content."
                        }
                    ]
                }
            })

        # Parse the response into a JSON object
        try:
            prescription = json.loads(gpt_response)
            print("+++++++ ++++++++++" , prescription)
            # Ensure all fields are present, filling in 'None' for missing fields
            for p in prescription.get("Prescriptions", []):
                p.setdefault("DiagnosisInformation", {"Diagnosis": None, "Medicine": None})
                p.setdefault("MedicationDetails", {
                    "Dose": None,
                    "DoseUnit": None,
                    "DoseRoute": None,
                    "Frequency": None,
                    "FrequencyDuration": None,
                    "FrequencyUnit": None,
                    "Quantity": None,
                    "QuantityUnit": None,
                    "Refill": None,
                    "Pharmacy": None
                })
                p.setdefault("Description", None)

            return jsonify({"response": prescription})
        except json.JSONDecodeError as e:
            print("Failed to parse OpenAI response as JSON. Returning default response.")
            return jsonify({
                "response": {
                    "Prescriptions": [
                        {
                            "DiagnosisInformation": {"Diagnosis": None, "Medicine": None},
                            "MedicationDetails": {
                                "Dose": None,
                                "DoseUnit": None,
                                "DoseRoute": None,
                                "Frequency": None,
                                "FrequencyDuration": None,
                                "FrequencyUnit": None,
                                "Quantity": None,
                                "QuantityUnit": None,
                                "Refill": None,
                                "Pharmacy": None
                            },
                            "Description": "Please try again with proper prescription content."
                        }
                    ]
                }
            })

    except Exception as e:
        print("Error in /transcribe endpoint. Returning default response.")
        return jsonify({
            "response": {
                "Prescriptions": [
                    {
                        "DiagnosisInformation": {"Diagnosis": None, "Medicine": None},
                        "MedicationDetails": {
                            "Dose": None,
                            "DoseUnit": None,
                            "DoseRoute": None,
                            "Frequency": None,
                            "FrequencyDuration": None,
                            "FrequencyUnit": None,
                            "Quantity": None,
                            "QuantityUnit": None,
                            "Refill": None,
                            "Pharmacy": None
                        },
                        "Description": "Please try again with proper prescription content."
                    }
                ]
            }
        })

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
import base64
import tempfile
from mutagen.mp3 import MP3  # To calculate audio duration
import time
import pyaudio

audio = pyaudio.PyAudio()

# List all available audio devices
print("Available devices:")
for i in range(audio.get_device_count()):
    device_info = audio.get_device_info_by_index(i)
    print(f"Device {i}: {device_info['name']}")

# Check the default input device
try:
    default_device = audio.get_default_input_device_info()
    print(f"Default input device: {default_device}")
except OSError as e:
    print(f"Error getting default input device: {e}")

# Store cart in a temporary storage
cart = []

# Define the menu items dynamically
menu_items = {
    "Pizza": 10.99,
    "Burger": 8.49,
    "Pasta": 12.99,
    "Salad": 7.99,
    "Soda": 2.49
}

def generate_voice_response(text):
    """Generate an audio file for the response."""
    tts = gTTS(text)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    return temp_file.name

def calculate_total(cart):
    return sum(menu_items[item] for item in cart)

def process_input(input_text):
    global cart
    response = ""

    if "price of" in input_text:
        matched_items = [item for item in menu_items if item.lower() in input_text]
        if len(matched_items) == 1:
            item = matched_items[0]
            response = f"The price of {item} is ${menu_items[item]:.2f}."
        elif len(matched_items) > 1:
            response = f"I detected multiple items in your input: {', '.join(matched_items)}. Please ask for the price of one item at a time."
        else:
            response = "I couldn't find that item on the menu. Please ask for an item available in the menu."
    elif any(item.lower() in input_text for item in menu_items):
        matched_items = [item for item in menu_items if item.lower() in input_text]
        if len(matched_items) == 1:
            item = matched_items[0]
            cart.append(item)
            response = f"{item} has been added to your cart. Your current cart includes:\n"
            for cart_item in cart:
                response += f"- {cart_item}\n"
            response += "\nWould you like to add anything else?"
        elif len(matched_items) > 1:
            response = f"I detected multiple items in your input: {', '.join(matched_items)}. Please mention one item at a time."
    elif "menu" in input_text:
        response = "Here is our menu:\n"
        for item in menu_items.keys():
            response += f"{item}\n"
        response += "\nWhat would you like to order?"
    elif "final order" in input_text or "submit order" in input_text:
        if cart:
            total = calculate_total(cart)
            response = "Your final order includes:\n"
            for item in cart:
                response += f"- {item}\n"
            response += f"\nTotal amount: ${total:.2f}. Thank you for ordering!"
            cart.clear()
        else:
            response = "Your cart is empty. Would you like to order something?"
    elif "stop assistant" in input_text:
        response = "Stopping the assistant. Goodbye!"
        return response, True
    else:
        response = "I didn’t quite catch that. Please tell me what you’d like to order or ask about."

    return response, False

def autoplay_audio(audio_file):
    """Generate HTML to autoplay audio."""
    with open(audio_file, "rb") as f:
        audio_data = f.read()
    audio_base64 = base64.b64encode(audio_data).decode()
    audio_html = f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

def get_audio_duration(audio_file):
    """Get the duration of the audio file in seconds."""
    audio = MP3(audio_file)
    return audio.info.length

def continuous_listen_and_respond():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    initial_prompt = "Ready to take your order! Speak now."
    st.write(initial_prompt)

    # Generate and play the initial prompt
    initial_audio_file = generate_voice_response(initial_prompt)
    autoplay_audio(initial_audio_file)
    time.sleep(get_audio_duration(initial_audio_file))

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)

    while True:
        try:
            with mic as source:
                st.write("Listening...")
                audio = recognizer.listen(source, timeout=5)
                st.write("Processing your input...")
                input_text = recognizer.recognize_google(audio).lower()
                st.write(f"You said: {input_text}")

                # Process input and respond
                response, stop = process_input(input_text)
                st.write(response)

                # Generate and autoplay audio response
                audio_file = generate_voice_response(response)
                autoplay_audio(audio_file)

                # Wait for the audio to finish playing
                duration = get_audio_duration(audio_file)
                time.sleep(duration)

                # If stop command is detected, exit the loop
                if stop:
                    break

        except sr.WaitTimeoutError:
            st.write("Timeout! No input detected. Restarting...")
        except sr.UnknownValueError:
            st.write("Could not understand audio. Please try again.")
            error_response = "I couldn't understand what you said. Can you repeat?"
            error_audio = generate_voice_response(error_response)
            autoplay_audio(error_audio)
            time.sleep(get_audio_duration(error_audio))

# Streamlit app layout
st.title("Continuous Hands-Free Voice Assistant")

if st.button("Start Assistant"):
    continuous_listen_and_respond()

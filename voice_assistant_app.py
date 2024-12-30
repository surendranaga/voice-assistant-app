import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import speech_recognition as sr
from gtts import gTTS
import tempfile
import base64
import os
from mutagen.mp3 import MP3
import time

# Define the menu items dynamically
menu_items = {
    "Pizza": 10.99,
    "Burger": 8.49,
    "Pasta": 12.99,
    "Salad": 7.99,
    "Soda": 2.49
}
cart = []

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
                response += f"- {cart_item}\n"
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

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def recv(self, frame):
        audio_data = frame.to_ndarray()
        # Save audio to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name

        # Process audio with speech recognition
        with sr.AudioFile(temp_audio_path) as source:
            audio = self.recognizer.record(source)

        try:
            input_text = self.recognizer.recognize_google(audio).lower()
            st.write(f"You said: {input_text}")

            # Process the input and respond
            response, stop = process_input(input_text)
            st.write(response)

            # Generate and autoplay the response
            audio_response = generate_voice_response(response)
            autoplay_audio(audio_response)

            # Stop assistant if the command is given
            if stop:
                st.write("Assistant stopped.")

        except sr.UnknownValueError:
            st.write("Sorry, I could not understand the audio.")
        except sr.RequestError as e:
            st.write(f"Could not request results from Google Speech Recognition service; {e}")

# Streamlit app layout
st.title("Hands-Free Voice Assistant")

st.write("Speak into your microphone. The assistant will listen and respond.")

webrtc_streamer(
    key="hands-free-voice-assistant",
    mode=WebRtcMode.SENDONLY,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

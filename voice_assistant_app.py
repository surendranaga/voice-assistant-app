import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import speech_recognition as sr
from gtts import gTTS
import tempfile
import base64
import os

# Define menu items and cart
menu_items = {
    "Pizza": 10.99,
    "Burger": 8.49,
    "Pasta": 12.99,
    "Salad": 7.99,
    "Soda": 2.49
}
cart = []

def generate_voice_response(text):
    """Generate a voice response and save it as an MP3 file."""
    tts = gTTS(text)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    return temp_file.name

def autoplay_audio(audio_file):
    """Generate an autoplay audio player for the response."""
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
    """Custom audio processor to handle real-time speech recognition."""
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.message_displayed = False

    def recv(self, frame):
        """Process incoming audio frames."""
        audio_data = frame.to_ndarray()

        # Save audio to a temp file for recognition
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name

        # Process the audio file
        with sr.AudioFile(temp_audio_path) as source:
            audio = self.recognizer.record(source)

        try:
            input_text = self.recognizer.recognize_google(audio).lower()
            st.write(f"You said: {input_text}")

            # Process input and respond
            response = process_input(input_text)
            st.write(f"Assistant: {response}")

            # Play response as audio
            audio_response = generate_voice_response(response)
            autoplay_audio(audio_response)

        except sr.UnknownValueError:
            st.write("Sorry, I could not understand the audio.")
        except sr.RequestError as e:
            st.write(f"Error with the speech recognition service: {e}")

def process_input(input_text):
    """Process user input and generate a response."""
    global cart
    response = ""

    if "menu" in input_text:
        response = "Here is our menu: " + ", ".join(menu_items.keys()) + ". What would you like to order?"
    elif "add" in input_text:
        for item in menu_items:
            if item.lower() in input_text:
                cart.append(item)
                response = f"{item} has been added to your cart. Your current cart is: {', '.join(cart)}."
                break
        else:
            response = "I couldn't find that item on the menu. Please try again."
    elif "price of" in input_text:
        for item in menu_items:
            if item.lower() in input_text:
                response = f"The price of {item} is ${menu_items[item]:.2f}."
                break
        else:
            response = "I couldn't find that item on the menu. Please try again."
    elif "final order" in input_text:
        if cart:
            total = sum(menu_items[item] for item in cart)
            response = f"Your final order is: {', '.join(cart)}. The total is ${total:.2f}. Thank you for your order!"
            cart = []  # Clear the cart after finalizing
        else:
            response = "Your cart is empty. Would you like to order something?"
    elif "stop assistant" in input_text:
        response = "Stopping the assistant. Goodbye!"
    else:
        response = "I didn't understand that. Could you please repeat?"

    return response

# Streamlit UI
st.title("Hands-Free Voice Assistant")
st.write("Click 'Start' to begin. Speak your commands into the microphone.")

# Initialize webrtc streamer
webrtc_streamer(
    key="voice-assistant",
    mode=WebRtcMode.SENDONLY,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

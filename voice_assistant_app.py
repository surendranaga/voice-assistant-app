import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
import time
import base64

# Define menu items and cart
menu_items = {
    "Pizza": 10.99,
    "Burger": 8.49,
    "Pasta": 12.99,
    "Salad": 7.99,
    "Soda": 2.49
}
cart = []

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

def generate_voice_response(text):
    """Generate a voice response using gTTS."""
    tts = gTTS(text)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    return temp_file.name

def autoplay_audio(audio_file):
    """Play the response audio automatically."""
    with open(audio_file, "rb") as f:
        audio_data = f.read()
    audio_base64 = base64.b64encode(audio_data).decode()
    audio_html = f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

def listen_and_respond():
    """Continuously listen to the user and respond."""
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    st.write("Assistant is listening... Speak now!")
    autoplay_audio(generate_voice_response("Ready to take your order! Speak now."))

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            try:
                st.write("Listening...")
                audio = recognizer.listen(source)

                # Process the speech input
                input_text = recognizer.recognize_google(audio).lower()
                st.write(f"You said: {input_text}")

                # Generate and process the response
                response = process_input(input_text)
                st.write(f"Assistant: {response}")

                # Play the response
                audio_response = generate_voice_response(response)
                autoplay_audio(audio_response)

                # Stop assistant on command
                if "stop assistant" in input_text:
                    st.write("Stopping the assistant. Goodbye!")
                    break

            except sr.UnknownValueError:
                st.write("Sorry, I didn't catch that. Please try again.")
                autoplay_audio(generate_voice_response("Sorry, I didn't catch that. Please try again."))
            except sr.RequestError as e:
                st.write(f"Error with the speech recognition service: {e}")
                break

# Streamlit UI
st.title("Hands-Free Voice Assistant")
st.write("The assistant will continuously listen to your commands and respond.")

if st.button("Start Assistant"):
    listen_and_respond()

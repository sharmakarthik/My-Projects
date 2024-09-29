import tkinter as tk
from tkinter import Entry, Button
import speech_recognition as sr
import pyttsx3
import os
from transformers import GPT2Tokenizer, TFGPT2LMHeadModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
import json
import threading
from datetime import datetime
import pywhatkit
from googlesearch import search
import webbrowser
from PIL import Image, ImageTk
from googletrans import Translator
from gtts import gTTS
import pygame
import google_trans_new
from tkinter import simpledialog

# Load spaCy model for English
nlp = spacy.load("en_core_web_sm")

# Load pre-trained language model (GPT-2)
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
gpt_model = TFGPT2LMHeadModel.from_pretrained("gpt2")

# Load or collect data for training/fine-tuning (replace with your actual data loading)
with open('D:/downloads/tech.json', 'r') as file:
    data = json.load(file)

class ChatbotApp:
    def _init_(self):
        self.root = tk.Tk()
        self.root.title(f"NLPAssistant")
        self.root.geometry('1000x800')  # Increased dimensions
        self.root.resizable(False, False)
        self.message = tk.StringVar()
        self.is_listening = False
        self.greeted = False
        
        self.textcon = tk.Text(self.root, bd=1, width=70, height=15, wrap='word', font=('Times New Roman', 12))  # Adjusted dimensions and added wrap='word'
        self.textcon.pack(fill="both", expand=True)

        self.mes_win = Entry(self.root, width=50, xscrollcommand=True, textvariable=self.message, font=('Times New Roman', 12))
        self.mes_win.place(x=1, y=720, height=60, width=679)  # Adjusted dimensions
        self.mes_win.focus()

        self.textcon.config(fg='black')
        self.textcon.tag_config('usr', foreground='black', justify='right',font=('Times New Roman', 14, 'bold'), background='lightgreen')
        self.textcon.tag_config('bot', foreground='black', justify='left',font=('Times New Roman', 14, 'bold'), background='lightblue')

        self.textcon.insert(tk.END, "\n")

        self.exit_list = ['goodbye', 'bye', 'off']

        self.user_icon_path = "D:/downloads/user_icon.png"
        self.bot_icon_path = "D:/downloads/bot_icon.png"

        self.user_icon = ImageTk.PhotoImage(Image.open(self.user_icon_path).resize((40, 40), Image.ANTIALIAS))
        self.bot_icon = ImageTk.PhotoImage(Image.open(self.bot_icon_path).resize((40, 40), Image.ANTIALIAS))

        self.mic_image_path = "D:/downloads/mic.png"

        try:
            mic_icon = Image.open(self.mic_image_path)
            mic_icon = mic_icon.resize((mic_icon.width // 2, mic_icon.height // 3), Image.ANTIALIAS)
            self.mic_image = ImageTk.PhotoImage(mic_icon)
        except Exception as e:
            print(f"Error loading mic image: {e}")
            self.mic_image = None

        self.mic_button = Button(self.root, image=self.mic_image, bg='blue', activebackground='white',
                                 command=self.activate_mic, width=12, height=2, font=('Times New Roman', 14))
        self.mic_button.place(x=800, y=720, height=60, width=110)  # Adjusted dimensions

        self.send_button = Button(self.root, text='Send', bg='cyan', activebackground='grey',
                                   command=self.send_msz, width=12, height=2, font=('Times New Roman', 14, "bold"))
        self.send_button.place(x=680, y=720, height=60, width=110)  # Adjusted dimensions

        self.root.bind('<Return>', self.send_msz)
        self.engine = pyttsx3.init()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Add a vertical scrollbar
        scrollbar = tk.Scrollbar(self.root, command=self.textcon.yview)
        scrollbar.pack(side="right", fill="y")
        # Configure the text widget to use the scrollbar
        self.textcon.config(yscrollcommand=scrollbar.set)

        # Start the greeting in a separate thread
        threading.Thread(target=self.greet_user).start()

        self.root.mainloop()

    def greet_user(self):
        if not self.greeted:
            self.greeted = True
            # Insert bot icon and name for greeting
            self.insert_user('bot', 'Friday', self.bot_icon)
            # Insert bot response for greeting
            self.insert_message('bot', "Hi! I am Friday, your assistant.")
            current_time = datetime.now().strftime("%I:%M %p")
            # Insert additional bot response
            self.insert_message('bot', f"The current time is {current_time}")
            # Speak the greeting
            self.speak("Hello sir! I am Friday.")
            self.speak(f"The current time is {current_time}")

    def send_msz(self, event=None):
        usr_input = self.message.get()
        usr_input = usr_input.lower()

        # Insert user icon and name
        self.insert_user('usr', 'You', self.user_icon)
        # Insert user input
        self.insert_message('usr', f'{usr_input}')

        if usr_input.lower() in ["goodbye", "bye", "off"]:
            response = "Thank You sir, I hope I assisted you properly"
            # Insert bot icon and name
            self.insert_user('bot', 'Friday', self.bot_icon)
            # Insert bot response
            self.insert_message('bot', f'{response}')
            self.speak(response)
            self.is_listening = False  # Stop the microphone listening thread
            return self.root.destroy()

        elif "play" in usr_input.lower():
            # Open YouTube using pywhatkit
            pywhatkit.playonyt(usr_input.replace("play", "").strip())
            response = f"Playing {usr_input.replace('play', '').strip()} on YouTube..."
            # Insert bot icon and name
            self.insert_user('bot', 'Friday', self.bot_icon)
            # Insert bot response
            self.insert_message('bot', f'{response}')
            self.speak(response)
            self.mes_win.delete(0, tk.END)

        elif "search" in usr_input.lower():
            search_query = usr_input.replace("search", "").strip()
            self.perform_search(search_query)

        elif "translate" in usr_input or "language" in usr_input:
            self.trans()
            self.mes_win.delete(0, tk.END)

        else:
            response = self.handle_user_input(usr_input)
            # Insert bot icon and name
            self.insert_user('bot', 'Friday', self.bot_icon)
            # Insert bot response
            self.insert_message('bot', f'{response}')
            # Speak only if the input is from the microphone
            if hasattr(self, 'input_source') and self.input_source == 'mic':
                self.speak(response)
            self.mes_win.delete(0, tk.END)

    def insert_user(self, tag, name, icon):
        # Insert icon
        self.textcon.image_create(tk.END, image=icon)
        # Insert name
        self.textcon.insert(tk.END, f'{name}: ')

    def insert_message(self, tag, message):
        # Insert user or bot message with the specified tag
        self.textcon.insert(tk.END, message, tag)
        self.textcon.insert(tk.END, "\n")  
        self.textcon.see(tk.END)
        
    def perform_search(self, search_query):
        try:
            search_results = search(search_query, num=1, stop=1, pause=2)
            first_result = next(search_results)

            # Insert bot icon and name
            self.insert_user('bot', 'Friday: here is the link', self.bot_icon)
            self.textcon.tag_config('link', foreground='blue', underline=True)
            self.textcon.insert(tk.END, f'{first_result}\n', 'link')
            self.textcon.tag_bind('link', '<Button-1>', lambda event, link=first_result: self.open_link(link))
            self.textcon.insert(tk.END, "\n")
        except StopIteration:
            response = f"Sorry, I couldn't find information about {search_query}."
            # Insert bot icon and name
            self.insert_user('bot', 'Friday', self.bot_icon)
            # Insert bot response
            self.insert_message('bot', f'{response}\n')

        self.mes_win.delete(0, tk.END)

    def open_link(self, link):
        webbrowser.open(link)

    def activate_mic(self):
        if not self.is_listening:
            if self.mic_image:
                self.mic_button.config(image=self.mic_image)
            else:
                self.mic_button.config(text="Mic")

            self.is_listening = True
            threading.Thread(target=self.listen_continuously).start()

    def listen_continuously(self):
        r = sr.Recognizer()

        while self.is_listening:
            engine = pyttsx3.init()
            rate = engine.getProperty('rate')
            engine.setProperty('rate', 170)
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[1].id)

            with sr.Microphone() as source:
                r.energy_threshold = 400
                r.adjust_for_ambient_noise(source, 1.2)

                # Insert bot icon and name
                self.insert_user('bot', 'Friday', self.bot_icon)
                # Insert bot response
                self.insert_message('bot', "Listening...")

                try:
                    audio = r.listen(source)
                    text = r.recognize_google(audio)

                    # Set the recognized text to the message attribute
                    self.message.set(text)

                    if "search" in text.lower() or "play" in text.lower():
                        # Perform search or play directly
                        self.send_msz()
                    else:
                        # Set input source to 'mic' and handle the user input
                        self.input_source = 'mic'
                        self.send_msz()

                except sr.UnknownValueError:
                    print("Friday: Sorry, I could not understand the audio. Please try again.")

                except sr.RequestError as e:
                    print(f"Friday: There was an error with the speech recognition service: {e}")



    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def handle_user_input(self, user_input):
        user_keywords = self.extract_keywords(user_input)

        for example in data.get("intents", []):
            if "question" in example:
                question_keywords = [keyword for q in example["question"] for keyword in self.extract_keywords(q)]

                if all(keyword in question_keywords for keyword in user_keywords):
                    answer = example.get("answer", [])
                    return f"{answer}"

        input_ids = tokenizer.encode(user_input, return_tensors="tf")
        output = gpt_model.generate(input_ids, max_length=150, num_beams=5, no_repeat_ngram_size=2, top_k=50, top_p=0.95,
                                    temperature=0.7)
        bot_response = tokenizer.decode(output[0], skip_special_tokens=True)

        # Adjust the response based on the user's technical ability
        technical_ability = "tech"  # You need to get this value from somewhere
        if technical_ability == "tech":
            # Customize response for technical users
            pass
        else:
            # Customize response for non-technical users
            pass

        candidate_answers = ["Your first answer", "Your second answer", "Your third answer"]
        relevancy_scores = self.score_relevancy(user_input, candidate_answers)

        # Store or update relevancy scores for future learning
        # Update your model based on user feedback and learning algorithm

        return bot_response

    def extract_keywords(self, text):
        doc = nlp(text)
        return [token.text.lower() for token in doc if token.is_alpha]

    def score_relevancy(self, user_input, candidate_answers):
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([user_input] + candidate_answers)
        similarity_matrix = cosine_similarity(vectors)
        relevancy_scores = similarity_matrix[0][1:]
        return relevancy_scores

    def trans(self):
        languages = google_trans_new.LANGUAGES

        # Insert bot icon and name
        self.insert_user('bot', 'Friday', self.bot_icon)

        # Check if the translation process is already ongoing
        if not hasattr(self, 'translation_in_progress'):
            # Insert bot response
            self.insert_message('bot', 'Available Languages:')
            # Insert available languages in the GUI
            for code, lang in languages.items():
                self.insert_message('bot', f'{code}: {lang}')

            mic = sr.Microphone()
            r = sr.Recognizer()

            with mic as source:
                translator = Translator()

                # Get input language from user using simpledialog
                input_language = simpledialog.askstring("Input Language", "Select Language from:")
                # Get output language from user using simpledialog
                output_language = simpledialog.askstring("Output Language", "Select your Language To:")

                self.insert_user('bot', 'Friday', self.bot_icon)
                self.insert_message('bot', 'speak the text you need to be translated..')
                r.adjust_for_ambient_noise(source, duration=0.2)
                audio3 = r.listen(source)
                text3 = r.recognize_google(audio3)
                
                self.insert_user('usr', 'You', self.user_icon)
                self.insert_message('usr',text3.lower())

                # Translate the user's question
                translated_question = translator.translate(text3, src=input_language, dest=output_language).text.lower()

                # Update GUI with the translation
                self.insert_user('bot', 'Friday', self.bot_icon)
                self.insert_message('bot', f'Translation: {translated_question}')
                if hasattr(self, 'input_source') and self.input_source == 'mic':
                    self.speak(translated_question)
                self.textcon.insert(tk.END, "\n")

                # Set the variable to indicate that translation is in progress
                self.translation_in_progress = True
                return  # Exit the function to avoid rerunning the translation process

        # If translation process is already in progress, clear the variable
        self.translation_in_progress = False


    def on_close(self):
        self.is_listening = False
        self.root.destroy()

if _name_ == "_main_":
    chatbot_app = ChatbotApp()
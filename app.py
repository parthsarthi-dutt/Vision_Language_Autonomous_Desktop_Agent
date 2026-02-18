"""
Virtual Assistant - AI-powered task automation with OmniParser screen understanding and Voice Input
Install dependencies:
pip install PyQt5 mss pillow google-generativeai pyautogui pynput requests python-dotenv SpeechRecognition pyaudio pocketsphinx
"""
import sys
import io
import json
import threading
import time
import math
import base64
import requests
from PyQt5 import QtWidgets, QtCore, QtGui
import mss
from PIL import Image
import pyautogui
import google.generativeai as genai
from dotenv import load_dotenv
import os 
import signal
from pynput import mouse
import numpy as np
import speech_recognition as sr

signal.signal(signal.SIGINT, signal.SIG_DFL)
load_dotenv()

# ----- Configuration -----
API_KEY = os.getenv("gemini_key")
MODEL_NAME = "gemini-2.5-flash"
OMNIPARSER_URL = "https://arrival-late-can-mason.trycloudflare.com/process" # This is a server running the OmniParser model 
HIDE_AND_CAPTURE_DELAY_MS = 120
SCREEN_CHANGE_THRESHOLD = 0.05  # 5% difference threshold
BUFFER_DELAY_MS = 500  # 500ms buffer after screen change detected
MAX_WAIT_FOR_CHANGE = 4000  # 4 seconds max wait

# Voice Recognition Settings
USE_OFFLINE_RECOGNITION = False  # Set to True for offline, False for Google API
WAKE_WORD = "hey vision"  # Wake word to activate voice input
SILENCE_DURATION = 1.5  # Seconds of silence before stopping recording
VOICE_ENABLED = True  # Global flag to enable/disable voice input

# System prompt for AI with OmniParser
SYSTEM_PROMPT = """You are a virtual assistant that helps users automate tasks by analyzing screenshots with numbered UI elements. Before making decisions, carefully examine the screenshot and the parsed content of each numbered element to understand what is the current state of the screen.

IMPORTANT: You will receive a screenshot where ALL clickable elements are labeled with numbers (e.g., [1], [2], [3]). You must respond with the NUMBER of the element to interact with. The numbers for each box is written adjacent to the bbox in the image, but sometimes it can be misleading due to multiple boxes together, for this i have given you the parsed content of each element as well, which contains the content of each box, so use that to verify what each element is. Also note that to open a program/application/desktop icon or a folder, you need to DOUBLE click the icon.

RESPONSE FORMAT:
You must respond with ONLY a valid JSON object:
{
  "steps": [
    {
      "type": "click" | "keyboard" | "scroll" | "wait" | "ask_question" | "end",
      ... additional fields based on type ...
    }
  ]
}

STEP TYPES:

1. "click" - Click on a numbered element
   {
     "type": "click",
     "element_number": 5,
     "description": "Click on the Chrome browser icon",
     "double_click": false
   }
   - element_number: The number shown in the screenshot (e.g., if you see [5], use 5)
   - description: What you're clicking
   - double_click: true for opening apps, false otherwise

2. "keyboard" - Type text (MUST be preceded by a click)
   {
     "type": "keyboard",
     "content": "lata mangeshkar songs",
     "element_number": 3,
     "description": "Type search query"
   }
   - element_number: The input field number where text will be typed
   - content: Text to type

3. "scroll" - Scroll the page
   {
     "type": "scroll",
     "magnitude": -3,
     "description": "Scroll down"
   }
   - magnitude: Negative for down, positive for up

4. "wait_and_send_image" - Wait for screen to stabilize and capture new screenshot
   {
     "type": "wait_and_send_image",
     "description": "Wait for page to load and analyze next state"
   }

5. "ask_question" - Ask user for clarification
   {
     "type": "ask_question",
     "question": "Which browser would you like me to open?",
     "description": "Need user input"
   }

6. "end" - Task completed
   {
     "type": "end",
     "message": "Successfully completed the task",
     "description": "Task complete"
   }

RULES:
1. Look at the numbered elements in the screenshot
2. Choose the appropriate element number for your action
3. If you are sure that clicking an element or typing text will not change the windows , you can chain multiple steps before a "wait_and_send_image"

4. ALWAYS end your steps array with either "wait_and_send_image", "end", or "ask_question"
5. Response must be ONLY valid JSON
6. if you get stuck at a step, i.e. you keep doing the same action again and again, you should try to do that by a different approach and if that still does not work you can ask the user for clarification using the "ask_question" step type.
7. if any personal information of the user is required, you should ask the user for that using the "ask_question" step type, do not use example values, you are working in a real work scenario not testing environment.
"""


class VoiceRecognitionThread(QtCore.QThread):
    """Thread for handling voice recognition"""
    wake_word_detected = QtCore.pyqtSignal()
    text_recognized = QtCore.pyqtSignal(str)
    listening_started = QtCore.pyqtSignal()
    listening_stopped = QtCore.pyqtSignal()
    error_occurred = QtCore.pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = SILENCE_DURATION
        self.is_running = False
        self.is_listening_for_command = False
        self.microphone = None
        
    def run(self):
        """Main voice recognition loop"""
        self.is_running = True
        
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                print("🎤 Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("✓ Voice recognition ready")
        except Exception as e:
            print(f"⚠️ Microphone initialization error: {e}")
            self.error_occurred.emit(f"Microphone error: {str(e)}")
            return
        
        while self.is_running:
            if not self.is_listening_for_command:
                # Listen for wake word
                self._listen_for_wake_word()
            else:
                # Listen for command
                self._listen_for_command()
            
            time.sleep(0.1)
    
    def _listen_for_wake_word(self):
        """Listen for the wake word"""
        try:
            with self.microphone as source:
                # Short listen with timeout
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                
            # Recognize speech
            try:
                if USE_OFFLINE_RECOGNITION:
                    text = self.recognizer.recognize_sphinx(audio).lower()
                else:
                    text = self.recognizer.recognize_google(audio).lower()
                
                print(f"🎤 Heard: {text}")
                
                # Check for wake word
                if WAKE_WORD.lower() in text:
                    print(f"✓ Wake word detected: '{WAKE_WORD}'")
                    self.wake_word_detected.emit()
                    self.is_listening_for_command = True
                    
            except sr.UnknownValueError:
                pass  # Could not understand audio
            except sr.RequestError as e:
                if not USE_OFFLINE_RECOGNITION:
                    print(f"⚠️ Recognition service error: {e}")
                    
        except sr.WaitTimeoutError:
            pass  # Timeout, continue listening
        except Exception as e:
            print(f"⚠️ Wake word listening error: {e}")
    
    def _listen_for_command(self):
        """Listen for voice command after wake word"""
        try:
            self.listening_started.emit()
            print("🎤 Listening for command...")
            
            with self.microphone as source:
                # Listen for command with longer timeout
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("🎤 Processing speech...")
            
            # Recognize speech
            try:
                if USE_OFFLINE_RECOGNITION:
                    text = self.recognizer.recognize_sphinx(audio)
                else:
                    text = self.recognizer.recognize_google(audio)
                
                print(f"✓ Recognized: {text}")
                self.text_recognized.emit(text)
                
            except sr.UnknownValueError:
                print("⚠️ Could not understand audio")
                self.error_occurred.emit("Could not understand audio")
            except sr.RequestError as e:
                print(f"⚠️ Recognition error: {e}")
                self.error_occurred.emit(f"Recognition error: {str(e)}")
                
        except sr.WaitTimeoutError:
            print("⚠️ No speech detected")
            self.error_occurred.emit("No speech detected")
        except Exception as e:
            print(f"⚠️ Command listening error: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.listening_stopped.emit()
            self.is_listening_for_command = False
    
    def stop(self):
        """Stop the voice recognition thread"""
        self.is_running = False
        self.is_listening_for_command = False


class StatusOverlay(QtWidgets.QWidget):
    """Floating status overlay with loading animation"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        # Main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container widget with background
        self.container = QtWidgets.QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background: rgba(30, 30, 30, 0.95);
                border-radius: 15px;
                border: 2px solid rgba(100, 100, 100, 0.3);
            }
        """)
        
        container_layout = QtWidgets.QVBoxLayout()
        container_layout.setContentsMargins(20, 15, 20, 15)
        container_layout.setSpacing(10)
        
        # Status text
        self.status_label = QtWidgets.QLabel("Initializing...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        container_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(50, 50, 50, 0.5);
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2ecc71);
                border-radius: 2px;
            }
        """)
        container_layout.addWidget(self.progress_bar)
        
        # Detail text
        self.detail_label = QtWidgets.QLabel("")
        self.detail_label.setStyleSheet("""
            QLabel {
                color: rgba(200, 200, 200, 0.9);
                font-size: 11px;
            }
        """)
        self.detail_label.setAlignment(QtCore.Qt.AlignCenter)
        self.detail_label.setWordWrap(True)
        container_layout.addWidget(self.detail_label)
        
        self.container.setLayout(container_layout)
        main_layout.addWidget(self.container)
        self.setLayout(main_layout)
        
        # Position at bottom center
        self.setFixedWidth(800)
        self.setFixedHeight(200)
        self.position_overlay()
        
        # Animation timer for loading effect
        self.animation_timer = QtCore.QTimer()
        self.animation_timer.timeout.connect(self._animate)
        self.animation_frame = 0
        
    def position_overlay(self):
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = screen.height() - self.height() - 80
        self.setGeometry(x, y, self.width(), self.height())
    
    def set_status(self, status, detail="", show_progress=True):
        """Update status message"""
        self.status_label.setText(status)
        self.detail_label.setText(detail)
        
        if show_progress:
            self.progress_bar.show()
            if not self.animation_timer.isActive():
                self.animation_timer.start(50)
        else:
            self.progress_bar.hide()
            self.animation_timer.stop()
        
        self.adjustSize()
        self.position_overlay()
    
    def _animate(self):
        """Simple animation effect"""
        self.animation_frame = (self.animation_frame + 1) % 360
    
    def showEvent(self, event):
        self.position_overlay()
        super().showEvent(event)


class VoiceIndicator(QtWidgets.QWidget):
    """Visual indicator for voice input status"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Container
        self.container = QtWidgets.QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background: rgba(52, 152, 219, 0.95);
                border-radius: 12px;
                border: 2px solid rgba(41, 128, 185, 0.8);
            }
        """)
        
        container_layout = QtWidgets.QHBoxLayout()
        container_layout.setContentsMargins(15, 10, 15, 10)
        container_layout.setSpacing(10)
        
        # Microphone icon
        self.mic_label = QtWidgets.QLabel("🎤")
        self.mic_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
            }
        """)
        container_layout.addWidget(self.mic_label)
        
        # Status text
        self.status_label = QtWidgets.QLabel("Listening...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        container_layout.addWidget(self.status_label)
        
        self.container.setLayout(container_layout)
        layout.addWidget(self.container)
        self.setLayout(layout)
        
        self.setFixedSize(200, 50)
        
        # Animation
        self.animation_timer = QtCore.QTimer()
        self.animation_timer.timeout.connect(self._animate)
        self.animation_state = 0
    
    def show_listening(self):
        """Show listening indicator"""
        self.status_label.setText("Listening...")
        self.container.setStyleSheet("""
            QWidget {
                background: rgba(46, 204, 113, 0.95);
                border-radius: 12px;
                border: 2px solid rgba(39, 174, 96, 0.8);
            }
        """)
        self.position_indicator()
        self.show()
        self.animation_timer.start(500)
    
    def show_processing(self):
        """Show processing indicator"""
        self.status_label.setText("Processing...")
        self.container.setStyleSheet("""
            QWidget {
                background: rgba(241, 196, 15, 0.95);
                border-radius: 12px;
                border: 2px solid rgba(243, 156, 18, 0.8);
            }
        """)
    
    def position_indicator(self):
        """Position at top center"""
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = 100
        self.setGeometry(x, y, self.width(), self.height())
    
    def _animate(self):
        """Pulse animation"""
        self.animation_state = (self.animation_state + 1) % 2
        if self.animation_state == 0:
            self.mic_label.setText("🎤")
        else:
            self.mic_label.setText("🎙️")
    
    def hideEvent(self, event):
        self.animation_timer.stop()
        super().hideEvent(event)


class FloatingButtonPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFixedWidth(120)
        self.setFixedHeight(180)
        
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        self.abort_btn = QtWidgets.QPushButton("Abort")
        self.abort_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px 0px;
                font-size: 15px;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        layout.addWidget(self.abort_btn)
        
        self.retry_btn = QtWidgets.QPushButton("Retry")
        self.retry_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px 0px;
                font-size: 15px;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        layout.addWidget(self.retry_btn)
        
        # Voice toggle button
        self.voice_btn = QtWidgets.QPushButton("🎤 Voice")
        self.voice_btn.setCheckable(True)
        self.voice_btn.setChecked(VOICE_ENABLED)
        self.update_voice_button_style()
        layout.addWidget(self.voice_btn)
        
        self.quit_btn = QtWidgets.QPushButton("Quit")
        self.quit_btn.setStyleSheet("""
            QPushButton {
                background: #7f8c8d;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px 0px;
                font-size: 15px;
            }
            QPushButton:hover { background: #636e72; }
        """)
        layout.addWidget(self.quit_btn)
        
        self.setLayout(layout)
        self.position_panel()
        self.quit_btn.clicked.connect(self.on_quit)
    
    def update_voice_button_style(self):
        """Update voice button style based on state"""
        if self.voice_btn.isChecked():
            self.voice_btn.setStyleSheet("""
                QPushButton {
                    background: #27ae60;
                    color: white;
                    font-weight: bold;
                    border-radius: 8px;
                    padding: 10px 0px;
                    font-size: 15px;
                }
                QPushButton:hover { background: #229954; }
            """)
        else:
            self.voice_btn.setStyleSheet("""
                QPushButton {
                    background: #95a5a6;
                    color: white;
                    font-weight: bold;
                    border-radius: 8px;
                    padding: 10px 0px;
                    font-size: 15px;
                }
                QPushButton:hover { background: #7f8c8d; }
            """)
    
    def on_quit(self):
        QtWidgets.QApplication.quit()
    
    def position_panel(self):
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        w = self.width()
        h = self.height()
        x = screen.right() - w - 10
        y = (screen.height() - h) // 2
        self.setGeometry(x, y, w, h)
    
    def showEvent(self, event):
        self.position_panel()
        super().showEvent(event)


class TaskContext:
    """Stores conversation history and task context"""
    def __init__(self):
        self.original_task = ""
        self.conversation_history = []
        self.steps_completed = []
        self.last_screenshot_path = None
    
    def reset(self):
        self.original_task = ""
        self.conversation_history = []
        self.steps_completed = []
        self.last_screenshot_path = None
    
    def add_user_message(self, msg):
        self.conversation_history.append({"role": "user", "content": msg})
    
    def add_step_completed(self, step):
        self.steps_completed.append(step)
    
    def get_context_summary(self):
        summary = f"Original task: {self.original_task}\n\n"
        summary += f"Steps completed so far:\n"
        for i, step in enumerate(self.steps_completed, 1):
            summary += f"{i}. {step.get('type', 'unknown')} - {step.get('description', 'no description')}\n"
        return summary


def call_omniparser(image_path, box_threshold=0.05, iou_threshold=0.1):
    """Call OmniParser API and return parsed results"""
    try:
        with open(image_path, "rb") as img_file:
            files = {"image": img_file}
            data = {
                "box_threshold": box_threshold,
                "iou_threshold": iou_threshold
            }
            print("📡 Calling OmniParser...")
            response = requests.post(OMNIPARSER_URL, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ OmniParser found {len(result['parsed_content'])} elements")
            
            # Save annotated image
            image_data = base64.b64decode(result["image_base64"])
            img = Image.open(io.BytesIO(image_data))
            timestamp = int(time.time() * 1000)
            annotated_path = f"annotated_screen_{timestamp}.png"
            img.save(annotated_path)
            print(f"✓ Annotated image saved: {annotated_path}")
            return result["parsed_content"], annotated_path
        else:
            print(f"⚠️ OmniParser error: {response.text}")
            return None, None
    except Exception as e:
        print(f"⚠️ Error calling OmniParser: {e}")
        return None, None


def compare_screenshots(img1_path, img2_path, threshold=SCREEN_CHANGE_THRESHOLD):
    """Compare two screenshots and return if they differ significantly"""
    try:
        img1 = Image.open(img1_path).convert('RGB')
        img2 = Image.open(img2_path).convert('RGB')
        
        # Resize to same size if different
        if img1.size != img2.size:
            img2 = img2.resize(img1.size)
        
        # Convert to numpy arrays
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # Calculate difference
        diff = np.abs(arr1.astype(float) - arr2.astype(float))
        mean_diff = np.mean(diff) / 255.0  # Normalize to 0-1
        
        changed = mean_diff > threshold
        print(f"📊 Screen difference: {mean_diff*100:.2f}% (threshold: {threshold*100:.0f}%)")
        
        return changed, mean_diff
    except Exception as e:
        print(f"⚠️ Error comparing screenshots: {e}")
        return True, 1.0  # Assume changed on error


def send_to_gemini(api_key, prompt, annotated_image_path, parsed_elements, context=None):
    """Send annotated image and parsed elements to Gemini"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    
    # Load annotated image
    with open(annotated_image_path, 'rb') as f:
        img_bytes = f.read()
    pil_img = Image.open(io.BytesIO(img_bytes))
    
    # Build prompt
    full_prompt = SYSTEM_PROMPT + "\n\n"
    full_prompt += f"**AVAILABLE ELEMENTS**:\n"
    to_save=""
    for i, elem in enumerate(parsed_elements, 0):
        to_save+=f"[{i}]: {elem}\n"
    full_prompt += "\n"

    # Save full prompt to a text file with timestamp
    timestamp = int(time.time())
    prompt_filename = f"gemini_prompt_{timestamp}.txt"
    with open(prompt_filename, "w", encoding="utf-8") as f:
        f.write(full_prompt)
        f.write(to_save)
    print(f"✓ Full prompt saved to {prompt_filename}")
    
    if context and context.steps_completed:
        full_prompt += context.get_context_summary() + "\n\n"
    
    full_prompt += f"User request: {prompt}\n\n"
    full_prompt += "Analyze the numbered screenshot and provide the next step(s) as JSON.\n"
    
    # Generate response
    response = model.generate_content([full_prompt, pil_img])
    response_text = response.text.strip()
    
    # Extract JSON
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    
    # Parse JSON
    try:
        result = json.loads(response_text)
        return result, response_text
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse JSON: {response_text}\nError: {e}")


class VirtualAssistant(QtWidgets.QWidget):
    # Signals for thread-safe UI updates
    status_signal = QtCore.pyqtSignal(str, str, bool)  # status, detail, show_progress
    
    def __init__(self):
        super().__init__()
        self.context = TaskContext()
        self._pending_steps = []
        self._current_step_index = 0
        self._parsed_elements = []
        self._awaiting_action = False
        self._voice_enabled = VOICE_ENABLED
        
        # Create status overlay
        self.status_overlay = StatusOverlay()
        self.status_signal.connect(self._update_status_overlay)
        
        # Create voice indicator
        self.voice_indicator = VoiceIndicator()
        
        # Create voice recognition thread
        self.voice_thread = None
        
        self.init_ui()
        
        # Start voice recognition if enabled
        if self._voice_enabled:
            self.start_voice_recognition()
    
    def init_ui(self):
        self.setWindowTitle("AI Assistant with OmniParser")
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool |
            QtCore.Qt.FramelessWindowHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        layout = QtWidgets.QVBoxLayout()
        
        self.status_label = QtWidgets.QLabel("Ready - Enter a task (or say 'Hey Vision')")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.status_label)
        
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText('Type or say: "Hey Vision, play lata mangeshkar songs"')
        self.input.returnPressed.connect(self.on_enter)

        # Voice activation button
        voice_input_layout = QtWidgets.QHBoxLayout()
        voice_input_layout.setSpacing(10)

        self.voice_activate_btn = QtWidgets.QPushButton("🎙️ Speak")
        self.voice_activate_btn.setFixedHeight(50)
        self.voice_activate_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover { background: #2980b9; }
            QPushButton:pressed { background: #21618c; }
        """)
        self.voice_activate_btn.clicked.connect(self.manual_voice_activate)

        voice_input_layout.addWidget(self.input, stretch=8)
        voice_input_layout.addWidget(self.voice_activate_btn, stretch=1)

        layout.addLayout(voice_input_layout)
        self.input.setMinimumWidth(1000)
        self.input.setMinimumHeight(100)
        self.input.setStyleSheet("""
            QLineEdit {
                padding: 24px;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.95);
                color: #111;
                font-size: 30px;
            }
        """)
        # layout.addWidget(self.input)

        
        self.button_panel = FloatingButtonPanel()
        self.button_panel.abort_btn.clicked.connect(self.on_abort)
        self.button_panel.retry_btn.clicked.connect(self.on_retry)
        self.button_panel.quit_btn.clicked.connect(QtWidgets.QApplication.quit)
        self.button_panel.voice_btn.clicked.connect(self.toggle_voice_input)
        self.button_panel.show()
        
        self.setLayout(layout)
        self.setFixedHeight(150)
        
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        w = 900
        h = 220
        x = (screen.width() - w) // 2
        y = 40
        self.setGeometry(x, y, w, h)
    
    def start_voice_recognition(self):
        """Start voice recognition thread"""
        if self.voice_thread is None or not self.voice_thread.isRunning():
            self.voice_thread = VoiceRecognitionThread()
            self.voice_thread.wake_word_detected.connect(self.on_wake_word_detected)
            self.voice_thread.text_recognized.connect(self.on_voice_text_recognized)
            self.voice_thread.listening_started.connect(self.on_listening_started)
            self.voice_thread.listening_stopped.connect(self.on_listening_stopped)
            self.voice_thread.error_occurred.connect(self.on_voice_error)
            self.voice_thread.start()
            print("✓ Voice recognition started")
    
    def stop_voice_recognition(self):
        """Stop voice recognition thread"""
        if self.voice_thread and self.voice_thread.isRunning():
            self.voice_thread.stop()
            self.voice_thread.wait(2000)
            print("✓ Voice recognition stopped")
    
    def toggle_voice_input(self):
        """Toggle voice input on/off"""
        self._voice_enabled = self.button_panel.voice_btn.isChecked()
        self.button_panel.update_voice_button_style()
        
        if self._voice_enabled:
            self.start_voice_recognition()
            self.status_label.setText("Ready - Enter a task (or say 'Hey Vision')")
            self.input.setPlaceholderText('Type or say: "Hey Vision, play lata mangeshkar songs"')
            print("✓ Voice input enabled")
        else:
            self.stop_voice_recognition()
            self.status_label.setText("Ready - Enter a task")
            self.input.setPlaceholderText('e.g., "play lata mangeshkar songs"')
            print("✓ Voice input disabled")
    
    def manual_voice_activate(self):
        """Manually activate voice listening without wake word"""
        if not self._voice_enabled:
            QtWidgets.QMessageBox.warning(self, "Voice Disabled", "Please enable voice input first using the 🎤 Voice button")
            return
        
        if not self.input.isEnabled():
            return  # Don't activate during task execution
        
        if self.voice_thread and self.voice_thread.isRunning():
            # Trigger manual listening
            self.voice_thread.is_listening_for_command = True
            print("🎤 Manual voice activation triggered")
            
    @QtCore.pyqtSlot()
    def on_wake_word_detected(self):
        """Called when wake word is detected"""
        print("✓ Wake word detected - ready for command")
        # Don't show indicator yet, wait for listening_started
    
    @QtCore.pyqtSlot()
    def on_listening_started(self):
        """Called when listening for command starts"""
        if self.input.isEnabled():
            self.voice_indicator.show_listening()
            print("🎤 Voice indicator shown")
    
    @QtCore.pyqtSlot()
    def on_listening_stopped(self):
        """Called when listening stops"""
        self.voice_indicator.hide()
        print("🎤 Voice indicator hidden")
    
    @QtCore.pyqtSlot(str)
    def on_voice_text_recognized(self, text):
        """Called when voice text is recognized"""
        if self.input.isEnabled():
            print(f"✓ Voice command: {text}")
            self.input.setText(text)
            # Automatically submit
            QtCore.QTimer.singleShot(2000, self.on_enter)
    
    @QtCore.pyqtSlot(str)
    def on_voice_error(self, error_msg):
        """Called when voice recognition error occurs"""
        print(f"⚠️ Voice error: {error_msg}")
        # Don't show error to user, just hide indicator
        self.voice_indicator.hide()
    
    @QtCore.pyqtSlot(str, str, bool)
    def _update_status_overlay(self, status, detail, show_progress):
        """Update status overlay from signal"""
        self.status_overlay.set_status(status, detail, show_progress)
        if not self.status_overlay.isVisible():
            self.status_overlay.show()
    
    def show_status(self, status, detail="", show_progress=True):
        """Thread-safe status update"""
        self.status_signal.emit(status, detail, show_progress)
    
    def hide_status(self):
        """Hide status overlay"""
        QtCore.QMetaObject.invokeMethod(
            self.status_overlay, "hide",
            QtCore.Qt.QueuedConnection
        )
    
    def on_abort(self):
        self.context.reset()
        self.hide_status()
        status_text = "Task aborted - Ready for new task"
        if self._voice_enabled:
            status_text += " (or say 'Hey Vision')"
        self.update_status(status_text)
        
        placeholder = 'Type or say: "Hey Vision, play lata mangeshkar songs"' if self._voice_enabled else 'e.g., "play lata mangeshkar songs"'
        self.input.setPlaceholderText(placeholder)
        self.input.setDisabled(False)
        self.input.clear()
        self.show()
        self.input.setFocus()
    
    def on_retry(self):
        self.update_status("Retrying: capturing screenshot...")
        self.input.setDisabled(True)
        self.hide()
        QtCore.QTimer.singleShot(HIDE_AND_CAPTURE_DELAY_MS, 
                                lambda: self.capture_and_process(self.context.original_task))
    
    def update_status(self, text):
        self.status_label.setText(text)
        if hasattr(self, 'button_panel') and not self.button_panel.isVisible():
            self.button_panel.show()
    
    def on_enter(self):
        user_input = self.input.text().strip()
        if not user_input:
            return
        
        if not self.context.original_task:
            self.context.original_task = user_input
            self.update_status(f"Task: {user_input}")
        else:
            self.context.add_user_message(user_input)
        
        self.input.clear()
        self.input.setDisabled(True)
        self.hide()
        QtCore.QTimer.singleShot(HIDE_AND_CAPTURE_DELAY_MS, 
                                lambda: self.capture_and_process(user_input))
    
    def capture_and_process(self, prompt):
        """Capture screenshot and process with OmniParser"""
        self.show_status("Capturing...", "Taking screenshot")
        self.hide_status()
        time.sleep(0.1)  # Ensure UI is hidden
        
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            img = sct.grab(monitor)
            pil_img = Image.frombytes("RGB", img.size, img.rgb)
            
            screenshot_path = "current_screen.png"
            pil_img.save(screenshot_path)
            self.context.last_screenshot_path = screenshot_path
            print(f"📸 Screenshot saved: {screenshot_path}")

        self.show_status("Processing...", "Analyzing screenshot with OmniParser")

        threading.Thread(target=self._process_with_omniparser, 
                        args=(prompt, screenshot_path), daemon=True).start()
    
    def _process_with_omniparser(self, prompt, screenshot_path):
        """Process screenshot with OmniParser then send to Gemini"""
        try:
            # Call OmniParser
            self.show_status("Analyzing Screen...", "Detecting UI elements with OmniParser")
            parsed_elements, annotated_path = call_omniparser(screenshot_path)
            
            if not parsed_elements or not annotated_path:
                raise Exception("OmniParser failed to process image")
            
            self._parsed_elements = parsed_elements
            self.show_status("Thinking...", f"Found {len(parsed_elements)} elements • Asking AI for next steps")
            
            # Send to Gemini
            response_json, raw_response = send_to_gemini(
                API_KEY, prompt, annotated_path, parsed_elements, self.context
            )
            print("\n===== RAW LLM RESPONSE =====\n" + raw_response + "\n===========================\n")
            timestamp = int(time.time())
            prompt_filename = f"gemini_response_{timestamp}.txt"
            with open(prompt_filename, "w", encoding="utf-8") as f:
                f.write(raw_response)
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ Processing error: {error_msg}")
            self.show_status("Error", f"Failed: {error_msg[:50]}...", False)
            time.sleep(3)
            QtCore.QMetaObject.invokeMethod(self, "_show_error", 
                                          QtCore.Qt.QueuedConnection,
                                          QtCore.Q_ARG(str, error_msg))
            return
        
        if not isinstance(response_json, dict) or "steps" not in response_json:
            error_msg = "Invalid response format from AI"
            self.show_status("Error", error_msg, False)
            time.sleep(2)
            QtCore.QMetaObject.invokeMethod(self, "_show_error", 
                                          QtCore.Qt.QueuedConnection,
                                          QtCore.Q_ARG(str, error_msg))
            return
        
        steps = response_json["steps"]
        if not isinstance(steps, list) or len(steps) == 0:
            error_msg = "No steps provided by AI"
            self.show_status("Error", error_msg, False)
            time.sleep(2)
            QtCore.QMetaObject.invokeMethod(self, "_show_error", 
                                          QtCore.Qt.QueuedConnection,
                                          QtCore.Q_ARG(str, error_msg))
            return
        
        self.show_status("Executing...", f"Performing {len(steps)} step(s)")
        QtCore.QMetaObject.invokeMethod(self, "_execute_steps", 
                                      QtCore.Qt.QueuedConnection,
                                      QtCore.Q_ARG(list, steps))
    
    @QtCore.pyqtSlot(list)
    def _execute_steps(self, steps):
        self._pending_steps = steps
        self._current_step_index = 0
        self._execute_next_step()
    
    def _execute_next_step(self):
        if self._current_step_index >= len(self._pending_steps):
            print(f"✓ All {len(self._pending_steps)} steps completed")
            
            # Check the last step to determine what to do next
            last_step = self._pending_steps[-1] if self._pending_steps else None
            last_step_type = last_step.get("type") if last_step else None
            
            # If last step was wait_and_send_image, capture and send to Gemini
            if last_step_type == "wait_and_send_image":
                print("📸 Last step was wait_and_send_image - capturing new screenshot for Gemini")
                self.show_status("Analyzing...", "Capturing new state for AI analysis", True)
                QtCore.QTimer.singleShot(HIDE_AND_CAPTURE_DELAY_MS, 
                                        lambda: self.capture_and_process(self.context.original_task))
                return
            
            # If last step was end or ask_question, we're done (handled in their execute methods)
            if last_step_type in ["end", "ask_question"]:
                self.hide_status()
                return
            
            # Safety: If Gemini forgot to add wait_and_send_image or end, send image anyway
            print("⚠️ No wait_and_send_image or end in response - sending image anyway for safety")
            self.show_status("Continuing...", "Getting next steps from AI", True)
            QtCore.QTimer.singleShot(HIDE_AND_CAPTURE_DELAY_MS, 
                                    lambda: self.capture_and_process(self.context.original_task))
            return
        
        step = self._pending_steps[self._current_step_index]
        step_type = step.get("type")
        
        print(f"\n>>> Step {self._current_step_index + 1}/{len(self._pending_steps)}: {step_type}")
        
        if step_type == "click":
            self._execute_click(step)
        elif step_type == "keyboard":
            self._execute_keyboard(step)
        elif step_type == "scroll":
            self._execute_scroll(step)
        elif step_type == "wait_and_send_image":
            self._execute_wait_and_send_image(step)
        elif step_type == "ask_question":
            self._execute_ask_question(step)
        elif step_type == "end":
            self._execute_end(step)
        else:
            print(f"⚠️ Unknown step type: {step_type}")
            self._current_step_index += 1
            self._execute_next_step()
    
    def _execute_click(self, step):
        elem_num = step.get("element_number")
        is_double = step.get("double_click", False)
        desc = step.get("description", "Click action")

        if elem_num is None or elem_num < 1 or elem_num > len(self._parsed_elements):
            print(f"⚠️ Invalid element number: {elem_num}")
            self.show_status("Error", f"Invalid element number: {elem_num}", False)
            time.sleep(2)
            self._current_step_index += 1
            self._execute_next_step()
            return

        elem = self._parsed_elements[elem_num]
        action_type = "Double-clicking" if is_double else "Clicking"
        self.show_status(f"{action_type}...", f"Element [{elem_num}]: {desc}", True)
        print(f"🖱️ {action_type} element [{elem_num}]: {elem}")

        try:
            # Support both string and dict element formats
            if isinstance(elem, dict):
                bbox = elem.get('bbox')
                if bbox and len(bbox) == 4:
                    screen = pyautogui.size()
                    x1 = int(bbox[0] * screen[0])
                    y1 = int(bbox[1] * screen[1])
                    x2 = int(bbox[2] * screen[0])
                    y2 = int(bbox[3] * screen[1])
                    click_x = int((x1 + x2) / 2)
                    click_y = int((y1 + y2) / 2)
                else:
                    raise ValueError("Element dict missing valid bbox")
            elif isinstance(elem, str):
                box_start = elem.find("<box>") + 5
                box_end = elem.find("</box>")
                coords_str = elem[box_start:box_end]
                x1, y1, x2, y2 = map(float, coords_str.split(','))
                click_x = int((x1 + x2) / 2)
                click_y = int((y1 + y2) / 2)
            else:
                raise ValueError("Element is neither dict nor str")

            print(f"✓ Clicking at ({click_x}, {click_y})")

            if is_double:
                pyautogui.click(click_x, click_y)
                pyautogui.click(click_x, click_y)
            else:
                pyautogui.click(click_x, click_y)

            self.context.add_step_completed(step)
            self._current_step_index += 1
            self._wait_for_screen_change()

        except Exception as e:
            print(f"⚠️ Click error: {e}")
            self.show_status("Error", f"Click failed: {str(e)[:40]}", False)
            time.sleep(2)
            self._current_step_index += 1
            self._execute_next_step()
    
    def _execute_keyboard(self, step):
        content = step.get("content", "")
        desc = step.get("description", "Type text")
        
        self.show_status("Typing...", f"Text: {content[:30]}...", True)
        print(f"⌨️ Typing: {content}")
        
        try:
            time.sleep(0.3)
            if content == "{ENTER}":
                pyautogui.press('enter')
            elif content == "{TAB}":
                pyautogui.press('tab')
            elif content == "{BACKSPACE}":
                pyautogui.press('backspace')
            else:
                pyautogui.write(content, interval=0.05)
                time.sleep(0.2)
                pyautogui.press('enter')
            
            print(f"✓ Typed: {content}")
            self.context.add_step_completed(step)
            self._current_step_index += 1
            self._wait_for_screen_change()
            
        except Exception as e:
            print(f"⚠️ Keyboard error: {e}")
            self.show_status("Error", f"Typing failed: {str(e)[:40]}", False)
            time.sleep(2)
            self._current_step_index += 1
            self._execute_next_step()
    
    def _execute_scroll(self, step):
        magnitude = step.get("magnitude", -3)
        desc = step.get("description", "Scroll")
        direction = "down" if magnitude < 0 else "up"
        
        self.show_status(f"Scrolling {direction}...", desc, True)
        print(f"📜 Scrolling: magnitude={magnitude}")
        
        try:
            pyautogui.scroll(int(magnitude * 100))
            self.context.add_step_completed(step)
            self._current_step_index += 1
            self._wait_for_screen_change()
            
        except Exception as e:
            print(f"⚠️ Scroll error: {e}")
            self.show_status("Error", f"Scroll failed: {str(e)[:40]}", False)
            time.sleep(2)
            self._current_step_index += 1
            self._execute_next_step()
    
    def _execute_wait_and_send_image(self, step):
        desc = step.get("description", "Waiting for screen and analyzing next state")
        self.show_status("Waiting...", desc, True)
        print("⏳ Waiting for screen to stabilize before capturing...")
        self.context.add_step_completed(step)
        self._current_step_index += 1
        self._wait_for_screen_change()
    
    def _wait_for_screen_change(self):
        """Wait for screen to change with timeout, then add buffer delay"""
        start_time = time.time()
        check_count = 0
        
        def check_change():
            nonlocal check_count
            check_count += 1
            elapsed_ms = (time.time() - start_time) * 1000
            
            if elapsed_ms > MAX_WAIT_FOR_CHANGE:
                print(f"⏱️ Timeout reached ({MAX_WAIT_FOR_CHANGE}ms). Proceeding anyway...")
                self.show_status("Proceeding...", "Screen check timeout - continuing", True)
                QtCore.QTimer.singleShot(BUFFER_DELAY_MS, self._execute_next_step)
                return
            
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                img = sct.grab(monitor)
                pil_img = Image.frombytes("RGB", img.size, img.rgb)
                new_path = "temp_check_screen.png"
                pil_img.save(new_path)
            
            if self.context.last_screenshot_path and os.path.exists(self.context.last_screenshot_path):
                changed, diff = compare_screenshots(self.context.last_screenshot_path, new_path)
                
                if changed:
                    print(f"✓ Screen changed! Adding {BUFFER_DELAY_MS}ms buffer...")
                    self.show_status("Screen changed", f"Waiting {BUFFER_DELAY_MS}ms buffer", True)
                    
                    stable_path = "last_stable_screen.png"
                    pil_img.save(stable_path)
                    self.context.last_screenshot_path = stable_path
                    
                    QtCore.QTimer.singleShot(BUFFER_DELAY_MS, self._execute_next_step)
                else:
                    remaining_ms = MAX_WAIT_FOR_CHANGE - elapsed_ms
                    self.show_status("Monitoring...", f"Waiting for screen change ({int(remaining_ms/1000)}s left)", True)
                    print(f"⏳ Screen unchanged (check {check_count}), checking again...")
                    QtCore.QTimer.singleShot(200, check_change)
            else:
                stable_path = "last_stable_screen.png"
                pil_img.save(stable_path)
                self.context.last_screenshot_path = stable_path
                self.show_status("Ready", "Initial screen captured", True)
                QtCore.QTimer.singleShot(BUFFER_DELAY_MS, self._execute_next_step)
        
        QtCore.QTimer.singleShot(300, check_change)
    
    def _execute_ask_question(self, step):
        question = step.get("question", "Need more information")
        self.hide_status()
        self.update_status(f"Question: {question}")
        self.context.add_step_completed(step)
        self.show()
        self.input.setDisabled(False)
        self.input.setPlaceholderText(f"Answer: {question}")
        self.input.setFocus()
    
    def _execute_end(self, step):
        message = step.get("message", "Task completed!")
        self.hide_status()
        QtWidgets.QMessageBox.information(self, "Task Complete", message)
        self.context.reset()
        status_text = "Ready - Enter a new task"
        if self._voice_enabled:
            status_text += " (or say 'Hey Vision')"
        self.update_status(status_text)
        
        placeholder = 'Type or say: "Hey Vision, play lata mangeshkar songs"' if self._voice_enabled else 'e.g., "play lata mangeshkar songs"'
        self.input.setPlaceholderText(placeholder)
        self.show()
        self.input.setDisabled(False)
        self.input.setFocus()
    
    @QtCore.pyqtSlot(str)
    def _show_error(self, msg):
        self.hide_status()
        QtWidgets.QMessageBox.warning(self, "Error", f"{msg}")
        self.show()
        self.input.setDisabled(False)
        self.input.setFocus()
    
    def closeEvent(self, event):
        """Clean up when closing"""
        self.stop_voice_recognition()
        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    assistant = VirtualAssistant()
    assistant.show()
    assistant.input.setFocus()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
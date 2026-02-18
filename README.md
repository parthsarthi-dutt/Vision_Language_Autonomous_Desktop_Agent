```txt
#🤖 Vision AI Assistant - Intelligent Screen Automation

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![Gemini](https://img.shields.io/badge/Gemini-2.5--Flash-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**An AI-powered virtual assistant that understands your screen and automates complex tasks through voice commands and visual understanding.**

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [Configuration](#-configuration)

</div>

```

##📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-features)
- [System Architecture](#-architecture)
- [How It Works](#-how-it-works)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [API Integration](#-api-integration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

```
##🌟 Overview

Vision AI Assistant is a breakthrough automation tool that combines **computer vision**, **natural language processing**, and **multimodal AI** to understand and interact with your computer screen like a human would. Unlike traditional automation tools that rely on brittle selectors or coordinates, this assistant **sees** your screen, **understands** the context, and **executes** tasks intelligently.

###🎯 What Makes It Special?

- **🔍 Visual Understanding**: Uses OmniParser to detect and parse ALL UI elements on screen
- **🧠 AI Decision Making**: Powered by Google's Gemini 2.5 Flash for intelligent action planning
- **🎤 Voice Control**: Natural language voice commands with wake word detection
- **🔄 Adaptive Execution**: Monitors screen changes and adapts strategy in real-time
- **🎨 Beautiful UI**: Modern, translucent overlay interface with status indicators

```
##✨ Features

###🖼️ Screen Understanding
```
┌─────────────────────────────────────────────┐
│  Your Screen                                │
│  ┌──────┐  ┌──────────┐  ┌─────────┐      │
│  │ [1]  │  │   [2]    │  │   [3]   │      │
│  │Chrome│  │  Search  │  │  Login  │      │
│  └──────┘  └──────────┘  └─────────┘      │
│                                             │
│         ↓ OmniParser Analysis ↓            │
│                                             │
│  Element [1]: Chrome Browser Icon           │
│  Element [2]: Search Input Field            │
│  Element [3]: Login Button                  │
└─────────────────────────────────────────────┘
```

###🎤 Voice Input System

**Two Activation Modes:**

1. **Wake Word Detection**
   ```
   User: "Hey Vision"
   System: 🎤 [Listening...]
   User: "Play Lata Mangeshkar songs"
   System: ✅ [Executing task...]
   ```

2. **Manual Button Activation**
   ```
   User: [Clicks 🎙️ Speak button]
   System: 🎤 [Listening...]
   User: "Open Chrome and search for AI news"
   System: ✅ [Executing task...]
   ```

**Voice Recognition Modes:**
- **Online Mode** (Default): Google Speech Recognition - High accuracy, requires internet
- **Offline Mode**: Sphinx Recognition - Works offline, lower accuracy

###🤖 AI-Powered Task Execution

The assistant breaks down complex tasks into atomic steps:

```
Task: "Play Lata Mangeshkar songs on YouTube"
         ↓
    [AI Analysis]
         ↓
Step 1: Click Chrome icon [Element 5]
         ↓
Step 2: Wait for browser to open
         ↓
Step 3: Click address bar [Element 12]
         ↓
Step 4: Type "youtube.com"
         ↓
Step 5: Wait for page load
         ↓
Step 6: Click search box [Element 8]
         ↓
Step 7: Type "Lata Mangeshkar songs"
         ↓
Step 8: Wait for results
         ↓
Step 9: Click first video [Element 3]
         ↓
    [Task Complete ✅]
```

###📊 Real-Time Monitoring

```
┌─────────────────────────────────────────────┐
│  Screen Change Detection System             │
├─────────────────────────────────────────────┤
│                                             │
│  Action Performed → Monitor Screen          │
│         ↓                                   │
│  Calculate Pixel Difference                 │
│         ↓                                   │
│  Threshold Check (5% default)               │
│         ↓                                   │
│  ┌─────────┐         ┌─────────┐          │
│  │Changed? │   YES   │ Wait    │          │
│  │         ├────────→│ Buffer  │          │
│  └────┬────┘         └────┬────┘          │
│       │ NO                 │               │
│       ↓                    ↓               │
│  Keep Checking      Proceed to Next Step   │
│  (Max 4s timeout)                          │
└─────────────────────────────────────────────┘
```

###🎨 User Interface

**Main Input Window**
```
┌─────────────────────────────────────────────────┐
│  Ready - Enter a task (or say 'Hey Vision')    │
├─────────────────────────────────────────────────┤
│                                                 │
│  Type or say: "Hey Vision, play music"  [🎙️]  │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Status Overlay** (Bottom Center)
```
┌─────────────────────────────────┐
│  🔄 Analyzing Screen...         │
│  ────────────────────────       │
│  Found 47 elements • Asking AI  │
└─────────────────────────────────┘
```

**Control Panel** (Right Side)
```
┌─────────┐
│ Abort   │ ← Stop current task
├─────────┤
│ Retry   │ ← Retry from current state
├─────────┤
│🎤 Voice │ ← Toggle voice input
├─────────┤
│ Quit    │ ← Exit application
└─────────┘
```

**Voice Indicator** (Top Center)
```
┌─────────────────┐
│ 🎤 Listening... │
└─────────────────┘
```


##🏗️ Architecture

###System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Vision AI Assistant                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   User       │    │   Voice      │    │   Screen     │ │
│  │   Input      │◄──►│ Recognition  │    │   Capture    │ │
│  │  (PyQt5)     │    │  (Speech_R)  │    │    (MSS)     │ │
│  └──────┬───────┘    └──────────────┘    └──────┬───────┘ │
│         │                                         │         │
│         └─────────────────┬─────────────────────┘         │
│                           ▼                                 │
│                  ┌──────────────────┐                      │
│                  │   Task Context   │                      │
│                  │    Management    │                      │
│                  └────────┬─────────┘                      │
│                           │                                 │
│         ┌─────────────────┼─────────────────┐             │
│         ▼                 ▼                 ▼              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ OmniParser  │  │   Gemini    │  │  PyAutoGUI  │       │
│  │   (API)     │  │  2.5 Flash  │  │  (Control)  │       │
│  │             │  │             │  │             │       │
│  │ UI Element  │  │ Decision    │  │ Click/Type  │       │
│  │ Detection   │  │ Making      │  │ Scroll      │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

###Data Flow

```
1. Input Stage
   ┌─────────────┐
   │ Voice Input │ ──┐
   └─────────────┘   │
                      ├──→ [Task Definition]
   ┌─────────────┐   │
   │ Text Input  │ ──┘
   └─────────────┘

2. Analysis Stage
   [Task Definition]
         ↓
   [Capture Screen] → [Screenshot.png]
         ↓
   [OmniParser API] → [Annotated Image + Element List]
         ↓
   [Gemini 2.5 Flash] → [Action Plan (JSON)]

3. Execution Stage
   [Action Plan]
         ↓
   [For each step]:
      • Parse step type
      • Execute action (click/type/scroll)
      • Monitor screen change
      • Wait for stabilization
      • Capture new state
         ↓
   [Next step or re-analyze]

4. Completion
   [All steps done]
         ↓
   [Show completion message]
         ↓
   [Ready for next task]
```

###JSON Response Format

```json
{
  "steps": [
    {
      "type": "click",
      "element_number": 5,
      "description": "Click Chrome browser",
      "double_click": false
    },
    {
      "type": "wait_and_send_image",
      "description": "Wait for Chrome to open"
    },
    {
      "type": "keyboard",
      "content": "youtube.com",
      "element_number": 3,
      "description": "Type YouTube URL"
    },
    {
      "type": "end",
      "message": "Successfully opened YouTube"
    }
  ]
}
```

```
##🚀 Installation

###Prerequisites

- **Python**: 3.8 or higher
- **Operating System**: Windows (primary), Linux/Mac (experimental)
- **Internet**: Required for Google Speech Recognition and Gemini API
- **Microphone**: Required for voice input

###Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/vision-ai-assistant.git
cd vision-ai-assistant
```

###Step 2: Create Virtual Environment (Recommended)

```bash
#Windows
python -m venv venv
venv\Scripts\activate

#Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

###Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install PyQt5 mss pillow google-generativeai pyautogui pynput requests python-dotenv numpy
```

###Step 4: Install Speech Recognition

```bash
#Main package
pip install SpeechRecognition

#For Windows - PyAudio
pip install pipwin
pipwin install pyaudio

#OR download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
#Then: pip install PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl

#For offline mode (optional)
pip install pocketsphinx
```

###Step 5: Setup Environment Variables

Create a `.env` file in the project root:

```env
gemini_key=YOUR_GEMINI_API_KEY_HERE
```

**Get Gemini API Key:**
1. Go to: https://aistudio.google.com/app/apikey
2. Create new API key
3. Copy and paste into `.env` file

###Step 6: Setup OmniParser

OmniParser requires a separate service. Options:

**Option A: Use Cloudflare Tunnel (Provided in code)**
```python
OMNIPARSER_URL = "https://settings-referred-belongs-scenic.trycloudflare.com/process"
```

**Option B: Run Your Own OmniParser Server**
```bash
#Clone OmniParser repository
git clone https://github.com/microsoft/OmniParser.git
cd OmniParser

#Follow their setup instructions
#Update OMNIPARSER_URL in code to your local endpoint
```

###Step 7: Verify Installation

```bash
python vision_assistant.py
```

You should see:
```
🎤 Adjusting for ambient noise...
✓ Voice recognition ready
```

```
##⚙️ Configuration

###Main Configuration Variables

Edit these at the top of `vision_assistant.py`:

```python
#===== API Configuration =====
API_KEY = os.getenv("gemini_key")           #Gemini API key from .env
MODEL_NAME = "gemini-2.5-flash"              #AI model to use
OMNIPARSER_URL = "https://your-url.com"      #OmniParser endpoint

#===== Timing Configuration =====
HIDE_AND_CAPTURE_DELAY_MS = 120              #Delay before screenshot (ms)
SCREEN_CHANGE_THRESHOLD = 0.05               #5% change detection
BUFFER_DELAY_MS = 500                        #Wait after change detected
MAX_WAIT_FOR_CHANGE = 4000                   #Max wait for screen change

#===== Voice Configuration =====
USE_OFFLINE_RECOGNITION = False              #False=Google, True=Sphinx
WAKE_WORD = "hey vision"                     #Wake word phrase
SILENCE_DURATION = 1.5                       #Seconds before stop recording
VOICE_ENABLED = True                         #Start with voice on/off
AUTO_SUBMIT_VOICE = False                    #Auto-submit after recognition
AUTO_SUBMIT_DELAY_MS = 1000                  #Delay before auto-submit
```

###Voice Recognition Modes

| Mode | Accuracy | Speed | Internet | Setup Difficulty |
|------|----------|-------|----------|------------------|
| **Google** (Recommended) | ⭐⭐⭐⭐⭐ | Fast | Required | Easy |
| **Sphinx** (Offline) | ⭐⭐⭐ | Medium | Not needed | Medium |

###Adjusting Sensitivity

**Screen Change Detection:**
```python
SCREEN_CHANGE_THRESHOLD = 0.05  #Lower = more sensitive (0.01 - 0.1)
```

**Voice Recognition:**
```python
#In VoiceRecognitionThread.__init__()
self.recognizer.energy_threshold = 4000      #Lower = more sensitive
self.recognizer.pause_threshold = 1.5        #Shorter = faster detection
```


##📖 Usage Guide

###Basic Usage

**Method 1: Voice Command (Wake Word)**
```
1. Launch application
2. Wait for "Ready" message
3. Say: "Hey Vision"
4. Wait for listening indicator
5. Say your command: "Open Chrome and search for Python tutorials"
6. System executes automatically
```

**Method 2: Voice Command (Manual Button)**
```
1. Launch application
2. Click 🎙️ Speak button
3. Say your command
4. Press Enter (or wait 1s for auto-submit if enabled)
```

**Method 3: Text Input**
```
1. Launch application
2. Type command in input field
3. Press Enter
```

###Example Commands

####Simple Tasks
```
✅ "Open Chrome"
✅ "Search for weather"
✅ "Open calculator"
✅ "Close this window"
```

####Complex Tasks
```
✅ "Open Chrome and search for best Italian restaurants near me"
✅ "Go to YouTube and play Lata Mangeshkar songs"
✅ "Open Gmail and compose new email"
✅ "Search for Python tutorials on Google"
```

####Multi-Step Tasks
```
✅ "Open Chrome, go to GitHub, search for AI projects, and open the first result"
✅ "Open calculator and calculate 25 * 37"
✅ "Go to Amazon, search for wireless headphones under $50"
```

###Control Panel Usage

```
┌─────────────────────────────────┐
│ Abort   │ Stop current task     │
├─────────┼───────────────────────┤
│ Retry   │ Retry from last state │
├─────────┼───────────────────────┤
│🎤 Voice │ Toggle voice on/off   │
├─────────┼───────────────────────┤
│ Quit    │ Exit application      │
└─────────┴───────────────────────┘
```

###Status Indicators

| Status | Meaning |
|--------|---------|
| 🔄 **Capturing...** | Taking screenshot |
| 🔍 **Analyzing Screen...** | Processing with OmniParser |
| 🧠 **Thinking...** | AI planning next steps |
| ⚡ **Executing...** | Performing actions |
| 🎤 **Listening...** | Recording voice input |
| ⏳ **Waiting...** | Monitoring screen changes |
| ✅ **Complete!** | Task finished |

```
##🔌 API Integration

###OmniParser API

**Endpoint:**
```
POST https://your-omniparser-url/process
```

**Request:**
```python
files = {"image": open("screenshot.png", "rb")}
data = {
    "box_threshold": 0.05,    #Detection confidence
    "iou_threshold": 0.1      #Overlap threshold
}
```

**Response:**
```json
{
  "parsed_content": [
    {
      "bbox": [0.1, 0.2, 0.3, 0.4],
      "content": "Chrome Browser",
      "type": "icon"
    }
  ],
  "image_base64": "iVBORw0KGgoAAAANS..."
}
```

###Gemini API

**Configuration:**
```python
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")
```

**Request:**
```python
response = model.generate_content([
    "Analyze this screen and provide next steps...",
    PIL_Image_Object
])
```

**Response Format:**
```json
{
  "steps": [
    {
      "type": "click|keyboard|scroll|wait_and_send_image|ask_question|end",
      ...additional fields...
    }
  ]
}
```

###Step Types Reference

| Type | Description | Required Fields |
|------|-------------|-----------------|
| **click** | Click UI element | `element_number`, `description`, `double_click` |
| **keyboard** | Type text | `content`, `element_number`, `description` |
| **scroll** | Scroll page | `magnitude`, `description` |
| **wait_and_send_image** | Wait and re-analyze | `description` |
| **ask_question** | Ask user | `question`, `description` |
| **end** | Complete task | `message`, `description` |

```
##🐛 Troubleshooting

###Common Issues

####1. Microphone Not Working

**Symptoms:** No wake word detection, voice recognition fails

**Solutions:**
```bash
#Test microphone
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"

#Adjust sensitivity in code
self.recognizer.energy_threshold = 300  #Lower value
```

####2. PyAudio Installation Fails

**Windows:**
```bash
#Method 1: pipwin
pip install pipwin
pipwin install pyaudio

#Method 2: Download wheel
#Get from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl
```

**Linux:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**Mac:**
```bash
brew install portaudio
pip install pyaudio
```

####3. Screen Capture Issues

**Symptoms:** Screenshots are black or empty

**Solutions:**
```python
#Try different monitor
monitor = sct.monitors[0]  #Change index

#Check permissions (Mac)
#System Preferences → Security & Privacy → Screen Recording
```

####4. API Errors

**OmniParser Connection Failed:**
```
- Check OMNIPARSER_URL is correct
- Verify service is running
- Check firewall/network settings
```

**Gemini API Error:**
```
- Verify API key in .env file
- Check API quota: https://aistudio.google.com/app/apikey
- Ensure internet connection
```

####5. Element Click Misses Target

**Symptoms:** Clicks wrong location

**Solutions:**
```python
#Adjust thresholds in OmniParser call
call_omniparser(
    image_path,
    box_threshold=0.03,  #Lower = more elements
    iou_threshold=0.15   #Higher = less overlap
)
```

###Debug Mode

Enable detailed logging:

```python
#Add at top of file
import logging
logging.basicConfig(level=logging.DEBUG)

#Or add print statements
print(f"DEBUG: Element {elem_num} at position {click_x}, {click_y}")
```

###Log Files

The application generates these files for debugging:

```
annotated_screen_*.png       #Annotated screenshots with element numbers
gemini_prompt_*.txt          #Full prompts sent to Gemini
gemini_response_*.txt        #AI responses
current_screen.png           #Latest screenshot
last_stable_screen.png       #Last verified stable screen
```

```
##🔬 Advanced Usage

###Custom System Prompt

Edit `SYSTEM_PROMPT` variable to customize AI behavior:

```python
SYSTEM_PROMPT = """You are a virtual assistant specialized in...
- Custom rule 1
- Custom rule 2
"""
```

###Adding New Step Types

1. **Define step type in prompt:**
```python
7. "custom_action" - Your custom action
   {
     "type": "custom_action",
     "param1": "value",
     "description": "What it does"
   }
```

2. **Add handler in `_execute_next_step()`:**
```python
elif step_type == "custom_action":
    self._execute_custom_action(step)
```

3. **Implement handler method:**
```python
def _execute_custom_action(self, step):
    #Your implementation
    pass
```

###Multi-Monitor Support

```python
#In capture_and_process()
with mss.mss() as sct:
    monitor = sct.monitors[2]  #Change to desired monitor (1, 2, 3...)
    img = sct.grab(monitor)
```

###Custom Voice Commands

```python
#In _listen_for_wake_word()
if "custom wake word" in text:
    #Trigger custom action
    pass
```

```
##🤝 Contributing

We welcome contributions! Here's how you can help:

###Ways to Contribute

1. **🐛 Report Bugs**
   - Use GitHub Issues
   - Include error logs
   - Provide steps to reproduce

2. **💡 Suggest Features**
   - Open a feature request
   - Explain use case
   - Provide examples

3. **📝 Improve Documentation**
   - Fix typos
   - Add examples
   - Translate to other languages

4. **🔧 Submit Code**
   - Fork repository
   - Create feature branch
   - Submit pull request

###Development Setup

```bash
#Fork and clone
git clone https://github.com/yourusername/vision-ai-assistant.git
cd vision-ai-assistant

#Create branch
git checkout -b feature/your-feature-name

#Make changes and test
python vision_assistant.py

#Commit and push
git add .
git commit -m "Add: your feature description"
git push origin feature/your-feature-name

#Create Pull Request on GitHub
```

###Code Style

- Follow PEP 8
- Add docstrings to functions
- Comment complex logic
- Use type hints where possible

```python
def example_function(param: str, threshold: float = 0.5) -> bool:
    """
    Brief description of function.
    
    Args:
        param: Description of param
        threshold: Description of threshold
        
    Returns:
        Description of return value
    """
    pass
```

```
##📊 Performance Tips

###Optimize Speed

```python
#Reduce capture delay
HIDE_AND_CAPTURE_DELAY_MS = 50  #Faster but less reliable

#Reduce buffer delay
BUFFER_DELAY_MS = 300  #Faster transitions

#Adjust threshold for quicker detection
SCREEN_CHANGE_THRESHOLD = 0.03  #More sensitive
```

###Reduce API Calls

```python
#Batch operations in single prompt
"Click element 5, type 'hello', then click element 8"

#Use wait_and_send_image strategically
#Only when screen will definitely change
```

###Memory Management

```python
#Clean old files periodically
import glob
for f in glob.glob("annotated_screen_*.png"):
    if file_age > 1_hour:
        os.remove(f)
```

```
##🔒 Security & Privacy

###Data Handling

- **Screenshots**: Stored locally, deleted on restart
- **Voice Data**: Processed in real-time, not stored
- **API Keys**: Kept in `.env`, never committed to Git

###Best Practices

1. **Never commit `.env` file**
```bash
#Add to .gitignore
.env
*.png
gemini_*.txt
```

2. **Use API key with restrictions**
   - Set usage quotas
   - Restrict to specific IPs if possible
   - Monitor usage at: https://aistudio.google.com

3. **Review screenshots before sharing**
   - May contain sensitive information
   - Check annotated images for personal data

```
##📜 License

```
MIT License

Copyright (c) 2024 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

```
##🙏 Acknowledgments

- **OmniParser** - Microsoft Research for UI element detection
- **Google Gemini** - Multimodal AI capabilities
- **PyQt5** - Cross-platform GUI framework
- **SpeechRecognition** - Voice input handling
- **Community Contributors** - For feedback and improvements

```
##📞 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/vision-ai-assistant/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/yourusername/vision-ai-assistant/discussions)
- **Email**: your.email@example.com
- **Twitter**: @yourusername

```
##🗺️ Roadmap

###Version 1.0 (Current)
- ✅ Screen understanding with OmniParser
- ✅ Voice input with wake word
- ✅ Basic task automation
- ✅ Real-time screen monitoring

###Version 1.1 (Planned)
- 🔲 Multi-monitor support
- 🔲 Task templates/macros
- 🔲 Scheduled automation
- 🔲 Browser extension integration

###Version 2.0 (Future)
- 🔲 Self-learning from user corrections
- 🔲 Plugin system for custom actions
- 🔲 Mobile app companion
- 🔲 Cloud sync for tasks
- 🔲 Collaborative automation sharing

```
##📈 Project Stats

![GitHub Stars](https://img.shields.io/github/stars/yourusername/vision-ai-assistant?style=social)
![GitHub Forks](https://img.shields.io/github/forks/yourusername/vision-ai-assistant?style=social)
![GitHub Issues](https://img.shields.io/github/issues/yourusername/vision-ai-assistant)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/yourusername/vision-ai-assistant)

```
<div align="center">

**If you find this project helpful, please consider giving it a ⭐!**

Made with ❤️ by [Your Name]

</div>

```

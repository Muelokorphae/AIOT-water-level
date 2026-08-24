# 🌾 Smart Farm IoT Irrigation & AI Assistant System

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Arduino](https://img.shields.io/badge/Arduino-IDE-00979D?style=for-the-badge&logo=arduino&logoColor=white)](https://www.arduino.cc/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)

An end-to-end intelligent IoT smart agriculture and automated irrigation system. The project integrates an **Arduino microcontroller** with sensors and actuators, a **Python Flask backend** with real-time serial communication, an interactive **Web Dashboard with Live Charting**, and an **LLM-Powered Conversational AI Assistant** (supporting Google Gemini 2.5 Flash and OpenAI GPT-4o-mini) that answers domain questions and executes hardware control commands via natural language.

---

## 📑 Table of Contents

- [Overview & Architecture](#-overview--architecture)
- [Key Features](#-key-features)
- [Project Directory Structure](#-project-directory-structure)
- [Hardware Setup & Wiring](#-hardware-setup--wiring)
- [Software Prerequisites & Installation](#-software-prerequisites--installation)
- [Configuration (.env)](#-configuration-env)
- [Running the Application](#-running-the-application)
- [System Workflow & Automation Logic](#-system-workflow--automation-logic)
- [REST API Endpoints](#-rest-api-endpoints)
- [LLM Assistant Integration](#-llm-assistant-integration)
- [Data Logging & Analytics](#-data-logging--analytics)

---

## 🏛 Overview & Architecture

```
                  ┌───────────────────────────────┐
                  │      Sensors & Actuators      │
                  │  • Analog Water Level Sensor  │
                  │  • 28BYJ-48 Stepper + ULN2003 │
                  │  • Status Indicator LED       │
                  └───────────────┬───────────────┘
                                  │ (GPIO / Analog / Step Pulses)
                  ┌───────────────┴───────────────┐
                  │       Arduino Controller      │
                  │   (AccelStepper Engine @115.2k)
                  └───────────────┬───────────────┘
                                  │ USB Serial (JSON/Byte Commands)
                  ┌───────────────┴───────────────┐
                  │      Flask Backend Engine     │
                  │  • Serial Background Thread   │
                  │  • Real-Time Control & Safety │
                  │  • Thread-Safe CSV Logging    │
                  │  • LLM Engine (Gemini/OpenAI) │
                  └───────┬───────────────┬───────┘
                          │               │
            ┌─────────────┴─────┐   ┌─────┴──────────────────┐
            │   Web Dashboard   │   │   AI Assistant Chat    │
            │ • Real-time Charts│   │ • Natural Language I/O │
            │ • Status Metrics  │   │ • Hardware Command NLP │
            │ • Manual Override │   │ • Context-Aware RAG    │
            └───────────────────┘   └────────────────────────┘
```

---

## ✨ Key Features

* **Automated Closed-Loop Irrigation**: Continuous water level monitoring reported every 3 seconds. Auto-starts pump when reservoir level drops below **15%** and auto-stops when reservoir recovers to **15%** or higher.
* **Smooth Acceleration Stepper Engine**: Utilizes Arduino `AccelStepper` in half-step mode with non-blocking 3-second safety pre-run delay, dynamic acceleration curve (`500 steps/s²`), target speed (`1000 steps/s`), and automatic coil de-energization to prevent motor overheating.
* **Dual LLM Provider Support**: Toggle between **Google Gemini** (`gemini-2.5-flash` via `google-genai` SDK) and **OpenAI** (`gpt-4o-mini` via `openai` SDK) seamlessly via configuration.
* **Natural Language Hardware Execution**: The conversational AI parses user intent (e.g., *"start pump"*, *"open valve"*, *"turn off motor"*) to dispatch hardware control bytes directly to the Arduino while generating intelligent feedback.
* **Interactive Live Dashboard**: Real-time Chart.js telemetry visualization, status metric cards (min, max, average, total logs, automated vs. manual starts), and manual override controls with automatic 60-second safety lockout.
* **Thread-Safe Historical Logging**: Sequential, atomic logging to `water_analytics.csv` tracking events (`3SEC_LOG`, `AUTO_START_LOW_WATER`, `AUTO_STOP_LEVEL_OK`, `USER_MANUAL_START`, `USER_MANUAL_STOP`).

---

## 📂 Project Directory Structure

```text
final_project/
├── .env.example              # Environment variables template
├── app.py                    # Flask server, serial loop, LLM handler, & REST API
├── water_analytics.csv       # Persistent CSV database logging water levels & events
├── sketch_jun25a/
│   └── sketch_jun25a.ino     # Arduino firmware (AccelStepper, Sensor, LED)
├── templates/
│   ├── dashboard.html        # Interactive monitoring dashboard with Chart.js
│   └── chat.html             # Smart conversational AI interface
└── README.md                 # Project documentation
```

---

## 🔌 Hardware Setup & Wiring

**Bill of Materials**

| Component | Description | Quantity |
|---|---|---|
| **Microcontroller** | Arduino Uno / Nano / Mega | 1 |
| **Water Level Sensor** | Analog Submersible / Depth Sensor | 1 |
| **Stepper Motor** | 28BYJ-48 (5V / 12V DC) | 1 |
| **Motor Driver** | ULN2003 Darlington Transistor Array Board | 1 |
| **Status LED** | 5mm LED + 220Ω Resistor | 1 |
| **Power Supply / Cable** | USB A-B Cable / 5V External Power Supply | 1 |

**Pin Connection Table**

| Arduino Pin | Connected Component & Pin | Details |
|---|---|---|
| **A0** | Water Sensor `Signal / S` | Analog input (`0–700` mapped to `0–100%`) |
| **5V** | Water Sensor `VCC` & ULN2003 `+` | Power supply |
| **GND** | Water Sensor `GND`, ULN2003 `-`, LED Cathode | Common ground |
| **Pin 8** | ULN2003 `IN1` | Stepper Coil 1 |
| **Pin 10** | ULN2003 `IN2` | Stepper Coil 2 |
| **Pin 9** | ULN2003 `IN3` | Stepper Coil 3 |
| **Pin 11** | ULN2003 `IN4` | Stepper Coil 4 |
| **Pin 7** | Status LED Anode (`+` via 220Ω resistor) | Indicator active during motor run/pending |

---

## 💻 Software Prerequisites & Installation

**1. Flash Arduino Firmware**
* Open the Arduino IDE.
* Install the **AccelStepper** library (*Sketch* ➔ *Include Library* ➔ *Manage Libraries...*).
* Open `sketch_jun25a/sketch_jun25a.ino`.
* Select your board and COM port, then click **Upload**.

**2. Setup Python Environment**
Ensure you have **Python 3.9+** installed:

```bash
# Clone the repository
git clone https://github.com/your-username/smart-farm-irrigation.git
cd smart-farm-irrigation

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install flask pyserial python-dotenv google-genai openai
```

---

## ⚙️ Configuration (.env)

Create your `.env` configuration file from the template:

```bash
cp .env.example .env
```

Configure your environment settings:

```ini
# Choose LLM Provider: 'gemini' or 'openai'
LLM_PROVIDER=gemini

# Google Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Serial Port Settings (e.g., COM3 on Windows, /dev/ttyUSB0 on Linux)
SERIAL_PORT=COM3
PORT=5000
```

> **Note:** If hardware is disconnected, the server launches in **Demo/Standalone mode**, allowing full dashboard testing and chat evaluation.

---

## 🚀 Running the Application

Launch the Flask backend server:

```bash
python app.py
```

Terminal output:
```text
[HARDWARE] Connected on COM3
[LLM] Google Gemini Client Initialized.

--- SMART FARM AI DASHBOARD & CHATBOT ONLINE ON PORT 5000 ---
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

Open your browser:
* **Dashboard:** [http://localhost:5000/dashboard](http://localhost:5000/dashboard)
* **AI Chat Assistant:** [http://localhost:5000/chat](http://localhost:5000/chat)

---

## 🔄 System Workflow & Automation Logic

```text
[Every 3s] Arduino reads A0 -> Transmits "WATER_LEVEL:<0-100>" via Serial (115200 baud)
                                  │
                                  ▼
                     Flask Serial Loop Receives Data
                                  │
          ┌───────────────────────┴───────────────────────┐
          │                                               │
   [Level < 15%]                                   [Level >= 15%]
          │                                               │
Is Motor STOPPED and No Override?               Is Motor RUNNING and No Override?
          │                                               │
    [Yes] Send '1'                                  [Yes] Send '0'
          │                                               │
  • LED ON                                        • LED OFF
  • 3s safety delay                               • AccelStepper stopped
  • AccelStepper runs                             • Coils de-energized
  • Log: AUTO_START_LOW_WATER                     • Log: AUTO_STOP_LEVEL_OK
```

* **Safety Override Guard**: Manual actuation commands trigger a **60-second override hold** (`time.time() + 60`) so automatic thresholding does not prematurely reverse intentional user commands.

---

## 📡 REST API Endpoints

| Method | Endpoint | Description | Payload / Response |
|---|---|---|---|
| `GET` | `/` | Redirects to `/dashboard` | HTTP 302 |
| `GET` | `/dashboard` | Renders Dashboard web interface | HTML |
| `GET` | `/chat` | Renders AI Assistant conversational interface | HTML |
| `GET` | `/api/metrics` | Returns live sensor values, motor state, & aggregate statistics | `{"current_water_level": 45, "motor_status": "STOPPED", "stats": {...}}` |
| `POST` | `/api/control` | Manual motor switch (`ON` / `OFF`) | **Body**: `{"action": "ON"}`<br>**Response**: `{"success": true, "status": "RUNNING"}` |
| `POST` | `/api/chat` | AI query handler with hardware intent parsing | **Body**: `{"message": "Turn on the motor"}`<br>**Response**: `{"reply": "...", "provider": "GEMINI"}` |

---

## 🤖 LLM Assistant Integration

The chatbot acts as a **domain-expert agronomy assistant and hardware controller**.

**Natural Language Intent Recognition**
* *"turn on motor"*, *"start pump"*, *"open valve"*, *"run motor"*, *"pump water"* ➔ Sends `'1'` to Arduino.
* *"turn off motor"*, *"stop pump"*, *"close valve"*, *"stop motor"* ➔ Sends `'0'` to Arduino.

**Dynamic Context Injection (RAG-lite)**
Every chat query injects live metrics and historical analytics directly into the system prompt:

```text
--- CURRENT LIVE FARM METRICS ---
- Current Water Reservoir Level: 42%
- Stepper Motor Pump State: STOPPED
- Recent Hardware Action Executed: Manually turned ON the motor.

--- HISTORICAL FARM STATISTICS ---
- Total Logs Recorded: 1420
- Average Water Level: 68.4%
- Min Water Level: 5% | Max: 98%
- Automated Motor Starts: 14 times
- Manual User Motor Starts: 3 times
```

---

## 📊 Data Logging & Analytics

All events and telemetry are recorded to `water_analytics.csv`:

```csv
id,timestamp,date,water_level_pct,motor_status,event_type
1,2026-08-07 19:08:00,2026-08-07,81,STOPPED,3SEC_LOG
2,2026-08-07 19:08:03,2026-08-07,59,STOPPED,3SEC_LOG
5,2026-08-07 19:08:12,2026-08-07,8,RUNNING,AUTO_START_LOW_WATER
6,2026-08-07 19:08:15,2026-08-07,8,RUNNING,3SEC_LOG
```

**Event Types**:
* `3SEC_LOG`: Periodic background telemetry logged every 3 seconds.
* `AUTO_START_LOW_WATER`: Triggered automatically when water level drops below 15%.
* `AUTO_STOP_LEVEL_OK`: Triggered automatically when water level recovers to 15% or above.
* `USER_MANUAL_START`: Initiated by user via Dashboard button or AI chat command.
* `USER_MANUAL_STOP`: Stopped by user via Dashboard button or AI chat command.
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
```[cite: 2]

---

## ✨ Key Features

* **Automated Closed-Loop Irrigation**: Continuous water level monitoring reported every 3 seconds[cite: 2]. Auto-starts pump when reservoir level drops below **15%** and auto-stops when reservoir recovers to **15%** or higher[cite: 2].
* **Smooth Acceleration Stepper Engine**: Utilizes Arduino `AccelStepper` in half-step mode with non-blocking 3-second safety pre-run delay, dynamic acceleration curve (`500 steps/s²`), target speed (`1000 steps/s`), and automatic coil de-energization to prevent motor overheating[cite: 2].
* **Dual LLM Provider Support**: Toggle between **Google Gemini** (`gemini-2.5-flash` via `google-genai` SDK) and **OpenAI** (`gpt-4o-mini` via `openai` SDK) seamlessly via configuration[cite: 2].
* **Natural Language Hardware Execution**: The conversational AI parses user intent (e.g., *"start pump"*, *"open valve"*, *"turn off motor"*) to dispatch hardware control bytes directly to the Arduino while generating intelligent feedback[cite: 2].
* **Interactive Live Dashboard**: Real-time Chart.js telemetry visualization, status metric cards (min, max, average, total logs, automated vs. manual starts), and manual override controls with automatic 60-second safety lockout[cite: 2].
* **Thread-Safe Historical Logging**: Sequential, atomic logging to `water_analytics.csv` tracking events (`3SEC_LOG`, `AUTO_START_LOW_WATER`, `AUTO_STOP_LEVEL_OK`, `USER_MANUAL_START`, `USER_MANUAL_STOP`)[cite: 2].

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
```[cite: 2]

---

## 🔌 Hardware Setup & Wiring

**Bill of Materials**[cite: 2]

| Component | Description | Quantity |
|---|---|---|
| **Microcontroller** | Arduino Uno / Nano / Mega[cite: 2] | 1[cite: 2] |
| **Water Level Sensor** | Analog Submersible / Depth Sensor[cite: 2] | 1[cite: 2] |
| **Stepper Motor** | 28BYJ-48 (5V / 12V DC)[cite: 2] | 1[cite: 2] |
| **Motor Driver** | ULN2003 Darlington Transistor Array Board[cite: 2] | 1[cite: 2] |
| **Status LED** | 5mm LED + 220Ω Resistor[cite: 2] | 1[cite: 2] |
| **Power Supply / Cable** | USB A-B Cable / 5V External Power Supply[cite: 2] | 1[cite: 2] |

**Pin Connection Table**[cite: 2]

| Arduino Pin | Connected Component & Pin | Details |
|---|---|---|
| **A0** | Water Sensor `Signal / S`[cite: 2] | Analog input (`0–700` mapped to `0–100%`)[cite: 2] |
| **5V** | Water Sensor `VCC` & ULN2003 `+`[cite: 2] | Power supply[cite: 2] |
| **GND** | Water Sensor `GND`, ULN2003 `-`, LED Cathode[cite: 2] | Common ground[cite: 2] |
| **Pin 8** | ULN2003 `IN1`[cite: 2] | Stepper Coil 1[cite: 2] |
| **Pin 10** | ULN2003 `IN2`[cite: 2] | Stepper Coil 2[cite: 2] |
| **Pin 9** | ULN2003 `IN3`[cite: 2] | Stepper Coil 3[cite: 2] |
| **Pin 11** | ULN2003 `IN4`[cite: 2] | Stepper Coil 4[cite: 2] |
| **Pin 7** | Status LED Anode (`+` via 220Ω resistor)[cite: 2] | Indicator active during motor run/pending[cite: 2] |

---

## 💻 Software Prerequisites & Installation

**1. Flash Arduino Firmware**
* Open the Arduino IDE[cite: 2].
* Install the **AccelStepper** library (*Sketch* ➔ *Include Library* ➔ *Manage Libraries...*)[cite: 2].
* Open `sketch_jun25a/sketch_jun25a.ino`[cite: 2].
* Select your board and COM port, then click **Upload**[cite: 2].

**2. Setup Python Environment**
Ensure you have **Python 3.9+** installed[cite: 2]:

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
```[cite: 2]

---

## ⚙️ Configuration (.env)

Create your `.env` configuration file from the template[cite: 2]:

```bash
cp .env.example .env
```[cite: 2]

Configure your environment settings[cite: 2]:

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
```[cite: 2]

> **Note:** If hardware is disconnected, the server launches in **Demo/Standalone mode**, allowing full dashboard testing and chat evaluation[cite: 2].

---

## 🚀 Running the Application

Launch the Flask backend server[cite: 2]:

```bash
python app.py
```[cite: 2]

Terminal output:
```text
[HARDWARE] Connected on COM3
[LLM] Google Gemini Client Initialized.

--- SMART FARM AI DASHBOARD & CHATBOT ONLINE ON PORT 5000 ---
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```[cite: 2]

Open your browser:
* **Dashboard:** [http://localhost:5000/dashboard](http://localhost:5000/dashboard)[cite: 2]
* **AI Chat Assistant:** [http://localhost:5000/chat](http://localhost:5000/chat)[cite: 2]

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
```[cite: 2]

* **Safety Override Guard**: Manual actuation commands trigger a **60-second override hold** (`time.time() + 60`) so automatic thresholding does not prematurely reverse intentional user commands[cite: 2].

---

## 📡 REST API Endpoints

| Method | Endpoint | Description | Payload / Response |
|---|---|---|---|
| `GET` | `/` | Redirects to `/dashboard`[cite: 2] | HTTP 302[cite: 2] |
| `GET` | `/dashboard` | Renders Dashboard web interface[cite: 2] | HTML[cite: 2] |
| `GET` | `/chat` | Renders AI Assistant conversational interface[cite: 2] | HTML[cite: 2] |
| `GET` | `/api/metrics` | Returns live sensor values, motor state, & aggregate statistics[cite: 2] | `{"current_water_level": 45, "motor_status": "STOPPED", "stats": {...}}`[cite: 2] |
| `POST` | `/api/control` | Manual motor switch (`ON` / `OFF`)[cite: 2] | **Body**: `{"action": "ON"}`<br>**Response**: `{"success": true, "status": "RUNNING"}`[cite: 2] |
| `POST` | `/api/chat` | AI query handler with hardware intent parsing[cite: 2] | **Body**: `{"message": "Turn on the motor"}`<br>**Response**: `{"reply": "...", "provider": "GEMINI"}`[cite: 2] |

---

## 🤖 LLM Assistant Integration

The chatbot acts as a **domain-expert agronomy assistant and hardware controller**[cite: 2].

**Natural Language Intent Recognition**[cite: 2]
* *"turn on motor"*, *"start pump"*, *"open valve"*, *"run motor"*, *"pump water"* ➔ Sends `'1'` to Arduino[cite: 2].
* *"turn off motor"*, *"stop pump"*, *"close valve"*, *"stop motor"* ➔ Sends `'0'` to Arduino[cite: 2].

**Dynamic Context Injection (RAG-lite)**[cite: 2]
Every chat query injects live metrics and historical analytics directly into the system prompt[cite: 2]:

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
```[cite: 2]

---

## 📊 Data Logging & Analytics

All events and telemetry are recorded to `water_analytics.csv`[cite: 2]:

```csv
id,timestamp,date,water_level_pct,motor_status,event_type
1,2026-08-07 19:08:00,2026-08-07,81,STOPPED,3SEC_LOG
2,2026-08-07 19:08:03,2026-08-07,59,STOPPED,3SEC_LOG
5,2026-08-07 19:08:12,2026-08-07,8,RUNNING,AUTO_START_LOW_WATER
6,2026-08-07 19:08:15,2026-08-07,8,RUNNING,3SEC_LOG
```[cite: 2]

**Event Types**[cite: 2]:
* `3SEC_LOG`: Periodic background telemetry logged every 3 seconds[cite: 2].
* `AUTO_START_LOW_WATER`: Triggered automatically when water level drops below 15%[cite: 2].
* `AUTO_STOP_LEVEL_OK`: Triggered automatically when water level recovers to 15% or above[cite: 2].
* `USER_MANUAL_START`: Initiated by user via Dashboard button or AI chat command[cite: 2].
* `USER_MANUAL_STOP`: Stopped by user via Dashboard button or AI chat command[cite: 2].
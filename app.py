import os
import csv
import time
import threading
import serial
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")
BAUD_RATE = 115200
CSV_FILE = "water_analytics.csv"
PORT = int(os.getenv("PORT", 5000))

app = Flask(__name__)

# Initialize LLM Clients dynamically
gemini_client = None
openai_client = None

if LLM_PROVIDER == "gemini":
    if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("your_"):
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("[LLM] Google Gemini Client Initialized.")
    else:
        print("[LLM WARNING] Missing GEMINI_API_KEY! Gemini features disabled.")

elif LLM_PROVIDER == "openai":
    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("your_"):
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("[LLM] OpenAI Client Initialized.")
    else:
        print("[LLM WARNING] Missing OPENAI_API_KEY! OpenAI features disabled.")

file_lock = threading.Lock()
ser_instance = None 

latest_water_level = 0
motor_status = "STOPPED"
manual_override_until = 0

def init_csv():
    """Initializes the CSV database file with a unique ordered ID column."""
    with file_lock:
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["id", "timestamp", "date", "water_level_pct", "motor_status", "event_type"])

def get_next_id():
    """Calculates the next row ID for ordered CSV recording."""
    if not os.path.exists(CSV_FILE):
        return 1
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        if len(rows) <= 1:
            return 1
        try:
            return int(rows[-1][0]) + 1
        except ValueError:
            return len(rows)

def log_event(water_level, status, event_type="3SEC_LOG"):
    """Thread-safe CSV event logger with sequential row IDs."""
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    date_str = now.strftime("%Y-%m-%d")

    with file_lock:
        row_id = get_next_id()
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([row_id, timestamp_str, date_str, water_level, status, event_type])

def calculate_statistics():
    """Calculates statistical metrics from ordered CSV logs."""
    with file_lock:
        if not os.path.exists(CSV_FILE):
            return {
                "avg_water_level": 0,
                "min_water_level": 0,
                "max_water_level": 0,
                "total_logs": 0,
                "auto_starts": 0,
                "manual_starts": 0,
                "recent_logs": []
            }
        
        water_levels = []
        auto_starts = 0
        manual_starts = 0
        recent_logs = []

        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    lvl = int(row["water_level_pct"])
                    water_levels.append(lvl)
                    event = row.get("event_type", "")
                    if event == "AUTO_START_LOW_WATER":
                        auto_starts += 1
                    elif event == "USER_MANUAL_START":
                        manual_starts += 1
                    recent_logs.append(row)
                except ValueError:
                    continue

        total_logs = len(water_levels)
        avg_lvl = round(sum(water_levels) / total_logs, 1) if total_logs > 0 else 0
        min_lvl = min(water_levels) if total_logs > 0 else 0
        max_lvl = max(water_levels) if total_logs > 0 else 0

        return {
            "avg_water_level": avg_lvl,
            "min_water_level": min_lvl,
            "max_water_level": max_lvl,
            "total_logs": total_logs,
            "auto_starts": auto_starts,
            "manual_starts": manual_starts,
            "recent_logs": recent_logs[-20:]  # Return last 20 logs for dashboard
        }

def send_arduino_command(cmd):
    """Sends control byte ('1' or '0') to Arduino."""
    global ser_instance
    if ser_instance and ser_instance.is_open:
        try:
            ser_instance.write(cmd.encode('utf-8'))
            return True
        except Exception as e:
            print(f"[SERIAL WRITE ERROR] {e}")
    return False

def handle_arduino_serial():
    """Background thread to read serial data and handle automated control logic."""
    global latest_water_level, motor_status, ser_instance, manual_override_until
    try:
        ser_instance = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(f"[HARDWARE] Connected on {SERIAL_PORT}")
    except Exception as e:
        print(f"[HARDWARE WARNING] Could not connect to {SERIAL_PORT}: {e}")
        print("[HARDWARE] Server running in demo/standalone mode.")

    while True:
        try:
            if ser_instance and ser_instance.in_waiting > 0:
                line = ser_instance.readline().decode('utf-8', errors='ignore').strip()

                if line.startswith("WATER_LEVEL:"):
                    try:
                        val = int(line.split(":")[1])
                        latest_water_level = val
                        now = time.time()

                        if now > manual_override_until:
                            if latest_water_level < 15 and motor_status != "RUNNING":
                                if send_arduino_command('1'):
                                    motor_status = "RUNNING"
                                    log_event(latest_water_level, motor_status, "AUTO_START_LOW_WATER")
                            elif latest_water_level >= 15 and motor_status != "STOPPED":
                                if send_arduino_command('0'):
                                    motor_status = "STOPPED"
                                    log_event(latest_water_level, motor_status, "AUTO_STOP_LEVEL_OK")

                        log_event(latest_water_level, motor_status, "3SEC_LOG")
                    except ValueError:
                        pass

            time.sleep(0.1)
        except Exception as err:
            print(f"[SERIAL LOOP ERROR] {err}")
            time.sleep(1)

def generate_ai_response(user_message, system_prompt):
    """Generates AI response using Gemini or OpenAI based on configuration."""
    global LLM_PROVIDER
    
    if LLM_PROVIDER == "gemini" and gemini_client:
        from google.genai import types
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=350,
            )
        )
        return response.text.strip()

    elif LLM_PROVIDER == "openai" and openai_client:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=350
        )
        return response.choices[0].message.content.strip()

    return f"AI provider '{LLM_PROVIDER}' is not properly configured with an API key."

# --- ROUTES ---

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Returns current system metrics, live status, and statistics."""
    stats = calculate_statistics()
    return jsonify({
        "current_water_level": latest_water_level,
        "motor_status": motor_status,
        "active_llm_provider": LLM_PROVIDER.upper(),
        "stats": stats
    })

@app.route('/api/control', methods=['POST'])
def manual_control():
    """Manual hardware trigger route for Dashboard buttons."""
    global motor_status, manual_override_until
    data = request.json or {}
    action = data.get("action")

    if action == "ON":
        if send_arduino_command('1'):
            motor_status = "RUNNING"
            manual_override_until = time.time() + 60
            log_event(latest_water_level, motor_status, "USER_MANUAL_START")
            return jsonify({"success": True, "status": "RUNNING"})
    elif action == "OFF":
        if send_arduino_command('0'):
            motor_status = "STOPPED"
            manual_override_until = time.time() + 60
            log_event(latest_water_level, motor_status, "USER_MANUAL_STOP")
            return jsonify({"success": True, "status": "STOPPED"})

    return jsonify({"success": False, "message": "Failed to send hardware command"}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    global motor_status, manual_override_until
    data = request.json or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message field is required."}), 400

    msg_lower = message.lower()
    hardware_action = None

    if any(k in msg_lower for k in ["turn on motor", "start pump", "open valve", "run motor", "pump water"]):
        if send_arduino_command('1'):
            motor_status = "RUNNING"
            manual_override_until = time.time() + 60
            hardware_action = "Manually turned ON the motor."
            log_event(latest_water_level, motor_status, "USER_MANUAL_START")

    elif any(k in msg_lower for k in ["turn off motor", "stop pump", "close valve", "stop motor"]):
        if send_arduino_command('0'):
            motor_status = "STOPPED"
            manual_override_until = time.time() + 60
            hardware_action = "Manually turned OFF the motor."
            log_event(latest_water_level, motor_status, "USER_MANUAL_STOP")

    stats = calculate_statistics()

    system_instruction = f"""
    You are an intelligent AI Smart Farm Assistant powering an automated irrigation system.
    Active Provider: {LLM_PROVIDER.upper()}

    --- CURRENT LIVE FARM METRICS ---
    - Current Water Reservoir Level: {latest_water_level}%
    - Stepper Motor Pump State: {motor_status}
    - Recent Hardware Action Executed: {hardware_action if hardware_action else "None"}

    --- HISTORICAL FARM STATISTICS ---
    - Total Logs Recorded: {stats['total_logs']}
    - Average Water Level: {stats['avg_water_level']}%
    - Min Water Level: {stats['min_water_level']}% | Max: {stats['max_water_level']}%
    - Automated Motor Starts: {stats['auto_starts']} times
    - Manual User Motor Starts: {stats['manual_starts']} times

    --- AUTOMATION LOGIC ---
    - Auto Rule: Water Level < 15% turns motor ON; >= 15% turns motor OFF.

    Provide helpful, professional, and concise responses.
    """

    try:
        reply = generate_ai_response(message, system_instruction)
    except Exception as e:
        print(f"[AI ERROR] {e}")
        reply = "I encountered an error attempting to process your request."

    return jsonify({"reply": reply, "provider": LLM_PROVIDER.upper()})

if __name__ == '__main__':
    init_csv()
    threading.Thread(target=handle_arduino_serial, daemon=True).start()
    print(f"\n--- SMART FARM AI DASHBOARD & CHATBOT ONLINE ON PORT {PORT} ---")
    app.run(host='0.0.0.0', port=PORT, debug=False)
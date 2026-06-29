# BEFORE AND AFTER 5MINS
import json
from datetime import datetime, timedelta
from twilio.rest import Client
import time

# Load timetable from JSON
with open("timetable.json", "r") as file:
    timetable = json.load(file)

# Load status from JSON
with open("status.json", "r") as file:
    status_data = json.load(file)

# Twilio credentials
account_sid = "AC6985f26ee2c78a2cfeb8587812334735"
auth_token = "3c5a60c14a5e1203599300f1aade5f47"
twilio_phone_number = "+17744687533"

client = Client(account_sid, auth_token)

def send_sms(message, phone):
    sms = client.messages.create(
        body=message,
        from_=twilio_phone_number,
        to=phone
    )
    print(f"Message sent to {phone} SID: {sms.sid}")

# Track already-sent alerts
sent_alerts = set()

while True:
    now = datetime.now()
    today = now.strftime("%A")  # Monday, Tuesday, etc.

    if today in timetable:
        for period in timetable[today]:
            start_time = datetime.strptime(period["start_time"], "%H:%M").time()
            start_dt = datetime.combine(now.date(), start_time)

            # Unique ID for this period (date + subject + faculty)
            period_id = f"{today}_{period['start_time']}_{period['faculty_name']}"

            # Alert 5 mins before class
            alert_time = (start_dt - timedelta(minutes=5)).time()
            if (now.time().hour == alert_time.hour 
                and now.time().minute == alert_time.minute 
                and f"{period_id}_before" not in sent_alerts):
                
                send_sms(
                    f"🔔 Reminder: {period['faculty_name']}, your {period['subject']} class starts in 5 minutes.",
                    period["phone"]
                )
                sent_alerts.add(f"{period_id}_before")

            # Alert if faculty absent after 5 mins
            absent_check_time = (start_dt + timedelta(minutes=5)).time()
            if (now.time().hour == absent_check_time.hour 
                and now.time().minute == absent_check_time.minute 
                and f"{period_id}_absent" not in sent_alerts):

                # Check if at least one room is absent
                if any(room["status"] == "Absent" for room in status_data):
                    send_sms(
                        f"⚠️ Alert: {period['faculty_name']}, your {period['subject']} class has already started!",
                        period["phone"]
                    )
                    sent_alerts.add(f"{period_id}_absent")

    time.sleep(60)  # Check every minute
from django.core.management.base import BaseCommand
from myapp.models import Vehicle, ServiceBooking
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
import os
import time


class Command(BaseCommand):
    help = "Send WhatsApp reminders 3 days before next service date"

    def handle(self, *args, **kwargs):
        today = date.today()
        reminder_date = today + timedelta(days=3)

        print("Today:", today)
        print("Reminder Date:", reminder_date)

        vehicles = Vehicle.objects.all()

        # ✅ Chrome profile (QR scan only once)
        chrome_options = webdriver.ChromeOptions()
        chrome_profile_path = os.path.join(os.getcwd(), "whatsapp_profile")

        if not os.path.exists(chrome_profile_path):
            os.makedirs(chrome_profile_path)

        chrome_options.add_argument(f"user-data-dir={chrome_profile_path}")
        chrome_options.add_argument("--profile-directory=Default")

        # ✅ Start driver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        driver.get("https://web.whatsapp.com/")
        print("👉 Scan QR ONLY FIRST TIME...")

        # ✅ Give time to scan QR
        time.sleep(15)

        print("⏳ Waiting for WhatsApp to load...")

        # ✅ Stable wait (fix Timeout issue)
        WebDriverWait(driver, 120).until(
            EC.any_of(
                EC.presence_of_element_located((By.XPATH, "//div[@id='pane-side']")),
                EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))
            )
        )

        print("✅ WhatsApp Loaded Successfully!")

        found = False

        for vehicle in vehicles:
            next_service = vehicle.next_service_date()

            if next_service != reminder_date:
                continue

            found = True

            user = vehicle.user
            profile = getattr(user, "userprofile", None)

            if not profile or not profile.mobile_number:
                print(f"❌ Skipping {user.username}: no mobile number")
                continue

            # ✅ Fix mobile format
            mobile = profile.mobile_number.strip()
            if not mobile.startswith("91"):
                mobile = "91" + mobile

            # ✅ Get booking details
            booking = ServiceBooking.objects.filter(
                vehicle=vehicle,
                service_date__gte=today
            ).order_by('-service_date').first()

            garage = "N/A"
            timeslot = "N/A"
            pickup_drop = "N/A"
            address = "N/A"
            note = "N/A"

            if booking:
                if booking.garage:
                    garage = f"{booking.garage.name} - {booking.garage.location}"
                if booking.timeslot:
                    timeslot = booking.timeslot
                if booking.pickup_drop:
                    pickup_drop = booking.pickup_drop
                if booking.pickup_drop_address:
                    address = booking.pickup_drop_address
                if booking.additional_note:
                    note = booking.additional_note

            # ✅ Message
            message_text = f"""
Hello {user.username},

Your vehicle {vehicle.name} ({vehicle.vehicle_number})
was last serviced on {vehicle.last_service_date}.

Next service (after {vehicle.service_interval_days} days)
is due on {next_service}.

Garage: {garage}
Timeslot: {timeslot}
Pickup/Drop: {pickup_drop}
Address: {address}

Note: {note}

Please visit the service center on time.

Thank you 🚗
"""

            message = urllib.parse.quote(message_text)

            try:
                print(f"📩 Opening chat for {mobile}")

                driver.get(f"https://web.whatsapp.com/send?phone={mobile}&text={message}")

                # ✅ Wait for chat to open
                time.sleep(10)

                # ✅ Message box (stable)
                message_box = WebDriverWait(driver, 40).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//footer//div[@contenteditable='true']")
                    )
                )

                message_box.send_keys(Keys.ENTER)

                print(f"✅ Sent to {mobile}")
                time.sleep(5)

            except Exception as e:
                print(f"❌ Failed for {mobile}: {e}")

        if not found:
            print("No reminders for today.")

        driver.quit()
        print("✅ Done.")
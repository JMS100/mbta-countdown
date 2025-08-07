import requests
import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime

# === CONFIG ===
MBTA_API_KEY = "8aede8c2cbe749a7b8cd1ab1445ea95f"
RED_LINE_STOP_ID = "place-cntsq"  # Central Sq
GREEN_B_STOP_IDS = ["70144", "70145"]  # BU Central (both directions)
MBTA_API_URL = "https://api-v3.mbta.com/predictions"

# === ASSETS ===
RED_CIRCLE_PATH = "media/MBTA-Red-Line.png"
GREEN_B_CIRCLE_PATH = "media/green_line.jpg"
BUS_PATH = "media/Logo_Ligne_Bus_RATP_47.svg.png"

class MBTATracker:
    def __init__(self):
        self.all_trains = []
        self.current_index = 0
        self.now = None
        self.headers = {"x-api-key": MBTA_API_KEY}

    def fetch_arrivals(self):
        self.all_trains = []
        self.now = datetime.now(datetime.now().astimezone().tzinfo)

        self._fetch_red_line()
        self._fetch_green_b_line()
        self._fetch_bus_47()

        self.all_trains.sort(key=lambda x: x[2])

    def _get_predictions(self, stop_id, route):
        params = {
            "filter[stop]": stop_id,
            "filter[route]": route,
            "sort": "departure_time"
        }
        resp = requests.get(MBTA_API_URL, headers=self.headers, params=params)
        if resp.status_code != 200:
            return []
        return resp.json().get("data", [])

    def _add_prediction(self, time_str, symbol, destination):
        if not time_str:
            return
        dt = datetime.fromisoformat(time_str)
        delta = (dt - self.now).total_seconds()
        if not (0 <= delta <= 1800):
            return
        minutes = int(delta / 60)
        self.all_trains.append((symbol, destination, minutes))

    def _fetch_red_line(self):
        data = self._get_predictions(RED_LINE_STOP_ID, "Red")
        directions = {0: "Ashmont/Braintree", 1: "Alewife"}
        for item in data:
            direction = item["attributes"].get("direction_id", 0)
            dest = directions.get(direction, "Unknown")
            self._add_prediction(item["attributes"].get("departure_time"), "🔴", dest)

    def _fetch_green_b_line(self):
        for stop_id, direction, destination in [
            ("70144", 1, "Government Center"),
            ("70145", 0, "Boston College")
        ]:
            data = self._get_predictions(stop_id, "Green-B")
            for item in data:
                self._add_prediction(item["attributes"].get("departure_time"), "🟩", destination)

    def _fetch_bus_47(self):
        for stop_id, destination in [
            ("1812", "Central Square"),
            ("11767", "Broadway")
        ]:
            data = self._get_predictions(stop_id, "47")
            for item in data:
                self._add_prediction(item["attributes"].get("departure_time"), "🚌", destination)


tracker = MBTATracker()

# === UI SETUP ===
root = tk.Tk()
root.title("MBTA Tracker – Central Sq, BU Central, Bus 47")
root.configure(bg="black")

# Load images
red_circle = ImageTk.PhotoImage(Image.open(RED_CIRCLE_PATH).resize((30, 30)))
green_b_circle = ImageTk.PhotoImage(Image.open(GREEN_B_CIRCLE_PATH).resize((30, 30)))
bus = ImageTk.PhotoImage(Image.open(BUS_PATH).resize((30, 30)))

symbol_images = {
    "🔴": red_circle,
    "🟩": green_b_circle,
    "🚌": bus
}

tk.Label(
    root, text="Red Line, Green B, & 47 Bus Tracker",
    fg="white", bg="black", font=("Helvetica", 26, "bold")
).pack(pady=(10, 10))

container = tk.Frame(root, bg="black")
container.pack(expand=True)

board_frame = tk.Frame(container, bg="black")
board_frame.pack(padx=40, pady=20)

def update_display():
    for widget in board_frame.winfo_children():
        widget.destroy()

    tk.Label(
        board_frame, text="Next Departures", fg="white", bg="black",
        font=("Helvetica", 26, "bold")
    ).pack(pady=(10, 10))

    upcoming = tracker.all_trains[tracker.current_index:tracker.current_index + 3]
    if not upcoming:
        tk.Label(
            board_frame, text="No upcoming departures", fg="white", bg="black",
            font=("Helvetica", 20)
        ).pack(pady=20)
    else:
        for symbol, dest, mins in upcoming:
            row = tk.Frame(board_frame, bg="black")
            row.pack(fill="x", pady=4)
            logo = symbol_images.get(symbol)
            tk.Label(row, image=logo, bg="black").pack(side="left", padx=12)
            tk.Label(row, text=dest, fg="white", bg="black", font=("Helvetica", 20)).pack(side="left")
            tk.Label(row, text=f"{mins} min" if mins > 0 else "Now", fg="white", bg="black",
                     font=("Helvetica", 20)).pack(side="right", padx=10)

    tracker.current_index = (tracker.current_index + 3) % max(len(tracker.all_trains), 1)
    root.after(5000, update_display)

def periodic_refresh():
    tracker.fetch_arrivals()
    root.after(30000, periodic_refresh)

tracker.fetch_arrivals()
update_display()
periodic_refresh()
root.mainloop()
import tkinter as tk

from turtle import width
from datetime import datetime as dt

from collections import deque

from ns import colours as c
from ns import api as api
from ns.stations import full_station_name

import util

import constants


pi_width = 480
pi_height = 320
row_height = pi_height / 8


root = tk.Tk()
root.configure(background='black')
root.minsize(width=pi_width, height=pi_height)
root.maxsize(width=pi_width, height=pi_height)
# Make the window borderless
root.overrideredirect(True)

# Header

# Define frame for header
header_frame = tk.Frame(root, width=pi_width, height=row_height)
header_frame.grid(row=0, column=0)

# Force dimensions
header_frame.grid_propagate(False)

# Configure the grid so the widgets can expand
header_frame.grid_columnconfigure(0, weight=1)
header_frame.grid_columnconfigure(1, weight=0)
header_frame.grid_rowconfigure(0, weight=1)

# Header common styling
header_text_args = {
    'font': ('Frutiger', 20),
    'fg': c.white,
    'bg': c.blue}


station_label = tk.Label(header_frame,
                         text="Test",  # station_codes[selected_station],
                         anchor=tk.W,
                         **header_text_args)
# Position, and fill cell with sticky
station_label.grid(row=0, column=0, sticky=tk.NSEW)

time_label = tk.Label(header_frame,
                      text="12:00:00",
                      **header_text_args)

time_label.grid(row=0, column=1, sticky=tk.NSEW)


def update_time():
    current_time = dt.now().strftime("%H:%M:%S")
    time_label.config(text=current_time)
    root.after(1000, update_time)


update_time()


# Trains
number_of_trains = 7  # Limit to 7

# Common styling
train_style = {
    'anchor': tk.W,
    'font': ('Frutiger', 16),
    'fg': c.blue,
    'bg': c.white}
delayed_style = train_style | {
    'fg': c.red}
track_style = train_style | {
    'anchor': tk.CENTER}


def create_dark_frame():
    # Define frame for trains
    tf = tk.Frame(root, width=pi_width, height=pi_height -
                  row_height, background='black')
    tf.grid(row=1, column=0)

    # Force dimensions
    tf.grid_propagate(False)
    return tf


def create_train_frame():
    # Define frame for trains
    tf = tk.Frame(root, width=pi_width, height=pi_height -
                  row_height, background=c.white)
    tf.grid(row=1, column=0)

    # Force dimensions
    tf.grid_propagate(False)

    # Configure the grid so the widgets can expand
    tf.grid_columnconfigure(0, weight=0)  # Time
    tf.grid_columnconfigure(1, weight=0)  # Delay
    tf.grid_columnconfigure(2, weight=0)  # Track
    tf.grid_columnconfigure(3, weight=1)  # Service
    tf.grid_columnconfigure(4, weight=0)  # Stock

    for i in range(number_of_trains):
        tf.grid_rowconfigure(i, weight=1)
    return tf


train_frame = create_train_frame()

live_departures = deque(map(lambda x: api.Departures(
    station_code=x, limit=number_of_trains, destination_filter=['ES']), constants.ns_stations))


def update_board():
    global train_frame
    # Suspend API calls between 0 and 5
    h = dt.now().hour
    if h >= 0 and h < 5:
        station_label.config(text="Offline till 5:00")
        train_frame.destroy()
    else:
        global live_departures
        board = live_departures[0]  # Select current station
        station_label.config(text=full_station_name(board.station_code))
        trains = board.get_trains()
        live_departures.rotate(-1)  # Cycles through stations

        # Fill the board with empty entries if api returned < 7
        for i in range(7 - len(trains)):
            trains.append(api.STOCK_TRAIN)

        # Destroy the old frame, and rebuild frame
        train_frame.destroy()
        del(train_frame)
        train_frame = create_train_frame()

        # Fill the frame with train data
        for n in range(number_of_trains):
            i = n*2
            train_frame.grid_rowconfigure(i, weight=1)  # Train

            t = trains[n]

            if not t['cancelled']:
                tk.Label(train_frame, text=t['time'], **train_style)\
                    .grid(row=i, column=0, sticky=tk.NSEW)
            else:
                tk.Label(train_frame, text=util.strike(t['time']), **delayed_style)\
                    .grid(row=i, column=0, sticky=tk.NSEW)

            delay = t['delay']
            if (delay > 0):
                tk.Label(train_frame, text='+{}'.format(delay), **delayed_style)\
                    .grid(row=i, column=1, sticky=tk.NSEW)

            track_frame = tk.LabelFrame(
                train_frame, text='spoor', highlightcolor=c.blue, highlightbackground=c.blue, background=c.white)
            track_frame.grid(row=i, column=2, sticky=tk.NSEW)
            tk.Label(track_frame, text=t['platform'], **track_style).pack()

            service_text = t['service']
            if not t['cancelled']:
                tk.Label(train_frame, text=service_text, **train_style)\
                    .grid(row=i, column=3, sticky=tk.NSEW)
            else:
                tk.Label(train_frame, text=util.strike(service_text), **delayed_style)\
                    .grid(row=i, column=3, sticky=tk.NSEW)

            rolling_stock_frame = tk.LabelFrame(
                train_frame, text='Materieel', highlightcolor=c.blue, highlightbackground=c.blue, background=c.white)
            rolling_stock_frame.grid(row=i, column=4, sticky=tk.NSEW)
            tk.Label(rolling_stock_frame,
                     text=t['rolling_stock'], **track_style).pack()

            train_frame.grid_rowconfigure(i+1, weight=0)  # Seperator
            tk.Frame(train_frame, background=c.blue).grid(
                row=i+1, columnspan=5, sticky=tk.EW)

    # Repeat API call after 30 seconds
    root.after(1000*15, update_board)


update_board()


# Add close button to esc
def close_app(event):
    root.destroy()


root.bind('<Escape>', close_app)

# Setup app
root.mainloop()

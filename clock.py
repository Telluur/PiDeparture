import tkinter as tk
from PIL import ImageTk, Image
import time

root = tk.Tk()
root.overrideredirect(True)  # This removes the window border

canvas = tk.Canvas(root, width=480, height=320)
canvas.pack()

img = ImageTk.PhotoImage(Image.open("assets/background.jpg"))
canvas.create_image(0, 0, anchor="nw", image=img)
root.update()  # Forces style update to propagate


def update_time():
    current_time = time.strftime("%H:%M:%S")
    canvas.itemconfig(text, text=current_time)
    root.after(1000, update_time)


text = canvas.create_text(canvas.winfo_width() / 2,
                          canvas.winfo_height() / 2,
                          text="00:00:00",
                          fill="white",
                          font=("Frutiger", 72))
update_time()


def close_app(event):
    root.destroy()


root.bind('<Escape>', close_app)


root.mainloop()

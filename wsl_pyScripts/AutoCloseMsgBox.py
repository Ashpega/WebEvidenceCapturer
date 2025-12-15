import tkinter as tk
from tkinter import messagebox

def show_auto_closing_message(message="This message is automatically closed",
                              seconds=5,
                              title="Progress Information"):
    # Create the window
    root = tk.Tk()
    root.title(title)

    # Force small popup style
    root.geometry("400x120")
    root.resizable(False, False)

    # Center the window on screen
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    win_w = 400
    win_h = 120
    x = (screen_w // 2) - (win_w // 2)
    y = (screen_h // 2) - (win_h // 2)
    root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    # Always on top
    root.attributes("-topmost", True)

    # Message label
    label = tk.Label(
        root,
        text=message,
        font=("Arial", 12),
        anchor="center"
    )
    label.pack(expand=True, fill="both")

    # Auto-close after N seconds
    root.after(seconds * 1000, root.destroy)

    root.mainloop()

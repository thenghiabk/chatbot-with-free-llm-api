import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

import database10 as db
from staff10 import Staff
from student10 import Student

try:
    users = db.get_users()
except:
    users = []
    messagebox.showinfo("Error", "ERROR: cannot connect to database")

# print out all the user details
for user in users:
    user.print_details()
    print()


def clicked():
    group = combo.get()
    print(f"To:      {group}")
    message = message_txt.get()
    print(f"Message: {message}")
    for user in users:
        send_message = False
        if group == "all":
            send_message = True
        elif group == "students":
            if isinstance(user, Student):
                send_message = True
        elif group == "staff":
            if isinstance(user, Staff):
                send_message = True
        else:  # group is a module
            if user.attached_to(group):
                send_message = True
        if send_message:
            user.send(message)
    print()


window = tk.Tk()
window.geometry("400x60")
window.title("Uni App")

groups = ["", "all", "staff", "students"]
for user in users:
    if hasattr(user, "modules"):
        for module in user.modules:
            if module not in groups:
                groups.append(module)

combo = ttk.Combobox(window)
combo["values"] = groups
combo.current(0)
combo.grid(column=0, row=0)

btn = tk.Button(window, text="Send message", command=clicked)
btn.grid(column=1, row=0)

message_txt = tk.Entry(window, width=60)
message_txt.grid(column=0, row=1, columnspan=2, padx=15, pady=5)

window.mainloop()

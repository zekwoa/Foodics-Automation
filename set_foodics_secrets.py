# set_foodics_secrets_gui.py
import keyring
import tkinter as tk
from tkinter import messagebox

SERVICE = "foodics"

def save():
    acct = e_account.get().strip()
    mail = e_email.get().strip()
    pwd  = e_password.get().strip()
    if not (acct and mail and pwd):
        messagebox.showerror("Error", "Please fill all fields.")
        return
    keyring.set_password(SERVICE, "account", acct)
    keyring.set_password(SERVICE, "email",   mail)
    keyring.set_password(SERVICE, "password",pwd)
    messagebox.showinfo("Saved", "Credentials saved to OS keychain.")
    root.destroy()

root = tk.Tk()
root.title("Save Foodics Credentials")
root.geometry("360x200")

tk.Label(root, text="Account number").pack(anchor="w", padx=12, pady=(12,0))
e_account = tk.Entry(root, width=40); e_account.pack(padx=12)

tk.Label(root, text="Email").pack(anchor="w", padx=12, pady=(8,0))
e_email = tk.Entry(root, width=40); e_email.pack(padx=12)

tk.Label(root, text="Password").pack(anchor="w", padx=12, pady=(8,0))
e_password = tk.Entry(root, width=40, show="*"); e_password.pack(padx=12)

tk.Button(root, text="Save", command=save).pack(pady=14)
root.mainloop()

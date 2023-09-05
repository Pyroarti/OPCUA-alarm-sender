import customtkinter
import time
from tkinter import IntVar, filedialog, messagebox
import os
from os import startfile
from PIL import Image
from cryptography.fernet import Fernet
from create_logger import setup_logger
from opcua_client import connect_opcua
from asyncua import Client
import asyncio
import threading
from queue import Queue
from threading import Thread
import json
from tkinter import ttk


logger = setup_logger('main')

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
assets_dir = os.path.join(parent_dir, 'assets')
config_dir = os.path.join(parent_dir, "configs")

backround_image = os.path.join(assets_dir, 'background.png')
about_text_file = os.path.join(assets_dir, 'about.txt')
opcua_config_file = os.path.join(config_dir, 'opcua_config.json')
phone_book_file = os.path.join(config_dir, 'phone_book.json')


def run_asyncio_loop(queue):
    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)
    try:
        while True:
            coro = queue.get()
            if coro is None:
                break
            task = loop.create_task(coro)
            loop.run_until_complete(task)

    finally:
        loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(loop)))
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


class CreateUserWindow(customtkinter.CTkToplevel):
    """ Class for the create a new user."""
    def __init__(self, parent, app_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = app_instance

        window_width = 300
        window_height = 400

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()

        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        pos_x = parent_x + (parent_width // 2) - (window_width // 2)
        pos_y = parent_y + (parent_height // 2) - (window_height // 2)

        self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        self.resizable(False, False)
        self.title("OPC UA Alarm Notifier")
        self.attributes('-topmost', True)

        header_label = customtkinter.CTkLabel(master=self,
                                            text="User creator",
                                            font=("Helvetica", 17),
                                            bg_color="transparent")
        header_label.pack(pady=10)

        self.name_label = customtkinter.CTkLabel(self, text="Name:", bg_color="transparent", font=("Helvetica", 16))
        self.name_label.pack()

        self.name_entry = customtkinter.CTkEntry(self,
                                                    font=("Helvetica", 16),
                                                    width=200)
        self.name_entry.pack()

        self.phone_number_label = customtkinter.CTkLabel(self, text="Number:", bg_color="transparent", font=("Helvetica", 16))
        self.phone_number_label.pack()

        self.phone_number_entry = customtkinter.CTkEntry(self,
                                                    font=("Helvetica", 16),
                                                    width=200)
        self.phone_number_entry.pack()

        self.submit_button = customtkinter.CTkButton(self,
                                                     text="Submit the user",
                                                     command=self.check_user_input,
                                                     width=200,
                                                     height=40,
                                                     font=("Helvetica", 18))
        self.submit_button.pack(pady=10)


    def check_user_input(self):
        """Checks the user input"""
        name = self.name_entry.get()
        phone_number = self.phone_number_entry.get()

        if name == "" or phone_number == "":
            messagebox.showerror("Error", "Please fill out all the fields")
            return

        with open(phone_book_file, "r",encoding="UTF8") as file:
            data = file.read()
            json_data = json.loads(data)

            for number in json_data:
                if number["phone_number"] == number:
                    messagebox.showerror("Error", "This number is already in use")
                    return

        user = {
            "Name": name,
            "phone_number": phone_number,
            "Active": "Yes"
            }

        with open(phone_book_file, "r",encoding="UTF8") as file:
            data = file.read()
            json_data = json.loads(data)
            json_data.append(user)

        with open(phone_book_file, "w",encoding="UTF8") as file:
            json.dump(json_data, file, indent=4)

        self.destroy()

        self.app.update_user_list()


class EditUserWindow(customtkinter.CTkToplevel):
    """Class for the how to use window with the video tutorial."""
    def __init__(self, parent, app_instance, user_name, user_number, user_active, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user_name = user_name
        self.user_number = user_number
        self.user_active = user_active
        self.app = app_instance

        window_width = 300
        window_height = 400

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()

        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        pos_x = parent_x + (parent_width // 2) - (window_width // 2)
        pos_y = parent_y + (parent_height // 2) - (window_height // 2)

        self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        self.resizable(False, False)
        self.title("OPC UA Alarm Notifier")
        self.attributes('-topmost', True)

        information_label = customtkinter.CTkLabel(master=self,
                                            text="User editor",
                                            font=("Helvetica", 17),
                                            bg_color="transparent")
        information_label.pack(pady=10)

        self.new_name_label = customtkinter.CTkLabel(self, text="Name:", bg_color="transparent", font=("Helvetica", 16))
        self.new_name_label.pack()

        self.new_name_entry = customtkinter.CTkEntry(self,
                                                    font=("Helvetica", 16),
                                                    width=200)
        self.new_name_entry.pack()
        self.new_name_entry.insert(0, self.user_name)

        self.new_phone_number_label = customtkinter.CTkLabel(self, text="Number:", bg_color="transparent", font=("Helvetica", 16))
        self.new_phone_number_label.pack()

        self.new_phone_number_entry = customtkinter.CTkEntry(self,
                                                    font=("Helvetica", 16),
                                                    width=200,)
        self.new_phone_number_entry.pack()
        self.new_phone_number_entry.insert(0, self.user_number)

        self.submit_button = customtkinter.CTkButton(self,
                                                     text="Submit the user",
                                                     command=self.check_user_input,
                                                     width=200,
                                                     height=40,
                                                     font=("Helvetica", 18))
        self.submit_button.pack(pady=10)


    def check_user_input(self):
        """Checks the user input"""
        new_name = self.new_name_entry.get()
        new_phone_number = self.new_phone_number_entry.get()

        if new_name == "" or new_phone_number == "":
            messagebox.showerror("Error", "Please fill out all the fields")
            return

        user = {
            "Name": new_name,
            "phone_number": new_phone_number,
            "Active": "Yes"
        }

        with open(phone_book_file, "r", encoding="UTF8") as file:
            data = file.read()
            json_data = json.loads(data)

        # Find the index of the user to edit
        user_index = None
        for i, current_user in enumerate(json_data):
            if current_user["Name"] == self.user_name and current_user["phone_number"] == self.user_number:
                user_index = i
                break

        # If user found, update its data
        if user_index is not None:
            json_data[user_index] = user
            with open(phone_book_file, "w", encoding="UTF8") as file:
                json.dump(json_data, file, indent=4)
        else:
            messagebox.showerror("Error", "User not found")

        self.destroy()
        self.app.update_user_list()


class AboutWindow(customtkinter.CTkToplevel):
    """Class for the how to use window with the video tutorial."""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        window_width = 300
        window_height = 200

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()

        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        pos_x = parent_x + (parent_width // 2) - (window_width // 2)
        pos_y = parent_y + (parent_height // 2) - (window_height // 2)

        self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        self.resizable(False, False)
        self.title("OPC UA Alarm Notifier")
        self.attributes('-topmost', True)

        with open(about_text_file, "r", encoding="utf-8") as text_file:
            about_text = text_file.read()

        information_label = customtkinter.CTkLabel(master=self,
                                            text=about_text,
                                            font=("Helvetica", 17),
                                            bg_color="transparent")
        information_label.pack(pady=10)


class App(customtkinter.CTk):
    """Class for the main app and main window"""


    def __init__(self, async_queue, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.async_queue: Queue = async_queue

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")

        self.geometry("800x600")
        self.title("OPC UA Alarm Notifier")
        self.resizable(False, False)

        self.toplevel_window = None
        self.edit_user_window = None
        self.create_new_user_window = None

        self.main_frame = customtkinter.CTkFrame(master=self, bg_color="black")
        self.main_frame.pack(pady=20, padx=40, fill="both")

        self.main_label = customtkinter.CTkLabel(master=self.main_frame, justify=customtkinter.LEFT,
                                            text="OPC UA Alarm Notifier",
                                            font=customtkinter.CTkFont(size=30, weight="bold"),
                                            bg_color="transparent")
        self.main_label.pack(pady=10, padx=10)

        self.create_new_user_button = customtkinter.CTkButton(master=self.main_frame,
                                                 command=self.open_create_user_window,
                                                 text="Create new user",
                                                 width=200,
                                                 height=50,
                                                 font=("Helvetica", 15))
        self.create_new_user_button.pack(pady=10, padx=10)

        self.config_opcua_serverbutton = customtkinter.CTkButton(master=self.main_frame,
                                                 command="",
                                                 text="Config the OPC UA server",
                                                 width=200,
                                                 height=50,
                                                 font=("Helvetica", 15))
        self.config_opcua_serverbutton.pack(pady=10, padx=10)

        self.test_opcua_connection_button = customtkinter.CTkButton(master=self.main_frame,
                                                 command=self.test_opcua_connection,
                                                 text="Test the OPC UA connection",
                                                 width=200,
                                                 height=50,
                                                 font=("Helvetica", 15))
        self.test_opcua_connection_button.pack(pady=10, padx=10)

        self.about_popup_button = customtkinter.CTkButton(master=self.main_frame,
                                                    command=self.open_about_window,
                                                    text="?",
                                                    width=30,
                                                    height=30,
                                                    corner_radius=60,
                                                    font=("Helvetica", 15),
                                                    bg_color="transparent")
        self.about_popup_button.place(x=670, y=8)

        self.user_list_label = customtkinter.CTkLabel(master=self.main_frame, justify=customtkinter.LEFT,
                                            text="User list",
                                            font=customtkinter.CTkFont(size=20, weight="bold"),
                                            bg_color="transparent")
        self.user_list_label.pack(pady=20, padx=10)

        self.users_treeview = ttk.Treeview(self.main_frame, columns=("Name", "Number", "Active"),
                                      show="headings", height=10,style="Treeview", selectmode="browse")

        self.users_treeview.heading("#0", text="", anchor="w")
        self.users_treeview.heading("Name", text="Name",anchor="center")
        self.users_treeview.heading("Number", text="Number",anchor="center")
        self.users_treeview.heading("Active", text="Active",anchor="center")

        self.users_treeview.column("#0", width=0)
        self.users_treeview.column("Name", width=150,anchor="center")
        self.users_treeview.column("Number", width=150,anchor="center")
        self.users_treeview.column("Active", width=50,anchor="center")

        self.users_treeview.pack(pady=2, padx=10)

        with open(phone_book_file, "r",encoding="UTF8") as file:
            data = file.read()
            json_data = json.loads(data)

            for user in json_data:
                Name = user["Name"]
                phone_number = user["phone_number"]
                user_active = user["Active"]
                self.users_treeview.insert("", "end", text="", values=(Name, phone_number, user_active))

        self.users_treeview.bind("<Double-1>", self.open_edit_user_window)


    def update_user_list(self):
        """Updates the user list"""

        for user in self.users_treeview.get_children():
            self.users_treeview.delete(user)

        with open(phone_book_file, "r",encoding="UTF8") as file:
            data = file.read()
            json_data = json.loads(data)

            for user in json_data:
                Name = user["Name"]
                phone_number = user["phone_number"]
                user_active = user["Active"]
                self.users_treeview.insert("", "end", text="", values=(Name, phone_number, user_active))


    def open_create_user_window(self):
        """Opens the how to use page"""
        if self.create_new_user_window is None or not self.create_new_user_window.winfo_exists():
            self.create_new_user_window = CreateUserWindow(self, self)
        self.create_new_user_window.lift()


    def open_about_window(self):
        """Opens the how to use page"""
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = AboutWindow(self)
        self.toplevel_window.lift()


    def open_edit_user_window(self, event):
        """Opens the how to use page"""

        item = self.users_treeview.selection()[0]
        user_name = self.users_treeview.item(item, "values")[0]
        user_number = self.users_treeview.item(item, "values")[1]
        user_active = self.users_treeview.item(item, "values")[2]

        if self.edit_user_window is None or not self.edit_user_window.winfo_exists():
            self.edit_user_window = EditUserWindow(self, self, user_name, user_number, user_active)
        self.edit_user_window.lift()


    def test_opcua_connection(self):
        """Tests the OPC UA connection"""

        with open(opcua_config_file, "r",encoding="UTF8") as file:
            data = file.read()
            json_data = json.loads(data)

            adresses = json_data["adress"]
            username = json_data["username"]
            password = json_data["password"]

        client = self.async_queue.put(connect_opcua(adresses, username, password))

        if client is None:
            messagebox.showerror("Error", "Connection error")
            return
        else:
            messagebox.showinfo("Success", "Connection successful")
            return


if __name__ == "__main__":
    async_queue = Queue()
    async_thread = Thread(target=run_asyncio_loop, args=(async_queue,), daemon=True)
    async_thread.start()

    app = App(async_queue)
    app.mainloop()

    async_queue.put(None)
    async_thread.join()

    logger.info("Started the program")
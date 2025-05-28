import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import shutil
import urllib.request
import tempfile
import subprocess

STARTUP_DIR = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
EXE_DOWNLOAD_URL = "https://tggamesyt.github.io/mcversion/mcversion.exe"
EXE_FILENAME = "mcversion.exe"

class InstallerWizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MCVersion Installer")
        self.geometry("520x320")
        self.resizable(False, False)

        self.page = 0
        self.selected_folder = os.getcwd()  # default to current working dir

        self.create_widgets()
        self.show_page()

    def create_widgets(self):
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        self.content = ttk.Label(self.container, wraplength=480, anchor="center", justify="center")
        self.content.pack(expand=True, pady=10)

        self.folder_label = ttk.Label(self.container, text="")
        self.folder_button = ttk.Button(self.container, text="Select Folder...", command=self.select_folder)

        self.nav_frame = ttk.Frame(self.container)
        self.nav_frame.pack(side="bottom", fill="x", pady=10)

        self.back_button = ttk.Button(self.nav_frame, text="Back", command=self.back)
        self.next_button = ttk.Button(self.nav_frame, text="Next", command=self.next)

        self.back_button.pack(side="left")
        self.next_button.pack(side="right")

    def show_page(self):
        # Hide folder widgets on pages where not needed
        self.folder_label.pack_forget()
        self.folder_button.pack_forget()

        if self.page == 0:
            self.content.config(
                text=(
                    "Welcome to the MCVersion Installer!\n\n"
                    "This application monitors Minecraft versions on a configured server, "
                    "notifies you when new versions are released, and starts automatically on Windows startup.\n\n"
                    "The installer will download the MCVersion app and set it up for automatic launch.\n\n"
                    "Click Next to continue."
                )
            )
            self.back_button.config(state="disabled")
            self.next_button.config(text="Next")

        elif self.page == 1:
            self.content.config(text="Select the folder where the MCVersion app should be installed:")
            self.folder_label.config(text=self.selected_folder)
            self.folder_label.pack(pady=10)
            self.folder_button.pack(pady=10)

            self.back_button.config(state="normal")
            self.next_button.config(text="Install")

        elif self.page == 2:
            self.content.config(
                text=(
                    "Thank you for installing MCVersion!\n\n"
                    "The app will now start automatically.\n\n"
                    "You can change the install folder or uninstall by deleting the files manually."
                )
            )
            self.folder_label.pack_forget()
            self.folder_button.pack_forget()
            self.back_button.config(state="disabled")
            self.next_button.config(text="Finish")

    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.selected_folder)
        if folder:
            self.selected_folder = folder
            self.folder_label.config(text=self.selected_folder)

    def back(self):
        if self.page > 0:
            self.page -= 1
            self.show_page()

    def next(self):
        if self.page == 0:
            self.page += 1
            self.show_page()
        elif self.page == 1:
            self.next_button.config(state="disabled")
            self.back_button.config(state="disabled")
            self.install_app()
        elif self.page == 2:
            self.destroy()

    def install_app(self):
        try:
            self.content.config(text="Downloading MCVersion executable...")
            self.update()

            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_path = temp_file.name
            temp_file.close()

            urllib.request.urlretrieve(EXE_DOWNLOAD_URL, temp_path)

            self.content.config(text=f"Copying to {self.selected_folder} ...")
            self.update()

            dest_exe_path = os.path.join(self.selected_folder, EXE_FILENAME)
            shutil.copy(temp_path, dest_exe_path)

            # Create startup batch file in startup folder to launch the exe on login
            startup_path = os.path.join(STARTUP_DIR, "mcversion_startup.bat")
            with open(startup_path, "w") as f:
                f.write(f'start "" "{dest_exe_path}"\n')

            os.remove(temp_path)

            self.content.config(text="Installation complete! Starting the app now...")
            self.update()

            # Auto-start the app now
            subprocess.Popen([dest_exe_path], shell=True)

            self.page = 2
            self.show_page()

            self.next_button.config(state="normal")
            self.back_button.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"Installation failed:\n{e}")
            self.next_button.config(state="normal")
            self.back_button.config(state="normal")

if __name__ == "__main__":
    app = InstallerWizard()
    app.mainloop()

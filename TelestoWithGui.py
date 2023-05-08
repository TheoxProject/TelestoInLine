# Generic imports
from subprocess import Popen, DEVNULL
# GUI imports
import tkinter as tk
from ttkthemes import ThemedStyle
from tkinter import messagebox
import tkinter.ttk as ttk
# Personnal TelestoClass imports
from functions import *

class MainWindow(tk.Frame):
    def __init__(self, master, start_callback, follow_callback, stop_follow_callback, close_callback, take_picture_callback, update_display_callback):
        super().__init__(master)

        self.start_callback = start_callback
        self.follow_callback = follow_callback
        self.stop_follow_callback = stop_follow_callback
        self.close_callback = close_callback
        self.take_picture_callback = take_picture_callback
        self.update_display_callback = update_display_callback

        self.master = master
        self.master.title("My TELESTO Control Software")
        
        # Set the theme
        self.style = ThemedStyle(root)
        self.style.set_theme("smog")

        # Change the font size and color
        self.style.configure("TLabel", font=("Calibri", 12), background="#f2f2ed")
        self.style.configure("TButton", font=("Calibri", 12), background="#f2f2ed")
        self.style.configure("TEntry", font=("Calibri", 12), background="#f2f2ed")
        self.style.map('TButton', foreground=[('pressed', 'black'), ('active', 'red'), ('disabled', 'grey')])
        
        #update the button when window is resized
        nbr_col = 10
        nbr_line = 15
        for i in range(nbr_col):
            self.master.grid_columnconfigure(i, weight=1)
        for i in range(nbr_line):
            self.master.grid_rowconfigure(i, weight=1)

        # Create the widgets
        self.title_label = ttk.Label(self.master, text="Welcome to the TELESTO control software", font=("Arial", 20))
        self.title_label.grid(row=0, column=0, columnspan=7, pady=10, padx=40)

        self.session_name_label = ttk.Label(self.master, text="Session name :")
        self.session_name_label.grid(row=4, column=2, padx=5, pady=5)
        self.session_name = ttk.Entry(self.master, width=10)
        self.session_name.grid(row=4, column=3, padx=5, pady=5)
        self.start_button = ttk.Button(self.master, text="     Start", command=self.start, width=10)
        self.start_button.grid(row=4, column=3, columnspan=4)

        self.close_button = ttk.Button(self.master, text="    Close", command=self.close, width=10, state="disabled")
        self.close_button.grid(row=11, column=3, columnspan=3)

        self.Norad_label = ttk.Label(self.master, text="NORAD ID :")
        self.Norad_label.grid(row=5, column=1, padx=5, pady=5)
        self.Norad = ttk.Entry(self.master, width=10)
        self.Norad.grid(row=5, column=2, padx=5, pady=5)
        self.follow_button = ttk.Button(self.master, text="Follow satellite", command=self.follow, state="disabled")
        self.follow_button.grid(row=5, column=3)
        

        self.stop_follow_button = ttk.Button(self.master, text="Stop following", command=self.stop_follow, state="disabled")
        self.stop_follow_button.grid(row=5, column=5)

        self.take_picture_button = ttk.Button(self.master, text="Take a picture", command=self.take_picture, state="disabled")
        self.take_picture_button.grid(row=8, column=6, columnspan=3)

        self.exposure_time_label = ttk.Label(self.master, text="Exposure time (s) :")
        self.exposure_time_label.grid(row=7, column=2, columnspan=2)
        self.exposure_time = ttk.Entry(self.master, width=10)
        self.exposure_time.grid(row=7, column=4, columnspan=2)

        self.binning_X_label = ttk.Label(self.master, text="Binning X :")
        self.binning_X_label.grid(row=8, column=2, columnspan=2)
        self.binning_X = ttk.Entry(self.master, width=10)
        self.binning_X.grid(row=8, column=4, columnspan=2)

        self.binning_Y_label = ttk.Label(self.master, text="Binning Y :")
        self.binning_Y_label.grid(row=9, column=2, columnspan=2)
        self.binning_Y = ttk.Entry(self.master, width=10)
        self.binning_Y.grid(row=9, column=4, columnspan=2)

        self.interval_pict_label = ttk.Label(self.master, text="(Only for multiple picture)    Interval (s) :                      ")
        self.interval_pict_label.grid(row=10, column=1, columnspan=3)
        self.interval_pict = ttk.Entry(self.master, width=10)
        self.interval_pict.grid(row=10, column=4, columnspan=2)

        # Add an inforative label that will be update by the update_display method
        self.info_label = ttk.Label(self.master, text="Waiting for the software to start", font=("Arial", 20))
        self.info_label.grid(row=13, column=1, columnspan=7, pady=10, padx=40)
        # Change slightly the font size and color for the info label
        self.info_label.configure(background="white")


        # call update_display method every 10 milliseconds
        self.master.after(100, self.update_display)


    def start(self):

        # Change button states
        self.close_button.configure(state="normal")
        self.follow_button.configure(state="normal")
        self.start_button.configure(state="disabled")
        self.take_picture_button.configure(state="normal")
        session_name = self.session_name.get()
        try:
            # Run the callback
            self.start_callback(session_name)
        except:
            messagebox.showerror("Error", "Cannot start the software")
            # Change button states
            self.close_button.configure(state="disabled")
            self.follow_button.configure(state="disabled")
            self.start_button.configure(state="normal")
        
    def close(self):
        try:
            # Run the callback
            self.close_callback()
            self.master.quit()
        except:
            messagebox.showerror("Error", "Cannot close the software")

    def follow(self):
        # Change button states
        self.follow_button.configure(state="disabled")
        self.close_button.configure(state="disabled")
        self.stop_follow_button.configure(state="normal")
        # Get the NORAD ID
        norad = self.Norad.get()
        # Run the callback
        try:
            success, error_message = self.follow_callback(norad)
            if not success:
                messagebox.showerror("Error", error_message)
                self.follow_button.configure(state="normal")
                self.close_button.configure(state="normal")
                self.stop_follow_button.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot follow the satellite : {e}")
            # Change button states
            self.follow_button.configure(state="normal")
            self.close_button.configure(state="normal")
            self.stop_follow_button.configure(state="disabled")

    def stop_follow(self):
        # Change button states
        self.follow_button.configure(state="normal")
        self.close_button.configure(state="normal")
        self.stop_follow_button.configure(state="disabled")
        # Run the callback
        try:
            self.stop_follow_callback()
        except:
            messagebox.showerror("Error", "Cannot stop following the satellite")
            # Change button states
            self.follow_button.configure(state="disabled")
            self.close_button.configure(state="normal")
            self.stop_follow_button.configure(state="normal")

    def take_picture(self):
        
        # Detect if it's only one picture or multiple pictures
        if self.interval_pict.get() == "":
            interval_pict = 0
        else:
            interval_pict = self.interval_pict.get()

        # convert arguments to int
        args = [self.exposure_time.get(), self.binning_X.get(), self.binning_Y.get(), interval_pict]
        try:
            args = [int(i) for i in args]
        except ValueError:
            messagebox.showerror("Error", "Exposure time and binning must be integers")
        exposure_time, binning_X, binning_Y, interval_pict = args
        
        # Run the callback
        try:
            success, error_message = self.take_picture_callback(exposure_time, binning_X, binning_Y, interval_pict)
            if not success:
                messagebox.showerror("Error", error_message)
                return
        except Exception as e:
            messagebox.showerror("Error", f"Cannot take a picture : {e}")

  
    def update_display(self):
        # get current state of Telesto and update info_label
        info = self.update_display_callback()
        self.info_label.configure(text=info)
        
        # call update_display method again in 100 milliseconds
        self.master.after(100, self.update_display)
        


if __name__ == '__main__':
    # Create the root window
    root = tk.Tk()
    root.geometry("700x350")
    root.maxsize(1000, 500)
    root.configure(background="#f2f2ed")


    # Create the TelestoParams object
    Telesto = TelestoClass()

    # Create the main window
    TelestoInLine = MainWindow(root, Telesto.start, Telesto.follow_satellites, Telesto.stop_following, Telesto.exit, Telesto.take_picture, Telesto.update_display)
    root.mainloop()




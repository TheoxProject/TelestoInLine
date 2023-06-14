# Generic imports
from subprocess import Popen, DEVNULL
# GUI imports
import tkinter as tk
from ttkthemes import ThemedStyle
from tkinter import messagebox
import tkinter.ttk as ttk
import winsound
# Personnal TelestoClass imports
from functions import *

class MainWindow(tk.Frame):
    def __init__(self, master, start_callback, follow_callback, stop_follow_callback, close_callback, take_picture_callback, stop_taking_picture_callback, move_foc_callback, update_display_callback):
        super().__init__(master)

        self.start_callback = start_callback
        self.follow_callback = follow_callback
        self.stop_follow_callback = stop_follow_callback
        self.close_callback = close_callback
        self.take_picture_callback = take_picture_callback
        self.stop_taking_picture_callback = stop_taking_picture_callback
        self.update_display_callback = update_display_callback
        self.move_foc_callback = move_foc_callback

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
        nbr_line = 25
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
        self.close_button.grid(row=nbr_line-1, column=3, columnspan=3)

        self.Norad_label = ttk.Label(self.master, text="NORAD ID :")
        self.Norad_label.grid(row=5, column=2, padx=5, pady=5)
        self.Norad = ttk.Entry(self.master, width=10)
        self.Norad.grid(row=5, column=3, padx=5, pady=5)
        self.follow_button = ttk.Button(self.master, text="Follow satellite", command=self.follow, state="disabled")
        self.follow_button.grid(row=5, column=4)
        

        # add a space between blocs
        self.space_label = ttk.Label(self.master, text=" ")
        self.space_label.grid(row=6, column=1, padx=5, pady=5)



        self.take_picture_button = ttk.Button(self.master, text="Take picture", command=self.take_picture, state="disabled")
        self.take_picture_button.grid(row=8, column=6, columnspan=3)
        
        # Entry for the duration of the continuous pictures
        self.duration_picture_label = ttk.Label(self.master, text="Duration (s) :")
        self.duration_picture_label.grid(row=9, column=2, columnspan=2)
        self.duration_picture = ttk.Entry(self.master, width=10)
        self.duration_picture.grid(row=9, column=4, columnspan=2)


        self.exposure_time_label = ttk.Label(self.master, text="Exposure time (s) :")
        self.exposure_time_label.grid(row=7, column=2, columnspan=2)
        self.exposure_time = ttk.Entry(self.master, width=10)
        self.exposure_time.grid(row=7, column=4, columnspan=2)

        self.binning_X_label = ttk.Label(self.master, text="Binning (1/2/3) :")
        self.binning_X_label.grid(row=8, column=2, columnspan=2)
        self.binning_X = ttk.Entry(self.master, width=10)
        self.binning_X.grid(row=8, column=4, columnspan=2)

        self.interval_pict_label = ttk.Label(self.master, text="(Only for multiple picture)    Interval (s) :                      ")
        self.interval_pict_label.grid(row=10, column=1, columnspan=3)
        self.interval_pict = ttk.Entry(self.master, width=10)
        self.interval_pict.grid(row=10, column=4, columnspan=2)

        self.filter_label = ttk.Label(self.master, text="Filter :")
        self.filter_label.grid(row=11, column=2, columnspan=3, padx=5, pady=5)
        self.filter = ttk.Combobox(self.master, width=10, state="readonly")
        self.filter['values'] = ('Clear', 'Red', 'Green', 'Blue')  
        self.filter.current(0)
        self.filter.grid(row=11, column=4, columnspan=2, padx=5, pady=5)

        self.frame_label = ttk.Label(self.master, text="Frame :")
        self.frame_label.grid(row=12, column=2, columnspan=3, padx=5, pady=5)
        self.frame = ttk.Combobox(self.master, width=10, state="readonly")
        self.frame['values'] = ('Light', 'Bias', 'Dark', 'Flat Field')  
        self.frame.current(0)
        self.frame.grid(row=12, column=4, columnspan=2, padx=5, pady=5)

        # Change the focus : one button plus, one button minus, one entry for the value
        self.focus_label = ttk.Label(self.master, text="Focus step:")
        self.focus_label.grid(row=13, column=2, columnspan=3)
        self.focus = ttk.Entry(self.master, width=10)
        self.focus.grid(row=13, column=5)
        self.focus_plus_button = ttk.Button(self.master, text="Out", state="disabled")
        self.focus_plus_button.grid(row=13, column=6)
        self.focus_minus_button = ttk.Button(self.master, text="In", padding=(10, -15), width=2, state="disabled")
        self.focus_minus_button.grid(row=13, column=4)



        # Add an inforative label that will be update by the update_display method
        self.info_label = ttk.Label(self.master, text="Waiting for the software to start", font=("Arial", 10))
        self.info_label.grid(row=nbr_line-2, column=1, columnspan=7, pady=10, padx=40)
        # Change slightly the font size and color for the info label
        self.info_label.configure(background="white")


        # call update_display method every 10 milliseconds
        self.master.after(100, self.update_display)


    def start(self):

        session_name = self.session_name.get()
        try:
            # Run the callback
            self.start_callback(session_name)
        except:
            messagebox.showerror("Error", "Cannot start the software")
            return
        # Change button states
        self.close_button.configure(state="normal")
        self.follow_button.configure(state="normal")
        self.start_button.configure(state="disabled")
        self.focus_plus_button.configure(state="normal")
        self.focus_minus_button.configure(state="normal")
     
    def close(self):
        try:
            # Run the callback
            self.close_callback()
            self.master.quit()
        except:
            messagebox.showerror("Error", "Cannot close the software")

    def follow(self):
        # detect the button label
        if self.follow_button.cget("text") == "Follow satellite":

            # Get the NORAD ID
            norad = self.Norad.get()
            # Run the callback
            try:
                success, error_message = self.follow_callback(norad)
                if not success:
                    messagebox.showerror("Error", error_message)
                else:
                    # Change button states
                    self.close_button.configure(state="disabled")
                    self.take_picture_button.configure(state="normal")
                    # Change the button label
                    self.follow_button.configure(text="Stop following")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot follow the satellite : {e}")
        else:
            try:
                self.stop_follow_callback()
                # Change button states
                self.follow_button.configure(state="normal")
                self.close_button.configure(state="normal")
                self.take_picture_button.configure(state="disabled")
                # Change the button label
                self.follow_button.configure(text="Follow satellite")

            except:
                messagebox.showerror("Error", "Cannot stop following the satellite")

    def take_picture(self):
        # detect the button label
        button_label = self.take_picture_button.cget("text")
        
        if button_label == "Take picture":
            # Detect if it's only one picture or multiple pictures
            interval_pict = self.interval_pict.get()
            if interval_pict == "":
                interval_pict = 0

            # Detect if there is a duration
            duration = self.duration_picture.get()
            if duration == "":
                duration = 0
                
            # convert arguments to int
            args = [self.exposure_time.get(), self.binning_X.get(), self.binning_X.get(), interval_pict, duration]
            try:
                args = [int(i) for i in args]
            except ValueError:
                messagebox.showerror("Error", "Exposure time and binning must be integers")
                return
            exposure_time, binning_X, binning_Y, interval_pict, duration = args
             
            # Run the callback
            try:
                success, error_message = self.take_picture_callback(exposure_time, binning_X, binning_Y, self.filter.get(), interval_pict, duration)
                if not success:
                    messagebox.showerror("Error", error_message)
                    return
            except Exception as e:
                messagebox.showerror("Error", f"Cannot take a picture : {e}")
                return
            
            #change button label
            self.take_picture_button.configure(text="Stop", state="normal")
            self.take_picture_button.configure(command=self.stop_taking_picture_callback)
        else:
            # Stop taking picture
            success, error_message = self.stop_taking_picture_callback()
            if not success:
                messagebox.showerror("Error", error_message)
                return
            #change button label
            self.take_picture_button.configure(text="Take picture", state="normal")
            self.take_picture_button.configure(command=self.take_picture_callback)

    def move_foc_out(self):
        # get the step
        step = self.focus.get()
        # Step must be an integer, positive
        if not step.isdigit():
            messagebox.showerror("Error", "Step must be a positive integer")
            return
        step = int(step)
        if step <= 0:
            messagebox.showerror("Error", "Step must be a positive integer")
            return
        
        # Run the callback
        try:
            self.move_foc_callback(step)
        except:
            messagebox.showerror("Error", "Cannot move the focus out")

    def move_foc_in(self):
        # get the step
        step = self.focus.get()
        # Step must be an integer, positive
        if not step.isdigit():
            messagebox.showerror("Error", "Step must be a positive integer")
            return
        step = int(step)
        if step <= 0:
            messagebox.showerror("Error", "Step must be a positive integer")
            return
        
        # Run the callback
        try:
            self.move_foc_callback(-step)
        except:
            messagebox.showerror("Error", "Cannot move the focus in")

    def update_display(self):
        # get current state of Telesto and update info_label
        info, tracking, tracking_msg, taking_picture  = self.update_display_callback()
        self.info_label.configure(text=info)
        
        # change button states
        if not tracking:
            self.follow_button.configure(state="normal")
            self.follow_button.configure(text="Follow satellite")
            self.close_button.configure(state="normal")
            self.take_picture_button.configure(state="disabled")
            if tracking_msg != "":
                # make a noise
                winsound.Beep(1000, 1000)
                messagebox.showerror("Error : ", tracking_msg)

        if not taking_picture:
            self.take_picture_button.configure(text="Take picture", state="normal")
            self.take_picture_button.configure(command=self.take_picture)


        # call update_display method again in 100 milliseconds
        self.master.after(100, self.update_display)
    


if __name__ == '__main__':
    # Create the root window
    root = tk.Tk()
    root.geometry("700x500")
    root.minsize(700, 500)
    root.maxsize(1000, 500)
    root.configure(background="#f2f2ed")


    # Create the TelestoParams object
    Telesto = TelestoClass()

    # Create the main window
    TelestoInLine = MainWindow(root, Telesto.start, Telesto.follow_satellites, Telesto.stop_following, Telesto.exit, Telesto.take_picture, Telesto.stop_taking_picture, Telesto.change_focus, Telesto.update_display)
    root.mainloop()




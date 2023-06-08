'''
Definition of the functions used in the TelestoInLine.py script

'''
### Import libraries
# Generic imports
import time
import threading
from subprocess import Popen, DEVNULL
from datetime import timedelta

# Skyfield is a Python library for computing positions of celestial bodies in the sky.
import skyfield
from skyfield.api import load
from skyfield.api import N, E

# Library to control the telescope, send command in javascript.
from PySkyX_ks import *



### Telesto control ###
class TelestoClass: 
    def __init__(self): 
    
        #Threading
        self.tracking_error_thread = None
        self.error_thread_stop_event = threading.Event()
        self.picture_thread = None
        self.picture_thread_stop_event = threading.Event()
        # String containing program status
        self.status = "Please start the program"

    

    ##### Public methods call by the user #####
    def take_picture(self, exposure_time, binning_X, binning_Y, interval=0):
        '''
        \nTake a picture \n
        input: exposure time, binning X, binning Y \n
        '''
        if exposure_time <= 0:
            print("\nInvalid argument: exposure time must be greater than 0\n")
            return False,"Invalid argument: exposure time must be greater than 0"

        if binning_X <= 0 or binning_Y <= 0:
            print("\nInvalid argument: binning must be greater than 0\n")
            return False,"Invalid argument: binning must be greater than 0"
        
        if interval <= 0:
            # Update status
            self.status = "Taking picture..."
            # Take a single picture
            print("Taking picture...")
            print("Picture taken")
            # Update status
            
            return True,""

        else:
            # Start a thread to take pictures
            # Update status
            
            self.picture_thread_stop_event = threading.Event()  #Reset the flag
            self.picture_thread = threading.Thread(target=self.__take_picture, args=(interval,))
            self.picture_thread.start()

            return True,""

    def stop_taking_picture(self):
        '''
        \nStop taking pictures\n
        '''
        self.picture_thread_stop_event.set()
        # Update status
        self.status = "Stopped taking pictures"


    ### Private methods ###
    def __control_error(self):
        '''
        Compute the error of the telescope each 30 second, if the error is too big, 
        the telescope will raise a flag.

        Input : [params]
        Ouput : None
        '''
        threshold = 0.0001 # Threshold of the error

        print('Start controlling error')
        while not self.error_thread_stop_event.is_set():
            # Waiting loop, need to close the thread if the stop_event is set
            wait_time = 30 # [s]
            for i in range(wait_time):
                if self.error_thread_stop_event.is_set():
                    return
                time.sleep(1)

            alt, _ = self.__compute_alt_az(30)
            if alt.degrees <= 10:
                print("Target will be too low in sky. Stop following\n")
                self.is_following = False
                setTrackingRate(switch=False) # stop tracking

                return
            
            # Compute the mean square error
            dec, ra, _, _, _, _ = self.__compute_celestial_parameters()
            try:
                mnt_ra, mnt_dec, _, _ = getPosition()
            except:
                print('Error while getting the position')
                continue
            error_ra = abs(ra._hours - mnt_ra)/24
            error_dec = abs(dec._degrees - mnt_dec)/360
            error = (error_ra**2 + error_dec**2)**0.5
            print('Error : ', error)
            if error > threshold:
                print('Error too big, stop following')
                self.is_following = False
                setTrackingRate(switch=False) # stop tracking
                return
        return
    
    def __take_picture(self, interval):
        '''
        Take a picture of the satellite each X second

        Input : [params]
        Ouput : None
        '''
        print('Start taking picture')
        print("Picture taken")
        time.time
        start = time.perf_counter()
        while not self.picture_thread_stop_event.is_set():
            # initialize the timer
            start = time.perf_counter()
            # Waiting loop, need to close the thread if the stop_event is set
            while time.perf_counter() - start < interval:
                if self.picture_thread_stop_event.is_set():
                    return
                time.sleep(1)
            
            # Take the picture
            if True:
                print("Picture taken after ", time.perf_counter() - start, "s")
            else :
                break
        return


        return



# Main
if __name__ == "__main__":
    # Create an object
    telesto = TelestoClass()

    # Take a picture
    print("Try to take a picture")
    telesto.take_picture(1,1,1,0)
    time.sleep(5)
    telesto.take_picture(1,1,1,3)
    time.sleep(5)
    print("Main thread ")
    time.sleep(5)
    print("Stop taking picture")
    telesto.stop_taking_picture()
    time.sleep(50)
    exit()




    

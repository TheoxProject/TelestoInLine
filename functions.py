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
        self.satellites = {}
        self.location = [46.30916667, 6.13472222]  # raw location of the observatory (WGS84), simpler than automatically get it
        self.observatory = skyfield.api.wgs84.latlon(self.location[0]*N, self.location[1]*E, elevation_m=443)  # vector used to compute topocentric coordinates
        self.confirm = False
        self.target = None
        self.is_following = False
        self.has_started = False
        #Threading
        self.tracking_error_thread = None
        self.error_thread_stop_event = threading.Event()
        self.picture_thread = None
        self.picture_thread_stop_event = threading.Event()

        # String containing program status
        self.status = "Please start the program"
        
        self.session_name = ''
        # if crash these are the original settings for observer and binning
        self.original_session_name = "chazelas"
        self.original_binning_X = "1"
        self.original_binning_Y = "1"
    

    ##### Public methods call by the user #####
    def start(self, session_name):
        '''
        \nInitialize all Telesto hardware and software for communication
        \nstart(session_name)\n
        '''
        # Update status
        self.status = "Starting..."

        ## Preliminary checks
        if self.has_started:
            print("Already started")
            return False

        print("Running Skyfield " + skyfield.__version__ + "\n")
        if skyfield.VERSION < (1, 45):
            print("This version is to old. Please upgrade Skyfield\n")
            print("run command : pip install skyfield\n")
            return False
        else:
            # initialize time
            self.__init_time()

            # initialize file
            self.__init_file()

            # Set session informations
            self.session_name = session_name
            print("Session name set to "+self.session_name)
            init_file = open('C:\\Users\\admin\\Documents\\Software Bisque\\TheSkyX Professional Edition\\Imaging System Profiles\\ImagingSystem.ini', 'rt')
            content = init_file.read()
            content = content.replace("m_csobserver="+self.original_session_name,"m_csobserver="+self.session_name)
            init_file.close()
            init_file = open('C:\\Users\\admin\\Documents\\Software Bisque\\TheSkyX Professional Edition\\Imaging System Profiles\\ImagingSystem.ini', 'wt')
            init_file.write(content)
            init_file.close()
            

            # start necessary software
            self.__launch_software()

            # wait for software to be correctly launch
            time.sleep(5)

            # connect camera
            TSXSend("ccdsoftCamera.Connect()")

            # check correct launch
            if preRun() == "Fail":
                return True

            self.has_started = True
            
            # Update status
            self.status = "Ready"

            return False

    def exit(self):
        '''
        \nexit the application.\n
        \nexit()\n
        '''
        # Update status
        self.status = "Closing..."

        if self.is_following:
            print("You are following a target. please stop following before exit.")
            return False
        # set back original settings
        TSXSend("cddsoftCamera.BinX = "+self.original_binning_X)
        TSXSend("cddsoftCamera.BinY = " + self.original_binning_Y)

        init_file = open(
            'C:\\Users\\admin\\Documents\\Software Bisque\\TheSkyX Professional Edition\\Imaging System Profiles\\ImagingSystem.ini',
            'rt')

        content = init_file.read()
        content = content.replace(self.session_name, self.original_session_name)
        init_file.close()
        init_file = open(
            'C:\\Users\\admin\\Documents\\Software Bisque\\TheSkyX Professional Edition\\Imaging System Profiles\\ImagingSystem.ini',
            'wt')
        init_file.write(content)
        init_file.close()

        print("Disconnect Cam...\n")
        camDisconnect("Imager")

        print("closing all app...\n")
        self.Maestro.terminate()
        self.SkyX.terminate()

        print("App closed")

        return True

    def follow_satellites(self, arg):

        '''\nMove the telescope to debris and then follow it. 
        target_debris [catalog number : NORAD ID]\n'''
        # Update status
        self.status = "Following..."

        # Preliminary checks
        if not self.has_started:
            print("\nLaunch starting procedure first\n")
            return False,"Launch starting procedure first"
        if self.is_following:
            print("You are following a satellite. Please stop following before moving to another target")
            return False,"You are following a satellite. Please stop following before moving to another target"

        args = arg.split()
        if len(args) != 1:
            print("\nInvalid argument number: target_satellites [catalog number]\n")
            return False,"Invalid argument number: target_satellites [Norad ID]"
        
        if int(args[0]) not in self.satellites:
            print("\nInvalid target: please use an existing target\n")
            return False,"Invalid target: please use an existing target"

        self.target = self.satellites[int(args[0])]
        # Update status
        self.status = "Following NORAD ID "+self.target.name+"..."

        if not self.__follow_sat_using_rate():
            return False,"Target will be too low in the sky. Please choose another target"

        # Start error thread
        self.error_thread_stop_event = threading.Event()  #Reset the flag
        self.tracking_error_thread = threading.Thread(target=self.__control_error_thread)
        self.tracking_error_thread.start()
        return True,""

    def stop_following(self):
        '''
        \nStop following the target\n
        '''
        # Update status
        self.status = "Stopping..."

        if not self.is_following:
            print("You are not following a target")
            return False,"You are not following a target"

        self.is_following = False
        #Stop error thread if running
        if self.tracking_error_thread is not None:
            self.error_thread_stop_event.set()
        # Stop picture thread if running
        if self.picture_thread is not None:
            self.picture_thread_stop_event.set()
        #Stop Telescope movement
        setTrackingRate(switch=False) # stop tracking

        # Update status
        self.status = "Ready"

        return True, ""

    def take_picture(self, exposure_time, binning_X, binning_Y, filter, interval=0, duration=0):
        '''
        \nTake a picture \n
        input: exposure time, binning X, binning Y, filter, interval between picture, duration of the thread \n
        '''
        # Preliminary checks
        if not self.has_started:
            print("\nLaunch starting procedure first\n")
            return False,"Launch starting procedure first"

        if exposure_time <= 0:
            print("\nInvalid argument: exposure time must be greater than 0\n")
            return False,"Invalid argument: exposure time must be greater than 0"

        if binning_X <= 0 or binning_Y <= 0:
            print("\nInvalid argument: binning must be greater than 0\n")
            return False,"Invalid argument: binning must be greater than 0"
        
        ## Settting parameters
        TSXSend("ccdsoftCamera.ExposureTime = " + str(exposure_time))
        TSXSend("ccdsoftCamera.BinX = "+str(binning_X))
        TSXSend("ccdsoftCamera.BinY = " + str(binning_Y))

        # Connect to the filter wheel
        if not TSXSend("ccdsoftCamera::filterWheelIsConnected()"):
            TSXSend("ccdsoftCamera::filterWheelConnect()")
        # Set filter :
        filter_num = 0
        if filter == "Filter1":
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 0")
            filter_num = 0
        elif filter == "Filter2":
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 1")
            filter_num = 1
        elif filter == "Filter3":
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 2")
            filter_num = 2
        elif filter == "Filter4":
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 3")
            filter_num = 3
        elif filter == "Filter5":
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 4")
            filter_num = 4
        elif filter == "Filter6":
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 5")
            filter_num = 5
        elif filter == "Filter7":
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 6")
            filter_num = 6
        elif filter == "Filter8":
            TSXSend("ccdsoftCamera.FilterIndexZeroBased = 7")
            filter_num = 7
        else: # Connect to the first filter
            print("Invalid filter name. Filter 1 selected by default")
            return False,"Invalid filter name. Filter 1 selected by default"

        if interval <= 0: # Only one observation
            # Update status
            self.status = "Taking picture..."
            time.sleep(1) # Wait for the status to be updated
            # Take picture
            success = self.__take_image()
            if not success:
                return False,"Unable to take picture"
            
            print("Picture taken")
            # Update status
            self.status = "Following NORAD ID "+self.target.name+"..."
            return True,""

        else:
            # Start a thread to take pictures
            # Update status
            self.status = "Taking pictures of NORAD ID "+self.target.name+"..."
            time.sleep(1) # Wait for the status to be updated
            print("Imager: " + str(exposure_time) + "s exposure through " \
                      + TSXSend("ccdsoftCamera.szFilterName(" + filter_num + ")") + " filter.")
            self.picture_thread_stop_event = threading.Event()  #Reset the flag
            self.picture_thread = threading.Thread(target=self.__take_picture_thread(interval,duration,))
            self.picture_thread.start()

            return True,""

    def stop_taking_picture(self):
        '''
        \nStop taking pictures\n
        '''
        # Update status
        self.status = "Following NORAD ID "+self.target.name+"..."

        if self.picture_thread is None:
            print("You are not taking pictures")
            return False,"You are not taking pictures"

        self.picture_thread_stop_event.set()
        # Update status
        self.status = "Following NORAD ID "+self.target.name+"..."
        return True,""

    def change_focus(self, step):
        '''
        \nChange the focus\n
        '''
        # Connect the focuser
        TSXSend("ccdsoftCamera::focConnect()")
        # Change focus
        if step > 0:
            TSXSend("ccdsoftCamera::focMoveOut("+str(step)+")")
        else:
            TSXSend("ccdsoftCamera::focMoveIn("+str(abs(step))+")")
        # Disconnect the focuser
        TSXSend("ccdsoftCamera::focDisconnect()")
        return True,""

    def update_display(self):
        return self.status



    ### Private methods ###
    #--------------## Start methods ##-------------
    def __launch_software(self):
        '''
        Launch the software needed to control the telescope
        '''
        current=''
        try:
            current = 'OSBus'
            self.OSBus = Popen('C:\\Program Files (x86)\\Officina Stellare Srl\\OSBusSetup\\OSBusController.exe', stdout=DEVNULL)
            print("OSBus launched")
            current = 'Maestro'
            self.Maestro = Popen('C:\\Program Files (x86)\\Astrometric\\Maestro\\Maestro.exe')
            print("Maestro launched")
            current = 'SkyX'
            self.SkyX = Popen('C:\\Program Files (x86)\\Software Bisque\\TheSkyX Professional Edition\\TheSkyX.exe')
            print("SkyX launched")
        except:
            print("Error while launching"+current)

    # Initialize the time object
    def __init_time(self):
        self.ts = load.timescale()
        self.time = self.ts.now()

    # Load all satellites and debris from TLE files
    def __init_file(self):
        # Read URLs from text files
        debris_urls = self.__read_url('debris_url.txt')
        satellites_urls = self.__read_url('satellites_url.txt')
        # Read personal TLE file
        personal_paths = 'personal_tle.txt'

        # load each files then append it in a general dictionary
        print("Load debris files\n")
        self.__load_file("deb", debris_urls)

        print("Load satellites files\n")
        self.__load_file("sat", satellites_urls)

        print("Load personal tle\n")
        temp = load.tle_file(personal_paths, reload=True)
        self.satellites.update({sat.model.satnum: sat for sat in temp})

        print('List of satellites :', self.satellites)


        print("Loaded", len(self.satellites), "debris and satellites")

    def __read_url(self, filename):
        '''
        Function that reads URL inside a text files in the same folder, return a list of urls.

        Input : [filename]
        Ouput : [urls]
        '''
        url_file = open(os.path.dirname(os.path.abspath(__file__))+'\\'+filename, 'r')

        # read debris url
        url_lines = url_file.readlines()
        urls = []
        for url in url_lines:
            urls.append(url)

        return urls

    def __load_file(self, url_type, urls):
        '''
        Function that loads TLE files from a list of urls, and append it in a general dictionary.

        Input : [Params, url_type, urls]
        Ouput : None
        '''
        for url in urls:
            temp = load.tle_file(url, reload=True)
            if url_type == "deb":
                self.satellites.update({debris.model.satnum: debris for debris in temp})
            elif url_type == "sat":
                self.satellites.update({sat.model.satnum: sat for sat in temp})
            

    def __compute_alt_az(self,offset=0):  
        '''
        Compute the altitude and azimuth of the satellite, from the observatory position :

        Input : [params, offset(in seconds)]
        Ouput : [Altitude, Azimuth]
        '''
        difference = self.target - self.observatory

        # add x seconds to the current time
        prevision_time = self.ts.now().utc_datetime() + timedelta(seconds=offset) 
        # Compute the position for the given time, coordinates (x,y,z)
        topocentric = difference.at(self.ts.utc(prevision_time)) 

        # altitude, azimuth, distance; 'standard' allow atmospheric correction
        alt, az, _ = topocentric.altaz('standard') 

        return alt, az

    def __compute_celestial_parameters(self,offset=0,frame='equatorial'):
        '''
        Compute the rate and coordinate of the satellite : 

        Input : [params, offset, frame]
        Ouput : [Declination, Right Ascension, Radial distance, ra_rate, dec_rate, Radial velocity]
        '''
        difference = self.target - self.observatory
        if offset:
            prevision_time = self.ts.now().utc_datetime() + timedelta(seconds=offset)

            topocentric = difference.at(self.ts.utc(prevision_time)) # position of the satellite at the next minute, coordinates (x,y,z)
        else:
            topocentric = difference.at(self.ts.now()) # position of the satellite at the current time, coordinates (x,y,z)

        # Switch depend on the frame
        if frame == 'equatorial': 
            Dec, Ra, rad_dist, ra_rate, dec_rate, rad_vel = topocentric.frame_latlon_and_rates(skyfield.framelib.true_equator_and_equinox_of_date)     
        elif frame == 'xxxx' : # Not tested, need to find another frame
            Dec, Ra, rad_dist, ra_rate, dec_rate, _ = topocentric.frame_latlon_and_rates(skyfield.framelib.xxxx)
            
        return Dec, Ra, rad_dist, ra_rate, dec_rate, rad_vel 

    def __follow_sat_using_rate(self):
        '''
        Follow the satellite using the rate computed from the current position 
        of the satellite

        Input : [params]
        Ouput : None 
        '''
        print('\n')
        start = time.perf_counter()
        deltaT_ahead = 30 # How many seconds ahead the telescope will be. 
        alt, az = self.__compute_alt_az(deltaT_ahead)
        if alt.degrees <= 10:
            print("Target will be too low in sky. Stop following\n")
            return False
        print('Coordinates : Altitude', alt._degrees, '- Azimuth', az._degrees)

        #Calculating the rate :
        print('Calculating celestial rate')
        dec, ra, _, ra_rate, dec_rate, _ = self.__compute_celestial_parameters(deltaT_ahead)
        #display the coordinates and rates
        print('Celestial coordinates : RA ', ra._hours, '- Dec', dec._degrees)
        print('Celestial rate : RA ', ra_rate.arcseconds.per_second, '- Dec', dec_rate.arcseconds.per_second,'\n')
        print('time elapsed = ', time.perf_counter() - start,'\n')

        print('Aligning the telescope')
        #slew
        slewToCoords((str(ra._hours), str(dec._degrees)), self.target.name)
        print('Telesto is in the target path\n')
        print('time elapsed = ', time.perf_counter() - start,'\n')

        print('##################################')
        disp = 0
        time_send_cmd = 3 # Time needed to send the command to the telescope, [s]
        while time.perf_counter() - start < deltaT_ahead-time_send_cmd:
            time.sleep(0.01)
            if disp%200 == 0:
                print('Waiting the target to be in the field of view',time.perf_counter() - start,'s')
            disp += 1
        print('##################################\n')
        print('time elapsed = ', time.perf_counter() - start,'\n')

        print('Start following')
        self.is_following=True
        #Set the rate 
        setTrackingRate((str(ra_rate.arcseconds.per_second),str(dec_rate.arcseconds.per_second)))
        return True

    def __control_error_thread(self):
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
    
    def __take_picture_thread(self, interval, duration):
        '''
        Take a picture of the satellite each X second

        Input : [params]
        Ouput : None
        '''
        # set starting time
        start_pict = time.perf_counter()
        if duration==0: # if duration is 0, the thread will run until the stop_event is set
            duration_flag = False
        else:
            duration_flag = True


        print('Start taking picture')
        success = self.__take_image()
        if not success:
            print('Error while taking the picture')
            return
        print("First picture taken")   

        # Thread loop, need to close the thread if the stop_event is set
        while not self.picture_thread_stop_event.is_set():
            # initialize the timer
            start = time.perf_counter()
            # Waiting loop, need to close the thread if the stop_event is set
            while time.perf_counter() - start < interval :
                if self.picture_thread_stop_event.is_set():
                    return
                if duration_flag and time.perf_counter() - start_pict > duration :
                    print('Max duration reached, stop taking picture')
                    self.picture_thread_stop_event.set()
                    return
                time.sleep(1)
            
            # Take the picture
            success = self.__take_image()
            if not success:
                print('Error while taking the picture')
                return
            print("Picture taken after ", time.perf_counter() - start, "s")
            if duration_flag :
                print("Time left : ", duration - time.perf_counter() - start_pict, "s")
        
        return

    def __take_image():
        '''
        Take a picture with the camera

        Input : [params]
        Ouput : None
        '''
        camMesg = TSXSend("ccdsoftCamera.TakeImage()")

        if camMesg == "0":

            TSXSend("ccdsoftCameraImage.AttachToActiveImager()")
            cameraImagePath = TSXSend("ccdsoftCameraImage.Path").split("/")[-1]

            if cameraImagePath == "":
                cameraImagePath = "Image not saved"

            print("Image completed: " + cameraImagePath)
            return True

        else:
            print("Error: " + camMesg)
            return False

#### TO DO ####
'''
## CAMERA ##
- Use CenterBrightestObject to center the satellite (see if applicable)
- Use the focusers : AtFocus2 # Will not be applicable, need to be set manually between each images

## EXTRA ##
- Find the minimum altitude satellite observable (tree obstruction)
- Find maximum satellite speed observable (telescope speed or dome speed)
- Maibe add a button to compensate the error of the telescope (if the error is too big, choice to compensate or stop following)


## TO DO ##
- Add a txt file that contain all parameters. (minimum altitude, etc.)
- Add a parameters to choose the time between first and last picture : take picture continuously between the two time
- Use the session name to save the pictures in a folder with the name of the session
- Use only one entry for binning 


'''

import threading
import sys
import time
from cmd import Cmd
from datetime import datetime
import skyfield
from skyfield.api import load
from skyfield.api import N, E
from subprocess import Popen, DEVNULL
from PySkyX_ks import *


class Prompt(Cmd):
    prompt = 'Telesto>'
    intro = "Welcome to the Telesto command line interface \n Type ? to list commands"

    has_started = False

    # dictionary that contain all debris and all satellites
    satellites = {}
    location = [46.30916667, 6.13472222]  # raw location of the observatory (WGS84), simpler than automatically get it
    observatory = skyfield.api.wgs84.latlon(location[0]*N, location[1]*E, elevation_m=443)  # vector used to compute topocentric coordinates
    confirm = False
    target = None
    is_following = False
    follow_thread = None

    session_name = ''
    # if crash these are the original settings for observer and binning
    original_session_name = "chazelas"
    original_binning_X = "1"
    original_binning_Y = "1"

    def do_exit(self, args):

        '''\nexit the application.\n
        \nexit()\n
        '''

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

    def do_EOF(self, args):
        return self.do_exit(self)

    def cmdloop(self, intro=None):
        print(self.intro)
        while True:
            try:
                super(Prompt, self).cmdloop(intro="")
                break
            except KeyboardInterrupt:
                self.do_exit(self)

    def do_start(self, update_TLE=True):

        '''\nInitialize all Telesto hardware and software for communication
        \nstart(update_TLE)
        \nupdate_TLE: if True update TLE files before starting\n
        '''

        if self.has_started:
            print("already started")
            return False

        print("Running Skyfield " + skyfield.__version__ + "\n")
        # check current version
        if skyfield.VERSION < (1, 45):
            print("This version is to old. Please upgrade Skyfield\n")
            print("run command : pip install skyfield\n")
            return False
        else:

            # initialize time
            self._init_time()
            
            if update_TLE :
                # initialize file
                self._init_file()
            else :
                self.satellites = load.tle_file('./gp.php') # load the file containing all satellites and debris

            # Enter a session name
            print("Enter a session name for your observation")
            self.session_name = input()
            init_file = open('C:\\Users\\admin\\Documents\\Software Bisque\\TheSkyX Professional Edition\\Imaging System Profiles\\ImagingSystem.ini', 'rt')
            content = init_file.read()
            content = content.replace("m_csobserver="+self.original_session_name,"m_csobserver="+self.session_name)
            init_file.close()
            init_file = open('C:\\Users\\admin\\Documents\\Software Bisque\\TheSkyX Professional Edition\\Imaging System Profiles\\ImagingSystem.ini', 'wt')
            init_file.write(content)
            init_file.close()

            # start necessary software
            self._launch_software()

            # wait for software to be correctly launch
            time.sleep(5)

            # connect camera
            TSXSend("ccdsoftCamera.Connect()")

            # check correct launch
            if preRun() == "Fail":
                return True

            self.has_started = True
            print("\nReady\n")
            return False

    def do_update_tle(self, args):
            
            '''\nUpdate TLE files
            \nupdate_tle()\n
            '''

            print("Update TLE files")
            self._init_file()
    
            return False
    
    def _init_file(self):
        # Read URLs from text files
        debris_urls, satellites_urls, personal_paths = self._read_url()

        # load each files then append it in a general dictionary
        print("Load debris files\n")
        self._load_file("deb", debris_urls)

        print("Load satellites files")
        self._load_file("sat", satellites_urls)

        print("Load personal tle")
        self._load_file("sat", personal_paths)

        print("Loaded", len(self.satellites), "debris and satellites")

    @staticmethod
    def _read_url():

        debris_url_file = open('debris_url.txt', 'r')
        satellites_url_file = open('satellites_url.txt', 'r')
        personal_tle_file = open('personal_tle.txt', 'r')

        # read debris url
        urls = debris_url_file.readlines()
        debris_url = []
        for url in urls:
            debris_url.append(url)

        # read satellites url
        urls = satellites_url_file.readlines()
        satellites_url = []
        for url in urls:
            satellites_url.append(url)

        # read personal tle file
        paths = personal_tle_file.readlines()
        personal_path = []
        for path in paths:
            personal_path.append(path)

        return debris_url, satellites_url, personal_path

    def _load_file(self, url_type, urls):

        for url in urls:
            temp = load.tle_file(url, reload=True)
            if url_type == "deb":
                self.satellites.update({debris.model.satnum: debris for debris in temp})
            elif url_type == "sat":
                self.satellites.update({sat.model.satnum: sat for sat in temp})

    def _init_time(self):
        self.ts = load.timescale()
        self.time = self.ts.now()
        print("You start observation at : " + str(self.time.astimezone(datetime.now().astimezone().tzinfo)))

    def _check_start(self):
        if not self.has_started:
            print("\nlaunch starting procedure first\n")
        return self.has_started

    def _launch_software(self):

        self.OSBus = Popen('C:\\Program Files (x86)\\Officina Stellare Srl\\OSBusSetup\\OSBusController.exe', stdout=DEVNULL)
        self.Maestro = Popen('C:\\Program Files (x86)\\Astrometric\\Maestro\\Maestro.exe')
        self.SkyX = Popen('C:\\Program Files (x86)\\Software Bisque\\TheSkyX Professional Edition\\TheSkyX.exe')

    def do_target_celestial_body(self, arg):

        '''\nMove the telescope to the body
        target_celestial_body [object name]\n'''

        if not self._check_start():
            return False

        if targExists(arg) == "No":
            print("Enter a valid target")
            return False

        if self.is_following:
            print("You are following a satellite. Please stop following before moving to another target")
            return False

        if arg == "Sun":
            print("Are you sure you want to target the Sun ? Make sure to have the correct equipment.\n")
            print("To confirm the command enter it again.")
            if not self.confirm:
                self.confirm = True
                return False

        self.confirm = False
        slew(arg)
        return False

    def do_target_satellites(self, arg):

        '''\nMove the telescope to debris
        target_debris [catalog number : NORAD ID]\n'''

        if not self._check_start():
            return False

        if self.is_following:
            print("You are following a satellite. Please stop following before moving to another target")
            return False

        args = arg.split()
        if len(args) != 1:
            print("\nInvalid argument number: target_satellites [catalog number]\n")
            return False
        
        if int(args[0]) not in self.satellites:
            print("\nInvalid target: please use an existing target\n")
            return False

        if not self._slew_coord(arg):
            print("whut")
            return False

        print('Performing rate test')
        self._perform_test()
        # set-uping thread to make the following asynchronous
        self.follow_thread = threading.Thread(target=self._follow_sat())
        print("Start following target")
        self.is_following=True
        self._follow_sat()
        self.follow_thread.start()
        return True

    def do_slew(self, arg):

        '''\nMove the telescope to the coordinates
        slew [ra] [dec]\n'''

        if not self._check_start():
            return False

        if self.is_following:
            print("You are following a satellite. Please stop following before moving to another target")
            return False

        args = arg.split()
        if len(args) != 2:
            print("\nInvalid argument number: slew [ra] [dec]\n")
            return False
        print('slew to', args[0], args[1])
        slewToCoords((str(args[0]), str(args[1])), "Target")
        

    def _slew_coord(self, arg):
        #-----Slew the telescope to the target
        self.target = self.satellites[int(arg)]
        print("You targeted "+str(self.target))
        coordinates_ra_dec, coordinates_alt_az = self._compute_relative_position(True)

        if coordinates_alt_az[0].degrees < 0:
            print("Target under horizons")
            return False
        print("Relative position :", coordinates_ra_dec[0],'Ra,', coordinates_ra_dec[1],'Dec')
        slewToCoordsAzAlt((str(coordinates_alt_az[1]._degrees), str(coordinates_alt_az[0]._degrees)), self.target.name)
        return True

    def _compute_relative_position(self, offset=0):   # using https://rhodesmill.org/skyfield/earth-satellites.html
        difference = self.target - self.observatory
        if offset:
            print('actual time', self.ts.now().utc_datetime())
            prevision = self.ts.now().utc_datetime().replace(minute=self.ts.now().utc.minute + 1)  # add x minute to the current time
            print('next minute', prevision)
            topocentric = difference.at(self.ts.utc(prevision)) # position of the satellite at the next minute, coordinates (x,y,z)
        else:
            topocentric = difference.at(self.ts.now()) # position of the satellite at the current time, coordinates (x,y,z)

        #apparent = topocentric.apparent()
        coordinates_ra_dec = topocentric.radec(epoch='date') 
        coordinates_alt_az = topocentric.altaz()  ## altaz('standard')

        return coordinates_ra_dec, coordinates_alt_az
    
 #################
    def do_perform_test(self, arg):
        '''\nPerform some test \n'''
        #Initial verification:
        if self.is_following:
            print("You are following a satellite. Please stop following before moving to another target")
            return False
        args = arg.split()
        if len(args) != 1:
            print("\nInvalid argument number: target_satellites [catalog number]\n")
            return False       
        if int(args[0]) not in self.satellites:
            print("\nInvalid target: please use an existing target\n")
            return False
        # The test is performed on the target
        self.target = self.satellites[int(arg)]
        print("You targeted "+str(self.target))

        coordinates_ra_dec, _ = self._compute_relative_position()
        print("Relative position :", coordinates_ra_dec[0], coordinates_ra_dec[1], 'using epoch date')
        slewToCoords((str(coordinates_ra_dec[0]._hours), str(coordinates_ra_dec[1]._degrees)), self.target.name)
        print("Slewing to target")
        TSXSend("sky6RASCOMTele.GetRaDec()")
        mntRa = round(float(TSXSend("sky6RASCOMTele.dRa")), 4)
        mntDec = round(float(TSXSend("sky6RASCOMTele.dDec")), 4)
        print("NOTE: Mount currently at: " + str(mntRa) + " Ra., " + str(mntDec) + " Dec.")
        self._follow_sat_using_rate1()
        time.sleep(60)
        TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")

    def _follow_sat_using_rate1(self):
        print('\n')
        start = time.perf_counter()
        coordinates_ra_dec, coordinates_alt_az = self._compute_relative_position(True)
        if coordinates_alt_az[0].degrees <= 10:
            print("Target will be too low in sky. Stop following\n")
            return False
        
        print('Celestial coordinates : RA ', coordinates_ra_dec[0].hours, '- Dec', coordinates_ra_dec[1].degrees)

        print('Aligning the telescope')
        #slew
        slewToCoords((str(coordinates_ra_dec[0]._hours), str(coordinates_ra_dec[1]._degrees)), self.target.name)
        print('Telesto is in the target path\n')
        
        #Calculating the rate :
        print('Calculating celestial rate')
        ra_rate, dec_rate = self._compute_celestial_rate(True)
        #display the rate 
        print('Celestial rate : RA ', ra_rate.arcseconds.per_second, '- Dec', dec_rate.arcseconds.per_second)

        

        print('time elapsed = ', time.perf_counter() - start,'\n')

        print('##################################')
        disp = 0
        while time.perf_counter() - start < 60:
            time.sleep(1)
            if disp%5 == 0:
                print('Waiting the target to be in the field of view',time.perf_counter() - start,'s')
            disp += 1
        print('##################################\n')
        print('time elapsed = ', time.perf_counter() - start,'\n')

        print('Start following')
        self.is_following=True
        #display the rate 
        print('Celestial rate : RA ', ra_rate.arcseconds.per_second, '- Dec', dec_rate.arcseconds.per_second,'\n')
        setTrackingRate((str(ra_rate.arcseconds.per_second),str(dec_rate.arcseconds.per_second)))

        coordinates_ra_dec, coordinates_alt_az = self._compute_relative_position()
        print('Celestial coordinates : RA ', coordinates_ra_dec[0].hours, '- Dec', coordinates_ra_dec[1].degrees)

    def _follow_sat_using_rate2(self):
        start = time.perf_counter()

        #Initialisation
        offset = 60 # s
        coordinates_ra_dec, coordinates_alt_az = self._compute_relative_position(True)
        if coordinates_alt_az[0].degrees <= 10:
            print("Target will be too low in sky. Stop following\n")
            return False
        print('Celestial coordinates : RA ', coordinates_ra_dec[0].hours, '- Dec', coordinates_ra_dec[1].degrees)
        print('Aligning the telescope')
        slewToCoords(coordinates_ra_dec[0].hours, coordinates_ra_dec[1].degrees)
        print('Telesto is in the target path\n')

        # wait for the target to be in the field of view
        print('##################################')
        disp = 0
        while time.perf_counter() - start < offset:
            time.sleep(1)
            if disp%5 == 0:
                print('Waiting the target to be in the field of view')
            disp += 1
        print('##################################\n')

        #Calculating the rate :
        print('Calculating celestial rate')
        coordinates_ra_dec, _ = self._compute_relative_position()
        coordinates_ra_dec_next, _ = self._compute_relative_position(True)
        ra_rate = (coordinates_ra_dec_next[0].arcseconds() - coordinates_ra_dec[0].arcseconds()) / offset
        dec_rate = (coordinates_ra_dec_next[1].arcseconds() - coordinates_ra_dec[1].arcseconds()) / offset
        #display the rate
        print('Celestial rate : dRA ', ra_rate.degrees, '- dDec', dec_rate.degrees)

        # Move the telescope with the rate
        print('Start following using rate')
        self.is_following=True
        setTrackingRate((str(ra_rate),str(dec_rate)))  # Should be in arcseconds/second

    def _compute_celestial_rate(self,offset=0):
        difference = self.target - self.observatory
        if offset:
            prevision = self.ts.now().utc_datetime().replace(minute=self.ts.now().utc.minute + 1)  # add 1 minute to the current time

            topocentric = difference.at(self.ts.utc(prevision)) # position of the satellite at the next minute, coordinates (x,y,z)
        else:
            topocentric = difference.at(self.ts.now()) # position of the satellite at the current time, coordinates (x,y,z)


        print(topocentric.frame_latlon_and_rates(skyfield.framelib.true_equator_and_equinox_of_date), sep='\n')
        Dec, Ra, _, ra_rate, dec_rate, _ = topocentric.frame_latlon_and_rates(skyfield.framelib.true_equator_and_equinox_of_date)
        print('Ra', Ra._hours, 'Dec', Dec._degrees, 'ra_rate', ra_rate.arcseconds.per_second, 'dec_rate', dec_rate.arcseconds.per_second)
        return ra_rate, dec_rate

    def _follow_sat_using_loop(self):
        print('\n')
        start = time.perf_counter()
        coordinates_ra_dec, coordinates_alt_az = self._compute_relative_position(True)
        if coordinates_alt_az[0].degrees <= 10:
            print("Target will be too low in sky. Stop following\n")
            return False
        
        print('Celestial coordinates : RA ', coordinates_ra_dec[0].hours, '- Dec', coordinates_ra_dec[1].degrees)

        print('Aligning the telescope')
        #slew
        slewToCoords((str(coordinates_ra_dec[0]._hours), str(coordinates_ra_dec[1]._degrees)), self.target.name)
        print('Telesto is in the target path\n')

        print('time elapsed = ', time.perf_counter() - start,'\n')
        print('##################################')
        disp = 0
        while time.perf_counter() - start < 60:
            time.sleep(1)
            if disp%5 == 0:
                print('Waiting the target to be in the field of view',time.perf_counter() - start,'s')
            disp += 1
        print('##################################\n')
        print('time elapsed = ', time.perf_counter() - start,'\n')

        print('Start following')
        self.is_following=True

        while self.is_following and coordinates_alt_az[0].degrees >= 10 and time.perf_counter() - start < 120:
            coordinates_ra_dec, coordinates_alt_az = self._compute_relative_position()
            print("Recompute position : " + str(coordinates_ra_dec[0]) + " " + str(coordinates_ra_dec[1]))
            slewToCoords((str(coordinates_ra_dec[0]._hours), str(coordinates_ra_dec[1]._degrees)), self.target.name)
            time.sleep(2)
            
        self.is_following=False
        print('Celestial coordinates : RA ', coordinates_ra_dec[0].hours, '- Dec', coordinates_ra_dec[1].degrees)


    def do_kill(self):
        """Kill the current process"""
        print('Killing the current process')
        # exit the program
        sys.exit(0)
##########################


    def _follow_sat(self):
        coordinates_ra_dec, coordinates_alt_az = self._compute_relative_position()
        i = 0
        while self.is_following and coordinates_alt_az[0].degrees >= 10 and i<2:
            coordinates_ra_dec, coordinates_alt_az = self._compute_relative_position()
            print("Recompute position : " + str(coordinates_ra_dec[0]) + " " + str(coordinates_ra_dec[1]))
            slewToCoordsAzAlt((str(coordinates_alt_az[1]._degrees), str(coordinates_alt_az[0]._degrees)), self.target.name)
            time.sleep(1) # wait 10 secondes before updating the position
            i = i + 1

        if coordinates_alt_az[0].degrees <= 10:
            print("Target too low in sky. Stop following")
        
        self.is_following = False

    def do_stop_following(self, arg):
        '''\nStop following the current satellite \n'''
        self.is_following = False
        self.follow_thread.join()
        print("Following stop")

    def do_add_catalog(self, arg):

        '''\nAdd an url to download TLE file for debris or satellites
        add_catalog [type] [url] or add_catalog [type] [path]
        type could be sat or deb or perso\n'''

        args = arg.split()
        if len(args) != 2:
            print("\nInvalid argument number: add_catalog [type] [url]\n")
            return False

        if not self._write_url(args[0], args[1]):
            return False

        if self.has_started:
            self._load_file(args[0], args[1])

        return False

    # TODO: Make this command work
    #def do_take_picture(self, arg):

        '''\nTake a picture with selected filter\n
            Format: take_picture [Exposure time in second] [number of image] [filter number]'''

        #splitted_arg = arg.split()
        #if len(splitted_arg) > 3:
        #    print("Wrong number of argument.\n"
        #          "Please use the right format. Use help take_picture to learn more.\n")

        #atFocus3("NoRTZ", arg[1])
        #for i in range(int(arg[1])):
        #    takeImage("Imager", arg[0], "1", arg[2])

        #return False

    # TODO: Not sure how its works
    @staticmethod
    #def do_dither():
    #    '''\nTake a series of images of a single field'''
    #    dither()

    def do_set_bin(args):
        """\nChange X and Y bin of the camera.\n
            Format: set_bin [BinX] [BinY]\n"""
        splitted_args = args.split()

        if len(splitted_args) != 2:
            print("Wrong number of argument\n"
                  "Please use the right format. Use help set_bin to learn more.\n")

        TSXSend("ccdsoftCamera.BinX = "+splitted_args[0])
        TSXSend("ccdsoftCamera.BinY = "+splitted_args[1])

    @staticmethod
    def _write_url(url_type, url):
        name = ''
        if url_type == "sat":
            name = 'satellites_url.txt'
            file = open(name, 'r')
        elif url_type == "deb":
            name = 'debris_url.txt'
            file = open(name, 'r')
        elif url_type == "perso":
            name = 'personal_tle.txt'
            file = open(name, 'r')
        else:
            print("Invalid argument: type should be deb, sat or perso")
            return False

        lines = file.readlines()

        if url+"\n" in lines:
            print("Invalid URL: The URL already exits")
            return False
        file.close()

        file = open(name, 'a')
        file.write(url + '\n')
        file.close()
        print("Url: "+url+" correctly written")

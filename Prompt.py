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
    location = [46.30916667, 6.13472222]  # raw location, simpler than automatically get it
    bluffton = skyfield.api.wgs84.latlon(location[0]*N, location[1]*E, elevation_m=443)  # vector used to compute topocentric coordinates
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

        '''\nexit the application.\n'''

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

    def do_start(self, arg):

        '''\nInitialize all Telesto hardware and software for communication\n'''

        if len(arg) > 0:
            print("\nStart don't take argument\n")
            return False

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

            # initialize file
            self._init_file()

            # Enter a session name
            print("Enter a session name for your observation")
            self.session_name = input()
            init_file = open('C:\\Users\\admin\\Documents\\Software Bisque\\TheSkyX Professional Edition\\Imaging System Profiles\\ImagingSystem.ini', 'rt')
            content = init_file.read()
            content = content.replace(self.original_session_name, self.session_name)
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
        target_debris [catalog number]\n'''

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
        self.is_following = True

        # set-uping thread to make the following asynchronous
        self.follow_thread = threading.Thread(target=self._follow_sat())
        print("Start following target")
        self.follow_thread.start()

    def _slew_coord(self, arg):
        self.target = self.satellites[int(arg)]
        print("You targeted "+str(self.target))
        coordinates_ra_dec, coordinates_alt_az = self._compute_relative_position(True)

        if coordinates_alt_az[0].degrees < 0:
            print("Target under horizons")
            return False
        print(coordinates_ra_dec[0], coordinates_ra_dec[1])
        slewToCoords((str(coordinates_ra_dec[0]._degrees), str(coordinates_ra_dec[1]._degrees)), self.target.name)
        return True

    def _compute_relative_position(self, offset=False):
        difference = self.target - self.bluffton
        if offset:
            prevision = self.ts.now().utc_datetime().replace(minute=self.ts.now().utc.minute + 1)
            topocentric = difference.at(self.ts.utc(prevision))
        else:
            topocentric = difference.at(self.ts.now())

        coordinates_ra_dec = topocentric.radec(epoch='date')
        coordinates_alt_az = topocentric.altaz()

        return coordinates_ra_dec, coordinates_alt_az

    def _follow_sat(self):
        coordinates_ra_dec, coordinates_alt_az = self._compute_relative_position()
        time.sleep(60)
        while self.is_following and coordinates_alt_az[0].degrees >= 10:
            coordinates_ra_dec, coordinates_alt_az = self._compute_relative_position()
            slewToCoords((str(coordinates_ra_dec[0]._degrees),
                          str(coordinates_ra_dec[1]._degrees)),
                         self.target.name)
        if coordinates_alt_az[0].degrees >= 10:
            print("Target too low in sky. Stop following")

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

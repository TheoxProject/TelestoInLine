from cmd import Cmd
from datetime import datetime
import skyfield
from skyfield.api import load
from subprocess import Popen, DEVNULL, run
from PySkyX_ks import *


class Prompt(Cmd):
    prompt = 'Telesto>'
    intro = "Welcome to the Telesto command line interface \n Type ? to list commands"

    has_started = False

    # dictionary that contain all debris and all satellites
    satellites = {}
    location = [46.3013889, 6.133611111111112]  # raw location, simpler than automatically get it
    bluffton = skyfield.api.wgs84.latlon(location[0], location[1])
    confirm = False
    target = None

    def do_exit(self, arg):

        '''\nexit the application.\n'''

        print("Disconnect Cam...\n")
        camDisconnect("Imager")

        print("closing all app...\n")
        # TODO: remove comment
        self.OSBus.terminate()
        self.Maestro.terminate()
        self.SkyX.terminate()

        print("App closed")

        return True

    def do_start(self, arg):

        '''\nInitialize all Telesto hardware and software for communication\n'''

        if len(arg) > 0:
            print("\nStart don't take argument\n")
            return False

        if self.has_started:
            print("already started")
            return False
        
        if preRun() == "Fail":
            print("bad configuration please fix config before start")
            return True

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

            # start necessary software
            # TODO: remove comment
            self._launch_software()

            # Connect Cam
            camConnect("Imager")

            self.has_started = True
            print("\nReady\n")
            return False

    def _init_file(self):
        # Read URLs from text files
        debris_urls, satellites_urls = self._read_url()

        # load each files then append it in a general dictionary
        print("Load debris files\n")
        self._load_file("deb", debris_urls)

        print("Load satellites files")
        self._load_file("sat", satellites_urls)

        print("Loaded", len(self.satellites), "debris and satellites")

    @staticmethod
    def _read_url():

        debris_url_file = open('debris_url.txt', 'r')
        satellites_url_file = open('satellites_url.txt', 'r')

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

        return debris_url, satellites_url

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

        args = arg.split()
        if len(args) != 1:
            print("\nInvalid argument number: target_satellites [catalog number]\n")
            return False

        if int(args[0]) not in self.satellites:
            print("\nInvalid target: please use an existing target\n")
            return False

        self._slew_coord(arg)

    def _slew_coord(self, arg):
        target = self.satellites[int(arg)]
        difference = target - self.bluffton
        topocentric = difference.at(self.ts.now())
        coordinates_ra_dec = topocentric.radec(epoch='date')
        coordinates_alt_az = topocentric.altaz()

        if coordinates_alt_az[0].degrees < 0:
            print("Target under horizons")
            return
        print(coordinates_ra_dec[0], coordinates_ra_dec[1])
        slewToCoords((str(coordinates_ra_dec[0]), str(coordinates_ra_dec[1])), target.name)

    def do_add_catalog(self, arg):

        '''\nadd an url to download TLE file for debris or satellites
        add_catalog [type] [url]
        type could be sat or deb\n'''

        args = arg.split()
        if len(args) != 2:
            print("\nInvalid argument number: add_catalog [type] [url]\n")
            return False

        if not self._write_url(args[0], args[1]):
            return False

        if self.has_started:
            self._load_file(args[0], args[1])

        return False

    def do_take_picture(self, arg):

        '''\nTake a picture with selected filter\n
            Format: take_picture [Exposure time in second] [number of image] [filter number]'''

        splitted_arg = arg.split()
        if len(splitted_arg) > 3:
            print("Wrong number of argument.\n"
                  "Please use the right format. Use help take_picture to learn more.\n")

        atFocus3("NoRTZ", arg[1])
        for i in range(int(arg[1])):
            takeImage("Imager", arg[0], "1", arg[2])

        return False

    def do_dither(self):
        '''\nTake a series of images of a single field'''
        dither()

    @staticmethod
    def _write_url(url_type, url):
        name = ''
        if url_type == "sat":
            name = 'satellites_url.txt'
            file = open(name, 'r')
        elif url_type == "deb":
            name = 'debris_url.txt'
            file = open(name, 'r')
        else:
            print("Invalid argument: type should be deb or sat")
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

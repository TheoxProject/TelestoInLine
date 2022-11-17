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
    debris = {}
    satellites = {}
    telescope = None
    location = [46.3013889, 6.133611111111112]  # raw location, simpler than automatically get it
    bluffton = skyfield.api.wgs84.latlon(location[0], location[1])

    @staticmethod
    def do_exit(arg):

        '''\nexit the application.\n'''

        print("closing all app")
        return True

    def do_start(self, arg):

        '''\nInitialize all Telesto hardware and software for communication\n'''

        if len(arg) > 0:
            print("\nStart don't take argument\n")
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
            self.__init_file()

            # start necessary software
            self.__launch_software()

            self.has_started = True
            print("\nReady\n")
            return False

    def __init_file(self):
        # Read URLs from text files
        debris_urls, satellites_urls = self.__read_url()

        # load each files then append it in a general dictionary
        print("Load debris files\n")
        self.__load_file("deb", debris_urls)

        print("Load satellites files")
        self.__load_file("sat", debris_urls)

        print("Loaded", len(self.debris)+len(self.satellites), "debris and satellites")

    @staticmethod
    def __read_url():

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

    def __load_file(self, url_type, urls):

        for url in urls:
            temp = load.tle_file(url, reload=True)
            if url_type == "deb":
                self.debris.update({debris.model.satnum: debris for debris in temp})
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

    @staticmethod
    def __launch_software():

        Popen('C:\\Program Files (x86)\\Officina Stellare Srl\\OSBusSetup\\OSBusController.exe', stdout=DEVNULL)
        Popen('C:\\Program Files (x86)\\Astrometric\\Maestro\\Maestro.exe')
        Popen('C:\\Program Files (x86)\\Software Bisque\\TheSkyX Professional Edition\\TheSkyX.exe')

    def do_target_celestial_body(self, arg):

        '''\nMove the telescope to the body and take a number of image with a duration time
        target_celestial_body [object name] [number of image]x[duration] can be repated for each filter\n'''

        if not self._check_start():
            return False

        run("py ..\\automat_0.1\\ScriptSkyX\\run_target-2.py " + arg)

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

        if int(args[0]) not in self.debris:
            print("\nInvalid target: please use an existing target\n")
            return False

        slew(arg)

    def slew(self, arg):
        target = self.satellites[arg]
        difference = target - self.bluffton
        topocentric = difference.at(self.ts.now())
        coordinates_ra_dec = topocentric.radec(epoch='date')
        coordinates_alt_az = topocentric.altaz()

        if coordinates_alt_az[0].degrees < 30:
            print("Target high enough in the sky")
            return
        slewToCoords((coordinates_ra_dec[0], coordinates_ra_dec[1]), target.name)

    def do_add_catalog(self, arg):

        '''\nadd an url to download TLE file for debris or satellites
        add_catalog [type] [url]
        type could be sat or deb\n'''

        args = arg.split()
        if len(args) != 2:
            print("\nInvalid argument number: add_catalog [type] [url]\n")
            return False

        if not self.__write_url(args[0], args[1]):
            return False

        if self.has_started:
            self.__load_file(args[0], args[1])

        return False

    @staticmethod
    def __write_url(url_type, url):

        if url_type == "sat":
            file = open('satellites_url.txt', 'rw')
        elif url_type == "deb":
            file = open('debris_url.txt', 'rw')
        else:
            print("Invalid argument: type should be deb or sat")
            return False

        lines = file.readlines()

        if url in lines:
            print("Invalid URL: The URL already exits")
            return False

        file.writelines(url + '\n')
        file.close()

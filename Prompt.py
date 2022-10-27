from cmd import Cmd
from rich import print
from datetime import datetime
import skyfield
from skyfield.api import load
from subprocess import Popen, DEVNULL, run


class Prompt(Cmd):
    prompt = 'Telesto>'
    intro = "Welcome to the Telesto command line interface \n Type ? to list commands"

    has_started = False

    # dictionary that contain all debris
    debris = {}

    @staticmethod
    def do_exit(self):

        '''exit the application.'''

        print("closing all app")
        return True

    def do_start(self, arg):

        '''Initialize all Telesto hardware and software for communication'''

        if len(arg) > 0:
            print("Start don't take argument")
            return False

        print("Running Skyfield " + skyfield.__version__ + "\n")
        # check current version
        if skyfield.VERSION < (1, 45):
            print("This version is to old. Please upgrade Skyfield\n")
            print("run command : pip install skyfield\n")
            return False
        else:

            # initialize time
            self.__init_time()

            # initialize file
            self.__init_file()

            # start necessary software
            #self.__launch_software()

            self.has_started = True
            print("Ready")
            return False

    def __init_file(self):
        # list of url of debris file
        debris_url = ["https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle",
                      "https://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=tle",
                      "https://celestrak.org/NORAD/elements/gp.php?GROUP=1982-092&FORMAT=tle",
                      "https://celestrak.org/NORAD/elements/gp.php?GROUP=1982-092&FORMAT=tle"]

        # load each files then append it in a general dictionary
        print("Load debris file\n")
        for url in debris_url:
            temp_debris = load.tle_file(url, reload=True)
            self.debris.update({debris.model.satnum: debris for debris in temp_debris})
        print("Loaded", len(self.debris), "debris")

    def __init_time(self):
        self.ts = load.timescale()
        self.time = self.ts.now()
        print("You start observation at : " + str(self.time.astimezone(datetime.now().astimezone().tzinfo)))

    @staticmethod
    def __launch_software():

        Popen('C:\\Program Files (x86)\\Officina Stellare Srl\\OSBusSetup\\OSBusController.exe', stdout=DEVNULL)
        Popen('C:\\Program Files (x86)\\Astrometric\\Maestro\\Maestro.exe')
        Popen('C:\\Program Files (x86)\\Software Bisque\\TheSkyX Professional Edition\\TheSkyX.exe')

    def do_target_celestial_body(self, arg):

        '''Move the telescope to the body and take a number of image with a duration time
        target_celestial_body [object name] [number of image]x[duration] can be repated for each filter'''

        if not self.has_started:
            print("launch starting procedure first\n")
            return False
        arg_string = str(arg)
        print(arg)
        run("py ..\\automat_0.1\\ScriptSkyX\\run_target-2.py " + arg_string)

        return False

    def do_target_debris(self, arg):

        '''Move the telescope to debris
        target_debris [catalog number]'''
                



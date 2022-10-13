from cmd import Cmd
from rich import print
from datetime import datetime
import skyfield
from Telescope import *
from subprocess import Popen


class Prompt(Cmd):
    prompt = 'Telesto>'
    intro = "Welcome to the Telesto command line interface \n Type ? to list commands"

    has_started = False
    ts = None
    time = None
    planets = None
    Telescope = None

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
            print("run command : pip install skyfield")
            return False
        else:

            # initialize time
            self.init_time()

            # initialize file
            self.init_file()

            # start necessary software
            self.launch_software()

            print("Ready")
            return False

    def init_file(self):
        print("Load planets file")
        self.Telescope = Telescope(self.time)

    def init_time(self):
        self.ts = load.timescale()
        self.time = self.ts.now()
        print("You start observation at : " + str(self.time.astimezone(datetime.now().astimezone().tzinfo)))
        self.has_started = True

    def launch_software(self):
        # Popen('C:\\Windows\\System32\\notepad.exe')
        Popen('C:\\Program Files (x86)\\Officina Stellare Srl\\OSBusSetup\\OSBusController.exe')

    def do_goTo(self, arg):
        print(arg)
        args = "bloup"
        if len(args) == 1:
            name = args[0]
            self.Telescope.goto_named(args[0])
            pass
        elif len(args) == 2:
            # TODO: use coordinates
            pass
        else:
            print("Wrong argument number\n")
            print("format: goTo [celestial object name]\n")
            print("or goTo [celestial coord 1] [celestial coord 2]")
        pass

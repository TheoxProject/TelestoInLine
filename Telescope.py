from skyfield.api import load

class Telescope:

    def __init__(self, time):
        self.time = time
        self.bodies_files = load('de440.bsp')

    def goto_named(self, name):
        observed_body = self.bodies_files['Earth'].at(self.time).observe(name)
        print(observed_body.radec()[1])
        # for bodies_file in self.bodies_files:
        # if bodies_file[name] is None:
        # pass

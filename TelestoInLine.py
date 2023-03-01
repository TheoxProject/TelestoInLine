# This is the entry point of the program : a command line interface for TelestoInLine 

from Prompt import *

def main():
    p = Prompt()
    p.cmdloop()

if __name__ == '__main__':
    # calling the main function
    main()

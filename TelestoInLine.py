from argumentReader import *


def main():
    is_running = True
    # Instantiate parser
    parser = ArgumentReader()
    while is_running:
        # Keep running in loop for new command
        input()
        parser.read_args(parser.parser.parse_args())


if __name__ == '__main__':
    # calling the main function
    main()

#-- Classes and functions for colored python printout
# Link : https://www.geeksforgeeks.org/print-colors-python-terminal/
# Link : https://pypi.org/project/colorama/ ; colorama is cross-platform

# //--------------------------------------------
# //--------------------------------------------

# Python program to print colored text and background
'''Colors class:reset all colors with colors.reset;
two sub classes : fg for foreground and bg for background;
use as colors.subclass.colorname, i.e. colors.fg.red or colors.bg.green
Also, the generic bold, dim, underline, reverse, strike through, and invisible work with the main class i.e. colors.bold'''
class colors:
    reset='\033[0m'
    bold='\033[01m'
    dim='\033[02m'
    ital='\033[03m'
    underline='\033[04m'
    reverse='\033[07m'
    strikethrough='\033[09m'
    invisible='\033[08m'

    class fg:
        black='\033[30m'
        red='\033[31m'
        green='\033[32m'
        orange='\033[33m'
        blue='\033[34m'
        purple='\033[35m'
        cyan='\033[36m'
        lightgrey='\033[37m'
        darkgrey='\033[90m'
        lightred='\033[91m'
        lightgreen='\033[92m'
        yellow='\033[93m'
        lightblue='\033[94m'
        pink='\033[95m'
        lightcyan='\033[96m'
    class bg:
        black='\033[40m'
        red='\033[41m'
        green='\033[42m'
        orange='\033[43m'
        blue='\033[44m'
        purple='\033[45m'
        cyan='\033[46m'
        lightgrey='\033[47m'

# //--------------------------------------------
# //--------------------------------------------

if __name__ == "__main__":
    print(colors.fg.blue, 'test', colors.reset)


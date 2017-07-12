#!/bin/usr/python
#config.py

import configparser
import os

configfile_name = "config.ini"

# Check if there is already a configurtion file

def check_for_config_file():
    if not os.path.isfile(configfile_name):
        # Create the configuration file as it doesn't exist yet
        cfgfile = open(configfile_name, 'w')

        # Add content to the file
        config = configparser.ConfigParser()
        config.add_section('setup')
        config.set('setup','spreadsheetid','1WIlw6BvlQtjXO9KtnT4b6XY8d3qAaK5RYDRnzekkVjM')
        config.write(cfgfile)
        cfgfile.close()
        print('A configuration file was created with default values, see \
                config.ini for configuration options')

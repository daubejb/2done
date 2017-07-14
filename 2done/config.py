#!/bin/usr/python
#config.py

import configparser
import os
import os.path

configfile_name = os.path.join(os.environ['HOME'], '.2done_config.ini')

# Check if there is already a configurtion file

def check_for_config_file():
    if not os.path.isfile(configfile_name):
        # Create the configuration file as it doesn't exist yet
        cfgfile = open(configfile_name, 'w')

        # Add content to the file
        config = configparser.ConfigParser()
        config.add_section('setup')
        config.set('setup','spreadsheetid','1WIlw6BvlQtjXO9KtnT4b6XY8d3qAaK5RYDRnzekkVjM')
        config.set('setup','actions','action, followUp, idea, research, schedule, update')
        config.set('setup','contexts','home, work')
        config.add_section('display_options')
        config.set('display_options','display_list_after_add_item','True')
        config.set('display_options','display_lines_between_items','False')
        config.set('display_options','header_row_color', 'GREEN')
        config.set('display_options','today_color', 'MAGENTA')
        config.write(cfgfile)
        cfgfile.close()
        print('A configuration file was created with default values, see config.ini for configuration options')
        inp = input('Press <Enter> to continue.')

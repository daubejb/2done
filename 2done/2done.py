#!/bin/usr/python
#2done.py

from __future__ import print_function
from terminaltables import AsciiTable
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.contrib.completers import WordCompleter
from .config import check_for_config_file
from configparser import ConfigParser

import httplib2
import os
import argparse
import textwrap

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CLIENT_SECRET_FILE = 'client_secrets.json'
APPLICATION_NAME = '2done'
SPREADSHEET_ID = '1WIlw6BvlQtjXO9KtnT4b6XY8d3qAaK5RYDRnzekkVjM'
RANGE = 'Sheet1!A2:D100'
ACTIONS = ['Action', 'FollowUp', 'Idea', 'Research', 'Schedule']
CONTEXTS = ['Home', 'Work']
DISPLAY_LIST_AFTER_ADD_ITEM = True
DISPLAY_LINES_BETWEEN_ITEMS = True

try:
    parser = argparse.ArgumentParser(description='a free and open source \
            to do application accessible from anywhere')
    parser.add_argument('-a', '--add',
            help='add an item to the list',
            action='store_true',
            dest='add')
    parser.add_argument('-c', '--context',
            help='list only the items with the specified context',
            action='store',
            dest='context',
            default='all',
            choices=['all','home','work'])
    parser.add_argument('-t','--type',
            help='list only the items with the specified type',
            action='store',
            dest='type',
            default='all',
            choices=ACTIONS)
    args = parser.parse_args()
    print(args.type)

except ImportError:
    flags = None

def get_terminal_size():
    # Gets window width from terinal
    # Returns:
    #     Tw, terminal width.
    import fcntl, termios, struct
    th, tw, hp, wp = struct.unpack('HHHH',
        fcntl.ioctl(0, termios.TIOCGWINSZ,
        struct.pack('HHHH', 0, 0, 0, 0)))
    return tw

def get_credentials():
   # Gets valid user credentials from storage.
   # If nothing has been stored, or if the stored credentials are invalid,
   # the OAuth2 flow is completed to obtain the new credentials.
   # Returns:
   #     Credentials, the obtained credential.

    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   CLIENT_SECRET_FILE)

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            flags=tools.argparser.parse_args(args=[])
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def decompose_item_string_to_parts(str):
    word_list = str.split()
    first_word = word_list[0]
    last_word = word_list[-1]
    word_one = " "
    word_last = " "
    if first_word in ACTIONS:
        word_one = first_word
        del word_list[0]
    if last_word in CONTEXTS:
        word_last = last_word
        del word_list[-1]
    item_words =' '.join(word_list)
    values = ['=row()-1', word_one, item_words, word_last]
    return values

def instantiate_api_service(object):
    credentials = object
    http = credentials.authorize(httplib2.Http())
    ###API Call 
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    return service

def add_item_to_list(object):
    service = object
    TypeCompleter = WordCompleter(ACTIONS, ignore_case=True)
    ContextCompleter = WordCompleter(CONTEXTS, ignore_case=True)
    inp = prompt('Enter to do item > ',
            history=FileHistory('history.txt'),
            auto_suggest=AutoSuggestFromHistory(),
            completer=TypeCompleter)
    print('the input text is %s' % (inp))
    
    values = decompose_item_string_to_parts(inp) 
    body = {
            "range": RANGE,
            "majorDimension": 'ROWS',
            "values": [
                    values
                ],
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=RANGE,
        valueInputOption='USER_ENTERED',
        body=body).execute()

def get_list_data(object):
    service = object
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()
    values = result.get('values', [])
    return values

def get_configs():
    parser = ConfigParser()
    parser.read('config.ini')

    global DISPLAY_LIST_AFTER_ADD_ITEM
    DISPLAY_LIST_AFTER_ADD_ITEM = parser.getboolean('display_options',
            'display_list_after_add_item')
    global DISPLAY_LINES_BETWEEN_ITEMS
    DISPLAY_LINES_BETWEEN_ITEMS = parser.getboolean('display_options',
            'display_lines_between_items')

def main():

    check_for_config_file()
    get_configs()
    credentials = get_credentials()
    service = instantiate_api_service(credentials)
    
    if args.add:
        add_item_to_list(service)

    values = get_list_data(service) 
       
    ###Filtering values based on context option
    final_values = []
    term_width = get_terminal_size() - 30
    
    if args.type != 'all' and args.context != 'all':
        for row in values:
            if row[1] == args.type and row[3] == args.context:
                final_values.append(row)
    elif (args.context != 'all'):
        for row in values:
            if row[3] == args.context:
                final_values.append(row)
    elif (args.type != 'all'):
        for row in values:
            if row[1] == args.type:
                final_values.append(row)
    else:
        final_values = values    
    if not values:
        print('No data found.')
    else:
        data = []
        data.append(['id', 'type', 'todo item', 'context'])
        for row in final_values:
            total_length = len(row[0]) + len(row[1]) + len(row[2]) + \
            len(row[3])
            other_columns = len(row[0]) + len(row[1]) + len(row[3]) - 5
            short_length = term_width - other_columns
            if(total_length > term_width):
                shortened_text = textwrap.fill(row[2], width=short_length)
                row[2] = shortened_text

        for row in final_values:
            data.append([row[0], row[1], row[2], row[3]])
        table = AsciiTable(data)
        width = table.table_width
        table.title = APPLICATION_NAME
        if DISPLAY_LINES_BETWEEN_ITEMS == True:
            table.inner_row_border = True
        print(table.table)
    if __name__ == '__main__':
        main()


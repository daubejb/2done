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

import time
import httplib2
import os
import os.path
import argparse
import textwrap
import webbrowser
import colorama

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from colorama import init, Fore, Back, Style

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CLIENT_SECRET_FILE = 'client_secrets.json'
APPLICATION_NAME = '2done'
SPREADSHEET_ID = '1WIlw6BvlQtjXO9KtnT4b6XY8d3qAaK5RYDRnzekkVjM'
RANGE = '2done!A2:E1000'
DONE_RANGE = 'done!A2:F1000'
ACTIONS = ['action', 'followUp', 'idea', 'research', 'schedule', 'update']
CONTEXTS = ['home', 'work']
DISPLAY_LIST_AFTER_ADD_ITEM = True
DISPLAY_LINES_BETWEEN_ITEMS = True
WEB = 'https://docs.google.com/spreadsheets/d/%s' % (SPREADSHEET_ID)
HISTORY_FILE = os.path.join(os.environ['HOME'], '.2done_history.txt')
CONFIG_FILE = os.path.join(os.environ['HOME'], '.2done_config.ini')
HEADER_ROW_COLOR = 'GREEN'

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
    parser.add_argument('--delete',
            help='delete an item by id',
            action='store',
            dest='id_to_delete')
    parser.add_argument('-do', '--done',
            help='mark an item as done by id',
            action='store',
            dest='id_done')
    parser.add_argument('-g','--group',
            help='list only the items with the specified group',
            action='store',
            dest='group',
            default='all',
            choices=ACTIONS)
    parser.add_argument('-t','--today',
            help='toggle an item as important for today by id',
            action='store',
            dest='id_to_prioritize')
    parser.add_argument('-w','--web',
            help='open %s file in a webbrowser' % (APPLICATION_NAME),
            action='store_true',
            dest='web')
    args = parser.parse_args()
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
    values = ['=row()-1', '', word_one, item_words, word_last]
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
    GroupCompleter = WordCompleter(ACTIONS, ignore_case=True)
    ContextCompleter = WordCompleter(CONTEXTS, ignore_case=True)
    inp = prompt('Enter to do item > ',
            history=FileHistory(HISTORY_FILE),
            auto_suggest=AutoSuggestFromHistory(),
            completer=GroupCompleter)
    word_list = inp.split()
    first_word = word_list[0]
    second_word = word_list[1]
    third_word = word_list[2]
    print('%s %s %s... added to the list' % (first_word, second_word,
        third_word))
    
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
    if DISPLAY_LIST_AFTER_ADD_ITEM != True:
        quit()

def delete_item_from_list(object, id):
    service = object
    id = int(id)
    startIndex = id
    endIndex = id + 1
    batch_update_values_request_body = {
        "requests": [
            {   
                "deleteDimension": {
                    "range": {
                        "sheetId": 0,
                        "dimension": "ROWS",
                        "startIndex": startIndex,
                        "endIndex": endIndex
                    }
                }
            }
        ]
    }

    request = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=batch_update_values_request_body)
    response = request.execute()
    print(response)
    if 'replies' in response and 'spreadsheetId' in response:
        print('Item # %s deleted from list' % id)

def done_item_from_list(object, id):
    service = object
    id = int(id)
    A1 = id + 1
    startIndex = id
    endIndex = id + 1
    ranges = ['%s!A%s:E%s' % (APPLICATION_NAME, A1, A1)]


    request = service.spreadsheets().values().batchGet(
            spreadsheetId=SPREADSHEET_ID,
            ranges=ranges,
            valueRenderOption='UNFORMATTED_VALUE',
            dateTimeRenderOption='FORMATTED_STRING')

    response = request.execute()
    
    values = response['valueRanges'][0]['values'][0]
    values[0] = '=row()-1'
    values.insert(len(values), time.strftime("%Y-%m-%d"))
    body = {
            "range": DONE_RANGE,
            "majorDimension": 'ROWS',
            "values": [
                    values
                ],
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=DONE_RANGE,
        valueInputOption='USER_ENTERED',
        body=body).execute()
    delete_item_from_list(service, id)
    
def get_list_data(object):
    service = object
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()
    values = result.get('values', [])
    return values

def get_ANSI_color(string):
    color = string
    color.upper()
    if color == 'GREEN': color = '\033[32m'
    elif color == 'RED': color = '\033[31m'
    elif color == 'YELLOW': color = '\033[33m'
    elif color == 'BLUE': color = '\033[34m'
    elif color == 'PINK': color = '\033[35m'
    elif color == 'CYAN': color = '\033[36m'
    elif color == 'NORMAL': color = '\033[39m'
    elif color == 'WHITE': color = '\033[37m'
    return color

def get_configs():
    parser = ConfigParser()
    parser.read(CONFIG_FILE)

    global DISPLAY_LIST_AFTER_ADD_ITEM
    DISPLAY_LIST_AFTER_ADD_ITEM = parser.getboolean('display_options',
            'display_list_after_add_item')
    global DISPLAY_LINES_BETWEEN_ITEMS
    DISPLAY_LINES_BETWEEN_ITEMS = parser.getboolean('display_options',
            'display_lines_between_items')
    global HEADER_ROW_COLOR
    temp_HEADER_ROW_COLOR = parser.get('display_options','header_row_color')
    HEADER_ROW_COLOR = get_ANSI_color(temp_HEADER_ROW_COLOR)
    
def open_list_in_webbrowser():
    webbrowser.open(WEB)

def display_table(object):
    table = object
    width = table.table_width
    table.title = APPLICATION_NAME
    if DISPLAY_LINES_BETWEEN_ITEMS == True:
        table.inner_row_border = True
    print(table.table)

def filter_table_items_for_display(object, values):
    args = object
    final_items = []
    if args.group != 'all' and args.context != 'all':
        for row in values:
            if row[2] == args.group and row[4] == args.context:
                final_items.append(row)
    elif (args.context != 'all'):
        for row in values:
            if row[4] == args.context:
                final_items.append(row)
    elif (args.group != 'all'):
        for row in values:
            if row[2] == args.group:
                final_items.append(row)
    else:
        final_items = values
    return final_items

def toggle_item_priority(object, id):
    service = object
    id = int(id)
    A1 = id + 1
    print(id)
    print(A1)
    range_ = '%s!B%s' % (APPLICATION_NAME, A1)
    range2_ = '%s!B%s:B%s' % (APPLICATION_NAME, A1, A1)
    request = service.spreadsheets().values().batchGet(
            spreadsheetId=SPREADSHEET_ID,
            ranges=range_,
            valueRenderOption='FORMATTED_VALUE',
            dateTimeRenderOption='FORMATTED_STRING')

    response = request.execute()
    
    if 'values' not in response['valueRanges'][0]:
        priority = "yes"
    else:
        priority = response['valueRanges'][0]['values'][0]
        if priority[0] == 'Yes' or priority[0] == 'yes':
            priority = " "
        else:
            priority = 'yes'
    
    value_input_option = 'USER_ENTERED'

    body_ = { 
        "values": [
               [ priority ]       
            ]
        }
    
    request = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_,
            valueInputOption=value_input_option,
            includeValuesInResponse=True,
            body=body_)
    response = request.execute()
    return

def main():
    #function from coloroma to render colors on all os
    init()
    check_for_config_file()
    get_configs()
    credentials = get_credentials()
    service = instantiate_api_service(credentials)
    global values
    values = get_list_data(service) 
    
    ###Evaluate options containing no arguments
    if args.web:
        open_list_in_webbrowser()

    if args.add:
        add_item_to_list(service)
    
    if args.id_to_delete:
        delete_item_from_list(service, args.id_to_delete)

    if args.id_done:
        done_item_from_list(service, args.id_done)
    
    if args.id_to_prioritize:
        toggle_item_priority(service, args.id_to_prioritize)
        values = get_list_data(service)

    if not values:
        print('No data found.')
    
    else:
        final_values = filter_table_items_for_display(args, values)
        item_id = args.id_to_prioritize
        term_width = get_terminal_size() - 30
        for row in final_values:
            total_length = len(row[0]) + len(row[1]) + len(row[2]) + \
            len(row[3]) + len(row[4])
            other_columns = len(row[0]) + len(row[1]) + len(row[2]) + \
                    len(row[4])
            short_length = term_width - other_columns
            if(total_length > term_width):
                shortened_text = textwrap.fill(row[3], width=short_length)
                row[3] = shortened_text
            yes = ['YES','Yes','yes','Y','y']
            if row[1] in yes:
                row[0] = Fore.YELLOW + row[0]
                row[4] = row[4] + Style.RESET_ALL
        data = []
        data.append([HEADER_ROW_COLOR + Style.BRIGHT + 'id',
            'today', 'group', 'todo item',
            'context' + Fore.RESET + Style.RESET_ALL])
    
        
        for row in final_values:
            data.append([row[0], row[1], row[2], row[3], row[4]])
        table = AsciiTable(data)
        os.system('cls' if os.name == 'nt' else 'clear')
        display_table(table)

    if __name__ == '__main__':
        main()


#!/bin/usr/python
#2done.py

from __future__ import print_function
from terminaltables import AsciiTable
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.contrib.completers import WordCompleter

import httplib2
import os
import argparse
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CLIENT_SECRET_FILE = 'client_secrets.json'
APPLICATION_NAME = '2done'
SPREADSHEET_ID = '1WIlw6BvlQtjXO9KtnT4b6XY8d3qAaK5RYDRnzekkVjM'

try:
    parser = argparse.ArgumentParser(description='a free and open source \
            to do application accessible from anywhere')
    parser.add_argument('--list','-ls', action='store_true')
    parser.add_argument('--add','-a', help='add an item to the \
            list', type=str)
    parser.add_argument('--context', '-c', help='list only the items \
            with the specified context', nargs='?', const='all',
            default='all', type=str)
    args = parser.parse_known_args()
except ImportError:
    flags = None

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
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

def main():
    

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    ###API Call 
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    ###Specific spreadsheet and retrieving items from data source
    listName = 'Sheet1!A2:C'
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=listName).execute()
    values = result.get('values', [])
       
    ###Filtering values based on context option
    final_values = []
    print(args[1])
    if (args[1] != 'all'):
        for row in values:
            if row[2] == args[1]:
                final_values.append(row)
    else:
        final_values = values    
    if not values:
        print('No data found.')
    else:
        data = []
        data.append(['id', 'todo item', 'context'])
        for row in final_values:
            data.append([row[0], row[1], row[2]])
        table = AsciiTable(data)
        table.title = '2done'
        print(table.table)

def add():
    listName = 'Sheet1!A2:C'
    service = api()
    words = ['Action', 'Schedule', 'Research', 'Idea']
    contexts = ['Home', 'Work']
    TypeCompleter = WordCompleter(words, ignore_case=True)
    ContextCompleter = WordCompleter(contexts, ignore_case=True)
    inp = prompt('Enter to do item > ',
            history=FileHistory('history.txt'),
            auto_suggest=AutoSuggestFromHistory(),
            completer=TypeCompleter)
    
    word_list = inp.split()
    count = len(word_list)
    first_word = word_list[0]
    last_word = word_list[-1]
    word_one = ""
    word_last = ""
    if first_word in words:
        word_one = first_word
        word_list = word_list[1:]
    if last_word in contexts:
        word_last = last_word
        word_list = word_list[-1:]
    values = [word_one, word_list, word_last]
    body = {
      'values': values
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=listName,
        body=body).execute()

    print(inp)

if __name__ == '__main__':
    main()


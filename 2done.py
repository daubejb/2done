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
import click
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = '2done'
SPREADSHEET_ID = '1WIlw6BvlQtjXO9KtnT4b6XY8d3qAaK5RYDRnzekkVjM'

def get_credentials():
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
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def api():

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    
    ###API Call 
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    return service


@click.group()
def cli():
    pass


@cli.command()
@click.option('--context', '-c', default='all',
            help='Displays only items for the specified context')
def ls(context):
    """Displays the to do list."""
    service = api()

    ###Specific spreadsheet and retrieving items from data source
    listName = 'Sheet1!A2:C'
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=listName).execute()
    values = result.get('values', [])
    
    ###Filtering values based on context option
    final_values = []
    if (context != 'all'):
        for row in values:
            if row[2] == context:
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

@cli.command()
def add():
    """Adds a to do item to the list"""
    TypeCompleter = WordCompleter(['Action Item', 'Schedule',
        'Research', 'Idea'], ignore_case=True)

    inp = prompt('Enter to do item > ',
            history=FileHistory('history.txt'),
            auto_suggest=AutoSuggestFromHistory(),
            completer=TypeCompleter)
    
    print(inp)


if __name__ == '__main__':
    main()


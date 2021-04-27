import jmespath, requests, base64
userpass = open('/opt/dagster/app/credentials/amplitude','r').read()
encoded_u = base64.b64encode(userpass.encode()).decode()
headers_amplitude = {"Authorization" : "Basic %s" % encoded_u}

userpass = open('/opt/dagster/app/credentials/AT','r').read()
encoded_u = base64.b64encode(userpass.encode()).decode()
headers_AT = {"Authorization" : "Basic %s" % encoded_u}



#------------------------- Slack
import os
from slack import WebClient
from slack.errors import SlackApiError

_slack = {}
def init_slack():
    _slack['client'] = WebClient(token=open('/opt/dagster/app/credentials/slack', 'r').read())

def send_slack(text, channel):
    """Send slack message in a public channel"""
    return _slack['client'].chat_postMessage(
        channel=channel,
        text=text)



#------------------------Google sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import math

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
client = None

sheets = {}
spreadsheets = {}

def init_google_sheets(credentials_file):
    """Read credentials in the GSheetsCredentials.json file, and init the connection """
    global client,sheets,spreadsheets
    sheets = {}
    spreadsheets = {}
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)

def _getSheet(spreadsheet, sheetname):
    """Cache system for tabs"""
    if(not sheetname in sheets):
        sheets[sheetname] = spreadsheet.worksheet(sheetname)
    return sheets[sheetname]

#système de cache pour les spreadsheets
def _getSpreadsheet(spreadsheetname):
    """cache system for spreadsheets"""
    if(not spreadsheetname in spreadsheets):
        spreadsheets[spreadsheetname] = client.open(spreadsheetname)
    return spreadsheets[spreadsheetname]

#injecte un tableau 2D dans un onglet d'une spreadsheet
def _exp2D(tab, sheet, cell):
    """send a 2D array to a specific cell in a specific sheet"""
    (r,c) = gspread.utils.a1_to_rowcol(cell)
    nbr = len(tab)
    nbc = len(tab[0])
    _range = sheet.range(r, c, r+nbr-1, c+nbc-1)
    for i,cell in enumerate(_range):
        cell.value = tab [math.floor(i/nbc)] [i%nbc]
    sheet.update_cells(_range)

def send_google_sheet(spreadsheet, sheet, cell, tab):
    """send a 2D array to a specific cell in a specific sheet (by sheet name) in a specific spreadsheet (by spreadsheet name)"""
    _exp2D(tab,_getSheet(_getSpreadsheet(spreadsheet),sheet),cell)

def getAll(spreadsheet, sheet):
    """get all data of a specific sheet (by sheet name) in a specific spreadsheet (by spreadsheet name)"""
    return _getSheet(_getSpreadsheet(spreadsheet),sheet).get_all_values()


def getCell(spreadsheet, sheet, cell):
    return _getSheet(_getSpreadsheet(spreadsheet),sheet).acell(cell).value

def getRow(spreadsheet, sheet, row):
    return _getSheet(_getSpreadsheet(spreadsheet),sheet).row_values(row)

def getCol(spreadsheet, sheet, col):
    return _getSheet(_getSpreadsheet(spreadsheet),sheet).col_values(col)

def clear_google_sheet(spreadsheet, sheet):
    """delete all data in a specific sheet (by sheet name) in a specific spreadsheet (by spreadsheet name)"""
    all = getAll(spreadsheet, sheet)
    if len(all)==0 :
        return None
    for i,row in enumerate(all):
        for j,cell in enumerate(row):
            all[i][j] = ' '
    send_google_sheet(spreadsheet, sheet, 'A1', all)

#------------------------------ amplitude
def _case_amplitude_event_segmentation(json):
    """Interpret ampllitude json response in the case of an event segmentation chart """
    dates = jmespath.search('data.xValues', json)
    values = jmespath.search('data.series[*][*].value', json)
    out = []
    for i in range(len(dates)):
        row = [dates[i]]
        for y in values:
            row.append(y[i])
        out.append(row)
    return out
    
def _case_amplitude_funnel(json):
    """Interpret ampllitude json response in the case of a funnel chart """
    dates = jmespath.search('data[0].dayFunnels.xValues', json) 
    values = jmespath.search('data[0].dayFunnels.series', json)
    rates = list(map(lambda a: 0 if a[0] == 0 else 100.*a[1]/a[0] , values))
    return list(map(lambda date, rate: [date,rate], dates, rates))

def _case_amplitude_formula(json):
    """Interpret ampllitude json response in the case of an event segmentation chart with formula"""
    dates = jmespath.search('data.xValues', json)
    values = jmespath.search('data.series[0][*].value', json)
    return list(map(lambda date, value : [date,value], dates, values))

def amplitude_to_array(amplitude_chart_id):
    """Makes the request to amplitude, interpret response, and return a data array. 
    Arg amplitude_chart_id : the chart id you can find in the url of a SAVED chart"""
    url = "https://amplitude.com/api/3/chart/" + amplitude_chart_id + "/query"
    r = requests.get(url, headers=headers_amplitude)
    if r.status_code == 404:
        raise Exception(f"Amplitude n'a pas trouvé le graphique {amplitude_chart_id}. Vérifiez qu'il sagit bien d'un id existant et que le graphique est sauvegardé")
    if r.status_code != 200:
        raise Exception (f"Erreur lors de la requête à amplitude. Erreur {r.status_code}")
    json = r.json()
    #cas funnel 
    if jmespath.search('data[0].dayFunnels.xValues', json):
        return _case_amplitude_funnel(json)
    #case user segmentation
    elif jmespath.search('data.seriesLabels', json):
        return _case_amplitude_event_segmentation(json)
    elif jmespath.search('data.series[0][*].value', json):
        return _case_amplitude_formula(json)
    #other cases
    else :
        raise Exception("Type de chart amplitude non géré (ni tunnel simple, ni event segmentation simple)")

#---------------------------- AT
def AT_to_array(url):
    """Makes the request to amplitude, interpret response, and return a data array """
    r = requests.get(url, headers=headers_AT)
    if r.status_code != 200:
        raise Exception (f"Erreur lors de la requête à AT xiti. Erreur {r.status_code}")
    json = r.json()
    data = json['DataFeed'][0]
    col_names = jmespath.search('Columns[*].Label', data)
    col_ids = jmespath.search('Columns[*].Name', data)
    values = list(map(lambda id: jmespath.search('Rows[*].'+id, data), col_ids))
    out = [col_names]
    for i in range(len(values[0])):
        row = []
        for j in range(len(values)):
            row.append(values[j][i])
        out.append(row)
    return out

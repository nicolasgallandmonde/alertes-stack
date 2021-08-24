import jmespath, requests, base64, json
import cachetools.func

def get_credentials():
    return  json.loads(open('/workspace/.credentials.json','r').read())


#------------------------- Slack
import os
from slack_sdk import WebClient


_slack = {}
def init_slack():
    _slack['client'] = WebClient(token=(get_credentials())['slack']['xoxb'] )

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
    creds = ServiceAccountCredentials.from_json_keyfile_dict( (get_credentials())['google_sheets'], scope)
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


@cachetools.func.ttl_cache(maxsize=528, ttl=60)
def amplitude(amplitude_chart_id):
    return amplitude_to_array(amplitude_chart_id)
    
def amplitude_to_array(amplitude_chart_id):
    """Makes the request to amplitude, interpret response, and return a data array.
    Arg amplitude_chart_id : the chart id you can find in the url of a SAVED chart"""
    credentials_amplitude = (get_credentials())['amplitude']
    userpass = credentials_amplitude["API_KEY"]+':'+credentials_amplitude["API_SECRET"]
    encoded_u = base64.b64encode(userpass.encode()).decode()
    headers_amplitude = {"Authorization" : "Basic %s" % encoded_u}

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

@cachetools.func.ttl_cache(maxsize=528, ttl=60) 
def AT(url):
    return AT_to_array(url)


def AT_to_array(url):
    """Makes the request to amplitude, interpret response, and return a data array """
    url = url.replace('/html/', '/json')
    credentials = (get_credentials())['AT']
    userpass = credentials['email']+':'+credentials['password']
    encoded_u = base64.b64encode(userpass.encode()).decode()
    headers_AT = {"Authorization" : "Basic %s" % encoded_u}
    r = requests.get(url, headers=headers_AT)
    if r.status_code != 200:
        raise Exception (f"Erreur lors de la requête à AT xiti. Erreur {r.status_code}")
    try:
        json = r.json()
    except Exception as e:
        raise e
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


#------------------------------ Alertes
def get_alerte_amplitude(logger):
    def alerte_amplitude(chart_id=None, channel=None, floor=None, ceil=None):
        def inner(func):
            def alert(comment=None, value=None):
                s_ceil = '' if ceil == None else ' seuil haut: '+str(round(ceil,2))
                s_floor = '' if floor == None else ' seuil bas: '+str(round(floor,2))
                s_value = '' if value == None else ' valeur: '+str(round(value,2))
                message = f"Alerte ! {func.__doc__}" +\
                    f"{':' if ceil!=None or floor!=None or value!=None else ''} {s_value} {s_floor} {s_ceil} "+\
                    f"{comment if comment!=None else ''}"+\
                    f"\nDonnées utilisées : https://analytics.amplitude.com/lemonde/chart/{chart_id}"
                if channel != None:
                    try:
                        send_slack(message, channel)
                    except:
                        send_slack("Impossible d'envoyer un message au channel: "+channel, "alertbot-erreurs-techniques")
                logger.error(message)
            if func.__doc__ == None:
                raise Exception("SVP ajoutez une doc à la fonction")
            logger.info('------------------- ' + func.__doc__)
            if channel == None:
                logger.error("Warning: Pas de channel slack défini pour l'alerte "+ func.__doc__)
            data = amplitude(chart_id)

            dates = list(map(lambda r:r[0], data))
            values = list(map(lambda r:r[1], data))
            value = func(dates, values, data, alert)
            if value != None and floor != None and value <= floor:
                alert(value=value)
            if value != None and ceil != None and value >= ceil :
                alert(value=value)
            logger.info(f"Amplitude : chart_id: {chart_id} - value: {value} - ceil: {ceil} - floor:{floor} - channel: {channel} ")
            #print values
            list(map(lambda d: logger.info(d), data))
        return inner
    return alerte_amplitude



def get_alerte_AT(logger):
    def alerte_AT(chart_id=None, channel=None, floor=None, ceil=None):
        def inner(func):
            def alert(comment=None, value=None):
                s_ceil = '' if ceil == None else ' seuil haut: '+str(round(ceil,2))
                s_floor = '' if floor == None else ' seuil bas: '+str(round(floor,2))
                s_value = '' if value == None else ' valeur: '+str(round(value,2))
                message = f"Alerte ! {func.__doc__}" +\
                    f"{':' if ceil!=None or floor!=None or value!=None else ''} {s_value} {s_floor} {s_ceil} "+\
                    f"{comment if comment!=None else ''}"+\
                    f"\nDonnées utilisées : {chart_id}"
                if channel != None:
                    try:
                        send_slack(message, channel)
                    except:
                        send_slack("Impossible d'envoyer un message au channel: "+channel, "alertbot-erreurs-techniques")
                logger.error(message)
            if func.__doc__ == None:
                raise Exception("SVP ajoutez une doc à la fonction")
            logger.info('------------------- ' + func.__doc__)
            if channel == None:
                logger.error("Warning: Pas de channel slack défini pour l'alerte "+ func.__doc__)
            data = AT_to_array(chart_id)
            value = func(data, alert)
            if value != None and floor != None and value <= floor:
                alert(value=value)
            if value != None and ceil != None and value >= ceil :
                alert(value=value)
            logger.info(f"AT : chart_id: {chart_id} - value: {value} - ceil: {ceil} - floor:{floor} - channel: {channel} ")
            #print values
            list(map(lambda d: logger.info(d), data))
        return inner
    return alerte_AT


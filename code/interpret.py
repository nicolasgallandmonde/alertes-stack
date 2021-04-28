import importlib
import connectors as con
import toml, json
from functools import reduce
from datetime import date, timedelta
import datetime as dt
import calendar
import traceback


#constants: toml entries
AMPLITUDE = "amplitude_chart_id" 
AT = "AT_request"
GSHEETS_OUT = "export_google_sheets"
ALERT_IF = "alert_if"
ALERT_TEXT = "description"
ALERT_CHANNEL = "alert_slack_channel"

# count occurence of entries in the job def
_count = lambda definitions, jobdef : reduce( lambda nb, cur: nb if cur not in jobdef else nb+1, definitions, 0)

#----------------- check : raises human readables exceptions about toml confs
def check_one_input(jobdef, job_name):
    """Checks if there one and only one input configured"""
    inputs = [AMPLITUDE, AT]
    nb_inputs = _count (inputs, jobdef)
    if nb_inputs != 1:
        raise Exception(f"erreur dans { job_name } : {nb_inputs} entrées trouvé(s). Il faut une entrée parmi { str(inputs) }")

def check_alert(jobdef, job_name):
    """Checks alert conf. return true if an alert is configured, false if not """
    if _count([ALERT_IF, ALERT_CHANNEL], jobdef) == 0: #no alert configured
        return False
    if ALERT_IF not in jobdef :
        raise Exception(f"job {job_name} : il faut configurer un '{ALERT_IF}'' pour définir une alerte")
    if ALERT_CHANNEL not in jobdef:
        raise Exception(f"job {job_name} : '{ALERT_CHANNEL}'' non configuré pour l'alerte")
    return True
    
def check_gsheets_export(jobdef, job_name):
    """Checks the format of the spreadsheet export conf """
    if GSHEETS_OUT not in jobdef:
        return False
    try:
        (ssheet, tab, cell) = (jobdef[GSHEETS_OUT]).split(':')
    except:
        raise Exception(f"job {job_name} : vérifiez le format de {GSHEETS_OUT} : il doit être 'nom du spreadsheet:onglet:cellule' et sans ':' dans le nom du spreadsheet ou dans le nom de l'onglet)")
    return True


#--------------- helpers
def get_yesterday(data):
    """Get the value of yesterday in the data"""
    yesterday = date.today() - timedelta(days=1)
    s_yesterday = yesterday.strftime('%Y-%m-%d')
    for s in reversed(data):
        d = ((s[0]).split('T'))[0]
        if d == s_yesterday:
            return s[1]
    raise Exception("Yesderday data not found")

def raise_alert_or_not(data, condition):
    """With data and condition, determines if we must raise an alert or not """
    condition = condition.lower().replace('%','').replace(',','.')
    actual = None
    if "yesterday" in condition:
        actual = get_yesterday(data)
        _condition = condition.replace('yesterday', actual)         
    elif "last_value" in condition:
        actual = str(round(data[-1][1],3))
        _condition = condition.replace('last_value', actual)
    elif "penultimate_value" in condition or "penultimate" in condition:
        actual = str(round(data[-2][1],3))
        _condition = condition.replace('penultimate_value', "penultimate").replace('penultimate', actual)
    else:
        raise Exception("no value found in alert condition (ex : last_value, penultimate_value, yesterday, ...")

    ext = {'actual': actual}
    formula = 'ext["result"] = ' + _condition
    exec(formula, {}, {'ext': ext })
    return ext


#--------------- interpret

def _interpret_job(log, jobdef, job_name):

    check_one_input(jobdef, job_name)

    #Management on inputs (amplitude and AT)
    if AMPLITUDE in jobdef:
        print("amplitude")
        data = con.amplitude_to_array(log, jobdef[AMPLITUDE])
                   
    if AT in jobdef:
        print("AT")
        data = con.AT_to_array(log, jobdef[AT])
    log.info("data : " + str(data))

    #spreadsheet export
    if check_gsheets_export(jobdef, job_name):
        (ssheet, tab, cell) = (jobdef[GSHEETS_OUT]).split(':')
        email_google = (json.loads(open('/opt/dagster/app/credentials/google_sheets', 'r').read()))["client_email"]
        try:
            con.send_google_sheet(log, ssheet, tab, cell, data)
        except Exception as e:            
            raise Exception( f"Erreur lors de l'enregistrement dans la spreadsheet. Vérifiez que le spreadsheet {ssheet} et l'onglet {tab} existent bien, que la cellule {cell} est accessible, et que la spreadsheet est bien partagée avec l'adresse mail : {email_google}", e)
        log.info(f"data exportées dans : {ssheet} => {tab} => {cell}")
    
    #alert management 
    if check_alert(jobdef, job_name):
        log.info ("gestion des alertes")
        _condition = jobdef[ALERT_IF]
        condition = _condition.replace('%', '').replace(',','.')
        alert_result = raise_alert_or_not(data, condition)
        actual = alert_result["actual"]
        if alert_result['result'] == True:    
            text = '' if ALERT_TEXT not in jobdef else jobdef[ALERT_TEXT] + '   - '
            text = f"Alert {job_name} : {text}, alert if :  {_condition} - actual : {actual}"
            log.warning("alert slack déclenchée : "+text)
            try:
                con.send_slack(log, channel=jobdef[ALERT_CHANNEL], text=text)
            except:
                raise Exception(f"Erreur lors de l'envoi à Slack. Vérifiez que le channel {ALERT_CHANNEL} n'est pas privé")
        else:
            log.info(f"pas d'alerte : {_condition} (actual : {actual})")
        
            
def interpret_job(log, jobdef, job_name):
    try:
        return _interpret_job(log, jobdef, job_name)
    except Exception as err:
        con.init_slack(log)
        log.error(f"Impossible d'interpréter le job {job_name}")
        log.error(traceback.format_exc())
        con.send_slack(log, f"Impossible d'interpréter le job {job_name}", "alertbot-erreurs-techniques")

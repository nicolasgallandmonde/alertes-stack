from dagster import execute_pipeline, pipeline, solid, String, composite_solid, repository, daily_schedule, schedule
from datetime import time, datetime
import toml, json
from os import listdir
from os.path import isfile, join
import os
import importlib
import connectors as con # external connectors (slack, gsheets, amplitude, ...)
importlib.reload(con)
import interpret # interpretation of toml files in order to create jobs
importlib.reload(interpret)
import git

# Au démarrage (refresh dans l'UI de dagster), fait un pull sur le repo git qui contient les configurations
try:
    repo = git.Repo('/confs/')
    repo.remotes.origin.pull('main')
except:
    print("impossible to git pull")

def get_all_toml_files(directory):
    allFiles = list()
    for entry in listdir(directory):
        fullPath = os.path.join(directory, entry)
        if os.path.isdir(fullPath):
            allFiles = allFiles + get_all_toml_files(fullPath)
        else:
            if ".toml" in entry and "_" not in entry:
                allFiles.append(fullPath)                
    return allFiles

def create_solid(jobdef, name):
    """Closure used to create a solid based on the job description from the toml file """
    @solid(name=name)
    def solid_template(context, previous=None):
        con.init_slack(context.log)
        con.init_google_sheets(context.log,'/opt/dagster/app/credentials/google_sheets')
        context.log.info('-------'+name)
        context.log.info(str(jobdef))
        interpret.interpret_job(context.log, jobdef, name)
        return 'dagster'
    
    return solid_template


def create_composite(conf, name):
    """Closure used to create a composite (composition of solid) based on categories found in the toml files (first level)"""
    @composite_solid(name=name)
    def group():
        last = None
        for kpi in conf:
            s = create_solid(conf[kpi], kpi)
            if last == None:
                last = s()
            else:
                last = s(last)
        return last

    return group()


@repository
def production():
    """Creation of dagster repo "production". Contains pipelines and schedulings """
    def name_from_file(toml_file):
        return ((toml_file.split('/'))[-1]).replace('.toml','') 

    def create_pipeline(toml_file):
        conf = toml.loads(open(toml_file,'r').read())
        name = name_from_file(toml_file)
        time = (conf["time"]).replace('h',':') if "time" in conf else '6:00'
        (hour,minutes) = time.split(':')
        day_of_week = conf['day_of_week'] if 'day_of_week' in conf else '*'
        week_days = ['sunday','monday','tuesday','wednesday','thursday', 'friday','saturday','sunday']
        day_of_week = ','.join(list(map(lambda d: '*' if d=='*' else str(week_days.index(d.lower().strip())), day_of_week.split(','))))
        day_of_month = str(conf['day_of_month']) if 'day_of_month' in conf else '*'
        day_of_month = ','.join(list(map(lambda d:d.strip(), day_of_month.split(','))))
        timezone = 'Europe/Paris' #conf['timezone'] if 'timezone' in conf else 'Etc/GMT' 
        

        @pipeline(name=name)
        def _pipeline():
            for cat in conf:
                if type(conf[cat]) == type({}):
                    create_composite(conf[cat], cat)

        @schedule(
            pipeline_name=name,
            name=name+'_schedule',
            cron_schedule=f"{minutes} {hour} {day_of_month} * {day_of_week}",
            execution_timezone=timezone,
        )
        def _schedule(_context):
            return {}
        
        return [_pipeline, _schedule]

        
    # loop over toml files
    toml_files = get_all_toml_files('/confs')
    pipelines_and_schedules = []
    for f in toml_files:
        try:
            p,s = create_pipeline(f)
            pipelines_and_schedules.append(p)
            pipelines_and_schedules.append(s)
        except Exception as e:
            con.init_slack()
            con.send_slack(f"Impossible d'interpréter le fichier {f}", "alertbot-erreurs-techniques")
            raise e
    
    return pipelines_and_schedules
    

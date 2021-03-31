from dagster import execute_pipeline, pipeline, solid, String, composite_solid, repository, daily_schedule
from datetime import time, datetime
import toml, json
from os import listdir
from os.path import isfile, join
import importlib
import connectors as con # external connectors (slack, gsheets, amplitude, ...)
importlib.reload(con)
import interpret # interpretation of toml files in order to create jobs
importlib.reload(interpret)
import git

# Au démarrage (refresh dans l'UI de dagster), fait un pull sur le repo git qui contient les configurations
repo = git.Repo('/confs/')
repo.remotes.origin.pull('main')


def create_solid(jobdef, name):
    """Closure used to create a solid based on the job description from the toml file """
    @solid(name=name)
    def solid_template(context, previous=None):
        con.init_slack()
        con.init_google_sheets('/opt/dagster/app/credentials/google_sheets')
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

        @pipeline(name=name)
        def _pipeline():
            for cat in conf:
                create_composite(conf[cat], cat)
        
        @daily_schedule(
            pipeline_name=name,
            name=name+'_schedule',
            start_date=datetime(2020, 1, 1),
            execution_timezone="Europe/Paris",
            execution_time= time(hour=6, minute=0, second=0, microsecond=0)
        )
        def _schedule(_context):
            return {}
        
        return [_pipeline, _schedule]

        
    # loop over toml files
    toml_files = [f for f in listdir("/confs") if isfile(join("/confs", f)) and ".toml" in f and "_" not in f]
    pipelines_and_schedules = []
    for f in toml_files:
        p,s = create_pipeline('/confs/'+f)
        pipelines_and_schedules.append(p)
        pipelines_and_schedules.append(s)
    
    return pipelines_and_schedules
    
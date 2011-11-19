from multiprocessing import Pool
import subprocess
import os
from os.path import abspath, join
import time 

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
# from django.db import connection
from django.db import connections, DEFAULT_DB_ALIAS
from functional_tests.helpers import print_exception
from django.template.loader import render_to_string
from django import VERSION

try:
    import djcelery
    CELERY_ENABLED = True
except:
    CELERY_ENABLED = False

def setup_selenium_stack(worker_index, verbosity, options):
    files = []
    silent_output = file('/dev/null', 'a+')
    files.append(silent_output)
    test_runner_settings = options.get('settings', None)
    if verbosity > 1:
        outputs={}
    else:
        outputs = {
            "stderr":silent_output,
            "stdout":silent_output,
        }
    
    manage_folder = ""
    try:
        import manage
        manage_folder = abspath(join(manage.__file__, ".."))
    except:
        pass

    test_settings = getattr(settings,"FUNCTIONAL_TEST_SERVER_SETTINGS", test_runner_settings)
    if test_settings:
        test_settings = "sel_worker_%s" % worker_index
    
    test_server_settings = "--settings=%s" % test_settings


    lots_of_options_dict = {
        've_path':              getattr(settings,"VIRTUALENV_PATH", abspath(join(abspath(__file__),"..","..","..","..","..",".."))),
        'http_port':            getattr(settings,"BASE_FUNCTIONAL_TESTS_LIVE_SERVER_PORT",8099)+worker_index, 
        'test_server_settings': test_server_settings,
        'lib_path' :            abspath(join(abspath(__file__), "..", "selenium_lib")), 
        "selenium_port":        getattr(settings,"BASE_FUNCTIONAL_TESTS_SELENIUM_PORT",4444)+worker_index,
        'file_uploader_port':   getattr(settings,"BASE_FUNCTIONAL_TESTS_FILE_UPLOADER_PORT", 8199)+worker_index,
        'project_root':         getattr(settings,"PROJECT_ROOT", manage_folder),
        'worker_index':         worker_index,
        'test_runner_settings': test_runner_settings,
    }
    settings_file = file('%s/sel_worker_%s.py' % (manage_folder, worker_index), 'w+')
    if test_settings != "":
        settings_file.write(render_to_string('functional_tests/settings.py.txt', lots_of_options_dict))
    settings_file.close()

    setup_databases(**lots_of_options_dict)

    sel_command =  "java -jar %(lib_path)s/selenium-server.jar -timeout 30 -port %(selenium_port)s -userExtensions %(lib_path)s/user-extensions.js" % lots_of_options_dict
    gun_command =  "%(ve_path)s/bin/python manage.py run_gunicorn -w 2 -b 0.0.0.0:%(http_port)s %(test_server_settings)s" % lots_of_options_dict
    cel_command =  "%(ve_path)s/bin/python manage.py celeryd %(test_server_settings)s" % lots_of_options_dict
    file_uploader_command = "%(ve_path)s/bin/python -m SimpleHTTPServer %(file_uploader_port)s" % lots_of_options_dict

    subprocesses = []    
    # subprocesses.append(subprocess.Popen(sync_command, shell=True, **outputs ))
    subprocesses.append(subprocess.Popen(sel_command, shell=True, **outputs ))
    subprocesses.append(subprocess.Popen(file_uploader_command, shell=True, cwd=join(settings.PROJECT_ROOT,"templates/functional_test_uploads"), **outputs ))
    # time.sleep(10)
    subprocesses.append(subprocess.Popen(gun_command, shell=True, **outputs ))
    if CELERY_ENABLED:
        subprocesses.append(subprocess.Popen(cel_command, shell=True, **outputs ))
    return subprocesses, silent_output

def teardown_selenium_stack(worker_index, subprocesses, silent_output):
    try:
        silent_output.close()    
    except:
        print_exception()
        pass

    for s in subprocesses:
        try:
            s.kill()
        except: 
            pass

    manage_folder = ""
    try:
        import manage
        manage_folder = abspath(join(manage.__file__, ".."))
    except:
        pass
    try:
        os.remove('%s/sel_worker_%s.py' % (manage_folder, worker_index))
        os.remove('%s/sel_worker_%s.pyc' % (manage_folder, worker_index))
    except Exception, e:
        pass

    print "Stopping..."
    time.sleep(8)



def setup_databases(**kwargs):
    if VERSION[0] == 1:
        if VERSION[1] == 2 and VERSION[2] < 4:
            return setup_databases_12(**kwargs)
        elif VERSION[2] >= 4 or VERSION[1] == 3:
            return setup_databases_13(**kwargs)

    raise Exception('Unsupported Django Version: %s' % (str(VERSION)))

def setup_databases_12(**kwargs):
    # Taken from django.test.simple
    old_names = []
    mirrors = []

    worker_index = kwargs.get('worker_index', None)
    for alias in connections:
        connection = connections[alias]
        database_name = 'test_%d_%s' % (worker_index, connection.settings_dict['NAME'])
        connection.settings_dict['TEST_NAME'] = database_name
        if connection.settings_dict['TEST_MIRROR']:
            mirrors.append((alias, connection))
            mirror_alias = connection.settings_dict['TEST_MIRROR']
            connections._connections[alias] = connections[mirror_alias]
        else:
            old_names.append((connection, connection.settings_dict['NAME']))
            connection.creation.create_test_db(verbosity=0, autoclobber=True)
    return old_names, mirrors

def setup_databases_13(**kwargs):
    # Taken from django.test.simple
    from django.test.simple import dependency_ordered

    mirrored_aliases = {}
    test_databases = {}
    dependencies = {}

    worker_index = kwargs.get('worker_index', None)
    for alias in connections:
        connection = connections[alias]
        database_name = 'test_%d_%s' % (worker_index, connection.settings_dict['NAME'])
        connection.settings_dict['TEST_NAME'] = database_name

        item = test_databases.setdefault(
            connection.creation.test_db_signature(),
            (connection.settings_dict['NAME'], [])
        )
        item[1].append(alias)
        if alias != DEFAULT_DB_ALIAS:
            dependencies[alias] = connection.settings_dict.get('TEST_DEPENDENCIES', [DEFAULT_DB_ALIAS])

    old_names = []
    mirrors = []
    for signature, (db_name, aliases) in dependency_ordered(test_databases.items(), dependencies):
        connection = connections[aliases[0]]
        old_names.append((connection, db_name, True))
        test_db_name = connection.creation.create_test_db(verbosity=0, autoclobber=True)
        for alias in aliases[1:]:
            connection = connections[alias]
            if db_name:
                old_names.append((connection, db_name, False))
                connection.settings_dict['NAME'] = test_db_name
            else:
                old_names.append((connection, db_name, True))
                connection.creation.create_test_db(verbosity=0, autoclobber=True)

    for alias, mirror_alias in mirrored_aliases.items():
        mirrors.append((alias, connections[alias].settings_dict['NAME']))
        connections[alias].settings_dict['NAME'] = connections[mirror_alias].settings_dict['NAME']

        return old_names, mirrors

class Command(BaseCommand):
    help = "Run the selenium tests."
    __test__ = False

    def handle(self, *args, **options):
                
        verbosity = int(options.get('verbosity', 1))
        base_port = int(options.get('base_port', 0))
        num_processes = int(options.get('functional_parallel_stacks', 1))


        self._pool = Pool(processes=num_processes)
        subprocess_stacks = []
        output_files = []
        results = []
        for base_port in range(0,num_processes):
            results.append(self._pool.apply_async(setup_selenium_stack, [base_port, verbosity, options]))

        for result in results:
            s,o = result.get()
            subprocess_stacks.append(s)
            output_files.append(o)
        
        try:
            call_command('test', "--with-selenium", *args, **options )
        except:
            pass

        self._pool.close()
        self._pool.join()
        self._pool = Pool(processes=num_processes)

        for base_port in range(0,num_processes):
            self._pool.apply_async(teardown_selenium_stack, [base_port, subprocess_stacks[base_port], output_files[base_port]])
            
        self._pool.close()
        self._pool.join()
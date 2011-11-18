from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
import subprocess
from os.path import abspath, join
import time 
from functional_tests.helpers import print_exception

class Command(BaseCommand):
    help = "Run the selenium tests."
    __test__ = False

    def handle(self, *args, **options):
        silent_output = file('/dev/null', 'a+')
        verbosity = int(options.get('verbosity', 1))
        base_port = int(options.get('base_port', 0))

        if verbosity > 1:
            outputs={}
        else:
            outputs = {
                "stderr":silent_output,
                "stdout":silent_output,
            }

        test_settings = getattr(settings,"FUNCTIONAL_TEST_SERVER_SETTINGS","")
        if test_settings != "":
            test_settings = "--settings=%s" % test_settings

        lots_of_options_dict = {
            've_path':              getattr(settings,"VIRTUALENV_PATH", abspath(join(abspath(__file__),"..","..","..","..","..",".."))),
            'http_port':            getattr(settings,"LIVE_SERVER_PORT",8099)+base_port, 
            'test_server_settings': test_settings,
            'lib_path' :            abspath(join(abspath(__file__), "..", "selenium_lib")), 
            "selenium_port":        getattr(settings,"SELENIUM_PORT",4444)+base_port,
            'file_uploader_port':   getattr(settings,"FUNCTIONAL_TEST_FILE_UPLOADER_PORT", 8199)+base_port
        }

        sel_command =  "java -jar %(lib_path)s/selenium-server.jar -timeout 30 -port %(selenium_port)s -userExtensions %(lib_path)s/user-extensions.js" % lots_of_options_dict
        gun_command =  "%(ve_path)s/bin/python manage.py run_gunicorn -w 2 -b 0.0.0.0:%(http_port)s %(test_server_settings)s" % lots_of_options_dict
        cel_command =  "%(ve_path)s/bin/python manage.py celeryd %(test_server_settings)s" % lots_of_options_dict
        file_uploader_command = "%(ve_path)s/bin/python -m SimpleHTTPServer %(file_uploader_port)s" % lots_of_options_dict
        
        selenium_subprocess = subprocess.Popen(sel_command,shell=True,              **outputs )
        file_uploader_subprocess = subprocess.Popen(file_uploader_command,shell=True, cwd=join(settings.PROJECT_ROOT,"templates/functional_test_uploads"), **outputs )
        time.sleep(10)
        gunicorn_subprocess = subprocess.Popen(gun_command,shell=True,              **outputs )
        celery_subprocess = subprocess.Popen(cel_command,shell=True,                **outputs )

        try:
            call_command('test', "--with-selenium", *args, **options )
            silent_output.close()    
        except:
            print_exception()
            pass
        
        try:
            gunicorn_subprocess.kill()
        except:
            pass

        try:
            selenium_subprocess.kill()
        except:
            pass

        try:
            celery_subprocess.kill()
        except:
            pass

        try:
            file_uploader_subprocess.kill()
        except:
            pass

                
        print "Stopping..."
        time.sleep(8)

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
import subprocess
from os.path import abspath, join
import time 

class Command(BaseCommand):
    help = "Run the selenium tests."
    __test__ = False

    def handle(self, *args, **options):
        output = file('/dev/null', 'a+')
        lots_of_options_dict = {
            've_path':              settings.VIRTUALENV_PATH, 
            'http_port':            settings.LIVE_SERVER_PORT, 
            'test_server_settings': settings.SELENIUM_TEST_SERVER_SETTINGS,
            'lib_path' :            join(abspath(settings.PROJECT_ROOT), "lib"), 
            "selenium_port":        settings.SELENIUM_PORT,
        }

        sel_command =  "java -jar %(lib_path)s/selenium-server.jar -timeout 30 -port %(selenium_port)s -userExtensions %(lib_path)s/user-extensions.js" % lots_of_options_dict
        gun_command =  "sleep 5;%(ve_path)s/bin/python manage.py run_gunicorn -w 2 -b 0.0.0.0:%(http_port)s --settings=envs.%(test_server_settings)s" % lots_of_options_dict
        cel_command =  "sleep 5;python manage.py celeryd --settings=envs.%(test_server_settings)s" % lots_of_options_dict
        selenium_subprocess = subprocess.Popen(sel_command,shell=True, stderr=output, stdout=output)
        gunicorn_subprocess = subprocess.Popen(gun_command,shell=True, stderr=output, stdout=output)
        celery_subprocess = subprocess.Popen(cel_command,shell=True, stderr=output, stdout=output)
        try:
            call_command('test', "--with-selenium", "--with-selenium-fixtures", "--with-xunit",
                                 "--with-xcoverage", *args, xcoverage_file="coverage.xml", xunit_file="xmlrunner/nosetests.xml", **options )
            output.close()    
        except:
            pass
        
        try:
            selenium_subprocess.kill()
        except:
            pass

        try:
            gunicorn_subprocess.kill()
        except:
            pass

        try:
            celery_subprocess.kill()
        except:
            pass
        
        time.sleep(6)
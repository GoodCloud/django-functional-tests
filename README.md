This project will provide a fairly easy way to get up and running with functional tests for Django, everything included.

It's currently in the process of being abstracted from some integrated, in-house code.  This README will be updated when that changes - in the meantime, it should be considered highly in flux.


Installation and requirements
=============================


Requires: (inital thoughts, don't trust these yet.)

* djangosanetesting
* nose
* django-nose
* nose-exclude
* django-nose-selenium
* gunicorn
* celery (do something smart to skip this)

settings.py
```
FORCE_SELENIUM_TESTS = False
SELENIUM_BROWSER_COMMAND = "*chrome"
LIVE_SERVER_PORT = 8099
SELENIUM_PORT = 64444
```

How to use
==========

At the core, `functional_tests` provides a set of useful classes you can use to easily write selenium tests.

After quite a bit of trial and error, we've found that this structure for tests works quite well.  However, the library doesn't lock you in - this is just a reccomended best practice.

```
/app
  __init__.py
  models.py
  /tests
     /__init__.py
     /unit_tests.py
     /selenium_abstractions.py (abstractions specific to the a)
     /selenium_tests.py
```

Where:

* `unit_tests.py` contains unit tests, django client tests, etc
* `selenium_abstractions.py` contains one or more classes that provide functional, common actions specific to the app. 
* `selenium_tests.py` contains the actual tests, subclassing one or more `selenium_abstractions` classes from this and other apps
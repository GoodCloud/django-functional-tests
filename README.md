This project will provide a fairly easy way to get up and running with functional tests for Django, everything (including the selenium server) is included.

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

`functional_tests` provides a set of useful classes you can use to easily write selenium tests, and a `manage.py` command to run them.

## Running Tests

`./manage.py selenium_tests`

That's it.  You can be more specific, if you'd like, as in:

`./manage.py selenium_tests accounts.tests.selenium_tests:TestAccessControl.test_that_staff_and_volunteers_can_not_see_the_account_link`

or just

`./manage.py selenium_tests accounts.tests.selenium_tests:TestAccessControl`


## Test Structure

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
* `selenium_abstractions.py` contains one or more classes that provide functional, common actions specific to the app. Expect them to be mixed in across apps.
* `selenium_tests.py` contains the actual tests, subclassing one or more `selenium_abstractions` classes from this and other apps



## Writing Tests

### General Test Structure 

Tests generally go something like this:

```
def test_something(self):
	sel = self.selenium  # Convention

	# Setup
	self.some_useful_abstractions()
	self.some_other_useful_abstractions()

	# Verify sterile conditions
	self.assertNotEqual(sel.get_text("css=.my_affected_element"), "Foo Bar")

	# The test actions
	sel.click("css=.my_test_element")

	# Verification
	self.assertEqual(sel.get_text("css=.my_affected_element"), "Foo Bar")
```

Tips:

* In general, the [selenium python API](http://release.seleniumhq.org/selenium-remote-control/0.9.0/doc/python/) is the best resource for what's available. 
* Sizzle.js is included, so if you use `css=` in your selector, you have access to pretty much all of the selectors you'd have in jQuery.



### Writing some useful abstractions

These examples are pulled mostly verbatim and trimmed from the GoodCloud codebase.  They're not perfectly illustrative, but they are real examples.

accounts/tests/selenium_abstractions.py

```
class AccountTestAbstractions(object):
   
    def create_demo_site(self, name="test", mostly_empty=False, **kwargs):
        return Factory.create_demo_site(name, quick=True, delete_existing=True,  mostly_empty=mostly_empty, **kwargs)

    def go_to_the_login_page(self, site=None):
        sel = self.selenium
        self.open("/login", site=site)
        sel.wait_for_page_to_load("30000")

    def log_in(self, username=None, password=None):
        sel = self.selenium
        if not username:
			username = "admin"
        if not password:
            password = username
        
        sel.type("css=input[name=username]",username)
        sel.type("css=input[name=password]",password)
        sel.click("css=.login_btn")
        sel.wait_for_page_to_load("30000")

    
    def setup_for_logged_in(self, name="test", mostly_empty=False, **kwargs):
        cache.clear()
        self.account = self.create_demo_site(name=name, mostly_empty=mostly_empty, **kwargs)
        self.go_to_the_login_page(site=name)
        self.log_in()

        return self.account
```


### Writing some tests

accounts/tests/selenium_tests.py

```
from functional_tests.selenium_test_case import DjangoFunctionalConservativeSeleniumTestCase
from accounts.tests.selenium_abstractions import AccountTestAbstractions

class TestAccessControl(DjangoFunctionalConservativeSeleniumTestCase, AccountTestAbstractions):

    def test_that_staff_and_volunteers_can_not_see_the_account_link(self):
        sel = self.selenium
        self.setup_for_logged_in()

        # Test staff
        self.go_to_the_login_page()
        self.log_in(username="staff", password="staff")
        assert not sel.is_element_present("css=.admin_btn")
        
        # Test volunteer
        self.go_to_the_login_page()
        self.log_in(username="volunteer", password="volunteer")
        assert not sel.is_element_present("css=.admin_btn")
```


## The Factory 

`functional_tests` also provides a useful factory class that provides a number of useful methods in setting up tests, entering randomish data, and generally injecting entropy into your tests.  The code's pretty straightforward, just subclass and build out your app-specific methods.

```
class Factory(DjangoFunctionalFactory):

    @classmethod
    def address(cls):
        apt_str = ""
        if cls.rand_bool():
            apt_str = "Apt. %s" % (cls.rand_int(1,1000))
        address = {
            "line_1": "%s %s %s" % (cls.rand_int(10,1000), cls.rand_plant_name(), cls.rand_street_suffix()),
            "line_2": apt_str,
            "city": cls.rand_plant_name(),
            "state": cls.rand_us_state(),
            "postal_code": cls.rand_int(10000,99999),
            "primary": cls.rand_bool(),
        }
        return address

```
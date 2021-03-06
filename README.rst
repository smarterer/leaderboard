leaderboard: a Smarterer API joint
===================================

An example application using the Smarterer API. The application is written in **Python** but is small
and simple enough that the ideas presented here should easily translate to any language.

This example application includes the following concepts:

* Oauth authenticating with Smarterer to access a user's smarterer data (sign in / sign up with Smarterer)
* Embedding a Smarterer test widget inside a third-party applicaiton.
* Making authenticated Smarterer API calls for a user's test scores.

This application creates a leaderboard from Smarterer scores for a specific test. Users sign in and/or sign up
with the leaderboard app using Smarterer. Once a user is authenticated with Smarterer, they are
presented the Smarterer embed widget to take a specific test on the application site.

The application uses Flask as a web framework and a simple sqlite database to store Smarterer tokens as well
as badge data for those users. It contains the main flows for conneting with the Smarterer API, oauth 
authenticating as well as using access tokens to make data requests on behalf of those authenticated users.

Getting started
---------------

Install
~~~~~~~

.. code-block:: bash

    $ git clone https://github.com/smarterer/leaderboard.git
    $ virtualenv --no-site-packages lb_env
    New python executable in lb_env/bin/python
    Installing setuptools............done.
    Installing pip...............done.
    $ source lb_env/bin/activate
    (lb_env)$ cd leaderboard
    (lb_env)$ pip install -r requirements.txt
    Downloading/unpacking Flask==0.9 (from -r requirements.txt (line 1))
    [...]
    Cleaning up...
    (lb_env)$ cp template_config.py config.py
    (lb_env)$ python util.py init
    DATABASE TABLES CREATED / DROPPED AND RECREATED


Configuring the example project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You will need to copy the ``template_config.py`` file to ``config.py``.

Then edit the file ``config.py`` and add values for your API registration and embed widget:

1) First you need to `sign up for a Smarterer API application registration <https://smarterer.com/api/reg>`_. 

   - If you're running this app on localhost you must specify ``http://localhost:5000/reg_complete`` as the Callback URL. 

2) Add your client_id and app_secret to the config file under SMARTERER_CLIENT_ID and SMARTERER_APP_SECRET. 
3) Choose a Smarterer TEST_URL_SLUG for the test you want to display a leaderboard for e.g. facebook, google-search.


Start the web app
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    (lb_env)$ python leaderboard.py
     * Running on http://127.0.0.1:5000/
     * Restarting with reloader


Visit 127.0.0.1:5000 in your browser and you should see the sample application.


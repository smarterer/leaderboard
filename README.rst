leaderboard: a smarterer API joint
===================================

An example application using the smarterer API.

Getting started
---------------

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

You need to configure the example project by editing the config.py file.

1) First `sign up for a smarterer API application registration <https://smarterercom/api/reg>`_.
2) Add your client_id and app_secret to the config gile under SMARTERER_CLIENT_ID and SMARTERER_APP_SECRET. 
3) Choose a Smarterer test_id to display a leaderboard for (2 = facebook).
4) Create a `smarterer test widget <http://smarterer.com/test-widget/create>`_.
5) Copy the embed html from the widget page to the config file under SMARTERER_WIDGET_EMBED.

Finally start the project:

.. code-block:: bash

    (lb_env)$ python leaderboard.py
     * Running on http://127.0.0.1:5000/
     * Restarting with reloader


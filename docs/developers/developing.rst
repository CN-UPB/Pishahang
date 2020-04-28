********************
Developing Pishahang
********************

If you want to contribute to Pishahang, this page provides you with common information on how to do so.

Managing Microservices
======================

As the docker containers that assemble Pishahang are managed by `docker-compose <https://docs.docker.com/compose/>`_, managing microservices means issuing `docker-compose` commands.
You can infer the available service names by looking at the :sourcefile:`docker-compose.yml` and :sourcefile:`docker-compose.override.yml` files.

.. note::

    All docker-compose commands have to be executed from the project root, as the ``.env`` file with the environment variables for the docker-compose files is located there.

Example Commands
----------------

Here is a short list of common commands to get you started:


.. rubric:: Running, stopping, and removing:

docker-compose up -d
    Run all microservices. If some service definitions or images have changed,
    update the changed ones.

docker-compose stop <my-service>
    Stop a service, leaving the container in place. You can resume it with ``docker-compose start <my-service>``.

docker-compose stop
    Stop all services. Resume with ``docker-compose start``.

docker-compose rm <my-service>
    Remove a service that has been stopped. This will also remove its volumes (except for named volumes).

docker-compose down <my-service>
    Stop a service and remove its container. Helpful for quickly resetting databases.

docker-compose down
    **Stop and remove all services**: This is like entirely uninstalling Pishahang. Use ``docker-compose stop`` if you just want to shut it down instead.


.. rubric:: Building images:

docker-compose build <my-service>
    Build the docker image of a specified service according to its Dockerfile

docker-compose build --parallel
    Build all docker images in parallel


.. rubric:: Viewing logs:

docker-compose logs -f <my-service>
    Follow the logs of a specified service

docker-compose logs -f
    Follow the logs of all microservices at the same time (helpful to find error messages)

Example Scenario
----------------

A common scenario for making changes to a microservice could be:

* Modify the source code of the service (you can find the mapping of service names to Dockerfiles in :sourcefile:`docker-compose.override.yml` to find out the corresponding source directory).
* Build the service's image by issuing ``docker-compose build <my-service>`` with the name of your service.
* Recreate the container of your service using the new image: ``docker-compose up -d``
* Take a look at the logs of the new container: ``docker-compose logs -f <my-service>``


Python Projects
===============

The majority of Pishahang microservices are written in Python.
They all share the same setup which is described in this section.

Poetry
------

`Poetry <https://python-poetry.org>`_ is a dependency manager for Python projects that also helps managing virtual environments and separating production and test dependencies.
In order to set up a microservice for local development, you will need to `install Poetry <https://python-poetry.org/docs/#installation>`_ first.

.. hint::

    By default, Poetry creates virtual environments in a platform-specific cache directory.
    If you plan to :ref:`use Visual Studio Code <vscode-setup>` (recommended), it is most comfortable to configure Poetry to create virtual environments within the respective project directory by running 
    
    .. code-block:: sh

        poetry config virtualenvs.in-project true
    
    before you follow the next paragraph.
    This way, Visual Studio Code will automatically detect the virtual environments created by Poetry.

Once Poetry itself is installed, you can open the python project of interest (the folder in which pyproject.toml is located) in a terminal and issue ``poetry install``.
This will create a virtual environment for the project and install the specified dependencies into it.
The project's microservice can then be started locally using ``poetry run start`` (because ``pyproject.toml`` defines a ``start`` script).
Make sure to stop the corresponding container beforehand, so it does not run in parallel to your local microservice instance.
You can run the tests for a project by issuing ``poetry run pytest``.


The MANO Base Package
---------------------

All microservices depend on the ``manobase`` package, which is located in the ``mano-framework/base`` folder and automatically linked into any other package's virtual environment by Poetry.
It implements comfortable utility classes for AMQP messaging and a plugin base class that the main class of each microservice inherits from.


Linting and Code Formatting
---------------------------

All python projects are configured to use flake8 for linting and Black for code formatting.
It is advisable to configure your editor to run these tools within the virtual environment that Poetry provides.


.. _vscode-setup:

Setup with Visual Studio Code
-----------------------------

If you use Visual Studio Code, here's the basic setup:
Within the root of the Pishahang repository, create a folder ``.vscode`` and add a ``settings.json`` with the following contents (if the file already exists, just add the properties to it):

.. code-block:: json

    {
      "python.linting.flake8Enabled": true,
      "python.linting.pylintEnabled": false,
      "python.formatting.provider": "black"
    }

Once you open Visual Studio Code in the root directory of the python project you want to edit, you can press `F1`, run "Python: Select Interpreter", and select the virtual environment created by Poetry (``./.venv/bin/python``).

Alternatively, if you did not yet run ``poetry install``, you can do it now and Visual Studio Code will ask you something like "We noticed a new virtual environment has been created. Do you want to select it for the workspace folder?", which you can accept then.

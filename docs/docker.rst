Docker Tips
~~~~~~~~~~~


Layout
------

* ``docker-compose.yml``

  Mail server and common file to use with other services

* ``rainloop.yml``

  Rainloop webmail server that exposes certain ports of the mail server.

The docker looks for ``docker-compose.yml`` file as a default if no files are
mentioned. So, the following two lines of code are equivalent:

   .. code-block:: console

     $ docker-compose -f docker-compose.yml up
     $ docker-compose up

Also, if, for example, server is started with:

  .. code-block:: console

    $ docker-compose -f docker-compose.yml -f rainloop.yml up -d

shutting it down with ``docker-compose down`` will only shutdown what's in
``docker-compose.yml`` file, i.e. only the mail server is closed.

To shutdown all services that were started, the same set of files that were
used before to start should be used. Otherwise, there's no way for
``docker-compose`` to understand which services are currently running.

To close server started with previous set of files, we can use:

  .. code-block:: console

     $ docker-compose -f docker-compose.yml -f rainloop.yml down

.. note:: When using multiple compose files, ``docker-compose.yml`` needs to be
   explicity mentioned.

Example Usages
--------------

.. warning:: All examples assume that the server is setup correctly. Refer
   :ref:`running-mail-server:Setting up server`.

* Running mailserver only

  .. code-block:: console

    $ docker-compose up -d

  .. note: ``-d`` flag runs containers in daemon/background mode.

  Or, mention docker-compose file:

  .. code-block:: console

    $ docker-compose -f docker-compose.yml up -d

* Running mailserver with ``rainloop`` webmail

  .. code-block:: console

    $ docker-compose -f docker-compose.yml \
                     -f rainloop.yml \
                        up -d

* Similarly, to close only mailserver,

  .. code-block:: console

    $ docker-compose down

  Or, mention docker-compose file:

  .. code-block:: console

    $ docker-compose -f docker-compose.yml down

* Likewise, for closing both mailserver and rainloop webmail server

  .. code-block:: console

    $ docker-compose -f docker-compose.yml \
                     -f rainloop.yml \
                        down

* To validate configuration and see merged compose file content:

  .. code-block:: console

    $ docker-compose -f docker-compose.yml \
                     -f rainloop.yml \
                        config

Inspecting network
------------------

* To get the list of networks:

  .. code-block:: console

    $ docker network ls

* To inspect default network for our server:

  .. code-block:: console

    $ docker network inspect server_default

* To remove network:

  .. code-block:: console

    $ docker network rm server_default

Inspecting volumes
------------------

* Getting list of volumes


  .. code-block:: console

    $ docker volume ls

* Inspect a volume:

  .. code-block:: console

    $ docker volume inspect <volume_name>

* Remove a volume:

  .. code-block:: console

    $ docker volume rm <volume_name>

.. _backup_volume:

* Backing up a volume:

  .. code-block:: console

    $ docker run --rm --volume <service_name> \
                  -v $(pwd)/../../output:/backup \
                  <any-container-name-having-tar> \
                  tar -cvf /backup/backup.tar -C <mounted-location> <directory_to_tar>

  For example, backing up ``rainloop`` volume:

  .. code-block:: console

    $ docker run --rm --volumes-from rainloop \
                  -v $(pwd)/../../output:/backup \
                  busybox \
                  tar -cvf /backup/backup.tar -C /rainloop/data _data_

  .. note:: Let's explain what's happening here:

     ``docker run``  creates a new container. After that:

        ``--rm``  flag tells Docker to remove the container once it stops.

        ``--volumes-from rainloop``:  Mounts all the volumes from container
        *rainloop* also to this temporary container.The mount points are the same
        as the original container.

        ``-v $(pwd)/../../output:/backup``:  Binds mount of the ``output`` directory
        from the host (assuming ``pwd`` is ``zippy/server``) to the ``/backup``
        directory inside the temporary container.

        ``busybox``:  Specifies that the container should run ``busybox`` image.
        Can be anything that can run ``tar``. Eg: *ubuntu*, *debian*, etc.

        ``tar -cvf /backup/backup.tar -C /rainloop/data _data_`` :
        Backs up the contents of ``_data_`` folder relative to ``rainloop/data``
        folder inside ``/backup/`` folder inside the container. This is the same
        ``output`` directory on the host system where a new ``backup.tar``
        file would appear.

* Restoring volume from backups

  - Remove the old volume

    .. code-block:: console

      $ docker volume rm <volume_name>

  - Recreate the volume

    .. code-block:: console

      $ docker volume create <volume_name>

  - Spin up a new container to recover from the tarball.

    .. code-block:: console

      $ docker run --rm -v <volume_name>:/recover \
                    -v <host_folder_to_backup_from>:/backup \
                    <any_image_that_has_tar> \
                    tar -C /recover -xvf /backup/backup.tar

    For example, to recover from previously backed up rainloop data,

    .. code-block:: console

      $ docker run --rm -v server_rainloop_data:/recover \
                   -v $(pwd)/../../output:/backup \
                   busybox \
                   tar -C /recover -xvf /backup/backup.tar

Troubleshooting rainloop
------------------------

TODO


Trobuleshooting mailserver
--------------------------

TODO



Executing arbitrary commands interactively
------------------------------------------

* To run on mail server:

  .. code-block:: console

    $ docker-compose exec mail bash

  Then, it should open ``bash`` shell to execute arbitrary commands.

* To run on rainloop server:

  .. code-block:: console

    $ docker-compose -f docker-compose.yml \
                     -f rainloop.yml \
                        exec rainloop sh

  Then, it should open shell to execute arbitrary commands. ``bash`` isn't
  available in *rainloop*.

Reading logs
------------

To read only mailserver logs:

  .. code-block:: console

    $ docker-compose logs

To follow logs, use ``-f`` flags.


To read logs from all services:

  .. code-block:: console

    $ docker-compose -f docker-compose.yml \
                     -f rainloop.yml \
                        logs

To follow logs, use ``-f`` flags.


To read from only one service:

  .. code-block:: console

    $ docker-compose -f docker-compose.yml \
                     -f rainloop.yml \
                        logs -f <service_name>

View running processes inside services
--------------------------------------

  .. code-block:: console

    $ docker-compose -f docker-compose.yml \
                     -f rainloop.yml \
                        top [<service_name>]

View running containers
-----------------------

  .. code-block:: console

    $ docker-compose -f docker-compose.yml \
                     -f rainloop.yml \
                        ps [<service_name>]

Dockerizing
-----------

We'll focus on developing algorithm. External services that we need or might need
could be used through docker which provides us reproducability and portability.

Hence, in future, we might use ``postgres``, ``redis``, etc. from the composition of
docker images.

References
^^^^^^^^^^

* `Getting Started with Docker`_
* `Getting Started with Docker Compose`_
* `Docker cheatsheet`_
* `docker-compose cheatsheet`_
* `docker-cli cheatsheet`_

..
.. Internal Links

.. _mail server is setup correctly: #setting-up-server

..
.. External Links

.. _Getting Started with Docker: https://docs.docker.com/get-started/
.. _Getting Started with Docker Compose: https://docs.docker.com/compose/gettingstarted/
.. _Docker cheatsheet: https://github.com/wsargent/docker-cheat-sheet
.. _docker-cli cheatsheet: https://devhints.io/docker
.. _docker-compose cheatsheet: https://devhints.io/docker-compose
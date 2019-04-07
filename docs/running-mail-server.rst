Running mail server
===================

Prerequisites
-------------
1. ``docker``
2. ``docker-compose``

.. warning:: If you are not in ``docker`` group, you might need to use sudo to
  use docker commands.

.. warning:: Start docker if it isn't already. ``systemctl start docker.service``.


Setting up server
-----------------
1. Open ``/etc/hosts`` and append following content in the file:

    .. code-block:: bash

      127.0.0.1 localhost.org

    .. note:: Required as some email client does not work with ``localhost``.

    .. note:: Sanity check:

      Running ``python -m http.server 8000`` and opening http://localhost.org:8000
      should work.

2. Change directory into ``zippy/server``.
3. Pull the docker image using:

    .. code-block:: console

      $ docker pull tvial/docker-mailserver:latest

4.  Copy ``env.dist`` file to ``.env`` (dot env).

    .. code-block:: console

      $ cp env.dist .env

5. Start container:

    .. code-block:: console

      $ docker-compose up -d mail

6. Make ``setup.sh`` executable.

    .. code-block:: console

      $ chmod +x setup.sh

7. Create a mail account.

    .. code-block:: console

      $ ./setup.sh email add test0@localhost.org test0
      $ ./setup.sh email add test1@localhost.org test1

    For simplicity, two email accounts with name ``test0`` and ``test1`` is created.
    Following is the format to create email account (refer
    :ref:`setup-sh:./setup.sh documentation` for further information.)

    .. code-block:: console

      $ ./setup.sh email add <user@domain> [<password>]

    .. note:: Use ``localhost.org`` as domain in above. This is done to make
      setup simpler.

    .. warning:: *Permission Denied*? Step 4 might have been skipped.

8. Generate dkim keys

    .. code-block:: console

      $ ./setup.sh config dkim

9. Restart container

    .. code-block:: console

      $ docker-compose down
      $ docker-compose up

10. Now, the mail server setup is complete. Refer :ref:`docker:Docker Tips` for more.


.. _running-server-with-rainloop:

Running mailserver with `Rainloop`_
-----------------------------------

.. warning:: It is assumed that the `mail server is setup correctly`_.

.. code-block:: console

  $ docker-compose -f docker-compose.yml \
                   -f rainloop.yml \
                      up -d

.. note:: Follow :ref:`Rainloop client setup <setting-mail-clients:rainloop>` later on.


Making backups of email
-----------------------

.. code-block:: console

  $ docker run --rm \
    --volume server_maildata:/var/mail \
    -v "$(pwd)/../../output":/backups \
    -ti tvial/docker-mailserver \
    tar cvzf /backups/docker-mailserver-`date +%y%m%d-%H%M%S`.tgz /var/mail

Assuming that the current directory is ``zippy/server``, this should make a
backup in ``output`` folder.
If backup is needed in any other folder, replace ``"$(pwd)/../../output"`` with
the folder where backup is to be placed.

:ref:`Volumes of container can be backed up similarly <backup_volume>`.

..
.. Internal Links

.. _mail server is setup correctly: #setting-up-server

..
.. External Links

.. _Rainloop: https://www.rainloop.net/
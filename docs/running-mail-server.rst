Running mail server
===================

Prerequisites
--------------
1. ``docker``
2. ``docker-compose``

.. warning:: If you are not in ``docker`` group, you might need to use sudo to
  use docker commands.

.. warning:: Start docker if it isn't already. ``systemctl start docker.service``.


Server setup
------------
1. Open ``/etc/hosts`` and append following content in the file:

    .. code-block:: bash

      127.0.0.1 localhost.org

    .. note:: Required as some email client does not work with ``localhost``.

    .. note:: Sanity check:

      Running ``python -m http.server 8000`` and opening http://localhost.org:8000
      should work.

2. Change directory into ``src/server``.
3. Pull the docker image using:

    .. code-block:: console

      $ docker pull tvial/docker-mailserver:latest

4.  Copy ``env.dist`` file to ``.env`` (dot env).

    .. code-block:: console

      $ cp env.dist .env

5. Start container

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
    Following is the format to create email account.

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
      $ docker-compose up mail

10. Now, the mail server setup is complete.


Setting up email client
-----------------------

Evolution
~~~~~~~~~

1. Install ``Evolution`` if you haven't already.

2. Open ``Evolution``. Then, **Edit**-> **Accounts**. From popup, click **Add**
   and select **Mail Account** from the dropdown.

3. The similar popup as follows should open. Click ``Next``.

    .. image:: ../assets/screenshots/01-email-client-setup.png

4. Enter name and email address to use on *Identity* section, as in example below.

    .. image:: ../assets/screenshots/02-email-client-setup.png

    Move on to ``Next``.

5. Then, on *Receiving Email* section, enter imap configuration as follows:

    .. image:: ../assets/screenshots/03-email-client-setup.png

    Move to the *Sending Email* section.

6. On *Sending Email* section, setup smtp configuration as follows:

    .. image:: ../assets/screenshots/04-email-client-setup.png

7. Then, check summary. It should look as:

    .. image:: ../assets/screenshots/05-email-client-setup.png

8. Then, click ``Apply`` on the last section *Done*.

    .. image:: ../assets/screenshots/06-email-client-setup.png

9. A popup asking for password should appear. Enter password and click ``Next``.

    .. image:: ../assets/screenshots/07-email-client-setup.png

10. Now, do the similar steps from [2-9] for ``test1@localhost.org``.

11. Try to send email from ``test0`` to ``test1``.

    .. image:: ../assets/screenshots/08-email-client-setup.png

12. If everything is setup correctly, ``test1`` should have received an email
    from ``test0``.

    .. image:: ../assets/screenshots/09-email-client-setup.png

.. note:: Approve encryption related messages. SSL has not been set.

Thunderbird
~~~~~~~~~~~

**Hamburger Menu** -> **Preferences** -> **Account Settings** -> **Account Action**
->  **Add Mail Account**

A popup should appear as follows. Fill everything as shown below:

  .. image:: ../assets/screenshots/10-email-client-setup.png

  Notice the server hostnames. They don't have `.` (dot) before `localhost.org`.
  Click ``Done`` and approve warning of not having encryption.


Making backups of email
-----------------------

.. code-block:: console

  $ docker run --rm \
    --volume server_maildata:/var/mail \
    -v "$(pwd)/../../output":/backups \
    -ti tvial/docker-mailserver \
    tar cvzf /backups/docker-mailserver-`date +%y%m%d-%H%M%S`.tgz /var/mail

Assuming that the current directory is ``src/server``, this should make a
backup in ``output`` folder.
If backup is needed in any other folder, replace ``"$(pwd)/../../output"`` with
the folder where backup is to be placed.


Running arbitrary command in server
-----------------------------------

Assuming container name as ``mail``, do following:

.. code-block:: console

  $ docker exec -ti mail bash

Then, it should open bash shell to execute arbitrary commands.


Running your own imapclient
---------------------------

Add following in ``[DEFAULT]`` section to ``setup.cfg`` file
in root of this repo.

.. code-block:: ini

  username = <user>@localhost.org
  password = <password>

Replace <user> and <password> with previously created username
and password.

Then run (from the root of the repo) following command:

.. code-block:: console

  $ python -m imapclient.interact -f setup.cfg

This should open an interactive session where client is available as ``c``
variable. Refer to the `imapclient documentation`_ for more information.

.. _imapclient documentation: https://imapclient.readthedocs.io/en/2.1.0/
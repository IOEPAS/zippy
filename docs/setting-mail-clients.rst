Setting up email client
=======================

.. warning:: Mail server should be up and running.

Rainloop
~~~~~~~~

.. warning:: To use this, you need to have :ref:`run server with rainloop <running-server-with-rainloop>`.

1. Open http://localhost.org:8888/?admin or http://localhost:8888/?admin.

2. Admin login page should load. Initially, admin credential is:
    *username* '**admin**' and *password* '**12345**'.

   Enter the credentals and login.

3. Admin page should open. In the left-hand sidebar, there should be **Domains**
   section. Open the section.

4. Then, click "+Add Domain" button. A popup should open.
   In the form, add ``localhost.org`` in **Name** field and ``mail`` in
   **Server** fields in *IMAP* and *SMTP* sections of the form.

  .. image:: ../assets/screenshots/11-email-client-setup.png

  .. _using_non_standard_ports:

  .. note:: We expose ports ``993`` (*TLS*/*SSL* *IMAP* port) and ``25``
    (*SMTP* relay port).

    Due to the possible collisions with system ports, we use ``1XXX`` ports
    instead (e.g. ``1993`` as *IMAP* port). We'll try to maintain standards
    *wherever*/*whenever* possible. If they are only two digits, we'll add zero
    (e.g. ``1025`` as *SMTP* port).

5. Click **Test** to check the connection and then, click **Update**/**Add**.

6. Now, open http://localhost.org:8888/ or http://localhost:8888/
   and you should be able to login to the email
   addresses created earlier.

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

    .. note:: `Why are we using non-standard ports`_?

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

Running your own imapclient
~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

..
.. Internal Links

.. _Why are we using non-standard ports: #using-non-standard-ports

..
.. External Links

.. _imapclient documentation: https://imapclient.readthedocs.io/en/2.1.0/
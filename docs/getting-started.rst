Getting started
===============

Installation
------------

1. Clone the repo, preferably using ssh clone instead of https.
2. Ensure that the environment has ``python3.6``.
    If it does not have one, then do either of the following:

   - Install from distro
   - Install ``python3.6`` from pyenv
   - Use conda to setup environment for python3.6

3. Create a virtual environment. Activate it.

4. Install all requirements.

    .. code-block:: console

       $ pip install -r requirements.txt

    .. warning::

      Installation might take a bit longer depending  on the internet speed.

5. Make sure the setup works by running tests. Refer :ref:`testing:Testing`
   for more details.

    .. code-block:: console

      $ make test
      $ make lint

6. Generate docs

    .. code-block:: console

      $ make docs

7. To run json log server,

    .. code-block:: console

      $ make log-server

8. Start coding...

Testing
=======


Running tests using make
------------------------

* To run all tests

  .. code-block:: console

    $ make test

* To run tests with coverage

  .. code-block:: console

    $ make test COVERAGE=true

* Further arguments can be passed using ``TEST_ARGS``.

Running tests using pytest
--------------------------

* To run all tests

  .. code-block:: console

    $ pytest

* Generating html coverage reports

  .. code-block:: console

    $ pytest --cov-report=html --cov=./

* Running tests from a specific file/folder

  .. code-block:: console

    $ pytest tests/test_hyperparams.py # all tests from `test_hyperparams.py`
    $ pytest tests # all tests from `tests` folder

* Running tests from a specific function

  .. code-block:: console

    $ pytest tests/test_hyperparams.py::<function_name>

    Eg:

  .. code-block:: console

    $ pytest tests/test_hyperparams.py::test_hyperparam_default

  So, running tests in general is in format:

  .. code-block:: console

    $ pytest <path_to_test_file/folder>[::<test_function_name>]

* Capturing output (append ``-s`` to arguments)

    .. code-block:: console

        $ pytest -s

* Getting list of available markers

  .. code-block:: console

    $ pytest --markers

* Getting list of fixtures

  .. code-block:: console

    $ pytest --fixtures


References
^^^^^^^^^^

* `pytest Documentation`_
* `pytest Cheatsheet`_

..
.. External Links

.. _pytest Documentation: https://docs.pytest.org/en/latest/contents.html
.. _pytest Cheatsheet: https://gist.github.com/kwmiebach/3fd49612ef7a52b5ce3a
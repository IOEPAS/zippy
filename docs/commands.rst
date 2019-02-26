Commands
========

The Makefile contains the central entry points for common tasks related to this project.


Type ``make help`` for commands.

  .. code-block:: console

    Usage:
      make <target>

    Available targets:

    clean               Delete all compiled Python files
    data                Data related operations
    docs                Make docs
    help                Show this help message
    lint                Lint using flake8
    models              Models related operations
    notebook            Create notebook
    run                 Run jupyter notebook
    test                Run tests
    test-cov            Run tests with coverage
    type-check          Run mypy for typecheck

.. note::

  Arguments/Code inside square brackets (``[]``) is optional, or only use if required.

Running tests
-------------

``make test [TESTARGS=<arguments>]``

Provide test arguments via ``TESTARGS``.

To run all tests: ``make test``

To run all tests from a package: ``make test TESTARGS=<path-to-package>``

To run tests from a given folder/file: ``make test TESTARGS=<path-to-file>``

To run a test: ``make test TESTARGS=<path-to-file>::<function-name>``

To run marked tests: ``make test TESTARGS=<marker_name>``


Running with code coverage
~~~~~~~~~~~~~~~~~~~~~~~~~~

``make test [TESTARGS=<arguments>]``

Provide test arguments via ``TESTARGS``.

To run all tests: ``make test-cov``

To run all tests from a package: ``make test-cov TESTARGS=<path-to-package>``

To run tests from a given folder/file: ``make test-cov TESTARGS=<path-to-file>``

To run a test: ``make test-cov TESTARGS=<path-to-file>::<function-name>``

To run marked tests: ``make test-cov TESTARGS=<marker_name>``

To generate html report:


Running test without make
~~~~~~~~~~~~~~~~~~~~~~~~~

To run all tests: ``pytest``

To run specific test file/folder/package: ``pytest <path/to>``
  Eg: ``pytest tests``

To run specific test: ``pytest <path-to-file>::<test-name>``
  Eg: ``pytest tests/test_hyperparameters.py::test_hyperparams_with_not_existing_config``

To run with code coverage: ``pytest --cov=.``

To run marked tests: ``pytest -m <marker>``

To generate html report:

.. note::

  Any arguments to pytest can also be provided through make commands.
  To escape, put all arguments in quotes. Eg:
  ``make test TESTARGS="-m <marker-name>"``



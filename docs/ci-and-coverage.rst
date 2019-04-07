Continuous Testing/Integration
==============================

At the moment, we create ``zippy`` package (an editable one) and use that for
testing purposes. We lint code, generate docs, test the code and track the
changes through ``codecov``. We also check ``types`` if used explicitly.

Linter
^^^^^^
We currently check for:

* Imports ordering through *isort*.
* Code style through *black*.
* Code lint using *pylint* and *flake8*.
* Docstyle using *pydocstyle*.

Documentation
^^^^^^^^^^^^^
We enable strict warnings when building documentation. Hence, any warnings
will fail the tasks.

Testing
^^^^^^^
We run tests with coverage enabled. The coverage reports are sent to
*codecov* which will be reported on every pull requests.

TypeChecking
^^^^^^^^^^^^
We run *mypy* to type-check code that uses "types". Otherwise, it won't bother.

Codefactor.io
^^^^^^^^^^^^^
`Codefactor.io`_ looks for any vulnerabilities and errors in the code. It runs
*pylint*, *bandit*, *yamllint*, *shellcheck* and checks for code duplications.


..
.. External Links

.. _Codefactor.io: https://www.codefactor.io
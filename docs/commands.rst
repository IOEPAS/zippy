Makefile Commands
=================

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
    package             Make zippy available as a package 
    run                 Run jupyter notebook 
    test                Run tests
    type-check          Run mypy for typecheck


* ``make clean``: Removes all ``.pyc`` files
* ``make docs``: Build documentation
* ``make lint``: Lint code for issues
* ``make lint:fix``: Fix codestyle issues
* ``make notebook TOPIC=<topic_name>``: Create new notebooks in ``notebooks`` directory.
* ``make mpackage``: Build project. Allows us to import code as ``zippy``.
* ``make mrun``: Run jupyter-notebook server.
* ``make test``: Runs tests. Refer :ref:`testing:Testing` for more information.
* ``make type-check``: Run type-checking using ``mypy``.

data
^^^^
* ``make data``: Shows help, and available *data* files in ``data`` directory.

  .. code-block:: console

    $ make data

      make data:push FILENAME=<DATA_FILENAME> To push specific dataset to Azure.
      make data:pull FILENAME=<DATA_FILENAME> To pull specific dataset from Azure.
      make <DATA_FILENAME> To build dataset locally.

* ``make data:push FILENAME=<DATA_FILENAME>``: Push given filename to Azure Storage
    (requires ``AZURE_STORAGE_KEY`` setup in ``.env.yml``).

* ``make data:pull FILENAME=<DATA_FILENAME>``: Pull given filename from Azure Storage.
    (requires ``AZURE_STORAGE_KEY`` setup in ``.env.yml``).

* ``make <DATA_FILENAME>``: Builds the dataset locally.

models
^^^^^^

* ``make models``: Shows help, and available *model* files in ``output/models`` directory.

  .. code-block:: console

    $ make models

      make models:push FILENAME=<MODEL_FILENAME>      To push specific model to Azure.
      make models:pull FILENAME=<MODEL_FILENAME>      To pull specific model from Azure.
      make <MODEL_FILENAME>                           To train model locally.

* ``make models:push FILENAME=<MODEL_FILENAME>``: Push given model to Azure Storage
    (requires ``AZURE_STORAGE_KEY`` setup in ``.env.yml``).

* ``make models:pull FILENAME=<MODEL_FILENAME>``: Pull given model from Azure Storage
    (requires ``AZURE_STORAGE_KEY`` setup in ``.env.yml``).

* ``make <MODEL_FILENAME>``: Builds the model locally.

Building Documentation
======================

Prerequisites
-------------

Install Sphinx and theme dependencies:

.. code-block:: bash

    pip install -r ../docs-requirements.txt

Building HTML Documentation
----------------------------

From the project root directory:

.. code-block:: bash

    make html

Or on Windows:

.. code-block:: cmd

    make.bat html

The built documentation will be in ``build/html/``. Open ``build/html/index.html`` in a browser to view.

Building Other Formats
----------------------

PDF (requires LaTeX):

.. code-block:: bash

    make pdf

Cleaning build artifacts:

.. code-block:: bash

    make clean

For more options:

.. code-block:: bash

    make help

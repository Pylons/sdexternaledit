sdexternaledit
==============

Overview
--------

:mod:`sdexternaledit` is a package which provides Zope External Editor
capabilities to Substance D.  Zope External Editor is a client program which
allows you to edit text and binary files stored on web servers in OS-native
editors.

Installation
------------

Obtain the source code from the git repository:

.. code-block:: text

  $ git clone git://github.com/Pylons/sdexternaledit.git

Use the "setup.py develop" command of the virtualenv that you use to run
Substance D to install the software:

.. code-block:: text

  $ cd sdexternaledit
  $ /path/to/my/substanced/virtualenv/bin/python setup.py develop

Server-Side Configuration
-------------------------

In your Substance D application's startup stanza, use
``config.include('sdexternaledit')``.  For example:

.. code-block:: python

   def main(global_config, **settings):
       """ This function returns a Pyramid WSGI application.
       """
       config = Configurator(settings=settings, root_factory=root_factory)
       config.include('substanced')
       config.include('sdexternaledit')
       ... and so on ...

Once you've done this and you've restarted your Substance D process, you will
see "pencil icons" appear next to each Substance D ``File`` object in your
site.  Clicking on one will cause a derivation of that file to be downloaded
with the ``application/x-zope-edit`` browser content type.  The derivation of
the file will include some headers at its start, and the remainder of the file
body (binary or text) after the headers.  In addition to having the
``application/x-zope-edit`` mimetype, the downloaded file derivation will
always start with the line ``application:zopeedit``.

How your operating system actually invokes the client portion of external
editor is OS-dependent, but all OS implementations make use of either the
``application/x-zope-edit`` content type or the fact that the file starts with
the line ``application:zopeedit`` to detect that the zope editor client should
be started when the file is downloaded.

Ubuntu 12.04 Client Installation Directions
-------------------------------------------

Download the ``zopeedit.py`` program:

.. code-block:: text

   $ wget http://svn.zope.org/*checkout*/Products.ExternalEditor/trunk/zopeedit.py?rev=67548

Make the resulting ``zopeedit.py`` program executable:

.. code-block:: text

   $ chmod 755 zopeedit.py

Copy the ``zopeedit.py`` file into your local user's ``/home/username/bin``
directory:

.. code-block:: text

   $ mkdir -p ~/bin
   $ cp zopeedit.py ~/bin

Run zopeedit.py once with a single bogus filename as an argument. This will
cause the program to generate a configuration file in
``~/.zope-external-edit``.

.. code-block:: text

   $ zopeedit.py foo

It will throw an error.  Ignore the error.  Edit the resulting
``~/.zope-external-edit`` file and uncomment the ``editor =`` line, setting it
to whatever your preferred text editor is.

.. code-block:: text

   # Uncomment and specify an editor value to override the editor
   # specified in the environment
   editor = emacs

You can change other options in that file as you like.  One help for debugging
things is setting ``cleanup_files = 0``.  This will cause external editor to
not delete the original file location it's editing, so that you can use
``zopeedit.py foo.bar`` to test that things are working without destroying
``foo.bar`` when that command is invoked.  Once you have things working,
however, it's a good idea to set it back to ``cleanup_files = 1``.

Now it's time to get your desktop environment set up so that it knows to launch
external editor from your browser when it downloads the file resulting from a
click of the pencil icon in the SDI.  Create a file named ``zopeedit.desktop``
in ``~/.local/share/applications`` with the fillowing content:

.. code-block:: text

   [Desktop Entry]
   Version=1.0
   Name=Zope External Editor
   GenericName=Zope External Editor
   Comment=View and edit files using Zope External Editor
   MimeType=application/x-zope-edit;
   Exec=/home/chrism/bin/zopeedit.py %f
   Icon=/usr/share/icons/gnome/48x48/apps/zen-icon.png
   Type=Application
   Terminal=false
   Categories=Utility;Development;TextEditor;

Create a new file at ``/usr/share/mime/packages/zopeedit.xml`` with the
following contents (this will require root privilege):

.. code-block:: xml

   <?xml version="1.0" encoding="utf-8"?>
   <mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
     <mime-type type="application/x-zope-edit">
       <comment>Zope external editor</comment>
       <glob pattern="*.zem"/>
       <magic priority="100">
         <match value="application:zopeedit" type="string" offset="0"/>
       </magic>
     </mime-type>
   </mime-info>

Run the following commands (the first will require root privilege):

.. code-block:: text

   $ sudo update-desktop-database && sudo update-mime-database /usr/share/mime
   $ xdg-mime install --novendor /usr/share/mime/packages/zopeedit.xml
   $ xdg-mime default zopeedit.desktop application/x-zope-edit

Restart your browser.  Now when you click on the pencil icon next to any
``File`` in the SDI, your preferred text editor should launch.  If it doesn't,
start debugging.  If it does, changes made to the file will be posted back to
the server every second or so.

Adding Pencil Icons For Custom Content Types
--------------------------------------------

Out of the box, ``sdexternaledit`` only puts pencil icons next to Substanced
``File`` types.  You can jigger things so that it will also put pencil icons
next to your custom types too.

XXX flesh out

Reporting Bugs / Development Versions
-------------------------------------

Visit http://github.com/Pylons/sdexternaledit to download development or
tagged versions.

Visit http://github.com/Pylons/sdexternaledit/issues to report bugs.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

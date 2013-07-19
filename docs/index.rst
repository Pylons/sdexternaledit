sdexternaledit
==============

Overview
--------

:mod:`sdexternaledit` is a package which provides Zope External Editor
capabilities to Substance D.  Zope External Editor is a client program which
allows you to edit text and binary files served by web servers in OS-native
editors by clicking on an icon in the web UI.

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
always start with the line ``application:zopeedit`` and will have an extension
of ``.zem``.

How your operating system actually invokes the client portion of external
editor is browser-dependent as well as OS-dependent, but all OS implementations
make use of either the ``application/x-zope-edit`` content type or the fact
that the file starts with the line ``application:zopeedit`` or the fact that
the downloaded file is suffixed with a ``.zem`` extension to detect that the
zope editor client should be started when the file is downloaded.

Ubuntu 12.04 Client Installation Directions
-------------------------------------------

Easy install the ``collective.zopeedit`` program into a convenient Python
2 installation on your system:

.. code-block:: text

   $ easy_install collective.zopeedit

Make a link from your Python's ``bin/zopeedit`` file into your local user's
``/home/username/bin`` directory:

.. code-block:: text

   $ mkdir -p ~/bin
   $ ln -s /path/to/my/python/bin/zopeedit ~/bin

Run zopeedit once without any arguments as an argument. This will cause the
program to generate a configuration file in
``~/.config/collective.zopeedit/ZopeEdit.ini``.

.. code-block:: text

   $ zopeedit

Edit the resulting ``~/.config/collective.zopeedit/ZopeEdit.ini`` file and
uncomment the ``editor =`` line, setting it to whatever your preferred text
editor is.

.. code-block:: text

   # Uncomment and specify an editor value to override the editor
   # specified in the environment
   editor = emacs

You can change other options in that file as you like.  One help for debugging
things is setting ``cleanup_files = 0``.  This will cause external editor to
not delete the original file location it's editing, so that you can use
``zopeedit foo.bar`` to test that things are working without destroying
``foo.bar`` when that command is invoked.  Once you have things working,
however, it's a good idea to set it back to ``cleanup_files = 1``.

You can also choose not to set the ``editor`` value, and let your operating
system figure out which editor to use when you click on a pencil icon.  In
practice, this may have undesirable effects if the process invoked by the edit
helper returns before the editing session is complete (e.g. if the process
invokes another process in the background, then quits).  You can alternately
set an editor per content-type in the ZopeEdit.ini file as per the
``collective.zopeedit`` documentation.

Now it's time to get your desktop environment set up so that it knows to launch
external editor from your browser when it downloads the file resulting from a
click of the pencil icon in the SDI.  Create a file named ``zopeedit.desktop``
in ``~/.local/share/applications`` with the following content:

.. code-block:: text

   [Desktop Entry]
   Version=1.0
   Name=Zope External Editor
   GenericName=Zope External Editor
   Comment=View and edit files using Zope External Editor
   MimeType=application/x-zope-edit;
   Exec=/home/chrism/bin/zopeedit %f
   Icon=/usr/share/icons/gnome/48x48/apps/zen-icon.png
   Type=Application
   Terminal=false
   Categories=Utility;Development;TextEditor;

Create a new file at ``~/zopeedit.xml`` with the following contents:

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

Run the following commands:

.. code-block:: text

   $ xdg-mime install --novendor ~/zopeedit.xml
   $ xdg-mime default zopeedit.desktop application/x-zope-edit
   $ update-desktop-database
   $ update-mime-database ~/.local/share/mime

Restart your browser.  Now when you click on the pencil icon next to any
textlike ``File`` in the SDI, your preferred text editor should launch with the
content in the file.  If it doesn't, start debugging.  If it does, changes made
to the file will be posted back to the server every second or so.

Adding Pencil Icons For Custom Content Types
--------------------------------------------

Out of the box, ``sdexternaledit`` only puts pencil icons next to Substanced
``File`` types.  You can jigger things so that it will also put pencil icons
next to your custom types too.  You'll need to create an adapter, which is a
class with a constructor that accepts two arguments (``context`` and
``request``).  The ``context`` will be an instance of your custom class.  The
class must also implement ``get`` and ``put`` methods, which will be called by
sdexternaledit to retrieve the editable content, and to save it, respectively.

.. code-block:: python

   class MyContentClass(Persistent):
       """ A custom content class """
       def __init__(self, data):
           """ Data should be unicode """
           self.data = data

   class MyContentClassAdapter(object):
       def __init__(self, context, request):
           self.context = context
           self.request = request

       def get(self):
           """ Return a tuple of iterable-of-bytes, mimetype. """
           return (
               [self.context.data.encode('utf-8')],
               self.context.mimetype,
               )
  
       def put(self, fp):
           """ Change the context using the file object ``fp`` passed in. """
           self.context.data = fp.read().decode('utf-8')

Then in the configuration stage, after including ``sdexternaledit`` into the
configuration, you can use the ``register_edit_adapter`` method of the
Configurator to associate the adapter with the content class:

.. code-block:: python

   config.include('sdexternaledit')
   config.register_edit_adapter(MyContentClassAdapter, MyContentClass)

Instead of using a class argument as the 2nd arg to ``register_edit_adapter``,
you can also use an interface.

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

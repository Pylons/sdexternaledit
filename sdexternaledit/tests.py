import unittest
from pyramid import testing

class TestExternalEditorViews(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, context, request):
        from . import ExternalEditorViews
        return ExternalEditorViews(context, request)

    def test_get_no_adapter(self):
        from pyramid.httpexceptions import HTTPNotFound
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        response = inst.get()
        self.assertEqual(response.__class__, HTTPNotFound)
        
    def test_get_no_existing_locks(self):
        from zope.interface import Interface
        from . import IEdit
        self.config.add_route('abc', '/')
        adapter = DummyEditAdapter((['abc'], 'application/foo'))
        self.config.registry.registerAdapter(
            adapter, (Interface, Interface), IEdit
            )
        context = testing.DummyResource()
        context.__name__ = 'fred'
        request = testing.DummyRequest()
        request.registry.content = DummyContentRegistry()
        request.matched_route = DummyRoute('abc')
        request.environ['HTTP_COOKIE'] = 'a=1'
        request.user = testing.DummyResource()
        inst = self._makeOne(context, request)
        inst.could_lock_resource = lambda *arg: True
        inst.discover_resource_locks = lambda *arg: []
        response = inst.get()
        self.assertEqual(
            list(response.app_iter),
            [b'application:zopeedit\n',
             b'borrow_lock:1\n',
             b'content_type:application/foo\n',
             b'cookie:a=1\n',
             b'meta_type:File\n',
             b'title:fred\n',
             b'url:http://example.com/\n',
             b'\n',
             'abc']
            )
        self.assertEqual(response.content_type, 'application/x-zope-edit')
        self.assertEqual(
            response.headers['Content-Disposition'],
            'attachment; filename*="fred.zem"; filename="fred.zem"'
            )

    def test_get_with_existing_locks(self):
        from zope.interface import Interface
        from . import IEdit
        self.config.add_route('abc', '/')
        adapter = DummyEditAdapter((['abc'], 'application/foo'))
        self.config.registry.registerAdapter(
            adapter, (Interface, Interface), IEdit
            )
        context = testing.DummyResource()
        context.__name__ = 'fred'
        request = testing.DummyRequest()
        request.registry.content = DummyContentRegistry()
        request.matched_route = DummyRoute('abc')
        request.environ['HTTP_COOKIE'] = 'a=1'
        request.user = testing.DummyResource()
        inst = self._makeOne(context, request)
        inst.could_lock_resource = lambda *arg: True
        lock1 = testing.DummyResource()
        lock1.__name__ = 'lock1' 
        inst.discover_resource_locks = lambda *arg: [lock1]
        response = inst.get()
        self.assertEqual(
            list(response.app_iter),
            [b'application:zopeedit\n',
             b'borrow_lock:1\n',
             b'content_type:application/foo\n',
             b'cookie:a=1\n',
             b'lock-token:lock1\n',
             b'meta_type:File\n',
             b'title:fred\n',
             b'url:http://example.com/\n',
             b'\n',
             'abc']
            )
        self.assertEqual(response.content_type, 'application/x-zope-edit')
        self.assertEqual(
            response.headers['Content-Disposition'],
            'attachment; filename*="fred.zem"; filename="fred.zem"'
            )

    def test_lock_with_lock_error(self):
        from pyramid.httpexceptions import HTTPPreconditionFailed
        from substanced.locking import LockError
        context = testing.DummyResource()
        context.__name__ = 'fred'
        request = testing.DummyRequest()
        request.user = testing.DummyResource()
        inst = self._makeOne(context, request)
        def raiser(_context, user, timeout):
            self.assertEqual(context, _context)
            self.assertEqual(user, request.user)
            self.assertEqual(timeout, 86400)
            raise LockError(None)
        inst.lock_resource = raiser
        response = inst.lock()
        self.assertEqual(response.__class__, HTTPPreconditionFailed)

    def test_lock_gardenpath(self):
        context = testing.DummyResource()
        context.__name__ = 'fred'
        request = testing.DummyRequest()
        request.user = testing.DummyResource()
        inst = self._makeOne(context, request)
        lock = testing.DummyResource()
        lock.__name__ = 'lock'
        def locker(_context, user, timeout):
            self.assertEqual(context, _context)
            self.assertEqual(user, request.user)
            self.assertEqual(timeout, 86400)
            return lock
        inst.lock_resource = locker
        response = inst.lock()
        self.assertEqual(response.text, ' >opaquelocktoken:lock<')

    def test_unlock_with_unlock_error(self):
        from pyramid.httpexceptions import HTTPPreconditionFailed
        from substanced.locking import UnlockError
        context = testing.DummyResource()
        context.__name__ = 'fred'
        request = testing.DummyRequest()
        request.user = testing.DummyResource()
        inst = self._makeOne(context, request)
        def raiser(_context, user):
            self.assertEqual(context, _context)
            self.assertEqual(user, request.user)
            raise UnlockError(None)
        inst.unlock_resource = raiser
        response = inst.unlock()
        self.assertEqual(response.__class__, HTTPPreconditionFailed)

    def test_unlock_gardenpath(self):
        context = testing.DummyResource()
        context.__name__ = 'fred'
        request = testing.DummyRequest()
        request.user = testing.DummyResource()
        inst = self._makeOne(context, request)
        def unlocker(_context, user):
            self.assertEqual(context, _context)
            self.assertEqual(user, request.user)
        inst.unlock_resource = unlocker
        response = inst.unlock()
        self.assertEqual(response.text, 'OK')

    def test_put_no_adapter(self):
        from pyramid.httpexceptions import HTTPNotFound
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        response = inst.put()
        self.assertEqual(response.__class__, HTTPNotFound)
        
    def test_put_gardenpath(self):
        from io import BytesIO
        from zope.interface import Interface
        from . import IEdit
        context = testing.DummyResource()
        request = testing.DummyRequest()
        body_file = BytesIO()
        request.body_file = body_file
        adapter = DummyEditAdapter(None)
        self.config.registry.registerAdapter(
            adapter, (Interface, Interface), IEdit
            )
        inst = self._makeOne(context, request)
        response = inst.put()
        self.assertEqual(adapter.fp, body_file)
        self.assertEqual(response.text, 'OK')

class TestFileEdit(unittest.TestCase):
    def _makeOne(self, context, request):
        from . import FileEdit
        return FileEdit(context, request)

    def test_get_context_has_mimetype(self):
        context = testing.DummyResource()
        context.mimetype = 'application/foo'
        blob = testing.DummyResource()
        here = __file__
        def committed():
            return here
        blob.committed = committed
        context.blob = blob
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        iterable, mimetype = inst.get()
        self.assertEqual(mimetype, 'application/foo')
        self.assertEqual(type(next(iterable)), bytes)

    def test_get_context_has_no_mimetype(self):
        context = testing.DummyResource()
        context.mimetype = None
        blob = testing.DummyResource()
        here = __file__
        def committed():
            return here
        blob.committed = committed
        context.blob = blob
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        iterable, mimetype = inst.get()
        self.assertEqual(mimetype, 'application/octet-stream')
        self.assertEqual(type(next(iterable)), bytes)

    def test_put(self):
        context = testing.DummyResource()
        fp = 'fp'
        def upload(_fp):
            self.assertEqual(_fp, fp)
        context.upload = upload
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.put(fp)

class TestFolderContentsWithEditIcon(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, context, request):
        from . import FolderContentsWithEditIcon
        return FolderContentsWithEditIcon(context, request)

    def test_get_columns_resource_is_None(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        def metadata(rsrc, name, default=None):
            return None
        content = DummyContentRegistry(metadata=metadata)
        request.registry.content = content
        request.sdiapi = DummySDIAPI()
        inst = self._makeOne(context, request)
        columns = inst.get_columns(None)
        self.assertEqual(columns, [])
        
    def test_get_columns_resource_is_not_None_no_adapter(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        def metadata(rsrc, name, default=None):
            return None
        content = DummyContentRegistry(metadata=metadata)
        request.registry.content = content
        request.sdiapi = DummySDIAPI()
        inst = self._makeOne(context, request)
        columns = inst.get_columns(context)
        self.assertEqual(columns, [])

    def test_get_columns_resource_is_not_None_with_adapter(self):
        from zope.interface import Interface
        from . import IEdit
        context = testing.DummyResource()
        request = testing.DummyRequest()
        def metadata(rsrc, name, default=None):
            return default
        content = DummyContentRegistry(metadata=metadata)
        request.registry.content = content
        request.sdiapi = DummySDIAPI()
        adapter = DummyEditAdapter(None)
        self.config.registry.registerAdapter(
            adapter, (Interface, Interface), IEdit
            )
        self.config.add_route('sdexternaledit', '/')
        inst = self._makeOne(context, request)
        columns = inst.get_columns(context)
        self.assertTrue('icon-pencil' in columns[0]['value'])
        
class DummyRoute(object):
    def __init__(self, name):
        self.name = name
        
class DummyContentRegistry(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
        
    def typeof(self, context):
        return 'File'

class DummyEditAdapter(object):
    def __init__(self, result):
        self.result = result

    def __call__(self, *arg):
        return self

    def get(self):
        return self.result

    def put(self, fp):
        self.fp = fp

class DummySDIAPI(object):
    def mgmt_path(self, *arg, **kw):
        return '/manage'
    

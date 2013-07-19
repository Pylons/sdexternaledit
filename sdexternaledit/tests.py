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

class DummyRoute(object):
    def __init__(self, name):
        self.name = name
        
class DummyContentRegistry(object):
    def typeof(self, context):
        return 'File'

class DummyEditAdapter(object):
    def __init__(self, result):
        self.result = result

    def __call__(self, *arg):
        return self

    def get(self):
        return self.result

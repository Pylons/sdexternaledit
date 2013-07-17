import itertools
from zope.interface import Interface
from pyramid.response import Response
from pyramid.traversal import resource_path_tuple
from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPPreconditionFailed,
    HTTPNotFound,
    )
from substanced.locking import (
    could_lock_resource,
    discover_resource_locks,
    LockError,
    UnlockError,
    lock_resource,
    unlock_resource,
    )
from substanced.util import chunks
from substanced.interfaces import IFile
from substanced.sdi.views.folder import FolderContents

class IEdit(Interface):
    pass

class ExternalEditorViews(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(
        route_name='sdexternaledit',
        request_method='GET',
        permission='sdi.edit-properties',
        http_cache=0,
        )
    def get(self):
        request = self.request
        context = self.context
        adapter = request.registry.queryMultiAdapter((context, request), IEdit)
        if adapter is None:
            return HTTPNotFound()
        body, mimetype = adapter.get()
        headers = {}
        headers['url'] = request.current_route_url()
        headers['meta_type'] = str(request.registry.content.typeof(context))
        headers['title'] = context.__name__
        headers['content_type'] = mimetype
        headers['cookie'] = request.environ.get('HTTP_COOKIE', '')
        headers['borrow_lock'] = str(
            could_lock_resource(context, request.user) and 1 or 0
            )
        locks = discover_resource_locks(context)
        if locks:
            lock = locks[0]
            headers['lock-token'] = lock.__name__

        headerlist = ['%s:%s\n' % (k, v) for k, v in sorted(headers.items())]
        headerlist.insert(0, 'application:zopeedit\n') 
        # Rationale for inserting "application:zopeedit" at position zero in
        # file: it can be used for desktop environment magic file detection.
        #
        # The browser's content-type is ignored in systems like Chromium, which
        # delegate to xdg-open to figure out the application to open.  xdg-open
        # isn't provided the browser content-type at all, and dead reckons
        # using the shared mime info provided by the OS, which is why we have
        # to register it here.
        #
        # The value of "application:zopeedit" is not used by the client at all,
        # but it is compatible with the format expected by the client.
        headerlist = [x.encode('utf-8') for x in headerlist]
        if request.params.get('skip_data'):
            return Response(app_iter=headerlist)
        app_iter = itertools.chain(headerlist, (b'\n',), body)
        response = Response(
            app_iter=app_iter,
            content_type='application/x-zope-edit'
            )
        return response

    @view_config(
        route_name='sdexternaledit',
        request_method='LOCK',
        permission='sdi.lock',
        http_cache=0,
        )
    def lock(self):
        try:
            lock = lock_resource(self.context, self.request.user)
        except LockError:
            return HTTPPreconditionFailed()
        return Response(' >opaquelocktoken:%s<' % lock.__name__)

    @view_config(
        route_name='sdexternaledit',
        request_method='UNLOCK',
        permission='sdi.lock',
        http_cache=0,
        )
    def unlock(self):
        try:
            unlock_resource(self.context, self.request.user)
        except UnlockError:
            return HTTPPreconditionFailed()
        return Response('OK')

    @view_config(
        route_name='sdexternaledit',
        request_method='PUT',
        permission='sdi.edit-properties',
        http_cache=0,
        )
    def put(self):
        request = self.request
        context = self.context
        adapter = request.registry.queryMultiAdapter((context, request), IEdit)
        if adapter is None:
            return HTTPNotFound()
        adapter.put(request.body_file)
        return Response('OK')

class FileEdit(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        return (
            chunks(open(self.context.blob.committed(), 'rb')),
            self.context.mimetype or 'application/octet-stream',
            )

    def put(self, fp):
        self.context.upload(fp)

class FolderContentsWithEditIcon(FolderContents):
    def get_columns(self, resource):
        columns = FolderContents.get_columns(self, resource)
        if resource is not None:
            adapter = self.request.registry.queryMultiAdapter(
                (resource, self.request), IEdit)
            if adapter is not None:
                for column in columns:
                    if column['name'] == 'Name':
                        if column['formatter'] == 'html':
                            url = self.request.route_url(
                                'sdexternaledit',
                                traverse=resource_path_tuple(resource)[1:]
                                )
                            value = (' <a href="%s"><i class="icon-pencil">'
                                     '</a></i>' % url)
                            column['value'] = column['value'] + value
                        break
        return columns
        
def includeme(config): # pragma: no cover
    config.includepath = ('substanced:includeme',)
    # I am sorry for the above hack.  But it means that the statements
    # (oparticularly the add_folder_contents_views statement) made in this
    # includeme will not conflict with (otherwise conflicting) statements made
    # via config.include('substanced').  We want to override the default
    # folder contents views, and the only other way to do that is to document
    # that the user should config.commit() before including this package,
    # which is awkward to document.  Maybe we can find a better way in the
    # future.
    prefix = config.registry.settings.get(
        'sdexternaledit.prefix', '/externaledit')
    non_slash_appended = prefix.rstrip('/')
    config.add_route(
        'sdexternaledit',
        pattern='%s/*traverse' % non_slash_appended
        )
    config.add_folder_contents_views(cls=FolderContentsWithEditIcon)
    config.registry.registerAdapter(FileEdit, (IFile, Interface), IEdit)
    config.scan()


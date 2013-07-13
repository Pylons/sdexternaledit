import itertools
from zope.interface import Interface
from pyramid.response import Response
from pyramid.view import view_config
from substanced.locking import (
    could_lock_resource,
    discover_resource_locks,
    )
from substanced.util import chunks

class IEdit(Interface):
    pass

@view_config(
    route_name='sdexternaledit',
    request_method='GET',
    permission='sdi.edit-properties',
    http_cache=0,
    )
def edit(context, request):
    adapter = request.registry.queryAdapter(context, IEdit)
    if adapter is None:
        adapter = FileEdit(context)
    body, mimetype = adapter()
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

    headerlist = ['%s: %s\n' % (k, v) for k, v in sorted(headers.items())]
    headerlist = [x.encode('utf-8') for x in headerlist]
    if request.params.get('skip_data'):
        return Response(app_iter=headerlist)
    app_iter = itertools.chain(headerlist, ('\n',), body)
    response = Response(
        app_iter=app_iter,
        content_type='application/x-zope-edit'
        )
    return response

class FileEdit(object):
    def __init__(self, context):
        self.context = context

    def __call__(self):
        return (
            chunks(open(self.context.blob.committed(), 'rb')),
            self.context.mimetype or 'application/octet-stream',
            )
    
def includeme(config):
    prefix = config.registry.settings.get(
        'sdexternaledit.prefix', '/externaledit')
    non_slash_appended = prefix
    while non_slash_appended.endswith('/'):
        non_slash_appended = non_slash_appended[:-1]
    config.add_route('sdexternaledit',
                     pattern='%s/*traverse' % non_slash_appended)
    config.scan()

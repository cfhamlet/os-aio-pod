from asyncio import Task


class BeanContext(object):
    def __init__(self, pod, id, label=None, **kwargs):
        self.id = id
        self.label = label
        self.pod = pod
        self.kwargs = kwargs
        self.instance = None


class Bean(Task):

    def __init__(self, context, coro, *, loop=None):
        super().__init__(coro, loop=loop)
        self.context = context

    @property
    def id(self):
        return self.context.id

    @property
    def label(self):
        return self.context.label

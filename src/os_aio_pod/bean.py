from asyncio import Task


class BeanContext(object):
    def __init__(self, pod, id, label=None):
        self.id = id
        self.label = label
        self.pod = pod
        self.instance = None


class Bean(Task):

    def __init__(self, context, coro, *, loop=None):
        super(Bean, self).__init__(coro, loop=loop)
        self.context = context

    def _repr_info(self):
        info = super(Bean, self)._repr_info()
        info.append(f'{self.id}-{self.label}')
        return info

    @property
    def id(self):
        return self.context.id

    @property
    def label(self):
        return self.context.label

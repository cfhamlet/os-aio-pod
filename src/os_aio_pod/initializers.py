import abc


class Initializer(abc.ABC):

    @abc.abstractmethod
    def init(self, pod, config):
        pass


class InitLoop(Initializer):

    def init(self, config, pod):
        pass


class InitLog(Initializer):

    def init(self, config, pod):
        pass


class InitBeans(Initializer):

    def init(self, config, pod):
        pass


class InitDebug(Initializer):

    def init(self, config, pod):
        pass


class InitSignal(Initializer):

    def init(self, config, pod):
        pass

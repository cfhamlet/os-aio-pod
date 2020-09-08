import os
import warnings

try:
    from uvicorn.config import Config
    from uvicorn.main import Server as BaseServer
except:
    warnings.warn("Should install uvicorn first!")
    raise


class Server(BaseServer):
    def __init__(self, config, context):
        super(Server, self).__init__(config)
        self.context = context

    async def run(self):
        await self.serve()

    async def serve(self):
        process_id = os.getpid()

        config = self.config
        if not config.loaded:
            config.load()

        app = config.loaded_app
        if hasattr(app, "app"):
            app = getattr(app, "app")
        app.aio_pod_context = self.context

        self.logger = config.logger_instance
        self.lifespan = config.lifespan_class(config)

        await self.install_signal_handlers()

        self.logger.info(f"Started server process [{process_id}]")
        await self.startup()
        await self.main_loop()
        await self.shutdown()
        self.logger.info(f"Finished server process [{process_id}]")

    async def install_signal_handlers(self):
        for sig in ("SIGINT", "SIGTERM"):
            await self.context.add_signal_handler(sig, self.handle_exit)

    def handle_exit(self, **kwargs):
        if self.should_exit:
            self.force_exit = True
        else:
            self.should_exit = True


class UvicornAdapter(object):
    def __init__(self, context):
        self.context = context

    async def __call__(self, **kwargs):
        kwargs.pop("loop", None)
        app = kwargs.pop("app")
        config = Config(app, **kwargs)
        server = Server(config=config, context=self.context)

        await server.run()

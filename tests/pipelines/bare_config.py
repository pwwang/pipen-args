# Can add arbitrary config items
from pipen import Pipen, Proc
from pipen_args import config


class process(Proc):
    ...


pipeline = Pipen(desc='Pipeline description.').set_start(process)
pipeline.config["a"] = config.get("a", 10)

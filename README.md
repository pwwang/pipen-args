# pipen-args

Command line argument parser for [pipen][1]

## Usage

```python
from pipen import Proc, Pipen
# Note that unlike other plugins, you need to import install
# to activate the plugin
from pipen_args import install  # noqa: F401

class Process(Proc):
    """My process

    Input:
        a: Input data
    """
    input = 'a'
    input_data = range(10)
    script = 'echo {{in.a}}'

Pipen().set_start(Process).run()
```

```shell
$ python example.py --help
Usage: test.py [-h | -h+] [options]

Undescribed process.
Use `@configfile` to load default values for the options.

Pipeline Options:
  --name NAME           The name for the pipeline, will affect the default workdir and
                        outdir. [default: pipen-0]
  --profile PROFILE     The default profile from the configuration to run the pipeline.
                        This profile will be used unless a profile is specified in the
                        process or in the .run method of pipen. You can check the
                        available profiles by running `pipen profile`
  --outdir OUTDIR       The output directory of the pipeline [default: ./<name>_results]
  --forks FORKS         How many jobs to run simultaneously by the scheduler
  --scheduler SCHEDULER
                        The scheduler to run the jobs

Namespace <in>:
  --in.a A [A ...]      Input data

Optional Arguments:
  -h, --help, -h+, --help+
                        show help message (with + to show more options) and exit
```

See more examples in `tests/pipelines/` folder.

[1]: https://github.com/pwwang/pipen

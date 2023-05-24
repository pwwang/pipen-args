# pipen-args

Command line argument parser for [pipen][1]

## Usage

```python
from pipen import Proc, Pipen


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
  --outdir OUTDIR       The output directory of the pipeline [default: ./<name>-output]
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

## Plugin options

- `args_hide`: (process level) Hide the arguments in the help message. Default: `False`
- `args_group`: (pipeline level) The group name for the arguments. Default: `pipeline options`
- `args_flatten`: (pipeline level) Flatten the arguments in the help message when there is only one process in the pipeline. Default: `auto` (flatten if single process, otherwise not)


## Metadata for Proc envs items

The metadata in the docstring of env items determines how the arguments are defined.

```python
class Process(Proc):
    """My process

    # other docstring sections

    Envs:
        a (<metadata>): ...
    """
```

The metadata could be key-value pairs separated by `;`. The separator `:` or `=` is used to
separate the key and value. The value is optional. If the value is not specified, it
will be set to `True`. The keys are valid arguments of `argx.ArgumentParser.add_argument`, except that `hidden` will be interpreted as `show=False` in `argx.ArgumentParser.add_argument`. If the value of `choices` is not specified, the subkeys of the env item will be used as the choices.

[1]: https://github.com/pwwang/pipen

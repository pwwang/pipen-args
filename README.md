# pipen-args

Command line argument parser for [pipen][1]

## Usage
```python
from pipen import Proc, Pipen
from pipen_args import args

class Process(Proc):
    input = 'a'
    input_data = range(10)
    script = 'echo {{in.a}}'

Pipen().run(Process)
```

```
> python example.py --help

DESCRIPTION:
  Pipeline description.

USAGE:
  example.py [OPTIONS]

OPTIONAL OPTIONS:
  --profile <STR>                 - The default profile from the configuration
                                    to run the pipeline. This profile will be
                                    used unless a profile is specified in the
                                    process or in the .run method of pipen.
                                    Default: default
  --loglevel <AUTO>               - The logging level for the main logger, only
                                    takes effect after pipeline is initialized.
                                    Default: <from config>
  --cache [BOOL]                  - Whether enable caching for processes.
                                    Default: <from config>
  --dirsig <INT>                  - The depth to check the Last Modification
                                    Time of a directory.
                                    Since modifying the content won't change its
                                    LMT.
                                    Default: <from config>
  --error_strategy <CHOICE>       - How we should deal with job errors.
                                     - ignore: Let other jobs keep running.
                                    But the process is still failing when done.
                                     - halt: Halt the pipeline, other running
                                    jobs will be killed.
                                     - retry: Retry this job on the scheduler
                                    system.
                                    Default: <from config>
  --num_retries <INT>             - How many times to retry the job when failed.
                                    Default: <from config>
  --forks <INT>                   - How many jobs to run simultaneously by the
                                    scheduler.
                                    Default: <from config>
  --submission_batch <INT>        - How many jobs to submit simultaneously to
                                    the scheduler system.
                                    Default: <from config>
  --workdir <PATH>                - The workdir for the pipeline.
                                    Default: <from config>
  --scheduler <STR>               - The default scheduler.
                                    Default: <from config>
  --scheduler_opts <JSON>         - The default scheduler options. Will update
                                    to the default one.
                                    Default: <from config>
  --plugins <LIST>                - A list of plugins to only enabled or
                                    disabled for this pipeline.
                                    To disable plugins, use no:<plugin_name>
                                    Default: <from config>
  --plugin_opts <JSON>            - Plugin options. Will update to the default.
                                    Default: <from config>
  --template_opts <JSON>          - Template options. Will update to the
                                    default.
                                    Default: <from config>
  --outdir <PATH>                 - The output directory for the pipeline.
                                    Default: <from config>
  -h, --help                      - Print help information for this command
```

See more examples in `examples/` folder.

[1]: https://github.com/pwwang/pipen

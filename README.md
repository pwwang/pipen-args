# pipen-args

Command line argument parser for [pipen][1]

## Usage
```python
from pipen import Proc, Pipen
from pipen_args import params

class Process(Proc):
    input_keys = 'a'
    input = range(10)
    script = 'echo {{in.a}}'

Pipen(starts=Process).run()
```

```
> python example.py --help
11-04 11:46:08 I /main                        _____________________________________   __
               I /main                        ___  __ \___  _/__  __ \__  ____/__  | / /
               I /main                        __  /_/ /__  / __  /_/ /_  __/  __   |/ /
               I /main                        _  ____/__/ /  _  ____/_  /___  _  /|  /
               I /main                        /_/     /___/  /_/     /_____/  /_/ |_/
               I /main
               I /main                                     version: 0.0.1
               I /main
               I /main    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ pipeline-0 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
               I /main    ┃ Undescribed.                                                                 ┃
               I /main    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
               I /main    Enabled plugins: ['verbose', 'main-0.0.1', 'args-0.0.0']
               I /main    Loaded processes: 1

DESCRIPTION:
  Undescribed.

USAGE:
  example.py [OPTIONS]

OPTIONAL OPTIONS:
  --profile <STR>                 - The default profile from the configuration
                                    to run the pipeline. Default: default
                                    This profile will be used unless a profile
                                    is specified in the process or in the .run
                                    method of pipen.
  --loglevel <STR>                - The logging level for the main logger, only
                                    takes effect after pipeline is initialized.
                                    Default: debug
  --cache [BOOL]                  - Whether enable caching for processes.
                                    Default: True
  --dirsig <INT>                  - The depth to check the Last Modification
                                    Time of a directory. Default: 1
                                    Since modify the content of a directory
                                    won't change its LMT.
  --error_strategy <CHOICE>       - How we should deal with job errors.
                                    Default: ignore
                                     - ignore: Let other jobs keep running.
                                    But the process is still failing when done.
                                     - halt: Halt the pipeline, other running
                                    jobs will be killed.
                                     - retry: Retry this job on the scheduler
                                    system.
  --num_retries <INT>             - How many times to retry the job when failed.
                                    Default: 3
  --forks <INT>                   - How many jobs to run simultaneously on the
                                    scheduler system. Default: 1
  --submission_batch <INT>        - How many jobs to submit simultaneously to
                                    the scheduler system. Default: 8
  --workdir <PATH>                - The workdir for the pipeline.
                                    Default: ./.pipen
  --envs <JSON>                   - The env variables for template rendering.
                                    Default: {}
                                    Will update to the default one.
  --scheduler <STR>               - The default scheduler Default: local
  --scheduler_opts <JSON>         - The default scheduler options. Will update
                                    to the default one. Default: {}
  --plugins <LIST>                - A list of plugins to only enabled or
                                    disabled for this pipeline. Default: []
                                    To disable plugins, use no:<plugin_name>
  --plugin_opts <JSON>            - Plugin options. Will update to the default
                                    one. Default: {}
  --outdir <PATH>                 - The output directory for the pipeline.
                                    Default: ./pipeline-0-output
  -h, --help                      - Print help information for this command
```

[1]: https://github.com/pwwang/pipen

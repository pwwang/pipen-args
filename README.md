# pipen-args

Command line argument parser for [pipen][1]

## Usage
```python
from pipen import Proc, Pipen
from pipen_args import args as _

class Process(Proc):
    input = 'a'
    input_data = range(10)
    script = 'echo {{in.a}}'

Pipen().set_start(Process).run()
```

```
❯ python example.py --help

DESCRIPTION:
  Pipeline description.
  My process

USAGE:
  example.py --in.a list [OPTIONS]

OPTIONS FOR <Process>:
  --in.a <list>                   - [Required] Undescribed.

OPTIONAL OPTIONS:
  --config <path>                 - Read options from a configuration file in TOML. Default: None
  -h, --help                      - Print help information for this command
  --full                          - Show full options for this command

PIPELINE OPTIONS:
  --profile <str>                 - The default profile from the configuration to run the pipeline.
                                    This profile will be used unless a profile is specified in the
                                    process or in the .run method of pipen. Default: default
  --outdir <path>                 - The output directory of the pipeline
                                    Default: ./<name>_results
  --name <str>                    - The workdir for the pipeline. Default: <pipeline-defined>
  --scheduler <str>               - The scheduler to run the jobs. Default: local
```

See more examples in `examples/` folder.

[1]: https://github.com/pwwang/pipen

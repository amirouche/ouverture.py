# Usage

```
usage: ouverture.py [-h]
                    {init,whoami,add,get,show,translate,run,review,log,search,remote,migrate,validate,caller,refactor,compile}
                    ...

ouverture - Function pool manager

positional arguments:
  {init,whoami,add,get,show,translate,run,review,log,search,remote,migrate,validate,caller,refactor,compile}
                        Commands
    init                Initialize ouverture directory and config
    whoami              Get or set user configuration
    add                 Add a function to the pool
    get                 Get a function from the pool
    show                Show a function with mapping selection support
    translate           Add translation for existing function
    run                 Execute function interactively
    review              Recursively review function and dependencies
    log                 Show git-like commit log of pool
    search              Search and list functions by query
    remote              Manage remote repositories
    migrate             Migrate functions from v0 to v1
    validate            Validate v1 function structure
    caller              Find functions that depend on a given function
    refactor            Replace a dependency in a function
    compile             Compile function to standalone executable

options:
  -h, --help            show this help message and exit
```

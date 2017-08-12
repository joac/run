# Run 

Always run, zombies are coming!

## Usage 

Write your Runfile (check the example) syntax is similar to a Makefile 

run targets like this:

`run.py target_3`

Optionally, if you used the magic `{argv}` reference all extra arguments will be sent to that command 

Try `run.py target_4 "Hello world"` with the provided example 

## Notes

- Targets can have local scope variables
- All variables, local or global can be overriden by an environment variable
- Variables are not typed, everything is text 
- First line in a target between single or doble quotes are considered a docstring 

## Todo
- Autocompletion 
- Better parser 
- Print targets and docstrings when run is called without targets
- Support for pythons < `3.6`

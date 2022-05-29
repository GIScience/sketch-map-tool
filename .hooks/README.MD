# Pre-Commit Pipeline
This project contains [pre-commit hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) for *git* written in 
Python. If you set them up correctly, they will be executed everytime you try to commit changes to a git repo. If they 
fail, the commit is rejected. This allows to facilitate a high code quality already before your code enters a CI/CD 
pipeline.
  
## Contents
1. [How to install](#how-to-install)
2. [How to activate/deactivate a stage](#how-to-activatedeactivate-a-stage)
3. [How to add a stage](#how-to-add-a-stage)
4. [What do the stages do?](#what-do-the-stages-do)

## How to install
### General requirements
* **Python 3** (you need to be able to run `python --version` in your terminal/cmd)
* **git** (you can only use these scripts in a git repository)

### Adding the hook script
Git hooks are stored in each git repository under the folder `.git/hooks`. So the first thing you need to do is to copy 
the file `pre-commit` and the directory `pre_commit_stages` in this folder. It should look like this:  
```
.git/hooks/
|   some-script.sample (each git repo already contains examples for hook scripts)
|   ...
|   pre-commit   
|   ...
|-- pre_commit_stages/
|   |   pylint_requirements.txt
|   |   ...
|   |   stage_base.py
|   |   ...
```
The file `pre-commit` contains the main script getting the staged changes and running the actual pipeline. The 
files under `pre_commit_stages` contain the classes for the different stages as well as other resources necessary for 
them.  

### Requirements for the stages  
Depending on which stages you want to use, you also need the following:
* **ESLint**
  * [NodeJS](https://nodejs.org/) with the [npm CLI](https://docs.npmjs.com/cli/v8/commands/npm)
* **HTMLHint**
  * [NodeJS](https://nodejs.org/) with the [npm CLI](https://docs.npmjs.com/cli/v8/commands/npm)
* **StyleLint**
  * [NodeJS](https://nodejs.org/) with the [npm CLI](https://docs.npmjs.com/cli/v8/commands/npm)     
    

## How to activate/deactivate a stage
The main script `pre-commit` contains a variable `STAGES` where you can comment-out all stages you want to deactivate 
and un-comment the ones you want to activate. If you deactivate a stage, you can of course also comment-out the corresponding 
`import pre_commit_stages.stage_that_should_be_deactivated` statement. 


## How to add a stage
If you want to add a stage, you need to create a Python file `my_new_stage.py` under `pre_commit_stages/`.  
In this file, you create a class `MyNewStage(Stage)`, that inherits from the abstract class `stage_base.Stage`.
```
from pre_commit_stages.stage_base import Stage

class MyNewStage(Stage):
    pass
```
You need to implement the following methods/attributes:
* `file_formats` should be a public variable or a property containing a list of all file formats for which the stage 
  should be executed, e.g. `["html", "js", "css"]` if you want to run it for all files of one these formats. Note that 
  this is case-sensitive, so you might want to add `"HTML", "JS", "CSS"` as well.
* `__str__(self)` should return the name of this stage to be printed to the console for the user  
* `run(self)` should contain the actual script for this stage. With `self.files` you can get a list of the paths 
  (Strings) to all files with staged changes  
  
So your class could look like this:
```
from pre_commit_stages.stage_base import Stage


class MyNewStage(Stage):
    file_formats = ["html", "js", "css"]

    def run(self) -> None:
        for file in self.files:
            if file.split(".")[-1] in self.file_formats:
                print(f"Running MyNewStage for {file}")
                ...  # Your script
                has_failed = ...
                if has_failed:
                    raise Exception("MyNewStage detected problems")

    def __str__(self) -> str:
        return "MyNewStage"

```  
To get a better idea of how this could look like, you can take a look at the code of the existing stages under
`pre_commit_stages`.  
  
To actually add it to the pipeline, the last step would be to open `pre-commit`, to add the import of your class
```
from pre_commit_stages.my_new_stage import MyNewStage
```  
and to add it to `STAGES`, i.e.
```
STAGES: List[Type[Stage]] = [
    # ...    
    MyNewStage,
    # ...
]
```
## What do the stages do?
* **Pylint**
  * Create and activate a virtual Python environment
  * Install [Pylint](https://pylint.org/) there
  * Run it on modified Python files
* **Mypy**
  * Create and activate a virtual Python environment
  * Install [mypy](http://mypy-lang.org/) there
  * Run it on modified Python files
* **ESLint**
  * Install [ESLint](https://eslint.org/) with the airbnb-base-style
  * Run it on modified JavaScript files
* **HTMLHint**
  * Install [HTMLHint](https://htmlhint.com/)
  * Run it on modified HTML files  
* **StyleLint**
  * Install [stylelint](https://stylelint.io/) with the standard-config
  * Run it on modified CSS files      
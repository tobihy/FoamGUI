# FoamGUI
FoamGUI is a graphical user interface (GUI) for the creation of OpenFOAM case input files.

Open Field Operation And Manipulation, also commonly known as OpenFOAM, is an open-source C++ toolbox for the development of customized numerical solvers, and pre-/post-processing utilities for the solution of CFD problems. 

Due to the text-based nature of OpenFOAM input files, users who wish to edit existing cases or create new cases will have to edit the text files individually, which can be quite time-consuming. FoamGUI therefore helps simplify this process by providing a user-friendly GUI for the user to interact with and edit files within their cases. This alleviates the pain point of editing text files one by one, resulting in a smoother experience.

## Requirements
- [Python 3.8.10](https://www.python.org/downloads/) installed

## Installation (via internet)
If the deployment environment is connected to the internet, we can install the GUI by following the steps below.

1. [Clone](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) the github repo.
2. Navigate to the project root directory.
3. Install project requirements via CLI.
```bash
python -m pip install -r requirements.txt
```
4. Run the GUI.

### Windows
```shell
python app.py
```
### Linux/Ubuntu:

```bash
python3.8 app.py
```

## Installation (via executable)
If the deployment environment is not connected to the internet, download the executable under the releases.


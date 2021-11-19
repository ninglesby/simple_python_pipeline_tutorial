from json.decoder import JSONDecodeError
import pathlib
import json
import os
import sys
import argparse

def capture_input(label, default, data_type="str"):
    '''
    Captures User Input on the command line.
    label (str) - Description of what data to enter
    default (str|int) - If user doesn't enter anything return this value
    data_type (str) - Validate answer against expected data type.

    returns (str|int) - The input or default value
    '''

  
    print(label)
    answer = input("Press Enter to Accept Default("+str(default)+"): ")

    # removes any blank spaces so we can check if the string is blank
    if answer.strip() == "":
        # if the string is blank we return nothing
        return default
    else:
        # otherwise check to see if the integer is valid
        if data_type == "int":
            try:
                # if it doesn't error than it is valid
                return int(answer)
            except ValueError:
                # otherwise we warn the user and ask again
                print("Please Enter A Number")
                return capture_input(label, default, data_type)
    # if the expected data_type isn't int, we can just return an answer
    return answer

def walk_structure(root_object, context={}):
    '''
    Generator function recurses through the structure 
    schema formatting and yielding a dict with the path
    and the type of object at the path.

    root_object (dict) - A dictionary formatted in the structure_object schema
    context (dict) - A dictionary that contains values for path substitution.

    yields (dict) - A sparse stucture_object with only path, and type.
    '''
  
    # Use context dict to format string
    new_path = root_object["path"].format(**context)
    # Set parent path in the context to the current root path
    new_context = context.copy()
    new_context["parent_path"] = new_path
    # yield the object
    yield {"path":new_path, "type":root_object["type"]}
    # get children or an empty list iterate through
    for child in root_object.get("children", []):
        # pass the context and child object
        for item in walk_structure(child, new_context):
            yield item

def get_structure_object(fp):
    '''
    Loads stucture object from a file path

    fp (str) - The filepath of the JSON file
    returns (dict) - the structure object.
    '''
    # Just return empty dict if the file doesn't exist
    if not pathlib.Path(fp).exists():
        return {}
    # open and load the JSON file
    with open(fp, "r") as f:
        try:
            # return just the structure portion
            return json.load(f).get("structure", {})
        # fail gracefully if there is a JSON error
        except JSONDecodeError:
            print("Invalid JSON")
            return {}


def get_context_for_object(object, kwargs={}):
    '''
    Extracts required args from the stucture object and
    prompts users for their input.

    object (dict) - root structure object from the JSON file

    returns (dict) - context dict for string formatting
    '''
    # instantiate a dictionary to hold args
    if kwargs == None:
        kwargs = {}
    context = kwargs
    # iterate through arguments from the structure object
    for item in object.get("args", []):
        
        # check the supplied command line args for values. If they exists
        # we can skip asking the user
        if kwargs.get(item["name"]) == None:
            # set the key for the dictionary equal to the name of the arg
            # set the value equal to the either user input or the default value
            context[item["name"]] = capture_input(item["label"], item["default"], item["data_type"])
            print()
    return context

def create_directories(object, context):
    '''
    Iterate through a root structure object and create
    and make a directory for all object types that are
    a directory.

    object (dict) - root structure object
    context (dict) - dict for string formatting
    '''
    print("\nCreating Directories\n")
    print("-"*50)
    print("\n")

    directory_counter = 0
    # iterate over our generator function
    for item in walk_structure(object, context):
        # from the output of the function test if the type is a directory
        if item["type"] == "directory" or directory_counter == 0:
            # if it is make a directory 
            # parents = True will create any folders that need to be made above the folder
            # exists_ok = True just means it won't error out of the folder already exists
            print(item["path"])
            pathlib.Path(item["path"]).mkdir(parents=True, exist_ok=True)
            directory_counter += 1

    print("\nCreated {} Directories\n".format(directory_counter))
    print("-"*50)
    print("\n")

def get_structures(root_path):
    '''
    Searches a path for any folders that contain a json file
    and then accepts user input to select a JSON File

    root_path (str | pathlib.Path) - path to folder containing folders with 
                                    folder structure jsons

    returns (list) - returns a list of pathlib.Path objects.
    '''

    # convert root path to pathlib.Path object
    root_path = pathlib.Path(root_path)

    # create a list of any file that is in a subfolder and
    # ends with .json
    return [x for x in root_path.glob("*/*.json")]
def selector(options, title="Make A Selection", auto_return=True):
    '''
    List Options on the Command Line and return the user selection.

    options (list) - collection of objects that can be represented by a string.

    title (str) - title to display to the user

    auto_return (bool) - Don't bother prompting the user if there is only one option

    return - the value selected by the user
    '''

    # if auto return is enabled and there is only one option we just return the option
    if len(options) == 1 and auto_return:
        print("Selecting {}".format(options[0]))
        return options[0]

    print("\n{}\n".format(title))
    print("-"*25)

    # iterate through all the options and print them with a corresponding number
    for idx, s in enumerate(options):
        # add one so the user doesn't have to pick zero
        idx+=1
        print("{}. {}".format(idx, s))
    print("\n")

    # capture the user input
    idx = capture_input("Enter the Number of the Desired Option", 1, "int")
    print()
    # subtract 1 so it matches back up with the index
    idx -= 1

    try:
        # if the option exists we return it
        return options[idx]
    except IndexError:
        # if it doesn't we warn the user and re-ask
        print("Invalid Selection")
        selector(options, title)

def select_structure(structures):
    '''
    Takes a list of pathlib.Path objects displays them to a user and
    has them choose.

    structures (list) - List of pathlib.Path objects of .json files

    returns (str) - path to chosen .json object
    '''
    str_structures = [str(x) for x in structures]
    return selector(str_structures, "Select Structure Template")

def select_root(starting_path):
    '''
    From a starting path recursively scan for any existing root_info JSON
    files

    starting_path (str) - The path to start the search.

    returns (str) - path to root_info JSON file
    '''
    ignored_paths = ["$RECYCLE.BIN"]
    root_paths = []
    for x in pathlib.Path(starting_path).rglob("*root_info.json"):
        for p in ignored_paths:
            if not p in str(x):
                root_paths.append(str(x))

    return selector(root_paths, title="Select Root Structure")
    
def select_folder_type(structure_object):
    '''
    Select a type of folder from a structure object

    structure_object (dict) - A dictionary of a structure_object

    returns (str) - The key of the folder type dict for the structure_obect
    '''
    folder_types = [key for key, value in structure_object.items()]

    return selector(folder_types, "Select Folder Type")


def update_root_info(path, info={}):
    '''
    Updates or creates the information JSON at the root of the project directory

    path (str) - the filepath of the JSON file
    info (dict) - the dictionary that contains the data for the JSON file.

    return (dict) - The updated information.
    '''
    src_info = {}

    if pathlib.Path(path).exists():
        with open(path, "r") as f:
            try:
                src_info = json.load(f)
            except JSONDecodeError:
                pass
    
    if info != {}:
        src_info.update(info)

        with open(path, "w") as f:
            json.dump(src_info, f, indent=4)

    return src_info

def get_root_info(path):
    '''
    Gets the root_info for a file at the path.

    path (str) - Path to a root_info object

    returns (dict) - root_info object
    '''
    return update_root_info(path)


def get_root_info_path(root_object, context):
    '''
    Builds the path to store the JSON file for 
    the project

    root_object (dict) - root structure_object
    context (dict) - context object for the string formatting
    '''
    root_path = pathlib.Path(root_object["path"].format(**context))
    return str(pathlib.Path(root_path, root_path.name + "_root_info.json"))

def get_sparse_context(folder_object, context):
    '''
    Reduces a dictionary down to only the keys in another dictionary

    folder_object (dict) - dictionary of a folder object. It contains a list args
                            The name of the name value in the arg dictionary
                            corresponds to a key of the context.
    context (dict) - A simple dictionary of key value pairs.

    returns (dict) - a reduced version of the context only contain keys from the names
                    in the args of the folder object.
    '''
    sparse_context = {}

    for arg in folder_object.get("args", []):
        if context.get(arg["name"]):
            sparse_context[arg["name"]] = context.get(arg["name"])

    return sparse_context


def create_root_folders(fp=None, kwargs={}):
    '''
    Initialize a folder structure at a specific root.

    fp (str) - Filepath where to make the root folder.

    kwargs (dict) - Set of arguments to pass on to context. Any value
                    provided in the kwargs will be skipped in the user
                    interaction
    '''

    # This is used to determine if the python script has be compiled
    # into an executable. That way we get the proper base dir for 
    # each use case.
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # if a file path isn't provided we prompt the user
    if not fp:
        fp = select_structure(get_structures(pathlib.Path(base_dir, "folder_structures")))

    structure_object = get_structure_object(fp)
    root_object = structure_object.get("root", {})
    context = get_context_for_object(root_object, kwargs)


    create_directories(root_object, context)

    root_info = {
        "context":context,
        "structure":structure_object
    }

    update_root_info(get_root_info_path(root_object, context), root_info)

def add_folders_to_root(folder_type=None, root_path=None, kwargs={}):
    '''
    Adds folders to a root folder. For example adding shots, or assets to a project.

    folder_type (str) - The name of the type of folder to be created.

    root_path (str) - The path of the project the folders are being added to.

    kwargs (dict) - Set of arguments to pass on to context. Any value
                    provided in the kwargs will be skipped in the user
                    interaction  
    '''
    if kwargs == None:
        kwargs = {}
    if not root_path:
        print()
        root_path = capture_input("Enter Starting Path to Search for Root Folders.", default="C:")
    if not root_path.endswith(".json"):
        root_path = select_root(root_path)

    root_info = get_root_info(root_path)
    structure_object = root_info.get("structure", {})

    if not folder_type or folder_type not in [key for key, value in structure_object.items()]:
        folder_type = select_folder_type(structure_object)

    folder_object = structure_object[folder_type]
    context = root_info.get("context", {}).copy()
    context.update(kwargs)

    context = get_context_for_object(folder_object, context)

    for req in folder_object.get("requires", []):

        req_pk = structure_object[req]["primary_key"]

        if not req_pk in [x for x in context.keys()]:
            options = root_info.get(req, [])
            for idx, opt in enumerate(options):
                options[idx] = opt[req_pk]
            options.append("New {}".format(req.capitalize()))
            req_value = selector(options, title="Select {}".format(req.capitalize()), auto_return=False)

            if req_value == options[-1]:
                new_context = add_folders_to_root(folder_type=req, root_path=root_path, kwargs=context)
                context.update(new_context)
                print(json.dumps(context))
                return add_folders_to_root(folder_type=folder_type, root_path=root_path, kwargs=context)

            else:
                context[req_pk] = req_value
                




    create_directories(folder_object, context)

    items = root_info.get(folder_type, [])

    items.append(get_sparse_context(folder_object, context))

    root_info[folder_type] = items
    update_root_info(root_path, root_info)

    return context




class ParseKwargs(argparse.Action):
    '''
    Custom action for the argparse library. It taks any values after the flag
    and turns key=value pairs into diction entries.
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, dict())
        for value in values:
            key, value = value.split('=')
            getattr(namespace, self.dest)[key] = value

def cli():
    '''
    Handles command line arguments for the app.
    '''
    parser = argparse.ArgumentParser(
        description="Command Line Utility for Manager Folder Structures",
        prog="simple_folders")

    subparsers = parser.add_subparsers(dest="command")

    create_root = subparsers.add_parser("init", description="Initialize Folder Structure")
    create_root.add_argument("-p", "--path", required=False, help="Path to Folder Structure JSON Document")
    create_root.add_argument("-k", "--kwargs", nargs="*", action=ParseKwargs, required=False,  help="Use key=value pairs to pass arguments to folder creation")

    add_folders = subparsers.add_parser("add", description="Add Folders to Existing Folder Structure")
    add_folders.add_argument("-t", "--type", help="Type of Folder to Create.", required=False)
    add_folders.add_argument("-p", "--path", required=False, help="Path to Folder Structure Root")
    add_folders.add_argument("-k", "--kwargs", nargs="*", action=ParseKwargs, required=False, help="Use key=value pairs to pass arguments to folder creation")

    args = parser.parse_args()

    if args.command == "init":
        create_root_folders(args.path, args.kwargs)
    elif args.command == "add":
        add_folders_to_root(args.type, args.path, args.kwargs)
    else:
        parser.print_help()



if __name__ == "__main__":

    cli()


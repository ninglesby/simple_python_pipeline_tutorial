import subprocess
import pathlib
import os
import shutil

# When you move on versions you can change the values here
MAJOR_VERSION = 0
MINOR_VERSION = 1
# What the name of your app should be
APP_NAME = "simple_folder"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_build_version():
    '''
    If there is a BUILD_VERSION file in the directory it
    reads in the number and increments it by one so that each
    new build is a new number

    returns (int) - version number of build
    '''
    version = 0
    if pathlib.Path("BUILD_VERSION").exists():
        with open("BUILD_VERSION", "r") as f:
            version = int(f.read())
    version += 1

    with open("BUILD_VERSION", "w") as f:
        f.write(str(version))
    
    return version

def get_version(build_version):
    '''
    Formats version string
    '''
    return "{}.{}.{}".format(MAJOR_VERSION, MINOR_VERSION, str(build_version).zfill(3))

def build_command_list(version):
    '''
    This is the arg list to use with subprocess.
    More details about the commands can be found at 
    https://www.pyinstaller.org/
    '''
    cmds = ["pyinstaller"]
    cmds.append("simple_folder.py")
    cmds.append("--icon=icon.ico")
    cmds.append("--onefile")
    cmds.append("--name={}_{}".format(APP_NAME, version))
    
    return cmds

def build(version):
    '''
    Executes the build command
    '''
    for x in build_command_list(version):
        print(x)
    proc = subprocess.check_output(build_command_list(version))

def package(version):
    '''
    Copies files and neccesary folders from the project directory and build location
    into a builds folder
    '''
    name = "{}_{}".format(APP_NAME, version)

    exe_name = pathlib.Path(BASE_DIR, "dist", name+".exe")
    custom_dist_folder = pathlib.Path(BASE_DIR, "builds", name.replace(".", "_"))
    custom_dist_folder.mkdir(parents=True, exist_ok=True)

    exe_src = str(exe_name)
    exe_dst = str(pathlib.Path(custom_dist_folder, APP_NAME + ".exe"))

    folder_structure = pathlib.Path(BASE_DIR, "folder_structures")
    folder_structure_dst = pathlib.Path(custom_dist_folder, "folder_structures")
    shutil.move(exe_src, exe_dst)
    shutil.copytree(str(folder_structure), str(folder_structure_dst))
    
def cleanup():
    '''
    Removes artifacts from the build process
    '''
    # cleanup .spec
    for f in pathlib.Path(BASE_DIR).glob("*.spec"):
        f.unlink()
    # cleanup dist folder
    for f in pathlib.Path(BASE_DIR, "dist").rglob("*"):
        if f.is_file():
            f.unlink()
    shutil.rmtree(pathlib.Path(BASE_DIR, "dist"))
    # cleanup build folder
    for f in pathlib.Path(BASE_DIR, "build").rglob("*"):
        if f.is_file():
            f.unlink()
    shutil.rmtree(pathlib.Path(BASE_DIR, "build"))


if __name__ == '__main__':
    build_version = get_build_version()
    version = get_version(build_version)
    build(version)
    package(version)
    cleanup()
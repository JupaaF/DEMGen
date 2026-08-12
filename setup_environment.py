#/////////////////////////////////////////////////
__author__      = "Chengshun Shang (CIMNE)"
__copyright__   = "Copyright (C) 2023-present by Chengshun Shang"
__version__     = "1.0.1"
__maintainer__  = "Chengshun Shang"
__email__       = "cshang@cimne.upc.edu"
__status__      = "development"
__date__        = "Feb 23, 2026"
__license__     = "BSD 2-Clause License"
#/////////////////////////////////////////////////

import platform, os, re, sys, zipfile, subprocess

def setup_environment():
    # Get the absolute path to the directory containing this script
    base = os.path.dirname(os.path.abspath(__file__))
    system = platform.system()
    
    if system == "Windows":
        # Construct absolute paths
        kratos_path = os.path.abspath(os.path.join(base, "src", "external", "kratos_win", "Release"))
        libs_path = os.path.join(kratos_path, "libs")
        
        # Unzip the Kratos release if it exists
        kratos_zip_path = os.path.abspath(os.path.join(base, "src", "external", "kratos_win"))
        release_zip = os.path.join(kratos_zip_path, "Release.zip")
        if os.path.exists(release_zip):
            with zipfile.ZipFile(release_zip, 'r') as zip_ref:
                zip_ref.extractall(kratos_zip_path)
        
        # --- PERMANENTLY UPDATE PYTHONPATH (Windows) ---
        current_pp = os.environ.get("PYTHONPATH", "")
        if kratos_path not in current_pp:
            new_pp = f"{kratos_path};{current_pp}".strip(";")
            try:
                subprocess.run(['setx', 'PYTHONPATH', new_pp], check=True, capture_output=True)
                print(f"Success: {kratos_path} added to PYTHONPATH permanently.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to set PYTHONPATH: {e}")

        # --- PERMANENTLY UPDATE PATH (Windows) ---
        current_path = os.environ.get("Path", "")
        if libs_path not in current_path:
            new_path = f"{libs_path};{current_path}".strip(";")
            try:
                subprocess.run(['setx', 'Path', new_path], check=True, capture_output=True)
                print(f"Success: {libs_path} added to Path permanently.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to set Path: {e}")

        # Update current process memory
        os.environ["PYTHONPATH"] = f"{kratos_path};{os.environ.get('PYTHONPATH', '')}"
        os.environ["Path"] = f"{libs_path};{os.environ.get('Path', '')}"

    elif system == "Linux":
        # The Linux build is installed locally from the Kratos source tree.
        kratos_path = os.path.abspath(os.path.join(base, "external", "kratos_linux", "bin", "Release"))
        libs_path = os.path.join(kratos_path, "libs")

        if not os.path.isdir(kratos_path) or not os.path.isdir(libs_path):
            raise RuntimeError(
                "Linux Kratos build not found. Build it in "
                "external/kratos_linux/bin/Release before running this script."
            )
        
        # --- PERMANENTLY UPDATE .bashrc (Linux) ---
        bashrc = os.path.expanduser("~/.bashrc")
        begin_marker = "# >>> DEMGen Kratos environment >>>"
        end_marker = "# <<< DEMGen Kratos environment <<<"
        env_block = (
            f"\n{begin_marker}\n"
            f'export PYTHONPATH="{kratos_path}:$PYTHONPATH"\n'
            f'export LD_LIBRARY_PATH="{libs_path}:$LD_LIBRARY_PATH"\n'
            f"{end_marker}\n"
        )

        if os.path.exists(bashrc):
            with open(bashrc, "r") as f:
                bashrc_contents = f.read()
        else:
            bashrc_contents = ""

        marker_pattern = re.compile(
            rf"\n?{re.escape(begin_marker)}.*?{re.escape(end_marker)}\n?",
            re.DOTALL,
        )
        # Remove the malformed legacy line written by earlier Linux setup versions.
        bashrc_contents = re.sub(
            r"\n?# Kratos Environment Variables[^\n]*\n?",
            "\n",
            bashrc_contents,
        )
        bashrc_contents = marker_pattern.sub("\n", bashrc_contents).rstrip() + env_block

        try:
            with open(bashrc, "w") as f:
                f.write(bashrc_contents)
            print(f"Success: Kratos paths added to {bashrc} permanently.")
            print("Please run 'source ~/.bashrc' or restart your terminal.")
        except Exception as e:
            print(f"Failed to update .bashrc: {e}")

        # --- UPDATE CURRENT PROCESS MEMORY ---
        os.environ["PYTHONPATH"] = f"{kratos_path}:{os.environ.get('PYTHONPATH', '')}"
        os.environ["LD_LIBRARY_PATH"] = f"{libs_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"
    
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
    
    # Update sys.path for the current Python interpreter session
    if kratos_path not in sys.path:
        sys.path.insert(0, kratos_path)

setup_environment()

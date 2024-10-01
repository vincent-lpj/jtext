from .tools import JText
import importlib.util
import os
import subprocess
import sys

def _get_unidic_mecabrc_path():
    """
    Returns the path to the mecabrc file in the unidic package.
    """
    # Find the location of the unidic module
    unidic_spec = importlib.util.find_spec("unidic")
    if unidic_spec is None:
        raise ImportError("The unidic package is not installed.")
    
    # Get the directory where unidic is installed
    unidic_dir = os.path.dirname(unidic_spec.origin)
    
    # Path to the mecabrc file in unidic/dicdir/
    mecabrc_path = os.path.join(unidic_dir, "dicdir", "mecabrc")
    
    return mecabrc_path

def _is_unidic_downloaded():
    """
    Check if the mecabrc file exists in the unidic/dicdir/ directory.
    """
    mecabrc_path = _get_unidic_mecabrc_path()
    return os.path.exists(mecabrc_path)

def _download_unidic():
    """
    Run the unidic download command if the mecabrc file is missing.
    """
    try:
        print("Downloading unidic data...")
        subprocess.check_call([sys.executable, '-m', 'unidic', 'download'])
        print("Successfully downloaded unidic.")
    except subprocess.CalledProcessError:
        print("Failed to download unidic.", file=sys.stderr)
        sys.exit(1)

# Check and download unidic when the package is first used
if not _is_unidic_downloaded():
    _download_unidic()
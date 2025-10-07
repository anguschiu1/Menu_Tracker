import os
from typing import Optional

# Module-level variable that other modules import
folder: Optional[str] = None

def _detect_base_dir() -> str:
    try:
        if os.path.exists('/content') and os.path.exists('/content/drive/MyDrive'):
            return '/content/drive/MyDrive/menutracker'
    except Exception:
        pass
    # Local default: repository root (cwd)
    return os.getcwd()

def create_collection(collection_name: str = "default_collection") -> str:
    """Create (if needed) and set the global collection folder.

    Args:
        collection_name: Name of the collection round folder (e.g., "Oct_collection_2025").

    Returns:
        The absolute path to the created/existing collection folder.
    """
    global folder
    base = _detect_base_dir()
    target = os.path.join(base, collection_name)
    try:
        os.makedirs(target, exist_ok=True)
    except Exception as e:
        print(f"Error creating folder '{target}': {e}")
        # Still set folder to allow downstream code to see attempted path
    folder = target
    print(f"Collection folder: {folder}")
    return target

# If executed directly, create a default collection to initialize `folder`
if __name__ == "__main__":
    create_collection()
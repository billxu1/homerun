import os

def to_txt(text, out_path):
    try:
        with open(out_path, 'w') as file:
            file.write(text)
    except IOError as e:
        print(f"could not write: {e}")

def read_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"file does not exist: {e}")
        return None

def list_files(file_path, remove_suffix=False):
    """List all files in the given directory."""
    files = []
    for entry in os.listdir(file_path):
        full_path = os.path.join(file_path, entry)
        if os.path.isfile(full_path):
            if remove_suffix:
                entry = os.path.splitext(entry)[0]
            files.append(entry)
    return files
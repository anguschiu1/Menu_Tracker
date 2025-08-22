import os

# start the collection - create a new master folder
folder = 'Sep_collection_2025'

def create_collection():
    try:
        os.mkdir(folder)
        print(f"Folder '{folder}' created successfully.")
    except FileExistsError:
        print(f"Folder '{folder}' already exists.")

if __name__ == "__main__":
    create_collection()
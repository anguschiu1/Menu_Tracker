import os

# Detect environment and set appropriate path
if os.path.exists('/content'):  # Running in Google Colab
    folder = '/content/drive/MyDrive/menutracker/Sep_collection_2025'
else:  # Running locally
    folder = 'Sep_collection_2025'

def create_collection():
    try:
        os.makedirs(folder, exist_ok=True)
        print(f"Folder '{folder}' created successfully.")
    except Exception as e:
        print(f"Error creating folder '{folder}': {e}")
        
if __name__ == "__main__":
    create_collection()
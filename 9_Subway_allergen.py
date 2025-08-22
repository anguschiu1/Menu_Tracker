import requests
import os  # Import the 'os' module for path manipulation

from define_collection_wave import folder
from helpers import create_folder

path_subway_allergen = create_folder('9_Subway_allergen', folder)

url = "https://www.subway.com/en-gb/-/media/emea/europe/uk/nutrition/sub119101_online_allergen_update_c1_with-hcb_rgb_v2.pdf"

response = requests.get(url)
response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

# Construct the full file path
file_name = "Allergen.pdf"
full_file_path = os.path.join(path_subway_allergen, file_name)

# Write the file to the specified path
with open(full_file_path, "wb") as file:
    file.write(response.content)

print(f"Successfully downloaded Allergen.pdf to: {full_file_path}")

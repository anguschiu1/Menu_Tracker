import requests

url = "https://www.krispykreme.co.uk/media/wysiwyg/PDFs/UK2024_Allergen_Nutrition_Book_301024_UK__GimmeSmore_.pdf"

response = requests.get(url)

with open("Nutrition.pdf", "wb") as file:
    file.write(response.content)
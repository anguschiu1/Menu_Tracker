import json

import requests

from define_collection_wave import folder
from helpers import create_folder, PDFDownloader


fg_path = create_folder('31_FlamingGrill', folder)
print(fg_path)

url_fordownload = 'https://gkbr-p-001.sitecorecontenthub.cloud/api/public/content/630af590a2944010a833eaa8c033bf29?v=ac8db31e'
print("Downloading:", url_fordownload)
filePath = fg_path + '/' + url_fordownload.split('/')[-1].replace('-','_').replace('?','')+'.pdf'
PDFDownloader(url_fordownload, filePath=filePath)

# coding: utf-8
import shutil
import os
import time

import requests
from bs4 import BeautifulSoup

from emosiac.utils.fs import ensure_directory

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
base_url = 'https://emojiisland.com/pages/free-download-emoji-icons-png'
headers = {'User-Agent': user_agent }
save_folder = 'images/popular_emojis'

# create folder if needed
ensure_directory(save_folder)

def download_image(url, savepath):
  response = requests.get(url, headers=headers, stream=True)
  with open(savepath, 'wb') as out_file:
    shutil.copyfileobj(response.raw, out_file)

# get main page
r = requests.get(base_url, headers=headers)
soup = BeautifulSoup(r.content, 'lxml')

# grab all the icon links of this form:
# https://emojiisland.com/products/slightly-smiling-face-emoji-icon
links = soup.findAll('a')
icon_links = []
for l in links:
  href = l.attrs['href'].lower()
  if '/products/' in href and href.endswith('icon'):
    icon_links.append(l.attrs['href'])

# download all the images
for icon_link in icon_links:
  if icon_link.startswith('/products/'):
    link = 'https://emoji-island.myshopify.com' + icon_link
  else:
    link = icon_link
    
  # find the link
  ri = requests.get(link, headers=headers)
  icon_soup = BeautifulSoup(ri.content, 'lxml')
  icon_dl_links = icon_soup.findAll('a', {"class": "button"})
  
  # download image
  dl_link = None
  for idl in icon_dl_links:
    if 'download png file' in idl.text.lower():
      dl_link = idl.attrs['href']
      savepath = os.path.join(save_folder, os.path.basename(dl_link).split('?')[0])
      download_image(dl_link, savepath)
      print("Downloading {dl_link} to {savepath}...".format(
        dl_link=dl_link, savepath=savepath))
      break
  
  # wait to be sneaky
  time.sleep(2)


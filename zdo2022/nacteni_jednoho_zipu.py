# -*- coding: utf-8 -*-


# Nacteni trenovacich dat
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials
import zipfile
import xml.etree.ElementTree as ET
import skimage
import skimage.io
import skimage.filters
import matplotlib.pyplot as plt
import math
import pickle
import numpy as np
import json
import cv2


def oprava_nazvu(i):
    # Metoda pro přidání nul k názvu
    if i >= 100000:
      return str(i)
    if i >= 10000:
      return "0" + str(i)
    if i >= 1000:
        return "00" + str(i)
    if i >= 100:
        return '000' + str(i)
    if i >= 10:
        return '0000' + str(i)
    return '00000' + str(i)
    
# Získání popisu RGB, hrany a pohybu z dostupných dat
def popisNeedleHolderu(obrazek, anotace, minulyObrazek):
  obrazekCB = skimage.color.rgb2gray(obrazek)
  minulyCB = skimage.color.rgb2gray(minulyObrazek)
  hrany = skimage.filters.roberts(obrazekCB)

  pocetBodu = 0
  RGB = [0, 0, 0]
  hrana = 0
  pohyb = 0

  for y in range(anotace["y"]-10, anotace["y"]+11):
    if y < 0 or y >= obrazek.shape[0]: continue
    for x in range(anotace["x"]-10, anotace["x"]+11):
      if x < 0 or x >= obrazek.shape[1]: continue
      pocetBodu += 1
      hodnotaPixelu = obrazek[y, x]
      for i in range(3):
        RGB[i] += hodnotaPixelu[i]
      hrana += hrany[y, x]
      pohyb += (1 if abs(obrazekCB[y, x] - minulyCB[y, x]) > 0.1 else 0)

  for i in range(3):
    RGB[i] /= pocetBodu
  hrana /= pocetBodu
  pohyb /= pocetBodu

  return RGB + [hrana, pohyb]

""" Nacteni zip archivu pri spousteni z Google Colabu
auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)

file_id = '1y5TDMsGVyfKG2A0PWZel0KbUvz121RcG'
downloaded = drive.CreateFile({'id':file_id})
downloaded.FetchMetadata(fetch_all=True)
downloaded.GetContentFile(downloaded.metadata['title'])
"""
cisloSouboru = 226
with zipfile.ZipFile(str(cisloSouboru) + ".zip", 'r') as zip_ref:
    zip_ref.extractall("data")

tree = ET.parse('data/annotations.xml')
root = tree.getroot()

# Zpracování dostupných anotací pro "needle holder" a odstranení nežádoucích anotací framu
anotace = {}
for track in root:
  if track.tag == "track" and track.attrib["label"] == "needle holder":
    for pozice in track:
      body = pozice.attrib["points"].split(",")
      slovnik = {"x": round(float(body[0])), "y": round(float(body[1])), "visible": (True if pozice.attrib["outside"] == "0" and pozice.attrib["occluded"] == "0" else False)}
      anotace[int(pozice.attrib["frame"])] = slovnik


# Inicializace histogramu popisu
histogram = []
for i in range(26):
  histogram.append([])
  for j in range(26):
    histogram[i].append([])
    for k in range(26):
      histogram[i][j].append([])
      for l in range(100):
        histogram[i][j][k].append([])
        for m in range(10):
          histogram[i][j][k][l].append(0)

# histogram vzdáleností
pohyby = []
for i in range(2500):
  pohyby.append(0)

# Procházení framu, získání popisu a následné ukládání do histogramu, histogramy ulozeny v pickle formatu
pocetFramu = 0
for frame in anotace:
  obrazek = skimage.io.imread("data/images/frame_" + oprava_nazvu(frame) + ".PNG")
  if anotace[frame]["visible"]:
    if (frame - 1) in anotace and anotace[frame - 1]["visible"]:
      minulyObrazek = skimage.io.imread("data/images/frame_" + oprava_nazvu(frame - 1) + ".PNG")
      pocetFramu += 1
      print("Probíhá frame", frame)
      popis = popisNeedleHolderu(obrazek, anotace[frame], minulyObrazek)
      index1 = math.floor(popis[0] / 10)
      index2 = math.floor(popis[1] / 10)
      index3 = math.floor(popis[2] / 10)
      index4 = min(math.floor(popis[3] * 100), 99)
      index5 = min(math.floor(popis[4] * 10), 9)
      histogram[index1][index2][index3][index4][index5] += 1
      indexPohybu = math.floor(math.sqrt((anotace[frame]["x"] - anotace[frame - 1]["x"])**2 + (anotace[frame]["y"] - anotace[frame - 1]["y"])**2) / 2)
      pohyby[indexPohybu] += 1

pickle.dump([histogram, pohyby, pocetFramu], open("vysledek" + str(cisloSouboru) + ".pckl", "ab"))

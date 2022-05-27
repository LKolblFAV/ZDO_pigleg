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

# Prumerovani vysledku
soubory = [202, 204, 206, 208, 220, 221, 224, 225, 226]
vysledky = []
pohyby = []
for i in range(2500):
  pohyby.append(0)
celkemFramu = 0
# Zpracování pickle souboru vsech dostupnych zipu
for j in range(len(soubory)):
  soubor = soubory[j]
  nazev = "vysledek" + str(soubor) + ".pckl"
  vysledky.append(pickle.load(open(nazev, "rb")))
  celkemFramu += vysledky[-1][2]

for j in range(len(soubory)):
  for i in range(len(vysledky[j][1])):
    pohyby[i] += vysledky[j][1][i] / celkemFramu

# Ulození jednotlivych hodnot do histogramu
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
          for n in range(len(soubory)):
            histogram[i][j][k][l][m] += vysledky[n][0][i][j][k][l][m] / celkemFramu
# Vysledek ulozen v pickle formatu pro dalsi uziti
pickle.dump([histogram, pohyby], open("vysledek.pckl", "ab"))

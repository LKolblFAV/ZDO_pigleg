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
import glob
import os
import pylab
import imageio
# moduly v lokálním adresáři musí být v pythonu 3 importovány s tečkou


# Vyber X nejlepsich/nejpravdepodobnejsich ctverecku
def vyberNejlepsichCtverecku(cenyCile):
  kliceSorted = []
  hodnotySorted = []
  for klic in cenyCile:
    cena = cenyCile[klic]
    if len(hodnotySorted) < 500: # moznost zmeny poctu nejlepsich ctverecku
      hodnotySorted = [cena] + hodnotySorted
      kliceSorted  = [klic] + kliceSorted
    else:
      if cena > hodnotySorted[-1]:
        hodnotySorted = [cena] + hodnotySorted[:-1]
        kliceSorted = [klic] + kliceSorted[:-1]
    for i in range(0, len(kliceSorted)-1):
      if hodnotySorted[i+1] > hodnotySorted[i]:
        hodnota = hodnotySorted[i]
        key = kliceSorted[i]
        hodnotySorted[i] = hodnotySorted[i+1]
        kliceSorted[i] = kliceSorted[i+1]
        hodnotySorted[i+1] = hodnota
        kliceSorted[i+1] = key
      else:
        break

  vysledek = {}
  for i in range(len(kliceSorted)):
    vysledek[kliceSorted[i]] = hodnotySorted[i]
    
  return vysledek


#  Ziskani popisu vsech ctverecku RGB, hrany, pohyb z integralnich obrazu
def popisCtverecku(pohybIntegralni, hranyIntegralni, integralniObrazR, integralniObrazG, integralniObrazB):
  vysledek = {}

  for y in range(11, integralniObrazR.shape[0]-11, 10):
    for x in range(11, integralniObrazR.shape[1]-11, 10):
      
      RGB = [0, 0, 0]
      RGB[0] = (integralniObrazR[y+10][x+10] + integralniObrazR[y-11][x-11] - integralniObrazR[y-11][x+10] - integralniObrazR[y+10][x-11]) / 441
      RGB[1] = (integralniObrazG[y+10][x+10] + integralniObrazG[y-11][x-11] - integralniObrazG[y-11][x+10] - integralniObrazG[y+10][x-11]) / 441
      RGB[2] = (integralniObrazB[y+10][x+10] + integralniObrazB[y-11][x-11] - integralniObrazB[y-11][x+10] - integralniObrazB[y+10][x-11]) / 441

      hrana = (hranyIntegralni[y+10][x+10] + hranyIntegralni[y-11][x-11] - hranyIntegralni[y-11][x+10] - hranyIntegralni[y+10][x-11]) / 441
      pohyb = 0
      if pohybIntegralni is not None:
        pohyb = (pohybIntegralni[y+10][x+10] + pohybIntegralni[y-11][x-11] - pohybIntegralni[y-11][x+10] - pohybIntegralni[y+10][x-11]) / 441
      vysledek[(x, y)] = RGB + [hrana, pohyb]

  return vysledek


class InstrumentTracker():
    def __init__(self):
        pass

    def predict(self, video_filename):
        vidcap = cv2.VideoCapture('video.mkv')

        # Nactení souboru pickle a vytvoreni histogramu 
        print("Načítám histogram")
        [histogram, pohyby] = pickle.load(open("vysledek.pckl", "rb"))

        pravdepodobnostiPohybu = {}
        obrazek = None
        success = True
        while success:   
          success, obrazek = vidcap.read()

          break


        rozliseni = (int(obrazek.shape[0]), int(obrazek.shape[1]))


        # pravdepodobnost pohybu o urcitou vzdalenost pro viterbiho algoritmus
        for y1 in [11]:
            for x1 in [11]:
              for y2 in range(11, rozliseni[0]-11, 10):
                for x2 in range(11, rozliseni[1]-11, 10):
                  dx = np.abs(x1 - x2)
                  dy = np.abs(y1 - y2)
                  if (dx, dy) not in pravdepodobnostiPohybu:
                    indexPohybu = math.floor(math.sqrt((dx)**2 + (dy)**2) / 2)
                    pst = pohyby[indexPohybu]
                    if pst == 0:
                      pravdepodobnostiPohybu[(dx, dy)] = -9999999
                    else:
                      pravdepodobnostiPohybu[(dx, dy)] = np.log(pohyby[indexPohybu])
        vidcap = cv2.VideoCapture('video.mkv')


        minulyPohyb = None
        minulyCB = None

        cenyCile = []
        ceny = []
        minulyCtverecek = []
        '''
        prochazeni videa a zpracování framu
        vyroba integralnich obrazu pro rgb, hranu a pohyb
        porovnani hodnot z histogramem zpracovanych framu
        viterbiho algoritmus
        '''
        while success:   
          success, obrazek = vidcap.read()
          if not success:
            break
          obrazek = obrazek[:, :, ::-1]

          print("Zpracovávám nový frame.")
          cenyCile.append({})
          ceny.append({})
          minulyCtverecek.append({})
          integralniObrazR = skimage.transform.integral_image(obrazek[:, :, 0])
          integralniObrazG = skimage.transform.integral_image(obrazek[:, :, 1])
          integralniObrazB = skimage.transform.integral_image(obrazek[:, :, 2])
          obrazekCB = skimage.color.rgb2gray(obrazek)
          hrany = skimage.filters.roberts(obrazekCB)
          hrany = skimage.transform.integral_image(hrany)
          pohyb = None
          if minulyCB is not None:
            pohyb = np.abs(obrazekCB - minulyCB)
            pohyb = pohyb > 0.1
            pohyb = skimage.transform.integral_image(pohyb)

          popis = popisCtverecku(pohyb, hrany, integralniObrazR, integralniObrazG, integralniObrazB)

          for xy in popis:
            index1 = math.floor(popis[xy][0] / 10)
            index2 = math.floor(popis[xy][1] / 10)
            index3 = math.floor(popis[xy][2] / 10)
            index4 = min(math.floor(popis[xy][3] * 100), 99)
            index5 = min(math.floor(popis[xy][4] * 10), 9)

            pstPopisu = max(histogram[index1][index2][index3][index4][index5], 1e-7)
            
            cenyCile[-1][(xy[0], xy[1])] = np.log(pstPopisu)

          cenyCile[-1] = vyberNejlepsichCtverecku(cenyCile[-1])

          for xy in cenyCile[-1]:
            ceny[-1][(xy[0], xy[1])] = cenyCile[-1][(xy[0], xy[1])]
            if len(ceny) > 1:
              nejvetsiCena = -999999999
              nejlepsiMinuly = None

              for xyMin in ceny[-2]:
                if pravdepodobnostiPohybu[(np.abs(xy[0] - xyMin[0]), np.abs(xy[1] - xyMin[1]))] > nejvetsiCena:
                  nejvetsiCena = pravdepodobnostiPohybu[(np.abs(xy[0] - xyMin[0]), np.abs(xy[1] - xyMin[1]))]
                  nejlepsiMinuly = xyMin
              
              ceny[-1][(xy[0], xy[1])] += nejvetsiCena
              minulyCtverecek[-1][(xy[0], xy[1])] = nejlepsiMinuly

          minulyCB = obrazekCB

        # Vyhodnoceni algoritmu
        nejlepsiCena = -99999999
        nejlepsiCtverecek = None
        for ctverecek in ceny[-1]:
          if ceny[-1][ctverecek] > nejlepsiCena:
            nejlepsiCena = ceny[-1][ctverecek]
            nejlepsiCtverecek = ctverecek
        ctverecky = [nejlepsiCtverecek]

        for frame in range(len(ceny)-1, 0, -1):
          nejlepsiCtverecek = minulyCtverecek[frame][nejlepsiCtverecek]
          ctverecky = [nejlepsiCtverecek] + ctverecky

        # Ulozeni anotaci
        print("Ukládám anotace.")
        vysledneAnotace = {"filename": []}
        vysledneAnotace["frame_id"] = []
        vysledneAnotace["object_id"] = []
        vysledneAnotace["x_px"] = []
        vysledneAnotace["y_px"] = []
        vysledneAnotace["annotation_timestamp"] = []
        for i, obrazek in enumerate(vid):
          vysledneAnotace["filename"].append(videoName + ".mkv")
          vysledneAnotace["frame_id"].append(i)
          vysledneAnotace["object_id"].append(0)
          vysledneAnotace["x_px"].append(ctverecky[i][0])
          vysledneAnotace["y_px"].append(ctverecky[i][1])
          vysledneAnotace["annotation_timestamp"].append(None)

        json_string = json.dumps(vysledneAnotace)
        with open('vysledne_anotace.json', 'w') as outfile:
            outfile.write(json_string)


        return vysledneAnotace
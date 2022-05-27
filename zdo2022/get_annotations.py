﻿# -*- coding: utf-8 -*-
 
import zdo2022.predictor
import pytest
import os
import skimage.io
from typing import Optional
from skimage.draw import polygon
import glob
import numpy as np
from pathlib import Path
import sklearn.metrics
import pandas as pd
from pathlib import Path
import lxml
from lxml import etree

def run():
    vdd = zdo2022.predictor.InstrumentTracker()
    # Nastavte si v operačním systém proměnnou prostředí 'ZDO_DATA_PATH' s cestou k datasetu.
    # Pokud není nastavena, využívá se testovací dataset tests/test_dataset
    dataset_path = os.getenv('ZDO_DATA_PATH_', default=Path(__file__).parent / 'test_dataset/')
    # dataset_path = Path(r"H:\biology\orig\zdo_varroa_detection_coco_001")

    # print(f'dataset_path = {dataset_path}')
    types = ('*.MP4', '*.mkv')  # the tuple of file types
    files = []
    for file_type in types:
        files.extend(dataset_path.glob(f"./{file_type}"))

    f1s = []
    for filename in files:
        prediction = vdd.predict(filename)
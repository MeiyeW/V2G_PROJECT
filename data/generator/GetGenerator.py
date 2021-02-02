import os, csv, operator, copy, time, random
import numpy as np
import datetime as dt
import pandas as pd

genFleetRaw=pd.read_csv('GeneratorRaw2019.csv')
genFleetWOHydro=genFleetRaw[genFleetRaw['PlantType']!='Hydro']
genFleetWOHydro=genFleetWOHydro.drop(columns='PlantType')
genFleetWOHydro.to_csv('GeneratorWOHydro2019.csv',index=False)
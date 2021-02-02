import pandas as pd
import numpy as np
from datetime import datetime

monthHydro=pd.read_csv('HydroMonthlyAggr.csv')

def get_load():
    df_load = pd.read_csv('../netload/CAISO2019Load.csv',header=0)
    return df_load
load=get_load()


load.index=load['Unnamed: 0']
load.index=[datetime.strptime(load.index[i][:10], "%Y-%m-%d") for i in range(load.shape[0])]
loadDailyAggre=np.asarray(load.groupby(by=load.index).sum())

load['month']=[str(load.index[i])[5:7] for i in range(load.shape[0])]
loadMonthly=load.groupby(by=load['month']).sum()
monthHydro.index=loadMonthly.index
loadMonthly['generation']=monthHydro['HydroGeneration(MWh)']

monthlyPercent=np.asarray(loadMonthly['generation']/loadMonthly['netload'])

hydroDaily=np.zeros((365))
monthDay=[31,28,31,30,31,30,31,31,30,31,30,31]
i=0
for m in range(12):
    for j in range(monthDay[m]):
        hydroDaily[i]=loadDailyAggre[i]*monthlyPercent[m]
        i+=1

hydroDailyGeneration=pd.DataFrame(data=hydroDaily,columns={'Capacity(MWh)'})
hydroDailyGeneration.to_csv('HydroDailyCapacity.csv')
import pandas as pd
import numpy as np 
from datetime import datetime
import os
from pytz import timezone

def GetLoadRawYearlyData():
    directory = r'/Users/meiyewang/Desktop/code/data/netload/ACTUAL/2019'
    df1=pd.DataFrame(columns=["INTERVALSTARTTIME_GMT",'MW','TAC_AREA_NAME'])
    for filename in os.listdir(directory):
        if filename.endswith(".csv") :
            df=pd.read_csv(os.path.join(directory, filename))
            df1=pd.concat([df1,df[["INTERVALSTARTTIME_GMT",'MW','TAC_AREA_NAME']]])
        else:
            continue
    return df1

def SortTimeOrder(df):
    timelist=[datetime.strptime(df.index[i][:16], "%Y-%m-%dT%H:%M").replace(tzinfo=timezone('UTC')).astimezone(timezone('US/Pacific')) for i in range(df.shape[0])]
    df.index=[str(timelist[i])[:16] for i in range(len(timelist))]
    return df

yearlyLoad=GetLoadRawYearlyData()
yearTotal.iloc[0]['INTERVALSTARTTIME_GMT']=yearlyLoad[yearlyLoad['TAC_AREA_NAME']=='CA ISO-TAC'].drop(columns='TAC_AREA_NAME')
yearlyLoadAggre=SortTimeOrder(yearTotal.groupby(by="INTERVALSTARTTIME_GMT").sum())
yearlyLoadAggre.to_csv('CAISO2019Load.csv')

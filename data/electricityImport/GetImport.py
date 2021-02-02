import pandas as pd
import numpy as np 
from datetime import datetime
import os
from pytz import timezone

def GetImportRawYearlyData():
    directory = r'/Users/meiyewang/Desktop/code/data/electricityImport/RTM/2019'
    df1=pd.DataFrame(columns=["INTERVALSTARTTIME_GMT",'MW'])
    for filename in os.listdir(directory):
        if filename.endswith(".csv") :
            df=pd.read_csv(os.path.join(directory, filename))
            df1=pd.concat([df1,df[["INTERVALSTARTTIME_GMT",'MW']]])
        else:
            continue
    return df1

yearlyImport=GetImportRawYearlyData()
yearlyImport.index=yearlyImport['INTERVALSTARTTIME_GMT']
timelist=[datetime.strptime(yearlyImport.index[i][:13], "%Y-%m-%dT%H").replace(tzinfo=timezone('UTC')).astimezone(timezone('US/Pacific')) for i in range(yearlyImport.shape[0])]
yearlyImport.index=[str(timelist[i])[:13] for i in range(len(timelist))]
yearlyImportAggre=yearlyImport.groupby(by=yearlyImport.index).sum()
yearlyImportAggre['MW']=yearlyImportAggre['MW']/12
ImportResultDF=pd.DataFrame(data=yearlyImportAggre)
ImportResultDF=ImportResultDF.rename(columns={'MW':'Import(MW)'})

ImportResultDF.to_csv('CAISO2019Import.csv')





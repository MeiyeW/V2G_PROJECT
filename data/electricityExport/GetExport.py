import pandas as pd
import numpy as np 
from datetime import datetime
import os
from pytz import timezone

def GetExportRawYearlyData():
    directory = r'/Users/meiyewang/Desktop/code/data/electricityExport/RTM/2019'
    df1=pd.DataFrame(columns=["INTERVALSTARTTIME_GMT",'MW'])
    for filename in os.listdir(directory):
        if filename.endswith(".csv") :
            df=pd.read_csv(os.path.join(directory, filename))
            df1=pd.concat([df1,df[["INTERVALSTARTTIME_GMT",'MW']]])
        else:
            continue
    return df1

yearlyExport=GetExportRawYearlyData()
yearlyExport.index=yearlyExport['INTERVALSTARTTIME_GMT']
timelist=[datetime.strptime(yearlyExport.index[i][:13], "%Y-%m-%dT%H").replace(tzinfo=timezone('UTC')).astimezone(timezone('US/Pacific')) for i in range(yearlyExport.shape[0])]
yearlyExport.index=[str(timelist[i])[:13] for i in range(len(timelist))]
yearlyExportAggre=yearlyExport.groupby(by=yearlyExport.index).sum()
yearlyExportAggre['MW']=yearlyExportAggre['MW']/12
ExportResultDF=pd.DataFrame(data=yearlyExportAggre)
ExportResultDF=ExportResultDF.rename(columns={'MW':'Export(MW)'})

ExportResultDF.to_csv('CAISO2019Export.csv')





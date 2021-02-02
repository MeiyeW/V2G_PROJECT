import os
import pandas as pd
import numpy as np
import  datetime 
from datetimerange import DateTimeRange

def GetSolarWindRawYearlyData():
    directory = r'/Users/meiyewang/Desktop/code/data/windsolar/ACTUAL/2019'
    df1=pd.DataFrame(columns=["INTERVALSTARTTIME_GMT","RENEWABLE_TYPE",'MW'])
    df2=pd.DataFrame(columns=["INTERVALSTARTTIME_GMT","RENEWABLE_TYPE",'MW'])
    df3=pd.DataFrame(columns=["INTERVALSTARTTIME_GMT","RENEWABLE_TYPE",'MW'])
    df4=pd.DataFrame(columns=["INTERVALSTARTTIME_GMT","RENEWABLE_TYPE",'MW'])
    df5=pd.DataFrame(columns=["INTERVALSTARTTIME_GMT","RENEWABLE_TYPE",'MW'])
    for filename in os.listdir(directory):
        if filename.endswith(".csv") :
            df=pd.read_csv(os.path.join(directory, filename))
            df=pd.read_csv(os.path.join(directory, filename))
            df1=pd.concat([df1,df[(df['TRADING_HUB']=='NP15') & (df['RENEWABLE_TYPE']=='Solar')][["INTERVALSTARTTIME_GMT","RENEWABLE_TYPE",'MW']]])
            df2=pd.concat([df2,df[(df['TRADING_HUB']=='NP15') & (df['RENEWABLE_TYPE']=='Wind')][["INTERVALSTARTTIME_GMT","RENEWABLE_TYPE",'MW']]])
            df3=pd.concat([df3,df[(df['TRADING_HUB']=='SP15') & (df['RENEWABLE_TYPE']=='Solar')][["INTERVALSTARTTIME_GMT","RENEWABLE_TYPE",'MW']]])
            df4=pd.concat([df4,df[(df['TRADING_HUB']=='SP15') & (df['RENEWABLE_TYPE']=='Wind')][["INTERVALSTARTTIME_GMT","RENEWABLE_TYPE",'MW']]])
            df5=pd.concat([df5,df[(df['TRADING_HUB']=='ZP26') & (df['RENEWABLE_TYPE']=='Solar')][["INTERVALSTARTTIME_GMT","RENEWABLE_TYPE",'MW']]])
        else:
            continue
    return df1,df2,df3,df4,df5

def SortTimeOrder(df):
    timelist=[datetime.datetime.strptime(df.iloc[i,0][:16], "%Y-%m-%dT%H:%M") for i in range(df.shape[0])]
    df["INTERVALSTARTTIME_GMT"]=timelist
    df_sort=df.sort_values(by="INTERVALSTARTTIME_GMT")
    df_sort.index=df_sort["INTERVALSTARTTIME_GMT"]
    return df_sort

#____________________ have to update the following from notebook

def FillMissingData(df_sort):
    
    time_range = DateTimeRange("2019-01-01 08:00:00", "2020-01-01 07:00:00")
    completeIndex= time_range.range(datetime.timedelta(hours=1))
    
    df_sort_complete=df_sort.reindex(completeIndex)
    df_sort_complete=df_sort_complete.interpolate(method='linear')
    return df_sort_complete

def CompileWindSolar(df1_complete,df2_complete,df3_complete,df4_complete,df5_complete):
    df1_complete[df1_complete['MW'] < 0] = 0
    df2_complete[df2_complete['MW'] < 0] = 0
    df3_complete[df3_complete['MW'] < 0] = 0
    df4_complete[df4_complete['MW'] < 0] = 0
    df5_complete[df5_complete['MW'] < 0] = 0

    Solar=df1_complete
    Solar['MW']=df1_complete['MW']+df3_complete['MW']+df5_complete['MW']
    Solar.index=range(8760)
    Solar=Solar.drop(['INTERVALSTARTTIME_GMT','RENEWABLE_TYPE'],axis=1)

    Wind=df2_complete
    Wind['MW']=df2_complete['MW']+df4_complete['MW']
    Wind.index=range(8760)
    Wind=Wind.drop(['INTERVALSTARTTIME_GMT','RENEWABLE_TYPE'],axis=1)
    return Solar,Wind

df1,df2,df3,df4,df5=GetSolarWindRawYearlyData()

df1_complete=FillMissingData(SortTimeOrder(df1))
df2_complete=FillMissingData(SortTimeOrder(df2))
df3_complete=FillMissingData(SortTimeOrder(df3))
df4_complete=FillMissingData(SortTimeOrder(df4))
df5_complete=FillMissingData(SortTimeOrder(df5))

Solar,Wind=CompileWindSolar(df1_complete,df2_complete,df3_complete,df4_complete,df5_complete)

# print(Solar.sum()/1000)
# print(Wind[pd.isna(Wind['MW'])])

Solar.to_csv('SolarCap.csv',index=False)
Wind.to_csv('WindCap.csv',index=False)
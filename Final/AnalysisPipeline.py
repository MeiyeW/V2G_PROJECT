import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
import seaborn as sns
import cPickle as pickle
# def show1():
#     print(1)
# show1()
def revenueVisualization(year,month,day,run_no,batteryCost,renewablePercentage,charger,regulation,timeRange,total_number_of_vehicles,V1G=False):
    if V1G:
        versionName='V1G'+str(year)+'_'+str(run_no)+'_battery_'+str(batteryCost)+'_renewable_'+str(renewablePercentage)+'_charger_'+str(charger)+'_regulation_'+str(regulation)
    else:
        versionName=str(year)+'_'+str(run_no)+'_battery_'+str(batteryCost)+'_renewable_'+str(renewablePercentage)+'_charger_'+str(charger)+'_regulation_'+str(regulation)
    
    path='../GLResult/'+month+'/'+versionName # path='../GLResult/Result/'+month+'/'+versionName
    revenue=pd.read_csv(path+'/'+versionName+'_'+str(day)+'_Revenue.csv')#[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

    aggregatedRevenue=revenue.sum()/total_number_of_vehicles

    batteryCostSum=revenue.sum().sum()*batteryCost

    df=pd.DataFrame(data={  'Charge Cost': [-aggregatedRevenue[0]],
                        'Discharge Revenue': [aggregatedRevenue[1]],
                        'Regulation Up Capacity Revenue':[aggregatedRevenue[2]],
                        'Regulation Down Capacity Revenue':[aggregatedRevenue[3]],
                        'Net Revenue':[aggregatedRevenue[4]]})
    plt.title(versionName+'_'+month+',Revenue '+str(round((aggregatedRevenue[4]),2))+'$/vehicle')#round((revenue-batteryCostSum)/total_number_of_vehicles,3)
    # plt.xlabel("Category")
    plt.ylabel("Revenue$/Vehicle",size=16)
    # sns.set(font_scale=10)
    sns.set(rc={'figure.figsize':(15,10)})
    # plt.plot()
    splot=sns.barplot(data=df, palette="Blues")#.get_figure()
    for p in splot.patches:
        splot.annotate(format(p.get_height(), '.2f'), 
                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha = 'center', va = 'center', 
                    xytext = (0, 9), 
                    textcoords = 'offset points')
    # splot
    # return splot#.get_figure()

revenueVisualization(2030,'Sep',269,5,8,0.56,'base','high','monthly',4196727)#1290000

from __future__ import division
import datetime
import matplotlib.pyplot as plt
import numpy as np
import v2gsim 
import utility
from pyomo.opt import SolverFactory
from pyomo.core import Var
from pyomo.core import Param
from operator import itemgetter
import pandas as pd
import os
from UCModel import model

'''
for days in 365:
    epsilon=100
    epsilon2=100
    load=load_input[days*24,days*24+48]
    load_firday=load_input[days*24,days*24+24]
    load_secday=load_input[days*24+24,days*24+48]
    price=UC(load,generator)

    while epsilon(pric)>0.1 & epsilon2>0.1:
        veh_load,veh_generation=V2GSIM(price,load)
        veh_generation=veh_generation.sum_tp_hourly
        load2=(veh_load,load_secday)         #load_firday2=veh_load.sum_to_hourly+load_firday #concat(load_firday2,load_secday)

        price2,veh_generation2=UC(load2,generator,veh_generation)
        epsilon=price2*veh_generation2-price*veh_generation
        epsilon2=(veh_generation2-veh_generation).sum 
        load=load2
        price=price2
'''
def sensitivity(vehNum,batteryprice):
    for vehNum,batteryprice in range(),range():
        iterationFunction(run_no,convergeCrit,vehNum=1500000,batteryprice=20):


def iterationFunction(run_no=1,convergeCrit,vehNum=1500000,batteryprice=20):
    daysInYear=365
    convergeCrit=1000
    for day in range(daysInYear=365):
        epislon=SetEpsilon()
        load,load_day1,load_day2=InitializeLoad(day)
        price,generation,regup,regdown=UC(load,generator,vehNum,batteryprice)
        while epsilon>convergeCrit:
            veh_load,veh_gen_cap,veh_regup_cap,veh_regdown_cap=v2gsim(price,load,vehNum,batteryprice)
            load_day1=loadUpdate(load_day1,veh_load)

            price2,generation2,regup2,regdown2=UC(load2,generator2,vehNum,batteryprice)
            epsilon=revenue(price2,generation2)-revenue(price,generation)
            load_day1=load_day2
            price=price2
        result=getResult(price,generation,regup,regdown)
    resultVisual(result)  

def SetEpsilon():
    return epsilon

def InitializeLoad(day):
    # load in a specific day
    return load

def UC(load,generator,vehNum,batteryprice):
    return price,generation,regup,regdown

def v2gsim(price,load,vehNum,batteryprice):
    return veh_load,veh_gen_cap,veh_regup_cap,veh_regdown_cap

def loadUpdate(load,veh_load):
    return load2

def revenue(price,generation):
    return revenue

def getResult(price,generation,regup,regdown):
    return result

def resultVisual(result):
    return plot
    
# go through UC, V2G, UC, just check how much things are changing
# strict criteria: min change for each hour 

##run number
yr=2018
run_no = 1

#read parameters for dispatchable generators  
df_gen = pd.read_csv('../data/generator/Generators.csv',header=0)
#read parameters for net load
df_load = pd.read_csv('../data/netload/CAISO1819.csv',header=0)


for day in range(365):
    epsilonRevenue=[]
    epsilonGeneration=[]

    
    
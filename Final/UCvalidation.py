from pyomo.opt import SolverFactory
from pyomo.core import Var
from pyomo.core import Param
from operator import itemgetter
import pandas as pd
from datetime import datetime
import os


#run number
yr=2019
run_no = 1
###Segment C.2
from UCModel import model
from UCModel import writeDatFile
from UCModel import readSolutionResult

def init_load(df_load,day,HorizonHours):
    df_load = df_load[24*day:(24*day+HorizonHours)]
    return df_load

def init_gen():
    df_gen = pd.read_csv('../data/generator/GeneratorWOHydro2019.csv',header=0)
    return df_gen

def init_hydro(df_hydro,df_hydro_cap,day):
    df_hydro_cap = df_hydro_cap[day:day+1]
    cap=df_hydro_cap['Capacity(MWh)']
    df_hydro.at[0, 'maxcap_h'] = cap/24
    return df_hydro

def init_solar(df_solar_cap,day,HorizonHours):
    df_solar_cap=df_solar_cap[24*day:(24*day+HorizonHours)]
    return  df_solar_cap

def init_wind(df_wind_cap,day,HorizonHours):
    df_wind_cap=df_wind_cap[24*day:(24*day+HorizonHours)]
    return df_wind_cap

def init_veh(myresult):
    veh=pd.concat([myresult,myresult],axis=0)
    veh.index=range(veh.shape[0])
    return veh

def v2gResultConversion(myresult,vehicleNumber):
    N = 6# from 10mins to 1 hour
    myresult=myresult.groupby(myresult.index // N).sum()/6/1000000*vehicleNumber/100# from the unit of W to MW, from 100 vehicles to actual number of vehicles
    myresult=myresult.rename(columns={'EnergyDemand':'netload','EnergyGeneration':'gen_capacity_veh','Regup':'regup_capacity_veh','Regdown':'regdown_capacity_veh'})
    return myresult

def saveResult(mwh_pd,myresult,versionName,day):
    mwh_pd.to_csv('../Result/validate'+versionName+"_"+str(day)+'_vehicleGeneration.csv',index=False)

SimDays = 2
SimHours = SimDays * 24
HorizonHours = 48  ##planning horizon (e.g., 24, 48, 72 hours etc.)
regup_margin = 0.064  ##minimum regulation up reserve as a percent of system demand, referenced from https://www.nrel.gov/docs/fy19osti/73590.pdf
regdown_margin = 0.072 ##minimum regulation down reserve as a percent of system demand from https://www.nrel.gov/docs/fy19osti/73590.pdf
vehicleNumber=15000000
batteryCost=8
versionName='UCValidation_'+str(run_no)+'_battery'+str(batteryCost)

# init vehicle
myresult=v2gResultConversion(pd.read_csv('../data/vehicle/VehiclesCap_V2G_validation.csv',header=0),vehicleNumber)   
veh=init_veh(myresult)
df_veh_cap=veh[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

#init generation
df_gen=init_gen()
df_hydro_com = pd.read_csv('../data/hydro/HydroGenerator.csv',header=0)
df_hydro_cap = pd.read_csv('../data/hydro/HydroDailyCapacity.csv',header=0)
df_load_com = pd.read_csv('../data/netload/CAISO2019Load.csv',header=0)
df_solar_cap_com =pd.read_csv('../data/generator/SolarCap.csv',header=0)
df_solar_cons =pd.read_csv('../data/generator/SolarConstraint.csv',header=0)
df_wind_cap_com =pd.read_csv('../data/generator/WindCap.csv',header=0)
df_wind_cons =pd.read_csv('../data/generator/WindConstraint.csv',header=0)

for day in range(364):

    #initialize load
    
    df_load=init_load(df_load_com,day,HorizonHours)
    # df_import=init_import(day,HorizonHours)
    # df_export=init_export(day,HorizonHours)
    # df_load['netload']=df_load['netload']-df_import['Import(MW)']+df_export['Export(MW)']
    ###initialize generators
    
    df_hydro=init_hydro(df_hydro_com,df_hydro_cap,day)
    df_solar_cap=init_solar(df_solar_cap_com,day,HorizonHours) 
    df_wind_cap=init_wind(df_wind_cap_com,day,HorizonHours)
   
    # reindex
    df_solar_cap.index=range(HorizonHours)
    df_wind_cap.index=range(HorizonHours)
    df_load.index=range(HorizonHours)

    # update load
    df_load['netload']= veh['netload']+df_load['netload']
    for col in df_veh_cap:
        df_veh_cap[col].values[:] = 0

    writeDatFile(df_gen,df_solar_cap,df_solar_cons,df_wind_cap,df_wind_cons,df_veh_cap,df_load,df_hydro,SimDays,SimHours,HorizonHours,regup_margin,regdown_margin,versionName,batteryCost)

    ###Create instand and solve 
    instance = model.create_instance(versionName+'.dat')
    opt = SolverFactory("gurobi") ##SolverFactory("cplex")
    # opt.options["threads"] = 1
    H = instance.HorizonHours
    K=range(1,H+1)

    pr2,vehCap2,mwh_pd=readSolutionResult(opt,instance,K,veh,df_gen,df_solar_cons,df_wind_cons,df_hydro,df_load,batteryCost)
    saveResult(mwh_pd,myresult,versionName,day)
    print(day)
    print("complete")
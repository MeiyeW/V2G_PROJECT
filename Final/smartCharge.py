from __future__ import division
from pyomo.opt import SolverFactory
from pyomo.core import Var
from pyomo.core import Param
from operator import itemgetter
import pandas as pd
from datetime import datetime
import os
import datetime as dt
import matplotlib.pyplot as plt
# import cPickle as pickle
import pickle
import numpy as np

import v2gsim
# will run the print('save_vehicle_state_for_optimization')
import seaborn as sns
import sys
# import gc 

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

def epsilon2(vehCap2,vehCap):
    return (abs(vehCap2[['gen_capacity_veh','regup_capacity_veh','regdown_capacity_veh']]-vehCap[['gen_capacity_veh','regup_capacity_veh','regdown_capacity_veh']])).sum().sum()

def saveResult(vehCap,pr,mwh_pd,myresult,vehicleSeperateResult,vehicles,versionName,day,month,path):
    vehCap.to_csv(path+'/'+versionName+"_"+str(day)+'_vehicleGeneration.csv',index=False)
    pr.to_csv(path+'/'+versionName+"_"+str(day)+'_price.csv',index=False)
    mwh_pd.to_csv(path+'/'+versionName+"_"+str(day)+'_Generator.csv',index=False)
    myresult.to_csv(path+'/'+versionName+"_"+str(day)+'_myresult.csv',index=False)
    vehicleSeperateResult.to_csv(path+'/'+versionName+"_"+str(day)+'_IndividualVehicle.csv',index=False)

def calculateRevenue(vehCap,pr,myresult):
    demandCost=np.asarray(myresult['netload']*pr['pr_e']).sum()
    generationRev=np.asarray(vehCap['gen_capacity_veh']*pr['pr_e']).sum()
    regupRev=np.asarray(vehCap['regup_capacity_veh']*pr['pr_fre_u']).sum()
    regdownRev=np.asarray(vehCap['regdown_capacity_veh']*pr['pr_fre_d']).sum()
    revenue=generationRev+regupRev+regdownRev-demandCost
    return demandCost,generationRev,regupRev,regdownRev,revenue

def init_charging(project):
    # Create some new charging infrastructures, append those new
    # infrastructures to the project list of infrastructures
    charging_stations = []
    charging_stations.append(
        v2gsim.model.ChargingStation(name='L1_controllable', maximum_power=1400, minimum_power=0, post_simulation=True))
    charging_stations.append(
        v2gsim.model.ChargingStation(name='L3_controllable', maximum_power=120000, minimum_power=0, post_simulation=True))
    charging_stations.append(    
        v2gsim.model.ChargingStation(name='L2_V2G', maximum_power=7200, minimum_power=0, post_simulation=True))
    project.charging_stations.extend(charging_stations)
     
    # Add the new charging infrastructure at each location
    temp1 = pd.DataFrame(index=['L1_controllable'],
                    data={'charging_station': charging_stations[0],
                    'probability': 0.0, 'available': float('inf'), 'total': float('inf')})
    temp3 = pd.DataFrame(index=['L3_controllable'],
                    data={'charging_station': charging_stations[2],
                    'probability': 0.0, 'available': float('inf'), 'total': float('inf')})
    temp4 = pd.DataFrame(index=['L2_V2G'],
                    data={'charging_station': charging_stations[2],
                    'probability': 0.0, 'available': float('inf'), 'total': float('inf')})
    for location in project.locations:
        location.available_charging_station = pd.concat([location.available_charging_station, temp1], axis=0)
        location.available_charging_station = pd.concat([location.available_charging_station, temp3], axis=0)
        location.available_charging_station = pd.concat([location.available_charging_station, temp4], axis=0)



def set_infrastructure_probabilities(project, home, work, other_location):
    """Set new probability for charging infrastructure
    """
    # Set the charging infrastructure at each location
    for location in project.locations:
        if location.category == 'Home':
            for key, value in home.iteritems():
                location.available_charging_station.loc[key, 'probability'] = value

        elif location.category == 'Work':
            for key, value in work.iteritems():
                location.available_charging_station.loc[key, 'probability'] = value
        else:
            for key, value in other_location.iteritems():
                location.available_charging_station.loc[key, 'probability'] = value

def init_v2g():
    # ### Require gurobi or CPLEX #####
    # Create a project and initialize it with some itineraries
    project = v2gsim.model.Project()
    project = v2gsim.itinerary.from_excel(project, '../data/NHTS/California.xlsx')
    project = v2gsim.itinerary.copy_append(project, nb_of_days_to_add=2)

    # This function from the itinerary module return all the vehicles that
    # start and end their day at the same location (e.g. home)
    project.vehicles = v2gsim.itinerary.get_cycling_itineraries(project)

    # Reduce the number of vehicles
    project.vehicles = project.vehicles[0:100]

    # init charging inform
    init_charging(project)

    return project

def run_v2g(project):
     # Initiate SOC and charging infrastructures
    v2gsim.core.initialize_SOC(project, nb_iteration=2)
    # print(project.vehicles[97].SOC)
    # Assign a basic result function to save power demand
    for vehicle in project.vehicles:
        vehicle.result_function = v2gsim.post_simulation.netload_optimization.save_vehicle_state_for_optimization
        
        if vehicle.SOC[0]>1:
            vehicle.SOC[0]=1
    # print(project.vehicles[97].SOC)
    # Launch the simulation
    v2gsim.core.run(project, date_from=project.date + dt.timedelta(days=1),
                    date_to=project.date + dt.timedelta(days=2),
                    reset_charging_station=False)

    # Look at the results
    total_power_demand = v2gsim.post_simulation.result.total_power_demand(project)

    # Optimization
    myopti = v2gsim.post_simulation.netload_optimization.CentralOptimization(project, 10,
                                                                            project.date + dt.timedelta(days=1),
                                                                            project.date + dt.timedelta(days=2),
                                                                            minimum_SOC=0.1, maximum_SOC=0.95)
    return myopti

#run number
# year=2025
run_no = 5
np.random.seed(1)
# init global parameters
daysInYear=62
MWtoW=1000000

#simulation parameters
SimDays = 2
SimHours = SimDays * 24
HorizonHours = 48  ##planning horizon (e.g., 24, 48, 72 hours etc.)

#TAKE INPUTS FROM SHELL SCRIPT
#Process inputs and call master function
inputData = sys.argv[1:] #exclude 1st item (script name)
# print(sys.argv[1:] )#['$1']
year=int(inputData[0])
renewablePercentage = float(inputData[1])
batteryCost= int(inputData[2])
charger=str(inputData[3])
regulation=str(inputData[4])
month=str(inputData[5])

# only 25% base, 50% of regulation up and down can come from vehicles 
if regulation=='base':
    regup_margin = 0.0064  ##minimum regulation up reserve as a percent of system demand, referenced from https://www.nrel.gov/docs/fy19osti/73590.pdf
    regdown_margin = 0.0072 ##minimum regulation down reserve as a percent of system demand from https://www.nrel.gov/docs/fy19osti/73590.pdf
    cap=0.25
elif regulation=='high':
    regup_margin = 0.01  ##minimum regulation up reserve as a percent of system demand, referenced from https://www.nrel.gov/docs/fy19osti/73590.pdf
    regdown_margin = 0.01 #https://www.nrel.gov/docs/fy13osti/55588.pdf
    cap=0.50
#create vehicle mix and available chargers for baseline scenario

yearList=[2020,2025,2030]
# Fleet mix
fleet_mix = pd.DataFrame(index=yearList, data={
    'PHEV': [652662,870000, 3172894],
    'BEV': [315235,420000, 1023833],
    'battery_capcity_increase': [ 2.0,2.5, 3.0],
    'BEV_performance_increase' : [ 1.26,1.33, 1.4375],
    'PHEV_performance_increase' : [1.19125, 1.25, 1.30625]})

# Charging infrastructure assumptions
# if charger=='high':
#     home = pd.DataFrame(index=yearList, data={
#         'no_charger':      [ 0.0, 0.0, 0.0],
        # 'L1':              [ 0.0,0.0, 0.0],
        # 'L2':              [ 0.0,0.0, 0.0],
#         'L1_controllable': [ 0.0, 0.0, 0.0],
#         'L2_V2G':          [ 0.0, 0.0, 0.0],
#         'L3_controllable': [ 1.0, 1.0, 1.0]})
#     work = pd.DataFrame(index=yearList, data={
#         'no_charger':      [ 0.0, 0.0, 0.0],
        # 'L1':              [ 0.0,0.0, 0.0],
        # 'L2':              [ 0.0,0.0, 0.0],
#         'L1_controllable': [ 0.0, 0.0, 0.0],
#         'L2_V2G':          [ 0.0, 0.0, 0.0],
#         'L3_controllable': [ 1.0, 1.0, 1.0]})
#     other_location = pd.DataFrame(index=yearList, data={ # changed other location
#         'no_charger':      [ 0.0, 0.0, 0.0],
        # 'L1':              [ 0.0,0.0, 0.0],
        # 'L2':              [ 0.0,0.0, 0.0],
#         'L1_controllable': [ 0.0, 0.0, 0.0],
#         'L2_V2G':          [ 0.0, 0.0, 0.0],
#         'L3_controllable': [ 1.0, 1.0, 1.0]})
# # Charging infrastructure assumptions
# elif charger=='low':
#     home = pd.DataFrame(index=yearList, data={
#         'no_charger':      [ 0.0, 0.0, 0.0],
        # 'L1':              [ 0.0,0.0, 0.0],
        # 'L2':              [ 0.0,0.0, 0.0],
#         'L1_controllable': [ 0.3, 0.25, 0.2],
#         'L2_V2G':          [ 0.7, 0.75, 0.8],
#         'L3_controllable': [ 0.0, 0.0, 0.0]})
#     work = pd.DataFrame(index=yearList, data={
#         'no_charger':      [ 0.2, 0.1, 0.0],
        # 'L1':              [ 0.0,0.0, 0.0],
        # 'L2':              [ 0.0,0.0, 0.0],
#         'L1_controllable': [ 0.0, 0.0, 0.0],
#         'L2_V2G':          [ 0.7, 0.75, 0.8],
#         'L3_controllable': [ 0.1, 0.15, 0.2]})
#     other_location = pd.DataFrame(index=yearList, data={ # changed other location
#         'no_charger':       [ 0.2, 0.1, 0.0],
        # 'L1':              [ 0.0,0.0, 0.0],
        # 'L2':              [ 0.0,0.0, 0.0],
#         'L1_controllable':  [ 0.0, 0.0, 0.0],
#         'L2_V2G':           [ 0.7, 0.75, 0.8],
#         'L3_controllable':  [ 0.1, 0.15, 0.2]})
# elif charger=='base': 
    #0.5 for level 1 and level 2 at home and work, if it runs okay in July/Aug, reduce them
home = pd.DataFrame(index=yearList, data={
    'no_charger':      [ 0.0, 0.0, 0.0],
    'L1':              [ 0.0,0.0, 0.0],
    'L2':              [ 0.0,0.0, 0.0],
    'L1_controllable': [0.175,0.1875, 0.2],
    'L2_V2G':          [0.825,0.8125,0.8],
    'L3_controllable': [ 0.0,0.0, 0.0]})
work = pd.DataFrame(index=yearList, data={
    'no_charger':      [0.2,0.1, 0.0],
    'L1':              [ 0.0,0.0, 0.0],
    'L2':              [ 0.0,0.0, 0.0],
    'L1_controllable': [ 0.0, 0.0, 0.0],
    'L2_V2G':          [ 0.2,0.3375, 0.4],
    'L3_controllable': [0.525,0.5625,0.6]})
other_location = pd.DataFrame(index=yearList, data={ # changed other location
    'no_charger':      [0.2,0.1, 0.0],
    'L1':              [ 0.0,0.0, 0.0],
    'L2':              [ 0.0,0.0, 0.0],
    'L1_controllable':[ 0.0, 0.0, 0.0] ,
    'L2_V2G':         [ 0.2,0.3375, 0.4],
    'L3_controllable':[0.525,0.5625,0.6]})


# yearList=[2025,2030]
# # Fleet mix
# fleet_mix = pd.DataFrame(index=yearList, data={
#     'PHEV': [870000, 3172894],
#     'BEV': [420000, 1023833],
#     'battery_capcity_increase': [ 2.5, 3.0],
#     'BEV_performance_increase' : [ 1.33, 1.4375],
#     'PHEV_performance_increase' : [1.25, 1.30625]})

# # Charging infrastructure assumptions
# home = pd.DataFrame(index=yearList, data={
#     'no_charger':[  0.0, 0.0],
#     'L1': [ 0.0, 0.0],
#     'L2': [ 0.0, 0.0],
#     'L1_controllable': [0.25, 0.2],
#     'L2_controllable': [0.75, 0.8],
#     'L3_controllable': [ 0.0, 0.0]})
# work = pd.DataFrame(index=yearList, data={
#     'no_charger':[0.1, 0.0],
#     'L1': [ 0.0, 0.0],
#     'L2': [ 0.0,0.0],
#     'L1_controllable': [ 0.0, 0.0],
#     'L2_controllable': [ 0.75, 0.8],
#     'L3_controllable': [ 0.15, 0.2]})
# other_location = pd.DataFrame(index=yearList, data={
#     'no_charger':[0.7, 0.6],
#     'L1': [ 0.0, 0.0],
#     'L2': [ 0.0, 0.0],
#     'L1_controllable': [  0.0, 0.0],
#     'L2_controllable': [ 0.25, 0.3],
#     'L3_controllable': [ 0.05, 0.1]})

# month='Feb'
# month='Mar'
# month='WholeYear'

# print(batteryCost)
# print(year)
# print(renewablePercentage)
# init sensitivity parametersbattery cost/ renewable portion/ vehicle numbers
# batteryCost = pd.DataFrame(index=yearList, data={
#     'batteryCost':[12, 8]})
#batteryCost= batteryCost.ix[year]['batteryCost']
# renewablePercentage = pd.DataFrame(index=yearList, data={
#     'renewablePercentage':[0.48,0.6]})
# renewablePercentage=renewablePercentage.ix[year]['renewablePercentage']

solarWindMulti=(renewablePercentage-0.1163-0.0645)/(0.1163+0.0645)

vehicleNumber=fleet_mix.ix[year]['BEV'] + fleet_mix.ix[year]['PHEV']

versionName='V1G'+str(year)+'_'+str(run_no)+'_battery_'+str(batteryCost)+'_renewable_'+str(renewablePercentage)+'_charger_'+str(charger)+'_regulation_'+str(regulation)
path='../Result/'+month+'/'+versionName
print(path)
if not os.path.exists('../Result/'+month):
    os.mkdir('../Result/'+month)
if not os.path.exists(path):
    os.mkdir(path)

# print('Version Name:' + versionName)
# print(vehicleNumber)
# Set the fleet mix
total_number_of_vehicles = fleet_mix.ix[year]['BEV'] + fleet_mix.ix[year]['PHEV']
battery_size = fleet_mix.ix[year]['battery_capcity_increase']
BEV_perf = fleet_mix.ix[year]['BEV_performance_increase']
PHEV_perf = fleet_mix.ix[year]['PHEV_performance_increase']
year_fleet_mix = pd.DataFrame(data={
    'percentage': [fleet_mix.ix[year]['BEV'] / total_number_of_vehicles,
                    fleet_mix.ix[year]['PHEV'] / total_number_of_vehicles],
    'car_model': [v2gsim.model.BasicCarModel('Model3',
                                                battery_capacity=82000 * battery_size,
                                                maximum_power=120000,
                                                UDDS=145.83 / BEV_perf,
                                                HWFET=163.69 / BEV_perf,
                                                US06=223.62 / BEV_perf,
                                                Delhi=138.3 / BEV_perf),
                    v2gsim.model.BasicCarModel('Prius',
                                                battery_capacity=12000 * battery_size,
                                                maximum_power=120000,
                                                UDDS=145.83 / PHEV_perf,
                                                HWFET=163.69 / PHEV_perf,
                                                US06=223.62 / PHEV_perf,
                                                Delhi=138.3 / PHEV_perf)
                    ]})


# init generator and load infomation
df_gen=init_gen()
df_hydro_com = pd.read_csv('../data/hydro/HydroGenerator.csv',header=0)
df_hydro_cap = pd.read_csv('../data/hydro/HydroDailyCapacity.csv',header=0)
df_load_com = pd.read_csv('../data/netload/CAISO2019Load.csv',header=0)
df_solar_cap_com =pd.read_csv('../data/generator/SolarCap.csv',header=0)*solarWindMulti
df_solar_cons =pd.read_csv('../data/generator/SolarConstraint.csv',header=0)
df_wind_cap_com =pd.read_csv('../data/generator/WindCap.csv',header=0)*solarWindMulti
df_wind_cons =pd.read_csv('../data/generator/WindConstraint.csv',header=0)
 # If not feasible, add NGCC 500MWh
if year==2030:
    for i in range(11):
        df_gen=df_gen.append({'name':'AddedNGCC'+str(i),'maxcap':500,'mincap':0,'opcost':28.374682864574172,'minup':0.0,'ramp':500,'st_cost':0.0,'var_om':3.5999999999999996,'fix_om':13170.0,'regcost':2.837468286457417},ignore_index=True)
    
revenueTotal=[]

if month=='Jan':
    dayRange=range(0,31)
elif month=='Feb':
    dayRange=range(31,59)
elif month=='Mar':
    dayRange=range(59,90)
elif month=='Apr':
    dayRange=range(90,120)
elif month=='May':
    dayRange=range(120,151)
elif month=='Jun':
    dayRange=range(151,181)
elif month=='Jul':
    dayRange=range(181,212)
elif month=='Aug':
    dayRange=range(212,243)
elif month=='Sep':
    dayRange=range(243,273)
elif month=='Oct':
    dayRange=range(273,304)
elif month=='Nov':
    dayRange=range(304,334)
elif month=='Dec':
    dayRange=range(334,364)
elif  month=='WholeYear':
    dayRange=range(0,364)

for day in dayRange: # 0,30;31,58;59,89
    # daysRange=range(date,date+1)
    # for day in daysRange:# daysRange: #range(days)
    print(day+1)
    i=0

    if i==0: 
        vehCap=pd.read_csv('../Result/V1G.csv',header=0)
        pr=pd.read_csv    ('../Result/2025_1_battery_12_renewable_0.44_182_price.csv',header=0)
     
    
    else:
        vehCap=pd.read_csv(path+'/'+versionName+"_"+str(day)+'_vehicleGeneration.csv',header=0)
        pr=pd.read_csv(path+'/'+versionName+"_"+str(day)+'_price.csv',header=0)

    # vehCap=pd.read_csv('../Result/2025_1_battery_10_renewable_0.4_182_vehicleGeneration.csv',header=0)
    # pr=pd.read_csv    ('../Result/2025_1_battery_10_renewable_0.4_182_price.csv',header=0)
       
    myresult=v2gResultConversion(pd.read_csv('../data/vehicle/VehiclesCap_V2G_0_2019_1_battery8_renewable0.7_vehicleNum1500000.csv',header=0),vehicleNumber)     
    
    vehCap=pd.concat([vehCap,vehCap],ignore_index=True)
    pr=pd.concat([pr,pr],ignore_index=True)
    
    iterNumber=1
    eps=vehicleNumber*0.1
    # eps2=vehicleNumber*0.1

    project= init_v2g()
    v2gsim.itinerary.set_fleet_mix(project.vehicles, year_fleet_mix)
    # print(project.vehicles[97])
    # Set the infrastructure mix
    set_infrastructure_probabilities(project, home.ix[year].to_dict(), 
        work.ix[year].to_dict(), other_location.ix[year].to_dict())

    pd.DataFrame(project.vehicles).to_csv('vehicleItinerary.csv',index=False)
    myopti=run_v2g(project)

    # initialize load
    df_load=init_load(df_load_com,day,HorizonHours)

    # initialize solar, wind, and hydro capacity and generators
    df_hydro=init_hydro(df_hydro_com,df_hydro_cap,day)
    df_solar_cap=init_solar(df_solar_cap_com,day,HorizonHours) 
    df_wind_cap=init_wind(df_wind_cap_com,day,HorizonHours)
    # reindex
    df_solar_cap.index=range(HorizonHours)
    df_wind_cap.index=range(HorizonHours)
    df_load.index=range(HorizonHours)

    while eps>vehicleNumber*0.05:
        # print("in iteration")

        # # Initialize the load data for v2gsim
        load=init_load(df_load_com,day,HorizonHours)[:25]
        load['Unnamed: 0'] = [dt.datetime.strptime(x,"%m/%d/%y %H:%M") for x in load['Unnamed: 0']]
        load=load.set_index(load['Unnamed: 0'])
        load=load.drop(columns='Unnamed: 0')
        # Initialize vehicle and price info for v2gsim
        vehCap_v2g=vehCap[:25].set_index(load[:25].index)
        
        pr_v2g=pr[:25].set_index(load[:25].index)
        # print(project.vehicles[97])
        # print(project.vehicles[97].SOC)

        # run v2sim
        print('v2gsim')
        myresult2= myopti.solve(project, load * MWtoW,vehicleNumber, price=pr_v2g, vehCap=vehCap_v2g*MWtoW,iterNumber=iterNumber, batteryCost=batteryCost, peak_shaving='economic', SOC_margin=0.05,path=path)# convert unit from MW to W
        vehicleSeperateResult=myresult2
        myresult2=myresult2.groupby(level=0).sum()
        myresult2=v2gResultConversion(myresult2,vehicleNumber)  
        for vehicle in project.vehicles:
            vehicle.result_function = v2gsim.post_simulation.netload_optimization.save_vehicle_state_for_optimization
        # print(project.vehicles[97].SOC)
        # update load with vehicle demand for UCED
        veh=init_veh(myresult2)
        # print(veh)
        df_veh_cap=veh[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]
        # print(df_veh_cap)
        df_load['netload']= veh['netload']+df_load['netload']

       
        # initialize UCED data
        writeDatFile(df_gen,df_solar_cap,df_solar_cons,df_wind_cap,df_wind_cons,df_veh_cap,df_load,df_hydro,SimDays,SimHours,HorizonHours,regup_margin,regdown_margin,versionName,batteryCost,path,cap)

        ###Create instand and solve 
        instance = model.create_instance(path+"/"+versionName+'.dat')
        opt = SolverFactory("gurobi") ##SolverFactory("cplex")
        # opt.options["threads"] = 1
        H = instance.HorizonHours
        K=range(1,H+1)
        print('UCED')
        pr2,vehCap2,mwh_pd,on_pd=readSolutionResult(opt,instance,K,veh,df_gen,df_solar_cons,df_wind_cons,df_hydro,df_load,batteryCost)
        # print(pr2)
        # print(vehCap2)        

        # calculate epsilon
        demandCost,generationRev,regupRev,regdownRev,revenue=calculateRevenue(vehCap[:24],pr[:24],myresult)
        demandCost2,generationRev2,regupRev2,regdownRev2,revenue2=calculateRevenue(vehCap2[:24],pr2[:24],myresult2)
        eps=abs(revenue-revenue2)
        # eps2=epsilon2(vehCap2,vehCap)
        
        # update vehicle cap and price, myresult, as well as iteration number
        vehCap=vehCap2
        pr=pr2
        myresult=myresult2
        iterNumber+=1
        print(revenue2)
        print(eps)
        # print(eps2)    
    saveResult(vehCap[:24],pr[:24],mwh_pd,myresult,vehicleSeperateResult,project.vehicles,versionName,day,month,path)
    on_pd.to_csv(path+'/'+versionName+"_"+str(day)+'_on.csv',index=False)
    revenueTotal.append([demandCost2,generationRev2,regupRev2,regdownRev2,revenue2])
    print(day+1)   
    print(revenue2)
    # visualize(vehCap,revenue,batteryCost,day,vehicleNumber,myresult)
    pd.DataFrame(data=revenueTotal,columns =['DemandCost', 'GenerationRevenue', 'RegUpRev','RegDownRev', 'RevenueTotal']).to_csv(path+'/'+versionName+"_"+str(day)+'_Revenue.csv',index=False)
    # gc.get_stats()
    i+=1
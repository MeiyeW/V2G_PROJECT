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
import cPickle as pickle
import numpy as np
import v2gsim
import matplotlib.pyplot as plt
import seaborn as sns

def init_load(day,HorizonHours):
    df_load = pd.read_csv('../data/netload/CAISO2019Load.csv',header=0)[24*day:(24*day+HorizonHours)]
    return df_load
    
def init_gen():
    df_gen = pd.read_csv('../data/generator/GeneratorWOHydro2019.csv',header=0)
    return df_gen

def init_hydro(df_hydro,df_hydro_cap,day):
    df_hydro_cap = df_hydro_cap[day:day+1]
    cap=df_hydro_cap['Capacity(MWh)']
    df_hydro.at[0, 'maxcap_h'] = cap/24
    return df_hydro

def init_solar(day,HorizonHours):
    df_solar_cap=pd.read_csv('../data/generator/SolarCap.csv',header=0)[24*day:(24*day+HorizonHours)]
    df_solar_cons=pd.read_csv('../data/generator/SolarConstraint.csv',header=0)
    return  df_solar_cap,df_solar_cons

def init_wind(day,HorizonHours):
    df_wind_cap=pd.read_csv('../data/generator/WindCap.csv',header=0)[24*day:(24*day+HorizonHours)]
    df_wind_cons=pd.read_csv('../data/generator/WindConstraint.csv',header=0)
    return df_wind_cap,df_wind_cons

def v2gResultConversion(myresult,vehicleNumber):
    N = 6# from 10mins to 1 hour
    myresult=myresult.groupby(myresult.index // N).sum()/6/1000000*vehicleNumber/100# from the unit of W to MW, from 100 vehicles to actual number of vehicles
    myresult=myresult.rename(columns={'EnergyDemand':'netload','EnergyGeneration':'gen_capacity_veh','Regup':'regup_capacity_veh','Regdown':'regdown_capacity_veh'})
    return myresult

def init_veh(myresult):
    veh=pd.concat([myresult,myresult],axis=0)
    veh.index=range(veh.shape[0])
    return veh

def epsilon1(pr2,vehCap2,myresult2,pr,vehCap,myresult):
    return abs(calculateRevenue(vehCap2[:24],pr2[:24],myresult2)-calculateRevenue(vehCap[:24],pr[:24],myresult))

def epsilon2(vehCap2,vehCap):
    return (abs(vehCap2[['gen_capacity_veh','regup_capacity_veh','regdown_capacity_veh']]-vehCap[['gen_capacity_veh','regup_capacity_veh','regdown_capacity_veh']])).sum().sum()


def saveResult(vehCap,pr,myresult,versionName,day):
    vehCap.to_csv('../Result/'+str(day)+"_"+versionName+'vehicleGeneration.csv',index=False)
    pr.to_csv('../Result/'+str(day)+"_"+versionName+'price.csv',index=False)
    # sns.lineplot(data=calculateRevenue(vehCap,pr,myresult),dashes=False).get_figure().savefig("../Figure/"+versionName+"Revenue.png")
    
def calculateRevenue(vehCap,pr,myresult):
    demandCost=np.asarray(myresult['netload']*pr['pr_e']).sum()
    generationRev=np.asarray(vehCap['gen_capacity_veh']*pr['pr_e']).sum()
    regupRev=np.asarray(vehCap['regup_capacity_veh']*pr['pr_fre_u']).sum()
    regdownRev=np.asarray(vehCap['regdown_capacity_veh']*pr['pr_fre_d']).sum()
    revenue=generationRev+regupRev+regdownRev-demandCost
    return revenue

def init_charging(project):
    # Create some new charging infrastructures, append those new
    # infrastructures to the project list of infrastructures
    charging_stations = []
    charging_stations.append(
        v2gsim.model.ChargingStation(name='L2', maximum_power=7200, minimum_power=0))
    charging_stations.append(
        v2gsim.model.ChargingStation(name='L1_V1G', maximum_power=1400, minimum_power=0, post_simulation=True))
    charging_stations.append(
        v2gsim.model.ChargingStation(name='L2_V2G', maximum_power=7200, minimum_power=-7200, post_simulation=True))
    project.charging_stations.extend(charging_stations)

    #Create a data frame with the new infrastructures mix and
    # apply this mix at all the locations
    df = pd.DataFrame(index=['L2', 'L1_V1G', 'L2_V2G'],
                        data={'charging_station': charging_stations,
                                'probability': [0.0, 0.4, 0.6]})
    for location in project.locations:
        if location.category in ['Work', 'Home']:
            location.available_charging_station = df.copy()

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

    # Initiate SOC and charging infrastructures
    v2gsim.core.initialize_SOC(project, nb_iteration=2)

    # Assign a basic result function to save power demand
    for vehicle in project.vehicles:
        vehicle.result_function = v2gsim.post_simulation.netload_optimization.save_vehicle_state_for_optimization


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
    return project, myopti

# veh300=pd.read_csv('../Result/300_2019_1_battery'+str(battery)+'_renewable0.7_vehicleNum1500000vehicleGeneration.csv')[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

# sns.set()
# sns.set_style("whitegrid")
# sns.color_palette("Set2")

# batteryCostSum=veh0.sum().sum()*battery
# revenue=5501398.549063967

# plt.title('November 27,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
# plt.xlabel("Hour")
# plt.ylabel("Aggregated Energy/MWh")
# sns.lineplot(data=veh300,dashes=False).get_figure().savefig("../Figure/501Project/Nov27_"+str(battery)+".png")
# plt.show()

# def visualize(vehCap,revenue,batteryCost,day,vehicleNumber,myresult):
#     vehCap=vehCap[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]
#     vehCap['demand']=myresult['netload']
    
#     sns.set()
#     sns.set_style("whitegrid")
#     sns.color_palette("Set2")
    
#     batteryCostSum=vehCap.sum().sum()*batteryCost
#     plt.title(str(day)+',Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
#     plt.xlabel("Hour")
#     plt.ylabel("Aggregated Energy/MWh")
#     sns.lineplot(data=vehCap,dashes=False).get_figure().savefig("../Figure/501Project/'"+str(day)+'_'+str(batteryCost)+".png")
#     plt.show()

#run number
yr=2019
run_no = 1
batteryCost=8
renewablePercentage=0.7
vehicleNumber=1500000# 1.5 million BEVs in California 
days=365

for date in [0]:#100,200,300
    daysRange=range(date,date+1)
    MWtoW=1000000
    # should have battery cost/ renewable portion/ vehicle numbers
    versionName=str(yr)+'_'+str(run_no)+'_battery'+str(batteryCost)+'_renewable'+str(renewablePercentage)+ '_vehicleNum'+str(vehicleNumber)

    SimDays = 2
    SimHours = SimDays * 24
    HorizonHours = 48  ##planning horizon (e.g., 24, 48, 72 hours etc.)
    regup_margin = 0.064  ##minimum regulation up reserve as a percent of system demand, referenced from https://www.nrel.gov/docs/fy19osti/73590.pdf
    regdown_margin = 0.072 ##minimum regulation down reserve as a percent of system demand from https://www.nrel.gov/docs/fy19osti/73590.pdf


    ###Segment C.2
    from UCModel import model
    from UCModel import writeDatFile
    from UCModel import readSolutionResult

    revenueTotal=[]
    df_hydro_com = pd.read_csv('../data/hydro/HydroGenerator.csv',header=0)
    df_hydro_cap = pd.read_csv('../data/hydro/HydroDailyCapacity.csv',header=0)

    for day in daysRange: #range(days)
        print(day+1)
        pr=pd.read_csv('../data/price/priceiteration2_version3_regupregdown20.csv',header=0) 
        vehCap=pd.read_csv('../data/vehicle/VehiclesCap_iteration2_version3_regupregdown20.csv',header=0) 
        myresult=v2gResultConversion(pd.read_csv('../data/vehicle/VehiclesCap_V2G_0_2019_1_battery8_renewable0.7_vehicleNum1500000.csv',header=0),vehicleNumber)     

        iterNumber=1
        eps=10000 
        eps2=10000

        project, myopti= init_v2g()
        df_hydro=init_hydro(df_hydro_com,df_hydro_cap,day)
        print(project.locations)
        print(project.vehicles )

        while eps>10000 or eps2>5000:
            # # Load the load data
            load=init_load(day,HorizonHours)[:25]
            #CAISO1819: netload in the unit of MW
            load['Unnamed: 0'] = [dt.datetime.strptime(x,"%Y-%m-%d %H:%M") for x in load['Unnamed: 0']]
            load=load.set_index(load['Unnamed: 0'])
            load=load.drop(columns='Unnamed: 0')

            vehCap_v2g=vehCap.set_index(load[:25].index)
            pr_v2g=pr[:25].set_index(load[:25].index)
            
            # print(iterNumber)
            myresult2= myopti.solve(project, load * MWtoW,vehicleNumber, price=pr_v2g, vehCap=vehCap_v2g*MWtoW,iterNumber=iterNumber, batteryCost=batteryCost, peak_shaving='economic', SOC_margin=0.05)# convert unit from MW to W
            myresult2=v2gResultConversion(myresult2,vehicleNumber)     
            veh=init_veh(myresult2)
        
            #initialize load, generator capacity
            df_load=init_load(day,HorizonHours)
            df_gen=init_gen()
            df_solar_cap,df_solar_cons=init_solar(day,HorizonHours)
            df_wind_cap,df_wind_cons=init_wind(day,HorizonHours)
            # reindex
            df_solar_cap.index=range(HorizonHours)
            df_wind_cap.index=range(HorizonHours)
            df_load.index=range(HorizonHours)

            df_load['netload']= veh['netload']+df_load['netload']
            df_veh_cap=veh[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

            # If not feasible, add NGCC 500MWh
            for i in range(200):
                df_gen=df_gen.append({'name':'AddedNGCC'+str(i),'maxcap':500,'mincap':0,'opcost':28.374682864574172,'minup':0.0,'ramp':500,'st_cost':0.0,'var_om':3.5999999999999996,'fix_om':13170.0,'regcost':2.837468286457417},ignore_index=True)
                
            # print(df_gen['maxcap'].sum())
            # writeDatFile(df_gen,df_solar_cap,df_solar_cons,df_wind_cap,df_wind_cons,df_veh_cap,df_load,SimDays,SimHours,HorizonHours,regup_margin,regdown_margin,versionName,batteryCost)
            writeDatFile(df_gen,df_solar_cap,df_solar_cons,df_wind_cap,df_wind_cons,df_veh_cap,df_load,df_hydro,SimDays,SimHours,HorizonHours,regup_margin,regdown_margin,versionName,batteryCost)
            
            # print(df_veh_cap)
            ###Create instand and solve 
            instance = model.create_instance(versionName+'.dat')
            opt = SolverFactory("gurobi") ##SolverFactory("cplex")
            # opt.options["threads"] = 1
            H = instance.HorizonHours
            K=range(1,H+1)
        
            # pr2,vehCap2=readSolutionResult(opt,instance,K,veh,df_gen,df_solar_cons,df_wind_cons,batteryCost)
            pr2,vehCap2,mwh_pd=readSolutionResult(opt,instance,K,veh,df_gen,df_solar_cons,df_wind_cons,df_hydro,df_load,batteryCost)
            
            eps=epsilon1(pr2,vehCap2,myresult2,pr,vehCap,myresult)
            eps2=epsilon2(vehCap2,vehCap)
            
            vehCap=vehCap2
            pr=pr2
            myresult=myresult2
            iterNumber+=1
            print(eps)
            print(eps2)    
        saveResult(vehCap[:24],pr[:24],myresult,versionName,day)
        revenue=calculateRevenue(vehCap[:24],pr[:24],myresult)
        revenueTotal.append(revenue)
        print(day+1)
        # print(eps)
        # print(eps2)    
        print(revenueTotal)
        # visualize(vehCap,revenue,batteryCost,day,vehicleNumber,myresult)
        pd.DataFrame(data=revenueTotal).to_csv('../Result/'+str(day)+"_"+versionName+'Revenue.csv',index=False)

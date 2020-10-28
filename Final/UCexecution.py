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

#run number
yr=2018
run_no = 1
###Segment C.2
from UCModel import model
from UCModel import writeDatFile

# first iteration
# data_name='iteration1_version3_regupregdown120' # from V2GSIM vehicle cap
# data_name2='iteration2_version3_regupregdown120'
# data_name3='iteration3_version3_regupregdown120'

# second iteration
# data_name='iteration3_version3_regupregdown120' # from V2GSIM vehicle cap
# data_name2='iteration4_version3_regupregdown120'
# data_name3='iteration5_version3_regupregdown120'

# third iteration
data_name='iteration5_version3_regupregdown120' # from V2GSIM vehicle cap
data_name2='iteration6_version3_regupregdown120'
data_name3='iteration7_version3_regupregdown120'

SimDays = 2
SimHours = SimDays * 24
HorizonHours = 48  ##planning horizon (e.g., 24, 48, 72 hours etc.)
regup_margin = 0.064  ##minimum regulation up reserve as a percent of system demand, referenced from https://www.nrel.gov/docs/fy19osti/73590.pdf
regdown_margin = 0.072 ##minimum regulation down reserve as a percent of system demand from https://www.nrel.gov/docs/fy19osti/73590.pdf

df_gen = pd.read_csv('../data/generator/Generator.csv',header=0)
df_solar_cap=pd.read_csv('../data/generator/SolarCap.csv',header=0)[:HorizonHours]
df_solar_cons=pd.read_csv('../data/generator/SolarConstraint.csv',header=0)
df_wind_cap=pd.read_csv('../data/generator/WindCap.csv',header=0)[:HorizonHours]
df_wind_cons=pd.read_csv('../data/generator/WindConstraint.csv',header=0)
myresult=pd.read_csv('../data/vehicle/VehiclesCap_V2G_'+data_name+'.csv',header=0)
N = 6# from 10mins to 1 hour
myresult=myresult.groupby(myresult.index // N).sum()/6/1000000# from the unit of W to MW
myresult=myresult.rename(columns={'EnergyDemand':'netload','EnergyGeneration':'gen_capacity_veh','Regup':'regup_capacity_veh','Regdown':'regdown_capacity_veh'})
myresult=pd.concat([myresult,myresult],axis=0)
myresult.index=range(myresult.shape[0])
df_veh_cap=myresult[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

df_load = pd.read_csv('../data/netload/20200801CAISO.csv',header=0)[:HorizonHours]
df_load['netload']=myresult['netload']+df_load['netload']


# If not feasible, add NGCC 500MWh if it's not feasible

# capacityScalar=1.5 
# df_gen['maxcap']*=capacityScalar
# df_solar_cap['maxcap_s']*=capacityScalar
# df_wind_cap['maxcap_w']*=capacityScalar

writeDatFile(df_gen,df_solar_cap,df_solar_cons,df_wind_cap,df_wind_cons,df_veh_cap,df_load,SimDays,SimHours,HorizonHours,regup_margin,regdown_margin,data_name)

###Create instand and solve 
instance = model.create_instance(data_name+'.dat')
# instance=model.create_instance('test_iteration1.dat')
print('instance created') 
opt = SolverFactory("gurobi") ##SolverFactory("cplex")
# opt.options["threads"] = 1
H = instance.HorizonHours
K=range(1,H+1)
start = 1 ##1 to 364
end  = 2 ##2 to 366
Hour=24*(end-start)

### Store result
#Space to store results
on=[]
switch=[]
mwh=[]
regup=[]
regdown=[]
mwh_w=[]
regup_w=[]
regdown_w=[]
mwh_s=[]
regup_s=[]
regdown_s=[]
mwh_veh=[]
regup_veh=[]
regdown_veh=[]
nse=[]

for day in range(start,end):
         
    for i in K:
            instance.HorizonDemand[i] = instance.SimDemand[(day-1)*24+i]

    opt.options['TimeLimit'] = 600
    # results = opt.solve(model, load_solutions=False, tee=True)
    result = opt.solve(instance,tee=True, load_solutions=False,keepfiles=True) ##,tee=True to check number of variables ##,load_solutions=False
    instance.solutions.load_from(result)  
    # instance.display() 
    print('solution found') 
    ##Read each value of the solution 
    for v in instance.component_objects(Var, active=True):
        varobject = getattr(instance, str(v))
        a=str(v)
       
        if a=='mwh':
            for index in varobject:
                if int(index[1]>0 and index[1]<26):
                    mwh.append((index[0], day,index[1]+((day-1)*24),varobject[index].value))
                    # print ("Generator", index, v[index].value)   
                    # print('Generator',instance.mwh.get_values())                                           
      
        if a=='regup':    
            for index in varobject:
                if int(index[1]>0 and index[1]<26):
                    regup.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))
                    # print ("   ", index, v[index].value)

        if a=='regdown':    
            for index in varobject:
                if int(index[1]>0 and index[1]<26):
                    regdown.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))
                    # print ("   ", index, v[index].value)
        
        if a=='mwh_w':
            for index in varobject:
                if int(index>0 and index<26):
                    mwh_w.append((index, day,index+((day-1)*24),varobject[index].value))
                    # print ("Wind", index, v[index].value)                                                  
      
        if a=='regup_w':    
            for index in varobject:
                if int(index>0 and index<26):
                    regup_w.append((index,day,index+((day-1)*24),varobject[index].value))

        if a=='regdown_w':    
            for index in varobject:
                if int(index>0 and index<26):
                    regdown_w.append((index,day,index+((day-1)*24),varobject[index].value))
        
        if a=='mwh_s':
            for index in varobject:
                if int(index>0 and index<26):
                    mwh_s.append((index, day,index+((day-1)*24),varobject[index].value))
                    # print ("Solar", index, v[index].value)                                                  
      
        if a=='regup_s':    
            for index in varobject:
                if int(index>0 and index<26):
                    regup_s.append((index,day,index+((day-1)*24),varobject[index].value))

        if a=='regdown_s':    
            for index in varobject:
                if int(index>0 and index<26):
                    regdown_s.append((index,day,index+((day-1)*24),varobject[index].value))
        if a=='mwh_veh':
            for index in varobject:
                if int(index>0 and index<26):
                    mwh_veh.append((index, day,index+((day-1)*24),varobject[index].value))
                    # print ("Vehicle", index, v[index].value)                                                  
      
        if a=='regup_veh':    
            for index in varobject:
                if int(index>0 and index<26):
                    regup_veh.append((index,day,index+((day-1)*24),varobject[index].value))

        if a=='regdown_veh':    
            for index in varobject:
                if int(index>0 and index<26):
                    regdown_veh.append((index,day,index+((day-1)*24),varobject[index].value))
                              
#         # if a=='on':        
#         #     for index in varobject:
#         #         if int(index[1]>0 and index[1]<25):
#         #             on.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))

#         # if a=='switch':  
#         #     for index in varobject:
#         #         if int(index[1]>0 and index[1]<25):
#         #             switch.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))

#         # if a=='nse':    
#         #     for index in varobject:
#         #         if int(index[1]>0 and index[1]<25):
#         #             nse.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))
#     print(day)
#     print(str(datetime.now()))
    
regup_pd=pd.DataFrame(regup,columns=('Generator','Day','Hour','Value'))
regdown_pd=pd.DataFrame(regdown,columns=('Generator','Day','Hour','Value'))  
mwh_pd=pd.DataFrame(mwh,columns=('Generator','Day','Hour','Generation'))
mwh_pd['Reg Up']=regup_pd['Value']
mwh_pd['Reg Down']=regdown_pd['Value']

regup_w_pd=pd.DataFrame(regup_w,columns=('Generator','Day','Hour','Value'))
regdown_w_pd=pd.DataFrame(regdown_w,columns=('Generator','Day','Hour','Value'))  
mwh_w_pd=pd.DataFrame(mwh_w,columns=('Generator','Day','Hour','Generation'))
mwh_w_pd['Generator']='wind'
mwh_w_pd['Reg Up']=regup_w_pd['Value']
mwh_w_pd['Reg Down']=regdown_w_pd['Value']

regup_s_pd=pd.DataFrame(regup_s,columns=('Generator','Day','Hour','Value'))
regdown_s_pd=pd.DataFrame(regdown_s,columns=('Generator','Day','Hour','Value'))  
mwh_s_pd=pd.DataFrame(mwh_s,columns=('Generator','Day','Hour','Generation'))
mwh_s_pd['Generator']='solar'
mwh_s_pd['Reg Up']=regup_s_pd['Value']
mwh_s_pd['Reg Down']=regdown_s_pd['Value']

regup_veh_pd=pd.DataFrame(regup_veh,columns=('Generator','Day','Hour','Value'))
regdown_veh_pd=pd.DataFrame(regdown_veh,columns=('Generator','Day','Hour','Value'))  
mwh_veh_pd=pd.DataFrame(mwh_veh,columns=('Generator','Day','Hour','gen_capacity_veh'))
mwh_veh_pd['Generator']='vehicle'
mwh_veh_pd['regup_capacity_veh']=regup_veh_pd['Value']
mwh_veh_pd['regdown_capacity_veh']=regdown_veh_pd['Value']

# # get the Marginal Clearing Price for energy, frequency regulation up, and frequency regulation down
mwh_pd=pd.concat([mwh_pd,mwh_w_pd],axis=0)
mwh_pd=pd.concat([mwh_pd,mwh_s_pd],axis=0)
mwh_veh=mwh_veh_pd.rename(columns={'gen_capacity_veh':'Generation','regup_capacity_veh':'Reg Up','regdown_capacity_veh':'Reg Down'})
mwh_pd=pd.concat([mwh_pd,mwh_veh],axis=0)

mwh_veh_pd[['gen_capacity_veh','regup_capacity_veh','regdown_capacity_veh']].to_csv('../data/vehicle/VehiclesCap_'+data_name2+'.csv',index=False)
mwh_pd.to_csv('../data/generator/GeneratorResult'+data_name2+'.csv',index=False)
mwh_pd_gr=mwh_pd.groupby(mwh_pd['Hour'])['Generation','Reg Up','Reg Down'].sum()
df_load = pd.read_csv('../data/netload/20200801CAISO.csv',header=0)[:26]
mwh_pd_gr['load']=myresult['netload']+df_load['netload']
mwh_pd_gr['Generation/Load']=mwh_pd_gr['Generation']/mwh_pd_gr['load']
mwh_pd_gr['Regup/Load']=mwh_pd_gr['Reg Up']/mwh_pd_gr['load']
mwh_pd_gr['RegDown/Load']=mwh_pd_gr['Reg Down']/mwh_pd_gr['load']
# print(mwh_s_pd.groupby(mwh_s_pd['Hour'])['Generation','Reg Up','Reg Down'].sum())
# print(mwh_w_pd.groupby(mwh_s_pd['Hour'])['Generation','Reg Up','Reg Down'].sum())
# print(mwh_veh_pd.groupby(mwh_veh_pd['Hour']).sum())

# generate the cost dataframe for each generator
df_gen_param = df_gen
df_solar_cons=df_solar_cons.rename(columns={'opcost_s':'opcost','var_om_s':'var_om','regcost_s':'regcost'})
df_wind_cons=df_wind_cons.rename(columns={'opcost_w':'opcost','var_om_w':'var_om','regcost_w':'regcost'})
cost_pd=pd.concat([df_gen_param,df_solar_cons],axis=0,sort=False)
cost_pd=pd.concat([cost_pd,df_wind_cons],axis=0,sort=False)
cost_pd=cost_pd[['name','opcost','var_om','regcost']]
cost_pd=cost_pd.append(pd.DataFrame([['vehicle',120,0,120]], columns=['name','opcost','var_om','regcost']))
cost_pd["cost_e"]=cost_pd["opcost"]+cost_pd["var_om"]
cost_pd["cost_fre_d"]=cost_pd["regcost"]
cost_pd["cost_fre_u"]=cost_pd["regcost"]

cost_pd=cost_pd[['name','cost_e','cost_fre_d','cost_fre_u']].fillna(9999)
# get hourly price
cost_pd=cost_pd.sort_values(by='name')
cost_pd.index=range(cost_pd.shape[0])
cost_pd.to_csv('../data/price/cost_pd'+data_name2+'.csv',index=False)
mwh_pd=mwh_pd.sort_values(by=['Generator','Hour'])
mwh_pd=mwh_pd.reset_index(drop=True)

Hour=25
price=[]
for i in range(Hour):
    pr_e=[]
    pr_a=[]
    pr_b=[]
    pr_fre_d=[]
    pr_fre_u=[]
    for j in range(cost_pd.shape[0]):  
        pr_e.append((mwh_pd.loc[j*Hour+i,'Generation']>0).astype(int)*1*cost_pd.loc[j,"cost_e"])
        pr_fre_u.append((mwh_pd.loc[j*Hour+i,'Reg Up']>0).astype(int)*1*cost_pd.loc[j,"cost_fre_u"])
        pr_fre_d.append((mwh_pd.loc[j*Hour+i,'Reg Down']>0).astype(int)*1*cost_pd.loc[j,"cost_fre_d"])
    price.append((i,max(pr_e),max(pr_fre_u),max(pr_fre_d)))#
price_pd=pd.DataFrame(price,columns=("Hour",'pr_e','pr_fre_u','pr_fre_d'))

###to save outputs

mwh_pd_gr=pd.concat([mwh_pd_gr,price_pd],axis=1,sort=False)
print(mwh_pd_gr)
price_pd.to_csv('../data/price/price'+data_name2+'.csv',index=False)

print("complete")


# data_name3='iteration1_version3_regupregdown120'

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


# # Load the load data
load = pd.read_csv('../data/netload/20200801CAISO.csv',header=0)

#CAISO1819: netload in the unit of MW
startday = dt.datetime(2020, 8, 1)#iterate through 1 day per time

load['date_time'] = [dt.datetime.strptime(x,"%m/%d/%y %H:%M") for x in load['date_time']]
load=load.set_index(load['date_time'])
load=load.drop(columns='date_time')

# ####################################### add the component of loop around day
load = pd.DataFrame(load[startday: startday +dt.timedelta(days=1)]['netload'])
vehCap=pd.read_csv('../data/vehicle/VehiclesCap_'+data_name2+'.csv',header=0)
vehCap=vehCap.set_index(load[:25].index)
#iteration1
pr=pd.read_csv('../data/price/price'+data_name2+'.csv',header=0)
pr=pr[:25].set_index(load[:25].index)
########## put into model already
myresult= myopti.solve(project, load * 1000000,1500000, price=pr, vehCap=vehCap*1000000, peak_shaving='economic', SOC_margin=0.05)# convert unit from MW to W

# total_power_demand['total']
# myresult,model=myresult 
# # myresult['vehicle_before'] 
# # myresult['vehicle_after']) *(1500000 / len(project.vehicles)) / (1000 * 1000) 

myresult.to_csv('../data/vehicle/VehiclesCap_V2G_'+data_name3+'.csv',index=False)

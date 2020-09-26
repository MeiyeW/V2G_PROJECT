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

##run number
yr=2018
run_no = 1
SimDays = 365
SimHours = SimDays * 24
HorizonHours = 48  ##planning horizon (e.g., 24, 48, 72 hours etc.)
regup_margin = 0.15  ##minimum regulation up reserve as a percent of system demand
regdown_margin = 0.50 ##minimum regulation down reserve as a percent of total reserve
data_name = 'test2'

#read parameters for dispatchable generators  
df_gen = pd.read_csv('../data/generator/Generators.csv',header=0)
#read parameters for net load
df_load = pd.read_csv('../data/netload/CAISO1819.csv',header=0)
datinput(df_gen,df_load,SimDays,SimHours,HorizonHour,regup_margin,regdown_margin,data_name)

# print ('Complete:',data_name)

from UCModel import model

instance = model.create_instance(str(data_name)+'.dat')

opt = SolverFactory("gurobi") ##SolverFactory("cplex")
opt.options["threads"] = 1
H = instance.HorizonHours
K=range(1,H+1)
start = 1 ##1 to 364
end  = start+SimDays ##2 to 366

# the following is for storing the Marginal Clearing Price for energy and capacity market 
cost_pd=MCPStore(df_gen)

# ### Require gurobi or CPLEX #####
# Create a project and initialize it with someitineraries
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
v2gsim.core.run(project, date_from=project.date + datetime.timedelta(days=1),
                date_to=project.date + datetime.timedelta(days=2),
                reset_charging_station=False)


# Look at the results
total_power_demand = v2gsim.post_simulation.result.total_power_demand(project)

# Optimization
myopti = v2gsim.post_simulation.netload_optimization.CentralOptimization(project, 10,
                                                                         project.date + datetime.timedelta(days=1),
                                                                         project.date + datetime.timedelta(days=2),
                                                                         minimum_SOC=0.1, maximum_SOC=0.95)

for day in range(start,end):
         #load Demand time series data
    for i in K:
        instance.HorizonDemand[i] = instance.SimDemand[(day-1)*24+i]
           
    result = opt.solve(instance) ##,tee=True to check number of variables
    instance.solutions.load_from(result)   
 
    price_pd=getprice(instance,cost_pd)

    # Load the load data
    load=pd.read_csv('../data/netload/CAISO1819.csv')
    startday = datetime.datetime(2018, 7, 2)#iterate through 1 day per time

    load['date_time'] = [datetime.datetime.strptime(x,"%m/%d/%Y %H:%M") for x in load['date_time']]
    load=load.set_index(load['date_time'])
    load=load.drop(columns='date_time')

    load = pd.DataFrame(load[day: startday + day-1 +datetime.timedelta(days=1)]['demand (MW)'])

    myresult = myopti.solve(project, load * 1000000,1500000, price=price_pd,
                        peak_shaving='economic', SOC_margin=0.05)

    # Get the result in the right format
    temp_vehicle = pd.DataFrame(
        (total_power_demand['total'] - myresult['vehicle_before'] + myresult['vehicle_after']) *
        (1500000 / len(project.vehicles)) / (1000 * 1000))  # Scale up and W to MW
    temp_vehicle = temp_vehicle.rename(columns={0: 'vehicle'})
    temp_vehicle['index'] = range(0, len(temp_vehicle))
    temp_vehicle = temp_vehicle.set_index(['index'], drop=True)

    temp_load = load.copy()
    temp_load = temp_load.resample('60S')
    temp_load = temp_load.fillna (method='ffill').fillna(method='bfill')
    temp_load = temp_load.head(len(temp_vehicle))
    tempIndex = temp_load.index
    temp_load['index'] = range(0, len(temp_vehicle))
    temp_load = temp_load.set_index(['index'], drop=True)

    temp_result = pd.DataFrame(temp_load['demand (MW)'] + temp_vehicle['vehicle'])
    temp_result = temp_result.rename(columns={0: 'demand (MW)'})
    temp_result = temp_result.set_index(tempIndex)
    temp_load = temp_load.set_index(tempIndex)
    temp_vehicle = temp_vehicle.set_index(tempIndex)

    temp_vehicle_demand = pd.DataFrame(
        (myresult['vehicle_after_demand']) *    (1500000 / len(project.vehicles)) / (1000 * 1000))  # Scale up and W to MW
    temp_vehicle_demand = temp_vehicle_demand.set_index(tempIndex)

    temp_vehicle_generation = pd.DataFrame(
        (-myresult['vehicle_after_generation']) *    (1500000 / len(project.vehicles)) / (1000 * 1000))  # Scale up and W to MW
    temp_vehicle_generation = temp_vehicle_generation.set_index(tempIndex)

    temp_vehicle_regdown = pd.DataFrame(
        (myresult['vehicle_after_regdown']) *    (1500000 / len(project.vehicles)) / (1000 * 1000))  # Scale up and W to MW
    temp_vehicle_demand = temp_vehicle_demand.set_index(tempIndex)

    temp_vehicle_regup = pd.DataFrame(
        (-myresult['vehicle_after_regup']) *    (1500000 / len(project.vehicles)) / (1000 * 1000))  # Scale up and W to MW
    temp_vehicle_generation = temp_vehicle_generation.set_index(tempIndex)


    plt.plot(temp_load['demand (MW)'], label='load')
    plt.plot(temp_result['demand (MW)'], label='load + vehicles')
    plt.ylabel('Power (MW)')
    plt.legend()
    plt.show()

    # update load and generation from temp_vehivle_demand/generation
    df_load_in=temp_result
    df_gen_in=

    datinput(df_gen_in,df_load_in,SimDays,SimHours,HorizonHour,regup_margin,regdown_margin,data_name)
    from UCModel import model
    data_name = 'inner'
    instance = model.create_instance(str(data_name)+'.dat')


# ###to save outputs
# price_pd.to_csv('out_camb_R'+str(run_no)+'_'+str(yr)+'_price.csv')

# print("complete")
        
print(day)
print(str(datetime.datetime.now()))
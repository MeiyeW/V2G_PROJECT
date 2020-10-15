from __future__ import division
import datetime
import matplotlib.pyplot as plt
import cPickle as pickle
import numpy as np
import v2gsim
import pandas as pd


data_name = 'iteration1_correct'
data_name2='iteration2_correct'
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


# # Load the load data
load = pd.read_csv('../data/netload/20200801CAISO.csv',header=0)

#CAISO1819: netload in the unit of MW
startday = datetime.datetime(2020, 8, 1)#iterate through 1 day per time

load['date_time'] = [datetime.datetime.strptime(x,"%m/%d/%y %H:%M") for x in load['date_time']]
load=load.set_index(load['date_time'])
load=load.drop(columns='date_time')

# ####################################### add the component of loop around day
load = pd.DataFrame(load[startday: startday +datetime.timedelta(days=1)]['netload'])

#iteration1
pr=pd.read_csv('../data/price/price'+data_name+'.csv',header=0)
pr=pr[:25].set_index(load[:25].index)
########## put into model already
myresult= myopti.solve(project, load * 1000000,1500000, price=pr, peak_shaving='economic', SOC_margin=0.05)

# total_power_demand['total']
# myresult,model=myresult 
# # myresult['vehicle_before'] 
# # myresult['vehicle_after']) *(1500000 / len(project.vehicles)) / (1000 * 1000) 

myresult.to_csv('../data/vehicle/VehiclesCap_'+data_name2+'.csv',index=False)

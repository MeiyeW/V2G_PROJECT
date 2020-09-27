from __future__ import division
import datetime
import matplotlib.pyplot as plt
import cPickle as pickle
import numpy as np
import v2gsim 
import pandas as pd

# ### Require gurobi or CPLEX #####
# Create a project and initialize it with some itineraries
project = v2gsim.model.Project()
project = v2gsim.itinerary.from_excel(project, '../../data/NHTS/California.xlsx')
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

# Load the net load data
finalResult = pd.DataFrame()
filename = '../../data/netload/2025.pickle'
# with open(filename, 'rb') as fp:
#     net_load = pickle.load(fp)
net_load=pd.read_pickle(filename)
day = datetime.datetime(2025, 6, 17)
net_load = pd.DataFrame(net_load[day: day + datetime.timedelta(days=1)]['netload'])
net_load.head()
net_load.shape

net_load.to_csv('../../UCED/netload.csv')

pr=pd.read_csv("../../UCED/out_camb_R1_2018_price.csv")
########## put into model already
# pr=pr.iloc[0:len(net_load)]
# pr=pr.set_index(net_load.index)

# time_index=[]

# for i in range(len(pr)):
#     time_index.append(datetime.datetime.utcfromtimestamp(pr['Hour'][i]*3600))

# pr=pr.set_index(np.array(time_index))

myresult = myopti.solve(project, net_load * 1000000,1500000, price=pr, peak_shaving='economic', SOC_margin=0.05)

# # Get the result in the right format
# temp_vehicle = pandas.DataFrame(
#     (total_power_demand['total'] - myresult['vehicle_before'] + myresult['vehicle_after']) *
#     (1500000 / len(project.vehicles)) / (1000 * 1000))  # Scale up and W to MW
# temp_vehicle = temp_vehicle.rename(columns={0: 'vehicle'})
# temp_vehicle['index'] = range(0, len(temp_vehicle))
# temp_vehicle = temp_vehicle.set_index(['index'], drop=True)

# temp_netload = net_load.copy()
# temp_netload = temp_netload.resample('60S')
# temp_netload = temp_netload.fillna(method='ffill').fillna(method='bfill')
# temp_netload = temp_netload.head(len(temp_vehicle))
# tempIndex = temp_netload.index
# temp_netload['index'] = range(0, len(temp_vehicle))
# temp_netload = temp_netload.set_index(['index'], drop=True)

# temp_result = pandas.DataFrame(temp_netload['netload'] + temp_vehicle['vehicle'])
# temp_result = temp_result.rename(columns={0: 'netload'})
# temp_result = temp_result.set_index(tempIndex)
# temp_netload = temp_netload.set_index(tempIndex)
# temp_vehicle = temp_vehicle.set_index(tempIndex)

# plt.plot(temp_netload['netload'], label='netload')
# plt.plot(temp_result['netload'], label='netload + vehicles')
# plt.ylabel('Power (MW)')
# plt.legend()
# plt.show()

# temp_vehicle_demand = pandas.DataFrame(
#     (myresult['vehicle_after_demand']) *    (1500000 / len(project.vehicles)) / (1000 * 1000))  # Scale up and W to MW
# temp_vehicle_demand = temp_vehicle_demand.set_index(tempIndex)
 

# temp_vehicle_generation = pandas.DataFrame(
#     (-myresult['vehicle_after_generation']) *    (1500000 / len(project.vehicles)) / (1000 * 1000))  # Scale up and W to MW
# temp_vehicle_generation = temp_vehicle_generation.set_index(tempIndex)

# Get the result in the right format
temp_vehicle = pd.DataFrame((total_power_demand['total'] - myresult['vehicle_before'] + myresult['vehicle_after']) *(1500000 / len(project.vehicles)) / (1000 * 1000))  # Scale up and W to MW
temp_vehicle = temp_vehicle.rename(columns={0: 'vehicle'})
temp_vehicle['index'] = range(0, len(temp_vehicle))
temp_vehicle = temp_veyyhicle.set_index(['index'], drop=True)

temp_load = load.copy()
temp_load = temp_load.resample('60S')
temp_load = temp_load.fillna (method='ffill').fillna(method='bfill')
temp_load = temp_load.head(len(temp_vehicle))
tempIndex = temp_load.index
temp_load['index'] = range(0, len(temp_vehicle))
temp_load = temp_load.set_index(['index'], drop=True)

temp_result = pd.DataFrame(temp_load['demand (MW)'] + temp_vehicle['vehicle']) # new load data
temp_result = temp_result.rename(columns={0: 'demand (MW)'})
temp_result = temp_result.set_index(tempIndex)
temp_load = temp_load.set_index(tempIndex)
temp_vehicle = temp_vehicle.set_index(tempIndex)

temp_vehicle_demand = pd.DataFrame((myresult['vehicle_after_demand']) *    (1500000 / len(project.vehicles)) / (1000 * 1000))  # Scale up and W to MW
temp_vehicle_demand = temp_vehicle_demand.set_index(tempIndex)

# get input data fro UC model
temp_vehicle_generation = pd.DataFrame(
    (-myresult['vehicle_after_generation']) *    (1500000 / len(project.vehicles)) / (1000 * 1000))  # Scale up and W to MW
temp_vehicle_generation['regdown_capacity_veh']=(myresult['vehicle_after_regdown']) * (1500000 / len(project.vehicles)) / (1000 * 1000)  # Scale up and W to MW
temp_vehicle_generation['regup_capacity_veh']=(-myresult['vehicle_after_regup']) *    (1500000 / len(project.vehicles)) / (1000 * 1000)  # Scale up and W to MW
temp_vehicle_generation = temp_vehicle_generation.set_index(tempIndex)
temp_vehicle_generation.rename(columns={"vehicle_after_generation": "gen_capacity_veh", "B": "c"})

temp_vehicle_generation.to_csv('../data/vehicle/VehicleCap.csv',index=False)

plt.plot(temp_load['demand (MW)'], label='load')
plt.plot(temp_result['demand (MW)'], label='load + vehicles')
plt.ylabel('Power (MW)')
plt.legend()
plt.show()
# import pdb
# pdb.set_trace()
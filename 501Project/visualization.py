import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
import seaborn as sns

# veh0=pd.read_csv('../Result/0_2019_1_battery8_renewable0.7_vehicleNum1500000vehicleGeneration.csv')[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

# sns.set()
# sns.set_style("whitegrid")
# sns.color_palette("Set2")
# vehicleNumber=1500000

# revenue=pd.read_csv('../Result/0_2019_1_battery8_renewable0.7_vehicleNum1500000Revenue.csv')[0,0]
# batteryCostSum=veh0.sum().sum()*8

# plt.title('January 01,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
# plt.xlabel("Hour")
# plt.ylabel("Aggregated Energy/MWh")
# sns.lineplot(data=veh0,dashes=False).get_figure().savefig("../Figure/501Project/Jan01_8.png")
# plt.show()

# ########################
# veh100=pd.read_csv('../Result/100_2019_1_battery8_renewable0.7_vehicleNum1500000vehicleGeneration.csv')
# veh100=veh100[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

# sns.set()
# sns.set_style("whitegrid")
# sns.color_palette("Set2")

# batteryCostSum=veh0.sum().sum()*8
# revenue=4957204.7555826465
# plt.title('May 11,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
# plt.xlabel("Hour")
# plt.ylabel("Aggregated Energy/MWh")
# sns.lineplot(data=veh100,dashes=False).get_figure().savefig("../Figure/501Project/May11_8.png")
# plt.show()
# #########################
# veh200=pd.read_csv('../Result/200_2019_1_battery8_renewable0.7_vehicleNum1500000vehicleGeneration.csv')
# veh200=veh200[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

# sns.set()
# sns.set_style("whitegrid")
# sns.color_palette("Set2")
# batteryCostSum=veh0.sum().sum()*8
# revenue=4311847.026029048
# plt.title('August 19,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
# plt.xlabel("Hour")
# plt.ylabel("Aggregated Energy/MWh")
# sns.lineplot(data=veh200,dashes=False).get_figure().savefig("../Figure/501Project/Aug19_8.png")
# plt.show()

# ###############
# veh300=pd.read_csv('../Result/300_2019_1_battery8_renewable0.7_vehicleNum1500000vehicleGeneration.csv')[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

# sns.set()
# sns.set_style("whitegrid")
# sns.color_palette("Set2")
# batteryCostSum=veh0.sum().sum()*8
# revenue=4753426.22792077
# plt.title('November 27,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
# plt.xlabel("Hour")
# plt.ylabel("Aggregated Energy/MWh")
# sns.lineplot(data=veh300,dashes=False).get_figure().savefig("../Figure/501Project/Nov27_8.png")
# plt.show()

# #######################
# veh0=pd.read_csv('../Result/0_2019_1_battery20_renewable0.7_vehicleNum1500000vehicleGeneration.csv')[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

# sns.set()
# sns.set_style("whitegrid")
# sns.color_palette("Set2")

# revenue=6183397.192447799
# batteryCostSum=veh0.sum().sum()*20

# plt.title('January 01,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
# plt.xlabel("Hour")
# plt.ylabel("Aggregated Energy/MWh")
# sns.lineplot(data=veh0,dashes=False).get_figure().savefig("../Figure/501Project/Jan01_20.png")
# plt.show()

# ########################
# veh100=pd.read_csv('../Result/100_2019_1_battery20_renewable0.7_vehicleNum1500000vehicleGeneration.csv')
# veh100=veh100[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

# sns.set()
# sns.set_style("whitegrid")
# sns.color_palette("Set2")

# batteryCostSum=veh0.sum().sum()*20
# revenue=6261247.665374686
# plt.title('May 11,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
# plt.xlabel("Hour")
# plt.ylabel("Aggregated Energy/MWh")
# sns.lineplot(data=veh100,dashes=False).get_figure().savefig("../Figure/501Project/May11_20.png")
# plt.show()
# #########################
# veh200=pd.read_csv('../Result/200_2019_1_battery20_renewable0.7_vehicleNum1500000vehicleGeneration.csv')
# veh200=veh200[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

# sns.set()
# sns.set_style("whitegrid")
# sns.color_palette("Set2")
# batteryCostSum=veh0.sum().sum()*20
# revenue=5594037.880173842
# plt.title('August 19,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
# plt.xlabel("Hour")
# plt.ylabel("Aggregated Energy/MWh")
# sns.lineplot(data=veh200,dashes=False).get_figure().savefig("../Figure/501Project/Aug19_20.png")
# plt.show()

# ###############
# veh300=pd.read_csv('../Result/300_2019_1_battery20_renewable0.7_vehicleNum1500000vehicleGeneration.csv')[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

# sns.set()
# sns.set_style("whitegrid")
# sns.color_palette("Set2")
# batteryCostSum=veh0.sum().sum()*20
# revenue=6397099.193238395
# plt.title('November 27,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
# plt.xlabel("Hour")
# plt.ylabel("Aggregated Energy/MWh")
# sns.lineplot(data=veh300,dashes=False).get_figure().savefig("../Figure/501Project/Nov27_20.png")
# plt.show()

battery=15
veh0=pd.read_csv('../Result/0_2019_1_battery'+str(battery)+'_renewable0.7_vehicleNum1500000vehicleGeneration.csv')[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

sns.set()
sns.set_style("whitegrid")
sns.color_palette("Set2")
vehicleNumber=1500000

revenue=5619000.520805471
batteryCostSum=veh0.sum().sum()*battery

plt.title('January 01,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
plt.xlabel("Hour")
plt.ylabel("Aggregated Energy/MWh")
sns.lineplot(data=veh0,dashes=False).get_figure().savefig("../Figure/501Project/Jan01_"+str(battery)+".png")
plt.show()

########################
veh100=pd.read_csv('../Result/100_2019_1_battery'+str(battery)+'_renewable0.7_vehicleNum1500000vehicleGeneration.csv')
veh100=veh100[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

sns.set()
sns.set_style("whitegrid")
sns.color_palette("Set2")

batteryCostSum=veh0.sum().sum()*battery
revenue=5680861.370283935
plt.title('May 11,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
plt.xlabel("Hour")
plt.ylabel("Aggregated Energy/MWh")
sns.lineplot(data=veh100,dashes=False).get_figure().savefig("../Figure/501Project/May11_"+str(battery)+".png")
plt.show()
#########################
veh200=pd.read_csv('../Result/200_2019_1_battery'+str(battery)+'_renewable0.7_vehicleNum1500000vehicleGeneration.csv')
veh200=veh200[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

sns.set()
sns.set_style("whitegrid")
sns.color_palette("Set2")
batteryCostSum=veh0.sum().sum()*battery
revenue=5515323.492570515
plt.title('August 19,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
plt.xlabel("Hour")
plt.ylabel("Aggregated Energy/MWh")
sns.lineplot(data=veh200,dashes=False).get_figure().savefig("../Figure/501Project/Aug19_"+str(battery)+".png")
plt.show()

###############
veh300=pd.read_csv('../Result/300_2019_1_battery'+str(battery)+'_renewable0.7_vehicleNum1500000vehicleGeneration.csv')[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

sns.set()
sns.set_style("whitegrid")
sns.color_palette("Set2")
batteryCostSum=veh0.sum().sum()*battery
revenue=5324092.935318929
plt.title('November 27,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
plt.xlabel("Hour")
plt.ylabel("Aggregated Energy/MWh")
sns.lineplot(data=veh300,dashes=False).get_figure().savefig("../Figure/501Project/Nov27_"+str(battery)+".png")
plt.show()
# ##########
###
# battery=12
# veh0=pd.read_csv('../Result/0_2019_1_battery'+str(battery)+'_renewable0.7_vehicleNum1500000vehicleGeneration.csv')[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

# sns.set()
# sns.set_style("whitegrid")
# sns.color_palette("Set2")
# vehicleNumber=1500000

# revenue=5430162.583468214
# batteryCostSum=veh0.sum().sum()*battery

# plt.title('January 01,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
# plt.xlabel("Hour")
# plt.ylabel("Aggregated Energy/MWh")
# sns.lineplot(data=veh0,dashes=False).get_figure().savefig("../Figure/501Project/Jan01_"+str(battery)+".png")
# plt.show()

# ########################
# veh100=pd.read_csv('../Result/100_2019_1_battery'+str(battery)+'_renewable0.7_vehicleNum1500000vehicleGeneration.csv')
# veh100=veh100[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

# sns.set()
# sns.set_style("whitegrid")
# sns.color_palette("Set2")

# batteryCostSum=veh0.sum().sum()*battery
# revenue=5672974.007113654
# plt.title('May 11,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
# plt.xlabel("Hour")
# plt.ylabel("Aggregated Energy/MWh")
# sns.lineplot(data=veh100,dashes=False).get_figure().savefig("../Figure/501Project/May11_"+str(battery)+".png")
# plt.show()
# #########################
# veh200=pd.read_csv('../Result/200_2019_1_battery'+str(battery)+'_renewable0.7_vehicleNum1500000vehicleGeneration.csv')
# veh200=veh200[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

# sns.set()
# sns.set_style("whitegrid")
# sns.color_palette("Set2")
# batteryCostSum=veh0.sum().sum()*battery
# revenue=5302461.011697237
# plt.title('August 19,Revenue '+str(round((revenue-batteryCostSum)/vehicleNumber,3))+'$/vehicle')
# plt.xlabel("Hour")
# plt.ylabel("Aggregated Energy/MWh")
# sns.lineplot(data=veh200,dashes=False).get_figure().savefig("../Figure/501Project/Aug19_"+str(battery)+".png")
# plt.show()

# ###############
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
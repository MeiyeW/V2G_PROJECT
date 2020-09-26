# run both UCModel.py and UCexecution.py in the terminal.
# UCModel.py: Segment A is for data setup, segment B is the optimization model
# UCexucetion.py: Segment C runs UC problem and post process result.

from __future__ import division # convert int or long division arguments to floating point values before division
from pyomo.environ import *
from pyomo.opt import SolverFactory
import itertools
import csv
import pandas as pd
import numpy as np

#  
SimDays = 365
SimHours = SimDays * 24
HorizonHours = 48  ##planning horizon (e.g., 24, 48, 72 hours etc.)
regup_margin = 0.15  ##minimum regulation up reserve as a percent of system demand
regdown_margin = 0.50 ##minimum regulation down reserve as a percent of total reserve

data_name = 'test2'
#read parameters for dispatchable generators  
df_gen = pd.read_csv('../data/generator/Generators.csv',header=0)
df_wind_cap=pd.read_csv('../data/generator/WindCap.csv',header=0)
df_solar_cap=pd.read_csv('../data/generator/SolarCap.csv',header=0)
df_windsolar_cons=pd.read_csv('../data/generator/WindSolarConstraint.csv',header=0)
df_vehicle=pd.read_csv('../data/netload/Vehicle.csv',header=0)

#read parameters for net load
df_load = pd.read_csv('../data/netload/CAISO1819.csv',header=0)
print('load_CAISO1819') 


######====== write data.dat file ======########
# data.dat file is the data files for loading data into optimization model with pyomo

with open(''+str(data_name)+'.dat', 'w') as f:

# generators set  
    f.write('set Generators :=\n')
    for gen in range(0,len(df_gen)):
        unit_name = df_gen.loc[gen,'name']
        unit_name = unit_name.replace(' ','_')
        f.write(unit_name + ' ')
    f.write(';\n\n')

# wind solar set  

f.write('set WindSolar :=\n')
    for gen in range(0,len(df_windsolar_cons)):
        unit_name = df_windsolar_cons.loc[gen,'name']
        unit_name = unit_name.replace(' ','_')
        f.write(unit_name + ' ')
    f.write(';\n\n')

# Vehicle set  
    f.write('set Vehicle :=\n')
    unit_name = 'vehicle'
    f.write(unit_name + ' ')
    f.write(';\n\n')
     
####### simulation period and horizon
    f.write('param SimHours := %d;' % SimHours)
    f.write('\n')
    f.write('param SimDays:= %d;' % SimDays)
    f.write('\n\n')   
    f.write('param HorizonHours := %d;' % HorizonHours)
    f.write('\n\n')
    f.write('param regup_margin := %0.3f;' % regup_margin)
    f.write('\n\n')
    f.write('param regdown_margin := %0.3f;' % regdown_margin)
    f.write('\n\n')


####### create parameter matrix for generators
    f.write('param:' + '\t')
    for c in df_gen.columns:
        if c != 'name':
            f.write(c + '\t')
    f.write(':=\n\n')
    for i in range(0,len(df_gen)):    
        for c in df_gen.columns:
            if c == 'name':
                unit_name = df_gen.loc[i,'name']
                unit_name = unit_name.replace(' ','_')
                f.write(unit_name + '\t')  
            else:
                f.write(str((df_gen.loc[i,c])) + '\t')               
        f.write('\n')
    f.write(';\n\n')     

####### create parameter matrix for solar wind generators
    f.write('param:' + '\t')
    for c in df_windsolar_cons.columns:
        if c != 'name':
            f.write(c + '\t')
    f.write(':=\n\n')
    for i in range(0,len(df_windsolar_cons)):    
        for c in df_windsolar_cons.columns:
            if c == 'name':
                unit_name = df_windsolar_cons.loc[i,'name']
                unit_name = unit_name.replace(' ','_')
                f.write(unit_name + '\t')  
            else:
                f.write(str((df_windsolar_cons.loc[i,c])) + '\t')               
        f.write('\n')
    f.write(';\n\n') 

####### Hourly timeseries (load)
    # load (hourly)
    f.write('param:' + '\t' + 'SimDemand:=' + '\n')      
    for h in range(0,len(df_load)): 
        f.write(str(h+1) + '\t' + str(df_load.loc[h,'cleaned demand (MW)']) + '\n')
    f.write(';\n\n')

####### Wind and Solar Cap data ###
f.write('param:' + '\t' + 'WindCap:=' + '\n')      
    for h in range(0,len(df_wind_cap)): 
        f.write(str(h+1) + '\t' + str(df_wind_cap.loc[h,'MW']) + '\n')
    f.write(';\n\n')

f.write('param:' + '\t' + 'SolarCap:=' + '\n')      
    for h in range(0,len(df_solar_cap)): 
        f.write(str(h+1) + '\t' + str(df_solar_cap.loc[h,'MW']) + '\n')
    f.write(';\n\n')

######## Vehicle Cap data ######


print ('Complete:',data_name)


# creating optimization with pyomo
model = AbstractModel()
########## ===== Generators set ====== #######
model.WindSolar=Set()
model.Vehicle=Set()
model.Generators = Set()

######===== Parameters/initial_conditions to run simulation ======####### 
# Full range of time series information
model.SimHours = Param(within=PositiveIntegers)
model.SH_periods = RangeSet(1,model.SimHours+1)
model.SimDays = Param(within=PositiveIntegers)
model.SD_periods = RangeSet(1,model.SimDays+1)

# Operating horizon information 
model.HorizonHours = Param(within=PositiveIntegers)
model.HH_periods = RangeSet(0,model.HorizonHours)
model.hh_periods = RangeSet(1,model.HorizonHours)
model.ramp_periods = RangeSet(2,24)

#Demand over simulation period
model.SimDemand = Param(model.SH_periods, within=NonNegativeReals)
#Horizon demand
model.HorizonDemand = Param(model.hh_periods,within=NonNegativeReals,initialize=0,mutable=True)

### Minimum reserve as a percent of total demand 
model.regup_margin= Param(within=NonNegativeReals)
model.regdown_margin= Param(within=NonNegativeReals) 

##Initial conditions
model.ini_on = Param(model.Generators, within=Binary, initialize=0,mutable=True)  
model.ini_mwh = Param(model.Generators,initialize=0,mutable=True)

#####==== Parameters for dispatchable resources ===####
#Max capacity
model.maxcap = Param(model.Generators)
#Min capacity
model.mincap = Param(model.Generators)
#operational cost 
model.opcost = Param(model.Generators)
#Variable O&M
model.var_om = Param(model.Generators)
#Start cost
model.st_cost = Param(model.Generators)
#Ramp rate: RL
model.ramp  = Param(model.Generators)
#Minimun up time
model.minup = Param(model.Generators)
#regulation eligibility
model.regelig = Param(model.Generators)
#regulation cost
model.regcost = Param(model.Generators)


#####=======================Decision variables for dispatchable resources======================########
##Amount of day-ahead energy generated by each generator at each hour
model.mwh = Var(model.Generators,model.HH_periods, within=NonNegativeReals,initialize=0)

##Amount of day-ahead capacity for regulation up by each generator at each hour
model.regup = Var(model.Generators,model.HH_periods, within=NonNegativeReals,initialize=0)

##Amount of day-ahead capacity for regulation down by each generator at each hour
model.regdown = Var(model.Generators,model.HH_periods, within=NonNegativeReals,initialize=0)

#1 if unit is on in hour i, otherwise 0
model.on = Var(model.Generators,model.HH_periods, within=Binary, initialize=0)

#1 if unit is switching on in hour i, otherwise 0
model.switch = Var(model.Generators,model.HH_periods, within=Binary,initialize=0)

#Amount of non served energy offered by an unit in each hour
model.nse = Var(model.HH_periods, within=NonNegativeReals,initialize=0)

#####==== Parameters for wind/solar ===####
#Max capacity
model.maxcap_ws = Param(model.WindSolar,model.HH_periods)
#Min capacity
model.mincap_ws = Param(model.WindSolar,model.HH_periods)
#operational cost
model.opcost_ws = Param(model.WindSolar)
#Variable O&M
model.var_om_ws = Param(model.WindSolar)
#Start cost
model.st_cost_ws = Param(model.WindSolar)
#Ramp rate: RL
model.ramp_ws  = Param(model.WindSolar)
#Minimun up time
model.minup_ws = Param(model.WindSolar)
#regulation eligibility
model.regelig_ws = Param(model.WindSolar)
#regulation cost
model.regcost_ws = Param(model.WindSolar)

#####=======================Decision variables for wind/solar======================########

##Amount of day-ahead energy generated by each generator at each hour
model.mwh_ws = Var(model.WindSolar,model.HH_periods, within=NonNegativeReals,initialize=0)

##Amount of day-ahead capacity for regulation up by each generator at each hour
model.regup_ws = Var(model.WindSolar,model.HH_periods, within=NonNegativeReals,initialize=0)

##Amount of day-ahead capacity for regulation down by each generator at each hour
model.regdown_ws = Var(model.WindSolar,model.HH_periods, within=NonNegativeReals,initialize=0)

#1 if unit is on in hour i, otherwise 0
model.on_ws = Var(model.WindSolar,model.HH_periods, within=Binary, initialize=0)

#1 if unit is switching on in hour i, otherwise 0
model.switch_ws = Var(model.WindSolar,model.HH_periods, within=Binary,initialize=0)

#Amount of non served energy offered by an unit in each hour
model.nse_ws = Var(model.HH_periods, within=NonNegativeReals,initialize=0)


######===========Parameters for Vehicles=============================###
#vehicle generation
model.gen_capacity_veh=Param(model.Vehicle,model.HH_periods)
model.regup_capacity_veh=Param(model.Vehicle,model.HH_periods)
model.regdown_capacity_veh=Param(model.Vehicle,model.HH_periods) 
model.var_veh=Param(model.HH_periods) 

#####=======================Decision variables for vehicles======================########
#Vehicle:
model.mwh_veh=Var(model.Vehicle,model.HH_periods, within=NonNegativeReals,initialize=0)
model.regup_veh=Var(model.Vehicle,model.HH_periods, within=NonNegativeReals,initialize=0)
model.regdown_veh=Var(model.Vehicle,model.HH_periods, within=NonNegativeReals,initialize=0)


def SysCost(model):
    operational = sum(model.mwh[j,i]*(model.opcost[j]+model.var_om[j]) for i in model.hh_periods for j in model.Generators)+
    sum(model.mwh_ws[j,i]*(model.opcost[j]+model.var_om_ws[j]) for i in model.hh_periods for j in model.WindSolar)+
    sum(model.mwh_veh[j,i]*(model.var_veh[j]) for i in model.hh_periods for j in model.Vehicle)

    starts = sum(model.st_cost[j]*model.switch[j,i] for i in model.hh_periods for j in model.Generators)+
    sum(model.st_cost_ws[j]*model.switch_ws[j,i] for i in model.hh_periods for j in model.WindSolar)

    regulationup_capacity = sum(model.regup[j,i]*model.regcost[j]  for i in model.hh_periods for j in model.Generators)+
    sum(model.regup_ws[j,i]*model.regcost[j] for i in model.hh_periods for j in model.WindSolar)+
    sum(model.regup_veh[j,i]*(model.var_veh[j]) for i in model.hh_periods for j in model.Vehicle)

    regulationdown_capacity = sum(model.regdown[j,i]*model.regcost[j] for i in model.hh_periods for j in model.Generators)+
    sum(model.regdown_ws[j,i]*model.regcost[j] for i in model.hh_periods for j in model.WindSolar)+
    sum(model.regdown_veh[j,i]*(model.var_veh[j]) for i in model.hh_periods for j in model.Vehicle) 
    #0.5 and 0.3 are the scalar factor for unit cost of regulation up and down compared to variable operational cost, can be changed
    nonserved = sum(model.nse[i]*20 for i in model.hh_periods)+
    sum(model.nse_ws[i]*10 for i in model.hh_periods)
    #20 is the cost of non-served energy [$/MWh], can be changed
    #10 is the cost of non-served energy for wind and solar[$/MWh], can be changed
    
    return operational +starts +regulationup_capacity + regulationdown_capacity + nonserved 
model.SystemCost = Objective(rule=SysCost, sense=minimize)

######========== Logical Constraint =========#############
##Switch is 1 if unit is turned on in current period
def SwitchCon(model,j,i):
    return model.switch[j,i] >= 1 - model.on[j,i-1] - (1 - model.on[j,i])
model.SwitchConstraint = Constraint(model.Generators,model.hh_periods,rule = SwitchCon)
 
 def SwitchCon_ws(model,j,i):
    return model.switch_ws[j,i] >= 1 - model.on_ws[j,i-1] - (1 - model.on_ws[j,i])
model.SwitchConstraint_ws = Constraint(model.WindSolar,model.hh_periods,rule = SwitchCon_ws)
 
######========== Up/Down Time Constraint =========#############
##Min Up time
def MinUp(model,j,i,k):
    if i > 0 and k > i and k < min(i+model.minup[j]-1,model.HorizonHours):
        return model.on[j,i] - model.on[j,i-1] <= model.on[j,k]
    else: 
        return Constraint.Skip
model.MinimumUp = Constraint(model.Generators,model.HH_periods,model.HH_periods,rule=MinUp)

def MinUp_ws(model,j,i,k):
    if i > 0 and k > i and k < min(i+model.minup_ws[j]-1,model.HorizonHours):
        return model.on_ws[j,i] - model.on_ws[j,i-1] <= model.on_ws[j,k]
    else: 
        return Constraint.Skip
model.MinimumUp_ws = Constraint(model.WindSolar,model.HH_periods,model.HH_periods,rule=MinUp_ws)

##Min Down time
def MinDown(model,j,i,k):
   if i > 0 and k > i and k < min(i+model.mindn[j]-1,model.HorizonHours):
       return model.on[j,i-1] - model.on[j,i] <= 1 - model.on[j,k]
   else:
       return Constraint.Skip
model.MinimumDown = Constraint(model.Generators,model.HH_periods,model.HH_periods,rule=MinDown)

##Min Down time
def MinDown_ws(model,j,i,k):
   if i > 0 and k > i and k < min(i+model.mindn_ws[j]-1,model.HorizonHours):
       return model.on_ws[j,i-1] - model.on_ws[j,i] <= 1 - model.on_ws[j,k]
   else:
       return Constraint.Skip
model.MinimumDown_ws = Constraint(model.WindSolar,model.HH_periods,model.HH_periods,rule=MinDown_ws)

######==========Ramp Rate Constraints =========#############
def Ramp1(model,j,i):
    a = model.mwh[j,i]
    b = model.mwh[j,i-1]
    return a - b <= model.ramp[j]* model.on[j,i]+ model.mincap[j]*model.switch[j,i]
model.RampCon1 = Constraint(model.Generators,model.ramp_periods,rule=Ramp1)

def Ramp1_ws(model,j,i):
    a = model.mwh_ws[j,i]
    b = model.mwh_ws[j,i-1]
    return a - b <= model.ramp_ws[j]* model.on_ws[j,i]+ model.mincap_ws[j,i]*model.switch_ws[j,i]
model.RampCon1_ws = Constraint(model.WindSolar,model.ramp_periods,rule=Ramp1_ws)

def Ramp2(model,j,i):
    a = model.mwh[j,i]
    b = model.mwh[j,i-1]
    return b - a <= model.ramp[j]* model.on[j,i-1]+ model.mincap[j]*(model.on[j,i-1]-model.on[j,i]+model.switch[j,i])
model.RampCon2 = Constraint(model.Generators,model.ramp_periods,rule=Ramp2)

def Ramp2_ws(model,j,i):
    a = model.mwh_ws[j,i]
    b = model.mwh_ws[j,i-1]
    return b - a <= model.ramp_ws[j]* model.on_ws[j,i-1]+ model.mincap_ws[j,i]*(model.on_ws[j,i-1]-model.on_ws[j,i]+model.switch_ws[j,i])
model.RampCon2_ws = Constraint(model.WindSolar,model.ramp_periods,rule=Ramp2_ws)

######=========== Capacity Constraints ============##########
#Constraints for Max & Min Capacity of dispatchable resources
def MaxC(model,j,i):
    return model.mwh[j,i]  <= model.on[j,i] * model.maxcap[j] 
model.MaxCap= Constraint(model.Generators,model.hh_periods,rule=MaxC)

def MaxC_ws(model,j,i):
    return model.mwh_ws[j,i]  <= model.on_ws[j,i] * model.maxcap_ws[j,i] 
model.MaxCap_ws= Constraint(model.WindSolar,model.hh_periods,rule=MaxC_ws)

def MinC(model,j,i):
    return model.mwh[j,i] >= model.on[j,i] * model.mincap[j]
model.MinCap= Constraint(model.Generators,model.hh_periods,rule=MinC)

def MinC_ws(model,j,i):
    return model.mwh_ws[j,i]  >= model.on_ws[j,i] * model.mincap_ws[j,i] 
model.MinCap_ws= Constraint(model.WindSolar,model.hh_periods,rule=MinC_ws)

def MaxC_veh(model,j,i):
    return model.mwh_veh[j,i]  <= model.gen_capacity_veh[j,i] 
model.MaxCap_veh= Constraint(model.Vehicle,model.hh_periods,rule=MaxC_veh)

def MinC_veh(model,j,i):
    return model.mwh_veh[j,i]  >= 0
model.MinCap_veh= Constraint(model.Vehicle,model.hh_periods,rule=MinC_veh)

def MaxRegUp_veh(model,j,i):
    return model.regup_veh[j,i]  <= model.regup_capacity_veh[j,i] 
model.MaxRegUp_veh= Constraint(model.Vehicle,model.hh_periods,rule=MaxRegUp_veh)

def MaxRegDown_veh(model,j,i):
    return model.regdown_veh[j,i]  <= model.regdown_capacity_veh[j,i] 
model.MaxRegDown_veh= Constraint(model.Vehicle,model.hh_periods,rule=MaxRegDown_veh)


######===================Energy, regulation capacity and zero-sum constraints ==================########

##System Energy Requirement
def SysEnergy(model,i):
    return sum(model.mwh[j,i] for j in model.Generators) +model.nse[i] +sum(model.mwh_ws[j,i] for j in model.WindSolar) +model.nse_ws[i] +sum(model.mwh_veh[j,i] for j in model.Vehicle)  >= model.HorizonDemand[i] 
model.SysEnergy = Constraint(model.hh_periods,rule=SysEnergy)

##Regulation up Reserve Requirement
def RegulationUp(model,i):
    return sum(model.regup[j,i] for j in model.Generators)+sum(model.regup_ws[j,i] for j in model.WindSolar)+sum(model.regup_veh[j,i] for j in model.Vehicle) >= model.regup_margin * model.HorizonDemand[i] 
model.RegulationUp = Constraint(model.hh_periods,rule=RegulationUp)           

##Regulation up reserve can only be offered by units that are online
def RegulationUp2(model,j,i):
    return model.regup[j,i] <= model.on[j,i]*model.maxcap[j]-model.mwh[j,i] 
model.RegulationUp2= Constraint(model.Generators,model.hh_periods,rule=RegulationUp2) 

##Regulation up reserve can only be offered by units that are online
def RegulationUp2_ws(model,j,i):
    return model.regup_ws[j,i] <= model.on_ws[j,i]*model.maxcap_ws[j,i]-model.mwh_ws[j,i] 
model.RegulationUp2_ws= Constraint(model.WindSolar,model.hh_periods,rule=RegulationUp_ws) 

##Regulation down Reserve Requirement
def RegulationDown(model,i):
    return sum(model.regdown[j,i] for j in model.Generators)+sum(model.regdown_ws[j,i] for j in model.WindSolar)+sum(model.regdown_veh[j,i] for j in model.Vehicle) >= model.regdown_margin * model.HorizonDemand[i] 
model.RegulationDown = Constraint(model.hh_periods,rule=RegulationDown)  

##Regulation up reserve can only be offered by units that are online
def RegulationDown2(model,j,i):
    return model.regdown[j,i] <= model.mwh[j,i]- model.on[j,i]*model.mincap[j] 
model.RegulationDown2= Constraint(model.Generators,model.hh_periods,rule=RegulationDown2) 

def RegulationDown2_ws(model,j,i):
    return model.regdown_ws[j,i] <= model.mwh_ws[j,i]- model.on_ws[j,i]*model.mincap_ws[j,i] 
model.RegulationDown2_ws= Constraint(model.WindSolar,model.hh_periods,rule=RegulationDown2_ws) 

######========== Zero Sum Constraint =========#############
# for each generator, total energy for energy market and capacity market can not exceed the maximum capacity
def ZeroSum(model,j,i):
    return model.mwh[j,i] + model.regup[j,i] - model.regdown[j,i]<= model.maxcap[j]
model.ZeroSumConstraint=Constraint(model.Generators,model.hh_periods,rule=ZeroSum)


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

#  coding: utf-8

######=================================================########
######               Segment A.1                       ########
######=================================================########


SimDays = 365
SimHours = SimDays * 24
HorizonHours = 24  ##planning horizon (e.g., 24, 48, 72 hours etc.)
regup_margin = 0.15  ##minimum regulation up reserve as a percent of system demand
regdown_margin = 0.50 ##minimum regulation down reserve as a percent of total reserve

data_name = 'test'#
######=================================================########
######               Segment A.2                       ########
######=================================================########

#read parameters for dispatchable generators  
df_gen = pd.read_csv('test_generators.csv',header=0)

#read parameters for net load
df_load = pd.read_csv('test_load.csv',header=0) 


######=================================================########
######               Segment A.4                       ########
######=================================================########

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

######=================================================########
######               Segment A.9                       ########
######=================================================########

####### Hourly timeseries (load)
    # load (hourly)
    f.write('param:' + '\t' + 'SimDemand:=' + '\n')      
    for h in range(0,len(df_load)): 
        f.write(str(h+1) + '\t' + str(df_load.loc[h,'Demand']) + '\n')
    f.write(';\n\n')

print ('Complete:',data_name)


######=================================================########
######               Segment B.1                       ########
######=================================================########
# creating optimization with pyomo


model = AbstractModel()

########## ===== Generators set ====== #######
model.Generators = Set( )

#####==== Parameters for dispatchable resources ===####

#Max capacity
model.maxcap = Param(model.Generators)
#Min capacity
model.mincap = Param(model.Generators)
#Heat rate
model.heat_rate = Param(model.Generators)
#Fuel cost
model.fuel_cost = Param(model.Generators)
#Variable O&M
model.var_om = Param(model.Generators)
#Start cost
model.st_cost = Param(model.Generators)
#Ramp rate: RL
model.ramp  = Param(model.Generators)
#Minimun up time
model.minup = Param(model.Generators)
#Minmun down time
model.mindn = Param(model.Generators)

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

######=======================Decision variables======================########
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

######================Objective function=============########

def SysCost(model):
    operational = sum(model.mwh[j,i]*(model.heat_rate[j]*model.fuel_cost[j]+model.var_om[j]) for i in model.hh_periods for j in model.Generators)
    starts = sum(model.st_cost[j]*model.switch[j,i] for i in model.hh_periods for j in model.Generators)
    regulationup_capacity = sum(model.regup[j,i]*(model.heat_rate[j]*model.fuel_cost[j]+ model.var_om[j])*0.5 for i in model.hh_periods for j in model.Generators)  
    regulationdown_capacity = sum(model.regdown[j,i]*(model.heat_rate[j]*model.fuel_cost[j]+ model.var_om[j])*0.3 for i in model.hh_periods for j in model.Generators)  
    #0.5 and 0.3 are the scalar factor for unit cost of regulation up and down compared to variable operational cost, can be changed
    nonserved = sum(model.nse[i]*20 for i in model.hh_periods)
    #20 is the cost of non-served energy [$/MWh], can be changed
    
    return operational +starts +regulationup_capacity + regulationdown_capacity + nonserved 
model.SystemCost = Objective(rule=SysCost, sense=minimize)

######========== Logical Constraint =========#############
##Switch is 1 if unit is turned on in current period
def SwitchCon(model,j,i):
    return model.switch[j,i] >= 1 - model.on[j,i-1] - (1 - model.on[j,i])
model.SwitchConstraint = Constraint(model.Generators,model.hh_periods,rule = SwitchCon)
 
######========== Up/Down Time Constraint =========#############
##Min Up time
def MinUp(model,j,i,k):
    if i > 0 and k > i and k < min(i+model.minup[j]-1,model.HorizonHours):
        return model.on[j,i] - model.on[j,i-1] <= model.on[j,k]
    else: 
        return Constraint.Skip
model.MinimumUp = Constraint(model.Generators,model.HH_periods,model.HH_periods,rule=MinUp)

##Min Down time
def MinDown(model,j,i,k):
   if i > 0 and k > i and k < min(i+model.mindn[j]-1,model.HorizonHours):
       return model.on[j,i-1] - model.on[j,i] <= 1 - model.on[j,k]
   else:
       return Constraint.Skip
model.MinimumDown = Constraint(model.Generators,model.HH_periods,model.HH_periods,rule=MinDown)

######==========Ramp Rate Constraints =========#############
def Ramp1(model,j,i):
    a = model.mwh[j,i]
    b = model.mwh[j,i-1]
    return a - b <= model.ramp[j]* model.on[j,i]+ model.mincap[j]*model.switch[j,i]
model.RampCon1 = Constraint(model.Generators,model.ramp_periods,rule=Ramp1)

def Ramp2(model,j,i):
    a = model.mwh[j,i]
    b = model.mwh[j,i-1]
    return b - a <= model.ramp[j]* model.on[j,i-1]+ model.mincap[j]*(model.on[j,i-1]-model.on[j,i]+model.switch[j,i])
model.RampCon2 = Constraint(model.Generators,model.ramp_periods,rule=Ramp2)

######=========== Capacity Constraints ============##########
#Constraints for Max & Min Capacity of dispatchable resources
def MaxC(model,j,i):
    return model.mwh[j,i]  <= model.on[j,i] * model.maxcap[j] 
model.MaxCap= Constraint(model.Generators,model.hh_periods,rule=MaxC)

def MinC(model,j,i):
    return model.mwh[j,i] >= model.on[j,i] * model.mincap[j]
model.MinCap= Constraint(model.Generators,model.hh_periods,rule=MinC)


######===================Energy, regulation capacity and zero-sum constraints ==================########

##System Energy Requirement
def SysEnergy(model,i):
    return sum(model.mwh[j,i] for j in model.Generators) +model.nse[i]  >= model.HorizonDemand[i] 
model.SysEnergy = Constraint(model.hh_periods,rule=SysEnergy)

##Regulation up Reserve Requirement
def RegulationUp(model,i):
    return sum(model.regup[j,i] for j in model.Generators) >= model.regup_margin * model.HorizonDemand[i] 
model.RegulationUp = Constraint(model.hh_periods,rule=RegulationUp)           

##Regulation up reserve can only be offered by units that are online
def RegulationUp2(model,j,i):
    return model.regup[j,i] <= model.on[j,i]*model.maxcap[j]-model.mwh[j,i] 
model.RegulationUp2= Constraint(model.Generators,model.hh_periods,rule=RegulationUp2) 

##Regulation down Reserve Requirement
def RegulationDown(model,i):
    return sum(model.regdown[j,i] for j in model.Generators) >= model.regdown_margin * model.HorizonDemand[i] 
model.RegulationDown = Constraint(model.hh_periods,rule=RegulationDown)  

##Regulation up reserve can only be offered by units that are online
def RegulationDown2(model,j,i):
    return model.regdown[j,i] <= model.mwh[j,i]- model.on[j,i]*model.mincap[j] 
model.RegulationDown2= Constraint(model.Generators,model.hh_periods,rule=RegulationDown2) 

######========== Zero Sum Constraint =========#############
# for each generator, total energy for energy market and capacity market can not exceed the maximum capacity
def ZeroSum(model,j,i):
    return model.mwh[j,i] + model.regup[j,i] - model.regdown[j,i]<= model.maxcap[j]
model.ZeroSumConstraint=Constraint(model.Generators,model.hh_periods,rule=ZeroSum)


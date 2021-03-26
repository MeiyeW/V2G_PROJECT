# run both UCexecution.py in the terminal.
# UCModel.py: Segment A is for data setup, segment B is the optimization model
# UCexucetion.py: Segment C runs UC problem and post process result.

from __future__ import division # convert int or long division arguments to floating point values before division
from pyomo.environ import *
from pyomo.opt import SolverFactory
import itertools
import csv
import pandas as pd
import numpy as np

# all unites in MWh and MW

######====== write data.dat file ======########
# data.dat file is the data files for loading data into optimization model with pyomo
def writeDatFile(df_gen,df_solar_cap,df_solar_cons,df_wind_cap,df_wind_cons,df_veh_cap,df_load,df_hydro,SimDays,SimHours,HorizonHours,regup_margin,regdown_margin,data_name,batteryCost,path,cap):
     
    with open(path+"/"+str(data_name)+'.dat', 'w') as f:
    # generators set  
        f.write('set Generators :=\n')
        for gen in range(0,len(df_gen)):
            unit_name = df_gen.loc[gen,'name']
            unit_name = unit_name.replace(' ','_')
            f.write(unit_name + ' ')
        f.write(';\n\n')

    # Hydro Set
        f.write('set Hydro :=\n')
        unit_name = 'hydro'
        f.write(unit_name + ' ')
        f.write(';\n\n')

    # wind set  

        f.write('set Wind :=\n')
        unit_name = 'wind'
        f.write(unit_name + ' ')
        f.write(';\n\n')

    # solar set 
        f.write('set Solar :=\n')
        unit_name = 'solar'
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
        f.write('param cap := %0.3f;' % cap)
        f.write('\n\n')

    ####### vehicle battery 
        f.write('param veh_batteryCost := %0.3f;' % batteryCost)
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
     

    ####### create parameter matrix for hydro generators
        f.write('param:' + '\t')
        for c in df_hydro.columns:
            if c != 'name':
                f.write(c + '\t')
        f.write(':=\n\n')
        for i in range(0,len(df_hydro)):    
            for c in df_hydro.columns:
                if c == 'name':
                    unit_name = df_hydro.loc[i,'name']
                    unit_name = unit_name.replace(' ','_')
                    f.write(unit_name + '\t')  
                else:
                    f.write(str((df_hydro.loc[i,c])) + '\t')               
            f.write('\n')
        f.write(';\n\n')   

    ####### create parameter matrix for wind generators
        f.write('param:' + '\t')
        for c in df_wind_cons.columns:
            if c != 'name':
                f.write(c + '\t')
        f.write(':=\n\n')
        for i in range(0,len(df_wind_cons)):    
            for c in df_wind_cons.columns:
                if c == 'name':
                    unit_name = df_wind_cons.loc[i,'name']
                    unit_name = unit_name.replace(' ','_')
                    f.write(unit_name + '\t')  
                else:
                    f.write(str((df_wind_cons.loc[i,c])) + '\t')               
            f.write('\n')
        f.write(';\n\n') 

    ####### create parameter matrix for solar generators
        f.write('param:' + '\t')
        for c in df_solar_cons.columns:
            if c != 'name':
                f.write(c + '\t')
        f.write(':=\n\n')
        for i in range(0,len(df_solar_cons)):    
            for c in df_solar_cons.columns:
                if c == 'name':
                    unit_name = df_solar_cons.loc[i,'name']
                    unit_name = unit_name.replace(' ','_')
                    f.write(unit_name + '\t')  
                else:
                    f.write(str((df_solar_cons.loc[i,c])) + '\t')               
            f.write('\n')
        f.write(';\n\n') 

    ####### Hourly timeseries (load)
        # load (hourly)
        f.write('param:' + '\t' + 'SimDemand:=' + '\n')      
        for h in range(0,len(df_load)): 
            f.write(str(h+1) + '\t' + str(df_load.loc[h,'netload']) + '\n')
        f.write(';\n\n')

    #######  Solar Cap data ###
        f.write('param:' + '\t'+'maxcap_s:='+'\n')
        for i in range(0,len(df_solar_cap)):    
            for c in df_solar_cap.columns: 
                f.write(str(i+1) + '\t' + str(df_solar_cap.loc[i,'maxcap_s']) + '\t')             
            f.write('\n')
        f.write(';\n\n')

    ####### Wind Cap data ###
        f.write('param:' + '\t'+'maxcap_w:='+'\n')
        for i in range(0,len(df_wind_cap)):    
            for c in df_wind_cap.columns: 
                f.write(str(i+1) + '\t' + str(df_wind_cap.loc[i,'maxcap_w']) + '\t')             
            f.write('\n')
        f.write(';\n\n')

    ######## Vehicle Cap data ######
        f.write('param:' + '\t')
        for c in df_veh_cap.columns:
            if c != 'name':
                f.write(c + '\t')
        f.write(':=\n\n')
        for i in range(0,len(df_veh_cap)):    
            for c in df_veh_cap.columns: 
                if c=='gen_capacity_veh':
                    f.write(str(i+1) + '\t' + str(df_veh_cap.loc[i,c]) + '\t') 
                else:
                    f.write(str(df_veh_cap.loc[i,c]) + '\t')            
            f.write('\n')
        f.write(';\n\n')

    # print ('Complete:',data_name)


# creating optimization with pyomo
model = AbstractModel()
########## ===== Generators set ====== #######
model.Wind=Set()
model.Solar=Set()
model.Vehicle=Set()
model.Hydro=Set()
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
model.cap=Param(within=NonNegativeReals) 

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
#Variable O&M
model.fix_om = Param(model.Generators)
#Start cost
model.st_cost = Param(model.Generators)
#Ramp rate: RL
model.ramp  = Param(model.Generators)
#Minimun up time
model.minup = Param(model.Generators)
# #regulation eligibility
# model.regelig = Param(model.Generators)
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

##########===Parameters for hydro


##Initial conditions
model.ini_on_h = Param(model.Hydro, within=Binary, initialize=0,mutable=True)  
model.ini_mwh_h = Param(model.Hydro,initialize=0,mutable=True)

#####==== Parameters for dispatchable resources ===####
#Max capacity
model.maxcap_h = Param(model.Hydro)
#Min capacity
model.mincap_h = Param(model.Hydro)
#operational cost 
model.opcost_h = Param(model.Hydro)
#Variable O&M
model.var_om_h = Param(model.Hydro)
#Variable O&M
model.fix_om_h = Param(model.Hydro)
#Start cost
model.st_cost_h = Param(model.Hydro)
#Ramp rate: RL
model.ramp_h  = Param(model.Hydro)
#Minimun up- time
model.minup_h = Param(model.Hydro)
# #regulation eligibility
# model.regelig_h = Param(model.Generators)
#regulation cost
model.regcost_h = Param(model.Hydro)


#####=======================Decision variables for dispatchable resources======================########
##Amount of day-ahead energy generated by each generator at each hour
model.mwh_h = Var(model.HH_periods, within=NonNegativeReals,initialize=0)

##Amount of day-ahead capacity for regulation up by each generator at each hour
model.regup_h = Var(model.HH_periods, within=NonNegativeReals,initialize=0)

##Amount of day-ahead capacity for regulation down by each generator at each hour
model.regdown_h = Var(model.HH_periods, within=NonNegativeReals,initialize=0)

#1 if unit is on in hour i, otherwise 0
model.on_h = Var(model.HH_periods, within=Binary, initialize=0)

#1 if unit is switching on in hour i, otherwise 0
model.switch_h = Var(model.HH_periods, within=Binary,initialize=0)


#####==== Parameters for solar ===####
#Max capacity
model.maxcap_s = Param(model.SH_periods)
#operational cost
model.opcost_s = Param(model.Solar)
#Variable O&M
model.var_om_s = Param(model.Solar)
#Start cost
model.st_cost_s = Param(model.Solar)
#Ramp rate: RL
model.ramp_s  = Param(model.Solar)
#Minimun up time
model.minup_s = Param(model.Solar)


#####=======================Decision variables for solar======================########

##Amount of day-ahead energy generated by each generator at each hour
model.mwh_s = Var(model.HH_periods, within=NonNegativeReals,initialize=0)

##Amount of day-ahead capacity for regulation up by each generator at each hour
model.regup_s = Var(model.HH_periods, within=NonNegativeReals,initialize=0)

##Amount of day-ahead capacity for regulation down by each generator at each hour
model.regdown_s = Var(model.HH_periods, within=NonNegativeReals,initialize=0)

#1 if unit is on in hour i, otherwise 0
model.on_s = Var(model.HH_periods, within=Binary, initialize=0)

#1 if unit is switching on in hour i, otherwise 0
model.switch_s = Var(model.HH_periods, within=Binary,initialize=0)

#Amount of non served energy offered by an unit in each hour
# model.nse_s = Var(model.HH_periods, within=NonNegativeReals,initialize=0)

#####==== Parameters for wind===####
#Max capacity
model.maxcap_w = Param(model.SH_periods)
#operational cost
model.opcost_w = Param(model.Wind)
#Variable O&M
model.var_om_w = Param(model.Wind)
#Start cost
model.st_cost_w = Param(model.Wind)
#Ramp rate: RL
model.ramp_w  = Param(model.Wind)
#Minimun up time
model.minup_w = Param(model.Wind)


#####=======================Decision variables for wind/solar======================########

##Amount of day-ahead energy generated by each generator at each hour
model.mwh_w = Var(model.HH_periods, within=NonNegativeReals,initialize=0)

##Amount of day-ahead capacity for regulation up by each generator at each hour
model.regup_w = Var(model.HH_periods, within=NonNegativeReals,initialize=0)

##Amount of day-ahead capacity for regulation down by each generator at each hour
model.regdown_w = Var(model.HH_periods, within=NonNegativeReals,initialize=0)

#1 if unit is on in hour i, otherwise 0
model.on_w = Var(model.HH_periods, within=Binary, initialize=0)

#1 if unit is switching on in hour i, otherwise 0
model.switch_w = Var(model.HH_periods, within=Binary,initialize=0)

######===========Parameters for Vehicles=============================###
#vehicle generation
model.veh_batteryCost=Param(within=NonNegativeReals)
model.gen_capacity_veh=Param(model.SH_periods)
model.regup_capacity_veh=Param(model.SH_periods)
model.regdown_capacity_veh=Param(model.SH_periods) 

#####=======================Decision variables for vehicles======================########
#Vehicle:
model.mwh_veh=Var(model.HH_periods, within=NonNegativeReals,initialize=0)
model.regup_veh=Var(model.HH_periods, within=NonNegativeReals,initialize=0)
model.regdown_veh=Var(model.HH_periods, within=NonNegativeReals,initialize=0)

def SysCost(model):
    operational = sum(model.mwh[j,i]*(model.opcost[j]+model.var_om[j]) for i in model.hh_periods for j in model.Generators)
    + sum(model.mwh_w[i]*(model.opcost_w[j]+model.var_om_w[j]) for i in model.hh_periods for j in model.Wind)
    + sum(model.mwh_s[i]*(model.opcost_s[j]+model.var_om_s[j]) for i in model.hh_periods for j in model.Solar)
    + sum(model.mwh_h[i]*(model.opcost_h[j]+model.var_om_h[j]) for i in model.hh_periods for j in model.Hydro)
    + sum(model.mwh_veh[i]*(model.veh_batteryCost) for i in model.hh_periods ) # update battery degradtaion cost 120$/MWh

    starts = sum(model.st_cost[j]*model.switch[j,i] for i in model.hh_periods for j in model.Generators)
    
    regulationup_capacity = sum(model.regup[j,i]*model.regcost[j]  for i in model.hh_periods for j in model.Generators)
    + sum(model.regup_veh[i]*(model.veh_batteryCost) for i in model.hh_periods )# update battery degradtaion cost

    regulationdown_capacity = sum(model.regdown[j,i]*model.regcost[j] for i in model.hh_periods for j in model.Generators)
    + sum(model.regdown_veh[i]*(model.veh_batteryCost) for i in model.hh_periods ) # update battery degradtaion cost

    return operational +starts +regulationup_capacity + regulationdown_capacity #+ nonserved 
model.SystemCost = Objective(rule=SysCost, sense=minimize)

######========== Logical Constraint =========#############
##Switch is 1 if unit is turned on in current period
def SwitchCon(model,j,i):
    return model.switch[j,i] >= 1 - model.on[j,i-1] - (1 - model.on[j,i])
model.SwitchConstraint = Constraint(model.Generators,model.hh_periods,rule = SwitchCon)

def SwitchCon_s(model,i):
    return model.switch_s[i] >= 1 - model.on_s[i-1] - (1 - model.on_s[i])
model.SwitchConstraint_s = Constraint(model.hh_periods,rule = SwitchCon_s)

def SwitchCon_w(model,i):
    return model.switch_w[i] >= 1 - model.on_w[i-1] - (1 - model.on_w[i])
model.SwitchConstraint_w = Constraint(model.hh_periods,rule = SwitchCon_w)

def SwitchCon_h(model,i):
    return model.switch_h[i] >= 1 - model.on_h[i-1] - (1 - model.on_h[i])
model.SwitchConstraint_h = Constraint(model.hh_periods,rule = SwitchCon_h)


######========== Up/Down Time Constraint =========#############
##Min Up time
def MinUp(model,j,i,k):
    if i > 0 and k > i and k < min(i+model.minup[j]-1,model.HorizonHours):
        return model.on[j,i] - model.on[j,i-1] <= model.on[j,k]
    else: 
        return Constraint.Skip
model.MinimumUp = Constraint(model.Generators,model.HH_periods,model.HH_periods,rule=MinUp)

######==========Ramp Rate Constraints =========#############
def Ramp1(model,j,i):
    a = model.mwh[j,i]
    b = model.mwh[j,i-1]
    return a - b <= model.ramp[j]* model.on[j,i]+ model.mincap[j]*model.switch[j,i]
model.RampCon1 = Constraint(model.Generators,model.ramp_periods,rule=Ramp1)

def Ramp1_w(model,j,i):
    a = model.mwh_w[i]
    b = model.mwh_w[i-1]
    return a - b <= model.ramp_w[j]* model.on_w[i]
model.RampCon1_w = Constraint(model.Wind,model.ramp_periods,rule=Ramp1_w)

def Ramp1_s(model,j,i):
    a = model.mwh_s[i]
    b = model.mwh_s[i-1]
    return a - b <= model.ramp_s[j]* model.on_s[i]
model.RampCon1_s = Constraint(model.Solar,model.ramp_periods,rule=Ramp1_s)

def Ramp1_h(model,j,i):
    a = model.mwh_h[i]
    b = model.mwh_h[i-1]
    return a - b <= model.ramp_h[j]* model.on_h[i]
model.RampCon1_h = Constraint(model.Hydro,model.ramp_periods,rule=Ramp1_h)

def Ramp2(model,j,i):
    a = model.mwh[j,i]
    b = model.mwh[j,i-1]
    return b - a <= model.ramp[j]* model.on[j,i-1]+ model.mincap[j]*(model.on[j,i-1]-model.on[j,i]+model.switch[j,i])
model.RampCon2 = Constraint(model.Generators,model.ramp_periods,rule=Ramp2)

def Ramp2_w(model,j,i):
    a = model.mwh_w[i]
    b = model.mwh_w[i-1]
    return b - a <= model.ramp_w[j]* model.on_w[i-1]
model.RampCon2_w = Constraint(model.Wind,model.ramp_periods,rule=Ramp2_w)

def Ramp2_s(model,j,i):
    a = model.mwh_s[i]
    b = model.mwh_s[i-1]
    return b - a <= model.ramp_s[j]* model.on_s[i-1]
model.RampCon2_s = Constraint(model.Solar,model.ramp_periods,rule=Ramp2_s)

def Ramp2_h(model,j,i):
    a = model.mwh_h[i]
    b = model.mwh_h[i-1]
    return b - a <= model.ramp_h[j]* model.on_h[i-1]
model.RampCon2_h = Constraint(model.Hydro,model.ramp_periods,rule=Ramp2_h)

######=========== Capacity Constraints ============##########
#Constraints for Max & Min Capacity of dispatchable resources
def MaxC(model,j,i):
    return model.mwh[j,i]  <= model.on[j,i] * model.maxcap[j] 
model.MaxCap= Constraint(model.Generators,model.hh_periods,rule=MaxC)

def MaxC_w(model,i):
    return model.mwh_w[i]  <= model.on_w[i] * model.maxcap_w[i] 
model.MaxCap_w= Constraint(model.hh_periods,rule=MaxC_w)

def MaxC_s(model,i):
    return model.mwh_s[i]  <= model.on_s[i] * model.maxcap_s[i] 
model.MaxCap_s= Constraint(model.hh_periods,rule=MaxC_s)

def MaxC_h(model,j,i):
    return model.mwh_h[i]  <= model.on_h[i] * model.maxcap_h[j] 
model.MaxCap_h= Constraint(model.Hydro,model.hh_periods,rule=MaxC_h)

def MaxC_veh(model,i):
    return model.mwh_veh[i]  <= model.gen_capacity_veh[i] 
model.MaxCap_veh= Constraint(model.hh_periods,rule=MaxC_veh)

def MinC(model,j,i):
    return model.mwh[j,i] >= model.on[j,i] * model.mincap[j]
model.MinCap= Constraint(model.Generators,model.hh_periods,rule=MinC)

def MaxRegUp_veh(model,i):
    return model.regup_veh[i]  <= model.regup_capacity_veh[i] 
model.MaxRegUp_veh= Constraint(model.hh_periods,rule=MaxRegUp_veh)

def MaxRegDown_veh(model,i):
    return model.regdown_veh[i]  <= model.regdown_capacity_veh[i] 
model.MaxRegDown_veh= Constraint(model.hh_periods,rule=MaxRegDown_veh)


######===================Energy, regulation capacity and zero-sum constraints ==================########

##System Energy Requirement
def SysEnergy(model,j,i):
    return sum(model.mwh[j,i] for j in model.Generators)  +model.mwh_w[i]+model.mwh_s[i]  +model.mwh_veh[i] + model.mwh_h[i]   >= model.HorizonDemand[i] 
model.SysEnergy = Constraint(model.Generators,model.hh_periods,rule=SysEnergy)

##Regulation up Reserve Requirement
def RegulationUp(model,i):
    return sum(model.regup[j,i] for j in model.Generators)+model.regup_veh[i]  >= model.regup_margin * model.HorizonDemand[i] 
model.RegulationUp = Constraint(model.hh_periods,rule=RegulationUp)           

# add two caps for vehicle, regup and regdown.
def RegulationUp2(model,i):
    return model.regup_veh[i]  <= model.regup_margin * model.HorizonDemand[i]*model.cap
model.RegulationUp2 = Constraint(model.hh_periods,rule=RegulationUp2)   

##Regulation up reserve can only be offered by units that are online
def RegulationUp3(model,j,i):
    return model.regup[j,i] <= model.on[j,i]*model.maxcap[j]-model.mwh[j,i] 
model.RegulationUp3= Constraint(model.Generators,model.hh_periods,rule=RegulationUp3) 

##Regulation down Reserve Requirement
def RegulationDown(model,i):
    return sum(model.regdown[j,i] for j in model.Generators)+model.regdown_veh[i]>= model.regdown_margin * model.HorizonDemand[i] 
model.RegulationDown = Constraint(model.hh_periods,rule=RegulationDown)  

def RegulationDown2(model,i):
    return model.regdown_veh[i]  <= model.regdown_margin * model.HorizonDemand[i]*model.cap
model.RegulationDown2 = Constraint(model.hh_periods,rule=RegulationDown2) 

##Regulation up reserve can only be offered by units that are online
def RegulationDown3(model,j,i):
    return model.regdown[j,i] <= model.mwh[j,i]- model.on[j,i]*model.mincap[j] 
model.RegulationDown3= Constraint(model.Generators,model.hh_periods,rule=RegulationDown3) 

######========== Zero Sum Constraint =========#############
# for each generator, total energy for energy market and capacity market can not exceed the maximum capacity
def ZeroSum(model,j,i):
    return model.mwh[j,i] + model.regup[j,i] - model.regdown[j,i]<= model.maxcap[j]
model.ZeroSumConstraint=Constraint(model.Generators,model.hh_periods,rule=ZeroSum)

def readSolutionResult(opt,instance,K,myresult,df_gen,df_solar_cons,df_wind_cons,df_hydro,df_load,veh_batteryCost):
 ## Store result
    # Space to store results
    on=[]
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
    mwh_h=[]
    regup_h=[]
    regdown_h=[]
      
    for i in K:
            instance.HorizonDemand[i] = instance.SimDemand[i]
    opt.options['TimeLimit'] = 800
    # results = opt.solve(model, load_solutions=False, tee=True)
    result = opt.solve(instance,load_solutions=False) ##,tee=True,to check number of variables ##,load_solutions=False,keepfiles=True
    instance.solutions.load_from(result)  
    # instance.display()  
    ##Read each value of the solution 
    date=1
    for v in instance.component_objects(Var, active=True):
        varobject = getattr(instance, str(v))
        a=str(v)

        if a=='on':
            for index in varobject:
                if int(index[1]>0 and index[1]<26):
                    on.append((index[0], date,index[1]+((date-1)*24),varobject[index].value))
                    # print ("Generator", index, v[index].value)   

        if a=='mwh':
            for index in varobject:
                if int(index[1]>0 and index[1]<26):
                    mwh.append((index[0], date,index[1]+((date-1)*24),varobject[index].value))
                    # print ("Generator", index, v[index].value)   
                    # print('Generator',instance.mwh.get_values())                                           
    
        if a=='regup':    
            for index in varobject:
                if int(index[1]>0 and index[1]<26):
                    regup.append((index[0],date,index[1]+((date-1)*24),varobject[index].value))
                    # print ("   ", index, v[index].value)

        if a=='regdown':    
            for index in varobject:
                if int(index[1]>0 and index[1]<26):
                    regdown.append((index[0],date,index[1]+((date-1)*24),varobject[index].value))
                    # print ("   ", index, v[index].value)
        
        if a=='mwh_w':
            for index in varobject:
                if int(index>0 and index<26):
                    mwh_w.append((index, date,index+((date-1)*24),varobject[index].value))
                    # print ("Wind", index, v[index].value)                                                  
    
        if a=='regup_w':    
            for index in varobject:
                if int(index>0 and index<26):
                    regup_w.append((index,date,index+((date-1)*24),varobject[index].value))

        if a=='regdown_w':    
            for index in varobject:
                if int(index>0 and index<26):
                    regdown_w.append((index,date,index+((date-1)*24),varobject[index].value))
        
        if a=='mwh_s':
            for index in varobject:
                if int(index>0 and index<26):
                    mwh_s.append((index, date,index+((date-1)*24),varobject[index].value))
                    # print ("Solar", index, v[index].value)                                                  
    
        if a=='regup_s':    
            for index in varobject:
                if int(index>0 and index<26):
                    regup_s.append((index,date,index+((date-1)*24),varobject[index].value))

        if a=='regdown_s':    
            for index in varobject:
                if int(index>0 and index<26):
                    regdown_s.append((index,date,index+((date-1)*24),varobject[index].value))
        if a=='mwh_veh':
            for index in varobject:
                if int(index>0 and index<26):
                    mwh_veh.append((index, date,index+((date-1)*24),varobject[index].value))
                    # print ("Vehicle", index, v[index].value)                                                  
    
        if a=='regup_veh':    
            for index in varobject:
                if int(index>0 and index<26):
                    regup_veh.append((index,date,index+((date-1)*24),varobject[index].value))

        if a=='regdown_veh':    
            for index in varobject:
                if int(index>0 and index<26):
                    regdown_veh.append((index,date,index+((date-1)*24),varobject[index].value))
        
        if a=='mwh_h':
            for index in varobject:
                if int(index>0 and index<26):
                    mwh_h.append((index, date,index+((date-1)*24),varobject[index].value))
                    # print ("Vehicle", index, v[index].value)                                                  
    
        if a=='regup_h':    
            for index in varobject:
                if int(index>0 and index<26):
                    regup_h.append((index,date,index+((date-1)*24),varobject[index].value))

        if a=='regdown_h':    
            for index in varobject:
                if int(index>0 and index<26):
                    regdown_h.append((index,date,index+((date-1)*24),varobject[index].value))
            
    
    regup_pd=pd.DataFrame(regup,columns=('Generator','Day','Hour','Value'))
    regdown_pd=pd.DataFrame(regdown,columns=('Generator','Day','Hour','Value'))  
    mwh_pd=pd.DataFrame(mwh,columns=('Generator','Day','Hour','Generation'))
    on_pd=pd.DataFrame(on,columns=('Generator','Day','Hour','On'))

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

    regup_h_pd=pd.DataFrame(regup_h,columns=('Generator','Day','Hour','Value'))
    regdown_h_pd=pd.DataFrame(regdown_h,columns=('Generator','Day','Hour','Value'))  
    mwh_h_pd=pd.DataFrame(mwh_h,columns=('Generator','Day','Hour','Generation'))
    mwh_h_pd['Generator']='hydro'
    mwh_h_pd['Reg Up']=regup_h_pd['Value']
    mwh_h_pd['Reg Down']=regdown_h_pd['Value']
    # print(mwh_h_pd)

    # # get the Marginal Clearing Price for energy, frequency regulation up, and frequency regulation down
    mwh_pd=pd.concat([mwh_pd,mwh_w_pd],axis=0)
    mwh_pd=pd.concat([mwh_pd,mwh_s_pd],axis=0)
    mwh_veh=mwh_veh_pd.rename(columns={'gen_capacity_veh':'Generation','regup_capacity_veh':'Reg Up','regdown_capacity_veh':'Reg Down'})
    mwh_pd=pd.concat([mwh_pd,mwh_veh],axis=0)
    mwh_pd=pd.concat([mwh_pd,mwh_h_pd],axis=0)

    # mwh_veh_pd[['gen_capacity_veh','regup_capacity_veh','regdown_capacity_veh']].to_csv('../data/vehicle/VehiclesCap_'+data_name2+'.csv',index=False)
    # mwh_pd.to_csv('../data/generator/GeneratorResult'+data_name2+'.csv',index=False)
    mwh_pd_gr=mwh_pd.groupby(mwh_pd['Hour'])['Generation','Reg Up','Reg Down'].sum()
    # df_load = pd.read_csv('../data/netload/20200801CAISO.csv',header=0)[:26]
    mwh_pd_gr['load']=df_load['netload']#myresult['netload']+
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
    df_hydro_cons=df_hydro.rename(columns={'opcost_h':'opcost','var_om_h':'var_om','regcost_h':'regcost'})
    cost_pd=pd.concat([df_gen_param,df_solar_cons],axis=0,sort=False)
    cost_pd=pd.concat([cost_pd,df_wind_cons],axis=0,sort=False)
    cost_pd=pd.concat([cost_pd,df_hydro_cons],axis=0,sort=False)
    cost_pd=cost_pd[['name','opcost','var_om','regcost']]
    cost_pd=cost_pd.append(pd.DataFrame([['vehicle',veh_batteryCost,0,veh_batteryCost]], columns=['name','opcost','var_om','regcost']))
    cost_pd["cost_e"]=cost_pd["opcost"]+cost_pd["var_om"]
    cost_pd["cost_fre_d"]=cost_pd["regcost"]
    cost_pd["cost_fre_u"]=cost_pd["regcost"]

    cost_pd=cost_pd[['name','cost_e','cost_fre_d','cost_fre_u']].fillna(9999)
    # get hourly price
    cost_pd=cost_pd.sort_values(by='name')
    cost_pd.index=range(cost_pd.shape[0])
    # cost_pd.to_csv('../data/price/cost_pd'+data_name2+'.csv',index=False)
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
    # print(mwh_pd_gr)
    # print("complete")
    return price_pd, mwh_veh_pd,mwh_pd,on_pd#,,cost_pd

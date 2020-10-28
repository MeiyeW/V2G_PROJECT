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

# all unites in MWh and MW

######====== write data.dat file ======########
# data.dat file is the data files for loading data into optimization model with pyomo
def writeDatFile(df_gen,df_solar_cap,df_solar_cons,df_wind_cap,df_wind_cons,df_veh_cap,df_load,SimDays,SimHours,HorizonHours,regup_margin,regdown_margin,data_name):
    with open(''+str(data_name)+'.dat', 'w') as f:

    # generators set  
        f.write('set Generators :=\n')
        for gen in range(0,len(df_gen)):
            unit_name = df_gen.loc[gen,'name']
            unit_name = unit_name.replace(' ','_')
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

    # ####### create parameter matrix for vehicles
    #  f.write('param:'+'\t'+'var_veh:='+'\n')
    #     f.write(0.2 + ' ') # var_veh
    #     f.write(';\n\n')

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

    print ('Complete:',data_name)


# creating optimization with pyomo
model = AbstractModel()
########## ===== Generators set ====== #######
model.Wind=Set()
model.Solar=Set()
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
#Variable O&M
model.fix_om = Param(model.Generators)
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

#Amount of non served energy offered by an unit in each hour
# model.nse_w = Var(model.HH_periods, within=NonNegativeReals,initialize=0)


######===========Parameters for Vehicles=============================###
#vehicle generation
model.gen_capacity_veh=Param(model.SH_periods)
model.regup_capacity_veh=Param(model.SH_periods)
model.regdown_capacity_veh=Param(model.SH_periods) 
# model.var_veh=Param(model.HH_periods) 

#####=======================Decision variables for vehicles======================########
#Vehicle:
model.mwh_veh=Var(model.HH_periods, within=NonNegativeReals,initialize=0)
model.regup_veh=Var(model.HH_periods, within=NonNegativeReals,initialize=0)
model.regdown_veh=Var(model.HH_periods, within=NonNegativeReals,initialize=0)

def SysCost(model):
    operational = sum(model.mwh[j,i]*(model.opcost[j]+model.var_om[j]) for i in model.hh_periods for j in model.Generators)
    + sum(model.mwh_w[i]*(model.opcost_w[j]+model.var_om_w[j]) for i in model.hh_periods for j in model.Wind)
    + sum(model.mwh_s[i]*(model.opcost_s[j]+model.var_om_s[j]) for i in model.hh_periods for j in model.Solar)
    + sum(model.mwh_veh[i]*(120) for i in model.hh_periods ) # update battery degradtaion cost 120$/MWh
    # sum(model.mwh_veh[j,i]*(model.var_veh[j]) for i in model.hh_periods for j in model.Vehicle)

    starts = sum(model.st_cost[j]*model.switch[j,i] for i in model.hh_periods for j in model.Generators)
    
    regulationup_capacity = sum(model.regup[j,i]*model.regcost[j]  for i in model.hh_periods for j in model.Generators)
    # sum(model.regup_veh[j,i]*(model.var_veh[j]) for i in model.hh_periods for j in model.Vehicle)
    + sum(model.regup_veh[i]*(120) for i in model.hh_periods )# update battery degradtaion cost

    regulationdown_capacity = sum(model.regdown[j,i]*model.regcost[j] for i in model.hh_periods for j in model.Generators)
    # sum(model.regdown_veh[j,i]*(model.var_veh[j]) for i in model.hh_periods for j in model.Vehicle)
    + sum(model.regdown_veh[i]*(120) for i in model.hh_periods ) # update battery degradtaion cost

    # nonserved = sum(model.nse[i]*20 for i in model.hh_periods)
    #20 is the cost of non-served energy [$/MWh], can be changed
    #10 is the cost of non-served energy for wind and solar[$/MWh], can be changed
    
    return operational +starts +regulationup_capacity + regulationdown_capacity #+ nonserved 
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

# ##Min Down time
# def MinDown(model,j,i,k):
#    if i > 0 and k > i and k < min(i+model.mindn[j]-1,model.HorizonHours):
#        return model.on[j,i-1] - model.on[j,i] <= 1 - model.on[j,k]
#    else:
#        return Constraint.Skip
# model.MinimumDown = Constraint(model.Generators,model.HH_periods,model.HH_periods,rule=MinDown)

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

def MinC(model,j,i):
    return model.mwh[j,i] >= model.on[j,i] * model.mincap[j]
model.MinCap= Constraint(model.Generators,model.hh_periods,rule=MinC)

def MaxC_veh(model,i):
    return model.mwh_veh[i]  <= model.gen_capacity_veh[i] 
model.MaxCap_veh= Constraint(model.hh_periods,rule=MaxC_veh)

def MaxRegUp_veh(model,i):
    return model.regup_veh[i]  <= model.regup_capacity_veh[i] 
model.MaxRegUp_veh= Constraint(model.hh_periods,rule=MaxRegUp_veh)

def MaxRegDown_veh(model,i):
    return model.regdown_veh[i]  <= model.regdown_capacity_veh[i] 
model.MaxRegDown_veh= Constraint(model.hh_periods,rule=MaxRegDown_veh)


######===================Energy, regulation capacity and zero-sum constraints ==================########

##System Energy Requirement
def SysEnergy(model,i):
    return sum(model.mwh[j,i] for j in model.Generators)  +model.mwh_w[i]+model.mwh_s[i]  +model.mwh_veh[i]   >= model.HorizonDemand[i] 
model.SysEnergy = Constraint(model.hh_periods,rule=SysEnergy)

##Regulation up Reserve Requirement
def RegulationUp(model,i):
    return sum(model.regup[j,i] for j in model.Generators)+model.regup_veh[i]  >= model.regup_margin * model.HorizonDemand[i] 
model.RegulationUp = Constraint(model.hh_periods,rule=RegulationUp)           

##Regulation up reserve can only be offered by units that are online
def RegulationUp2(model,j,i):
    return model.regup[j,i] <= model.on[j,i]*model.maxcap[j]-model.mwh[j,i] 
model.RegulationUp2= Constraint(model.Generators,model.hh_periods,rule=RegulationUp2) 

##Regulation down Reserve Requirement
def RegulationDown(model,i):
    return sum(model.regdown[j,i] for j in model.Generators)+model.regdown_veh[i]>= model.regdown_margin * model.HorizonDemand[i] 
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

# def readSolutionResult(instance,resultLength,day):
#     #Space to store results
#     on=[]
#     switch=[]
#     mwh=[]
#     regup=[]
#     regdown=[]
#     mwh_w=[]
#     regup_w=[]
#     regdown_w=[]
#     mwh_s=[]
#     regup_s=[]
#     regdown_s=[]
#     mwh_veh=[]
#     regup_veh=[]
#     regdown_veh=[]
#     nse=[]
    
#     for v in instance.component_objects(Var, active=True):
#         varobject = getattr(instance, str(v))
#         a=str(v)
        
#         if a=='mwh':
#             for index in varobject:
#                 if int(index[1]>0 and index[1]<resultLength):
#                     mwh.append((index[0], day,index[1]+((day-1)*24),varobject[index].value))
#                     # print ("Generator", index, v[index].value)   
#                     # print('Generator',instance.mwh.get_values())                                           
        
#         if a=='regup':    
#             for index in varobject:
#                 if int(index[1]>0 and index[1]<resultLength):
#                     regup.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))
#                     # print ("   ", index, v[index].value)

#         if a=='regdown':    
#             for index in varobject:
#                 if int(index[1]>0 and index[1]<resultLength):
#                     regdown.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))
#                     # print ("   ", index, v[index].value)
        
#         if a=='mwh_w':
#             for index in varobject:
#                 if int(index>0 and index<resultLength):
#                     mwh_w.append((index, day,index+((day-1)*24),varobject[index].value))
#                     # print ("Wind", index, v[index].value)                                                  
        
#         if a=='regup_w':    
#             for index in varobject:
#                 if int(index>0 and index<resultLength):
#                     regup_w.append((index,day,index+((day-1)*24),varobject[index].value))

#         if a=='regdown_w':    
#             for index in varobject:
#                 if int(index>0 and index<resultLength):
#                     regdown_w.append((index,day,index+((day-1)*24),varobject[index].value))
        
#         if a=='mwh_s':
#             for index in varobject:
#                 if int(index>0 and index<resultLength):
#                     print ("Solar", index,day, index+((day-1)*24),varobject[index].value)                                                  
#                     mwh_s.append([index, day,index+((day-1)*24),varobject[index].value])
#                     print ("Solar", mwh_s)                                                  
        
#         if a=='regup_s':    
#             for index in varobject:
#                 if int(index>0 and index<resultLength):
#                     regup_s.append((index,day,index+((day-1)*24),varobject[index].value))

#         if a=='regdown_s':    
#             for index in varobject:
#                 if int(index>0 and index<resultLength):
#                     regdown_s.append((index,day,index+((day-1)*24),varobject[index].value))
#         if a=='mwh_veh':
#             for index in varobject:
#                 if int(index>0 and index<resultLength):
#                     # print ("Vehicle", index,day, index+((day-1)*24),varobject[index].value)                                                  
#                     mwh_veh.append([index, day,index+((day-1)*24),varobject[index].value])
#                     print ("Vehicle", mwh_veh)                                                  
        
#         if a=='regup_veh':    
#             for index in varobject:
#                 if int(index>0 and index<resultLength):
#                     regup_veh.append((index,day,index+((day-1)*24),varobject[index].value))

#         if a=='regdown_veh':    
#             for index in varobject:
#                 if int(index>0 and index<resultLength):
#                     regdown_veh.append((index,day,index+((day-1)*24),varobject[index].value))
                                
#     #         # if a=='on':        
#     #         #     for index in varobject:
#     #         #         if int(index[1]>0 and index[1]<25):
#     #         #             on.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))

#     #         # if a=='switch':  
#     #         #     for index in varobject:
#     #         #         if int(index[1]>0 and index[1]<25):
#     #         #             switch.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))

#     #         # if a=='nse':    
#     #         #     for index in varobject:
#     #         #         if int(index[1]>0 and index[1]<25):
#     #         #             nse.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))
#     #     print(day)
#     #     print(str(datetime.now()))

#         regup_pd=pd.DataFrame(regup,columns=('Generator','Day','Hour','Value'))
#         regdown_pd=pd.DataFrame(regdown,columns=('Generator','Day','Hour','Value'))  
#         mwh_pd=pd.DataFrame(mwh,columns=('Generator','Day','Hour','Generation'))
#         mwh_pd['Reg Up']=regup_pd['Value']
#         mwh_pd['Reg Down']=regdown_pd['Value']

#         regup_w_pd=pd.DataFrame(regup_w,columns=('Generator','Day','Hour','Value'))
#         regdown_w_pd=pd.DataFrame(regdown_w,columns=('Generator','Day','Hour','Value'))  
#         mwh_w_pd=pd.DataFrame(mwh_w,columns=('Generator','Day','Hour','Generation'))
#         mwh_w_pd['Generator']='wind'
#         mwh_w_pd['Reg Up']=regup_w_pd['Value']
#         mwh_w_pd['Reg Down']=regdown_w_pd['Value']

#         regup_s_pd=pd.DataFrame(regup_s,columns=('Generator','Day','Hour','Value'))
#         regdown_s_pd=pd.DataFrame(regdown_s,columns=('Generator','Day','Hour','Value'))  
#         mwh_s_pd=pd.DataFrame(mwh_s,columns=('Generator','Day','Hour','Generation'))
#         mwh_s_pd['Generator']='solar'
#         mwh_s_pd['Reg Up']=regup_s_pd['Value']
#         mwh_s_pd['Reg Down']=regdown_s_pd['Value']

#         regup_veh_pd=pd.DataFrame(regup_veh,columns=('Generator','Day','Hour','Value'))
#         regdown_veh_pd=pd.DataFrame(regdown_veh,columns=('Generator','Day','Hour','Value'))  
#         mwh_veh_pd=pd.DataFrame(mwh_veh,columns=('Generator','Day','Hour','gen_capacity_veh'))
#         mwh_veh_pd['Generator']='vehicle'
#         mwh_veh_pd['regup_capacity_veh']=regup_veh_pd['Value']
#         mwh_veh_pd['regdown_capacity_veh']=regdown_veh_pd['Value']

#         # # get the Marginal Clearing Price for energy, frequency regulation up, and frequency regulation down
#         mwh_pd=pd.concat([mwh_pd,mwh_w_pd],axis=0)
#         mwh_pd=pd.concat([mwh_pd,mwh_s_pd],axis=0)
#         mwh_veh=mwh_veh_pd.rename(columns={'gen_capacity_veh':'Generation','regup_capacity_veh':'Reg Up','regdown_capacity_veh':'Reg Down'})
#         mwh_pd=pd.concat([mwh_pd,mwh_veh],axis=0)
#     return mwh_veh_pd,mwh_pd

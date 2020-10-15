from pyomo.opt import SolverFactory
from pyomo.core import Var
from pyomo.core import Param
from operator import itemgetter
import pandas as pd
from datetime import datetime
import os

#run number
yr=2018
run_no = 1
###Segment C.2
from UCModel import model
from UCModel import writeDatFile

# first iteration

data_name = 'iteration2_correct'
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
myresult=pd.read_csv('../data/vehicle/VehiclesCap_iteration2_correct.csv',header=0)
N = 6# from 10mins to 1 hour
myresult=myresult.groupby(myresult.index // N).sum()/6
myresult=myresult.rename(columns={'EnergyDemand':'netload','EnergyGeneration':'gen_capacity_veh','Regup':'regup_capacity_veh','Regdown':'regdown_capacity_veh'})
myresult=pd.concat([myresult,myresult],axis=0)
myresult.index=range(myresult.shape[0])
df_veh_cap=myresult[['gen_capacity_veh'	,'regup_capacity_veh',	'regdown_capacity_veh']]

df_load = pd.read_csv('../data/netload/20200801CAISO.csv',header=0)[:HorizonHours]
df_load['netload']=myresult['netload']+df_load['netload']

df_gen['maxcap']=df_gen['maxcap']*3
df_solar_cap['maxcap_s']=df_solar_cap['maxcap_s']*3
df_wind_cap['maxcap_w']=df_wind_cap['maxcap_w']*3

writeDatFile(df_gen,df_solar_cap,df_solar_cons,df_wind_cap,df_wind_cons,df_veh_cap,df_load,SimDays,SimHours,HorizonHours,regup_margin,regdown_margin,data_name)

###Segment C.3
instance = model.create_instance(data_name+'.dat')
# instance=model.create_instance('test_iteration1.dat')
print('instance created') 
###Segment C.4
opt = SolverFactory("gurobi") ##SolverFactory("cplex")
# opt.options["threads"] = 1
H = instance.HorizonHours
K=range(1,H+1)
start = 1 ##1 to 364
end  = 2 ##2 to 366
Hour=24*(end-start)
###Segment C.5
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
         #load Demand and Reserve time series data
    for i in K:
            instance.HorizonDemand[i] = instance.SimDemand[(day-1)*24+i]

    opt.options['TimeLimit'] = 600
    # results = opt.solve(model, load_solutions=False, tee=True)

    result = opt.solve(instance,tee=True, load_solutions=False,keepfiles=True) ##,tee=True to check number of variables ##,load_solutions=False
    instance.solutions.load_from(result)  
    # instance.display() 
    print('solution found') 
##The following section is for storing and sorting results
    # for v in instance.component_objects(Var, active=True):
    #     print ("Variable component object",v)
    #     print ("Type of component object: ", str(type(v))[1:-1]) # Stripping <> for nbconvert
    #     varobject = getattr(instance, str(v))
    #     print ("Type of object accessed via getattr: ", str(type(varobject))[1:-1])
    #     for index in varobject:
    #         print ("   ", index, varobject[index].value)

    # for v in instance.component_objects(Var, active=True):
    #     print ("Variable component object",v)
    #     for index in v:
    #         print ("   ", index, v[index].value)

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

mwh_veh_pd[['gen_capacity_veh','regup_capacity_veh','regdown_capacity_veh']].to_csv('../data/vehicle/VehiclesCap'+data_name+'.csv',index=False)
mwh_pd.to_csv('../data/generator/GeneratorResult'+data_name+'.csv',index=False)
print(mwh_pd.groupby(mwh_pd['Hour'])['Generation','Reg Up','Reg Down'].sum())
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
cost_pd=cost_pd.append(pd.DataFrame([['vehicle',1,0,1]], columns=['name','opcost','var_om','regcost']))
cost_pd["cost_e"]=cost_pd["opcost"]+cost_pd["var_om"]
cost_pd["cost_fre_d"]=cost_pd["regcost"]
cost_pd["cost_fre_u"]=cost_pd["regcost"]

cost_pd=cost_pd[['name','cost_e','cost_fre_d','cost_fre_u']].fillna(9999)
# get hourly price
cost_pd=cost_pd.sort_values(by='name')
cost_pd.index=range(cost_pd.shape[0])
cost_pd.to_csv('../data/price/cost_pd'+data_name+'.csv',index=False)
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
price_pd.to_csv('../data/price/price'+data_name+'.csv',index=False)
print("complete")


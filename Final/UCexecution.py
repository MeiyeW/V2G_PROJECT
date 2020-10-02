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


data_name = 'test2'
###Segment C.3
instance = model.create_instance(data_name+'.dat')

###Segment C.4
opt = SolverFactory("gurobi") ##SolverFactory("cplex")
opt.options["threads"] = 1
H = instance.HorizonHours
K=range(1,H+1)
start = 1 ##1 to 364
end  = 366 ##2 to 366

###Segment C.5
#Space to store results
on=[]
switch=[]

mwh=[]
regup=[]
regdown=[]
nse=[]

for day in range(start,end):
         #load Demand and Reserve time series data
    for i in K:
            instance.HorizonDemand[i] = instance.SimDemand[(day-1)*24+i]
           
    result = opt.solve(instance) ##,tee=True to check number of variables
    instance.solutions.load_from(result)   
 
##The following section is for storing and sorting results
    for v in instance.component_objects(Var, active=True):
        varobject = getattr(instance, str(v))
        a=str(v)
       
        if a=='mwh':
            for index in varobject:
                if int(index[1]>0 and index[1]<25):
                    mwh.append((index[0], day,index[1]+((day-1)*24),varobject[index].value))                                              
      
        if a=='regup':    
            for index in varobject:
                if int(index[1]>0 and index[1]<25):
                    regup.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))

        if a=='regdown':    
            for index in varobject:
                if int(index[1]>0 and index[1]<25):
                    regdown.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))
                              
        # if a=='on':        
        #     for index in varobject:
        #         if int(index[1]>0 and index[1]<25):
        #             on.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))

        # if a=='switch':  
        #     for index in varobject:
        #         if int(index[1]>0 and index[1]<25):
        #             switch.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))

        # if a=='nse':    
        #     for index in varobject:
        #         if int(index[1]>0 and index[1]<25):
        #             nse.append((index[0],day,index[1]+((day-1)*24),varobject[index].value))
    print(day)
    print(str(datetime.now()))
    
    regup_pd=pd.DataFrame(regup,columns=('Generator','Day','Hour','Value'))
    regdown_pd=pd.DataFrame(regdown,columns=('Generator','Day','Hour','Value'))  
    mwh_pd=pd.DataFrame(mwh,columns=('Generator','Day','Hour','Value'))    
    # on_pd=pd.DataFrame(on,columns=('Generator','Day','Hour','Value'))
    # switch_pd=pd.DataFrame(switch,columns=('Generator','Day','Hour','Value'))
    # nse_pd=pd.DataFrame(nse,columns=('Generator','Day','Hour','Value'))
    
# the following is for storing the Marginal Clearing Price for energy and capacity market    
df_gen_param = pd.read_csv('test_generators.csv',header=0)
gen_name = df_gen_param['name']
gen_maxcap = df_gen_param['maxcap']
gen_heat_rate = df_gen_param['heat_rate']
gen_var_om = df_gen_param['var_om']
gen_fuel_cost = df_gen_param['fuel_cost']
gen_st_cost = df_gen_param['st_cost']

cost= []
price=[]

# get the cost for energy, frequency regulation up, and frequency regulation down for each generator
for i in range(len(gen_name)):
    cost_e =  gen_heat_rate[i]*gen_fuel_cost[i]+gen_var_om[i]
    cost_fre_u =  gen_heat_rate[i]*gen_fuel_cost[i]+gen_var_om[i]*0.5
    cost_fre_d = gen_heat_rate[i]*gen_fuel_cost[i]+gen_var_om[i]*0.3
    cost.append((gen_name[i],cost_e,cost_fre_u,cost_fre_d))

cost_pd=pd.DataFrame(cost,columns=('Generator','cost_e','cost_fre_u','cost_fre_d'))
cost_pd=cost_pd.sort_values(by="Generator")
cost_pd=cost_pd.reset_index(drop=True)
cost_pd


# get the Marginal Clearing Price for energy, frequency regulation up, and frequency regulation down

mwh_pd=mwh_pd.sort_values(by=["Generator","Hour"])
mwh_pd=mwh_pd.reset_index(drop=True)
# mwh_pd.head()

regup_pd=regup_pd.sort_values(by=["Generator","Hour"])
regup_pd=regup_pd.reset_index(drop=True)
# regup_pd.head()

regdown_pd=regdown_pd.sort_values(by=["Generator","Hour"])
regdown_pd=regdown_pd.reset_index(drop=True)
# regdown_pd.head()


for i in range(8760):
    pr_e=[]
    pr_fre_u=[]
    pr_fre_d=[]
    for j in range(len(gen_name)):    
        pr_e.append((mwh_pd['Value'][i+j*8760]>0).astype(int)*1*cost_pd["cost_e"][j])
        pr_fre_u.append((regup_pd['Value'][i+j*8760]>0).astype(int)*1*cost_pd["cost_fre_u"][j])
        pr_fre_d.append((regdown_pd['Value'][i+j*8760]>0).astype(int)*1*cost_pd["cost_fre_d"][j])
    price.append((i,max(pr_e),max(pr_fre_u),max(pr_fre_d)))
# print(price)


price_pd=pd.DataFrame(price,columns=("Hour",'pr_e','pr_fre_u','pr_fre_d'))

###to save outputs
price_pd.to_csv('out_camb_R'+str(run_no)+'_'+str(yr)+'_price.csv')
# mwh_pd.to_csv('out_camb_R'+str(run_no)+'_'+str(yr)+'_mwh.csv')
# on_pd.to_csv('out_camb_R'+str(run_no)+'_'+str(yr)+'_on.csv')
# switch_pd.to_csv('out_camb_R'+str(run_no)+'_'+str(yr)+'_switch.csv')
# regup_pd.to_csv('out_camb_R'+str(run_no)+'_'+str(yr)+'_regup.csv')
# regdown_pd.to_csv('out_camb_R'+str(run_no)+'_'+str(yr)+'_regdown.csv')
# nse_pd.to_csv('out_camb_R'+str(run_no)+'_'+str(yr)+'_nse.csv')

print("complete")
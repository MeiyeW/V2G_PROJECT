import pandas as pd

def datinput(df_gen,df_load,SimDays,SimHours,HorizonHour,regup_margin,regdown_margin,data_name):
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

####### Hourly timeseries (load)
    # load (hourly)
        f.write('param:' + '\t' + 'SimDemand:=' + '\n')      
        for h in range(0,len(df_load)): 
            f.write(str(h+1) + '\t' + str(df_load.loc[h,'demand (MW)']) + '\n')
        f.write(';\n\n')

    
    return f

def MCPStore(df_gen_param):

    #Space to store results
    on=[]
    switch=[]
    mwh=[]
    regup=[]
    regdown=[]
    nse=[]

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

    return cost_pd

def getprice(instance,cost_pd):
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
                              
        regup_pd=pd.DataFrame(regup,columns=('Generator','Day','Hour','Value'))
        regdown_pd=pd.DataFrame(regdown,columns=('Generator','Day','Hour','Value'))  
        mwh_pd=pd.DataFrame(mwh,columns=('Generator','Day','Hour','Value'))

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

        for i in range(24):
            pr_e=[]
            pr_fre_u=[]
            pr_fre_d=[]
            for j in range(len(gen_name)):    
                pr_e.append((mwh_pd['Value'][i+j*24]>0).astype(int)*1*cost_pd["cost_e"][j])
                pr_fre_u.append((regup_pd['Value'][i+j*24]>0).astype(int)*1*cost_pd["cost_fre_u"][j])
                pr_fre_d.append((regdown_pd['Value'][i+j*24]>0).astype(int)*1*cost_pd["cost_fre_d"][j])
            price.append((i,max(pr_e),max(pr_fre_u),max(pr_fre_d)))

        price_pd=pd.DataFrame(price,columns=("Hour",'pr_e','pr_fre_u','pr_fre_d'))
    return price_pd


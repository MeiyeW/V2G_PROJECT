for days in 365:
    epsilon=100
    epsilon2=100
    load=load_input[days*24,days*24+48]
    load_firday=load_input[days*24,days*24+24]
    load_secday=load_input[days*24+24,days*24+48]
    price=UC(load,generator)

    while epsilon>0.1 & epsilon2>0.1:
        veh_load,veh_generation=V2GSIM(price,load_firday)
        load_firday2=veh_load.sum_to_hourly+load_firday
        veh_generation=veh_generation.sum_tp_hourly
        load2=concat(load_firday2,load_secday)

        price2,veh_generation2=UC(load2,generator,veh_generation)
        epsilon=price2*veh_generation2-price*veh_generation
        epsilon2=(veh_generation2-veh_generation).sum 
        load_firday=load_firday2
        price=price2

# go through UC, V2G, UC, just check how much things are changing
# strict criteria: min change for each hour 
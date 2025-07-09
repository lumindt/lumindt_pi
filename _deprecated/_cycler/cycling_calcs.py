import pandas as pd
import numpy as np
import z_factors 

# size reference volume
sample_mass = 630 #grams
grams_stored = 6.3
mol_H2_gas_sample = grams_stored / 2.01588
# size reference volume so that a 6.3g uptake corresponds to a 5 bar drop in pressure
R = 8.3144598 # J / (mol K)
dp_desired = 5  #bar, determined by sensor + volume
T = 295 #k
V_ref = mol_H2_gas_sample * R * T / (dp_desired* 100000) * 1000
print("ref_v = " + str(V_ref)[0:5] + " Liters")

#input PT stats here


# #for the Omega we have - 
# p_err = 0.5 #percent error
# range  = 1000 #psi
# #sensor_type = "differential"
# sensor_type = "regular"

#for the Omega PX309-500GI - $399
p_err = 0.25 #percent error
range  = 500 #psi
#sensor_type = "differential"
sensor_type = "regular"

# #for the Omega PX409-250DDUV - $1080.49
# p_err = 0.08 #percent error
# range  = 250 #psi
# sensor_type = "differential"
# #sensor_type = "regular"


range = range / 14.504 #bar
if sensor_type == "regular":
    sensor_error = p_err * 0.01 * range # error% * psi rating
    total_error = np.sqrt(sensor_error**2 + sensor_error**2)
elif sensor_type == "differential":
    total_error = p_err * 0.01 * range

print("sensor error [bar] = " + str(total_error)[0:5])



g_per_dp = grams_stored / dp_desired
error = g_per_dp*total_error

V_vessel = 5.604*3 #liters
extra_v = 0.5 #liters

V_tot = V_vessel + extra_v
T_gas = 295 #k

P_initial = 25

dp_meas = 3

# assumptions -> hydride heating during absorb doesnt do significant work on the gas inside the vessel
n = V_tot/1000 *(dp_meas*100000) / (R*T_gas)
grams_h2 = n * 2.01588
print("num grams h2 = " + str(n)[0:5])



vol_uncertainty = 0.1 #L
T_uncertainty = 1.5 #K
PT_uncertainty = total_error
error_propagated = ((vol_uncertainty/V_tot)**2 + (PT_uncertainty/dp_meas)**2 + (T_uncertainty/T)**2)**0.5

#print("total propagated error [%]= " + str(error_propagated*100)[0:5])

Z = z_factors.compressibility_factor_calc("Hydrogen", T*1.8, P_initial-dp_meas)
#print(Z)
wt_percent = 100 * grams_h2 / (sample_mass * Z)
print("weight_percent = " +str(wt_percent)[0:5] + " +/- " + str(error_propagated*wt_percent)[0:5] + " %")
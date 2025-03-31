import pylab as plt
import numpy as np
import datetime

# user inputs here:
'''
voltage_file = ""
ampereage_file = "2017_05_12_4"
plot_title = "Coating WTh 3.3 mm rod C (Side 2) with heater + steerer"
'''
'''
voltage_file = ""
ampereage_file = "2017_05_12_3"
plot_title = "Coating WTh 3.3 mm rod C (Side 1) with heater + steerer"
'''
'''
voltage_file = ""
ampereage_file = "2017_05_12_2"
plot_title = "Coating WTh 3.3 mm rod B (Side 2) with heater + steerer"
'''

voltage_file = ""
ampereage_file = "2017_05_12_1"
plot_title = "Coating WTh 3.3 mm rod B (Side 1) with heater + steerer"

'''
voltage_file = ""
ampereage_file = "2017_05_11_1"
plot_title = "Coating WTh 1 mm rod fragment with heater + steerer"
'''


# all measures in cm (assuming a cylindrical rod)
#for the 3.3mm rods

coated_length = 18./2
coated_inner_diameter = 0.33

#for the 1mm rod
'''
coated_length = 2.335
coated_inner_diameter = 0.1
'''
# define some constants
electron_charge = 1.69e-19
avogadro = 6.02214086e23
density_copper = 8.92 		# density in g/cm^3
molar_mass_cu = 63.546

# also load the header in order to match the time axises between both sets

#f1 = open(voltage_file, "r") 
f2 = open(ampereage_file, "r")
#volt_header = f1.read()
amp_header = f2.read()
format = '%H:%M:%S'
#volt_start_time = datetime.datetime.strptime(volt_header[11:19], format)
amp_start_time = datetime.datetime.strptime(amp_header[11:19], format)
#print("voltage record time:", volt_start_time)
print("ampereage record time:", amp_start_time)
'''
delta_sec =  0
if(amp_start_time > volt_start_time):
	delta = amp_start_time - volt_start_time
	delta_sec = -delta.seconds
else:
	delta =  volt_start_time - amp_start_time
	delta_sec = delta.seconds

print("difference (ampere - volt): ", delta_sec)
f1.close()
'''
f2.close()

# load the two data sets for voltage and ampereage (without header)
#voltage = np.loadtxt(voltage_file, skiprows=3)
current = np.loadtxt(ampereage_file, skiprows=3)

integral_charge = np.zeros_like(current[:,1])

for i in range(current.shape[0]-1):
	
	integral_charge[i+1] = current[i,1]*(current[i+1,0] - current[i,0]) + integral_charge[i]

total_charge = integral_charge[current.shape[0]-1]
N_Cu_atoms = total_charge/electron_charge/2.

# copper mass in gramms
m_cu = N_Cu_atoms/avogadro * molar_mass_cu

print("Deposited copper mass (in gram): ", m_cu)

# assuming rod
coated_surface = np.pi*coated_inner_diameter*coated_length
# neglecting effect of increase of diameter due to coating (V = A*coating_thickness)

volume_copper = m_cu/density_copper
thickness_coating = volume_copper/coated_surface

print("coating thickness (nm) = ", thickness_coating*1e7)

current_density = current[:,1] / coated_surface*1E3
deposition_rate = current_density /(2*electron_charge)/avogadro * molar_mass_cu *1E3


# compute the offset between the data sets and shift the one that was first to start
#voltage[:,0] += delta_sec

fig = plt.figure()
ax1 = fig.add_subplot(111)
plt1 = ax1.plot(current[:,0], current_density , '-b', label='Current')
ax1.plot(0, 0, '-r', label='Deposited mass')
ax2 = ax1.twinx()
plt2 = ax2.plot(current[:,0], integral_charge /(2*electron_charge)/avogadro * molar_mass_cu *1E3, '-r', label='Deposition Rate')
ax1.legend(loc=0)
ax1.grid()
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Current density (mA/cm^2)")
ax2.set_ylabel("Deposited mass (mg)")
mass_string = "Deposited mass: \n" + "%.4f" % (m_cu*1e3) + " mg\n\nCoating thickness: \n" + "%.2f" % (thickness_coating*1e7) +" nm"
# str(m_cu*1e3) + "mg"
text = ax1.text(current[:,0].max()*0.65, current_density.max()*0.6, mass_string)
plt.title(plot_title)
plt.show()

fig.savefig("plot.png")

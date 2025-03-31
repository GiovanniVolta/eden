from PyQt5 import QtCore as _qc
from PyQt5 import QtGui as _qg
from eden import Class_PSC as _psc
import time
import numpy as _np

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as _FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as _NavigationToolbar
import matplotlib.pyplot as _plt

class Plotter(_qc.QThread):

    def __init__(self, gui):
        _qc.QThread.__init__(self)
        self.gui = gui
        self.stop_thread = False
        
        # define some constants
        self.e = 1.69e-19
        self.na = 6.02214086e23
        self.rho_cu = 8.92 		# density in g/cm^3
        self.m_cu = 63.546
        
        self.surface = None
        self.charge = None
        self.mass = None
        self.thickness = None
        self.current_density = None
        self.time = None

        self.fig = _plt.figure()
        self.canvas = _FigureCanvas(self.fig)
        self.nav_toolbar = _NavigationToolbar(self.canvas, self.canvas)

        
    def get_surface(self):

        self.surface = self.gui.sample_area        

    def get_current(self):
        
        self.data = self.gui.data

    def integrate_current(self):
        
        self.charge = _np.trapz(self.data[:,1], self.data[:,0])
        
    def get_mass(self):
       
        self.mass = self.charge/self.e/2. / self.na*self.m_cu
        
    def get_thickness(self):

        self.thickness = self.mass / self.rho_cu / self.surface
        
    def get_current_density(self):
    
        self.current_density = self.data[:,1] / self.surface * 1E3
        
    def get_time(self):
        
        self.time = self.data[:,0] - self.data[0,0]
        
    def get_title(self):
    
        return self.gui.sample_name+" "+self.gui.coating_step
        
    def do_plot(self):
    
        self.fig.clear()
        
        self.get_current()
        self.get_surface()
        
        if self.data.any() and self.surface:
        
            self.integrate_current()
            self.get_mass()
            self.get_thickness()
            self.get_current_density()
            self.get_time()
            
            
            ax1 = self.fig.add_subplot(111)
            plt1 = ax1.plot(self.time, self.current_density , '-b', label='Current')
            ax1.plot(0, 0, '-r', label='Voltage')
            ax2 = ax1.twinx()
            plt2 = ax2.plot(self.time, self.data[:,2], '-r', label='Voltage')
            ax1.legend(loc=0)
            ax1.grid()
            ax1.set_xlabel("Time (s)")
            ax1.set_ylabel("Current density (mA/cm^2)")
            ax2.set_ylabel("Voltage (V)")
            '''
            mass_string = "Deposited mass: \n" + "%.4f" % (m_cu*1e3) + " mg\n\nCoating thickness: \n" + "%.2f" % (thickness_coating*1e7) +" nm"
            # str(m_cu*1e3) + "mg"
            text = ax1.text(current[:,0].max()*0.65, current_density.max()*0.6, mass_string)
            '''
            #_plt.title(self.get_title())

            self.canvas.draw()

    def run(self):
    
        while True:
        
            if self.stop_thread:
                break
                
            self.do_plot()
            time.sleep(0.5)
        return
        
class PscReader(_qc.QThread):


    def __init__(self, psc_module):
        
        _qc.QThread.__init__(self)
        self.psc = psc_module
        self.stop_thread = False
        self.halt_thread = False
        self.temp_file_name = "tmp_"+str(int(time.time()))+".dat"
        self.is_recording = False
        self.reader_data = []
        
    def run(self):
        
        f_tmp = open(self.temp_file_name, "w")
        while True:
            if self.stop_thread:
                self.psc.board_busy = False
                break
            if self.halt_thread:
                self.psc.board_busy = False
                time.sleep(0.1)
                continue
                
            self.psc.board_busy = True
            self.psc.get_mea_vol()
            self.psc.get_mea_cu()
            timestamp = time.time()
            voltage = self.psc.mea_vol
            current = self.psc.mea_cu
            f_tmp.write(str(timestamp)+' '+str(voltage)+' '+str(current)+'\n')
            if self.is_recording:
                self.reader_data = _np.append(self.reader_data, ((timestamp, current, voltage)))
                self.reader_data = self.reader_data.reshape((-1,3))
        f_tmp.close()
            

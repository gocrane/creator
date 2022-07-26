'''
Crane v0.3.0 fft and max prediction.
'''

import logging
from scipy.fft import fft, ifft
import numpy as np
import pandas as pd
import math

# default estimator is fft estimator with different parameters
# min_spectrum_items_nums low_amplitude_threshould margin
# 3  1.0  0.01-0.20
# 50 0.05 0.01-0.20
def fft_get_estimator(data,sample_interval,cycle_duration,*args):
    args = args[0]
    sample_rate = 1.0/sample_interval
    # result = pd.DataFrame(columns=['amp', 'freq','sample_rate','sample'])
    result = pd.DataFrame(columns=['sample_rate','sample'])
    fft_y = fft(data)
    sample_length = len(data)
    amps = np.abs(fft_y)/sample_length*2
    # result['freq'] = sample_rate*np.arange(sample_length)/sample_length
    freqs = sample_rate*np.arange(sample_length)/sample_length
    result['sample_rate'] = sample_rate
    max_spectrum_items_nums = args[0]["max_spectrum_items_nums"]
    min_spectrum_items_nums = args[0]["min_spectrum_items_nums"]
    low_amplitude_threshould = args[0]["low_amplitude_threshould"]
    high_frequency_threshold = args[0]["high_frequency_threshold"]
    margin = args[0]["margin"]
    
    # amps = amps[1:int(len(amps)/2)]
    amps[::-1].sort() # reverse sort
    if len(amps) > max_spectrum_items_nums:
        min_amplitude = amps[max_spectrum_items_nums-1]
    else:
        min_amplitude = amps[-1]
    
    if min_amplitude < low_amplitude_threshould :
        min_amplitude = low_amplitude_threshould
        
    if (len(amps) >= min_spectrum_items_nums) & (amps[min_spectrum_items_nums-1]<min_amplitude):
        min_amplitude = amps[min_spectrum_items_nums-1]
    # Filter out the noise, which is of high frequency and low amplitude
    np.where((amps < min_amplitude)&(freqs > high_frequency_threshold),amps,0.0)
    '''
    for i in range(len(amps)):
        # Filter out the noise, which is of high frequency and low amplitude
        if (amps[i] < min_amplitude) & (freqs[i] > high_frequency_threshold):
             amps[i] = 0.0
    '''
    
    ifft_y = ifft(fft_y)
   
    n_samples_per_cycle = int(cycle_duration*sample_rate)
    samples=np.zeros(n_samples_per_cycle)
    for i in np.arange(len(ifft_y) - n_samples_per_cycle,len(ifft_y),1):
        a = np.real(ifft_y[i])
        if a <=0.0:
            a = 0.01
        samples[i+n_samples_per_cycle-len(ifft_y)] = a*(1.0+margin)
    result['sample'] = samples
    return result
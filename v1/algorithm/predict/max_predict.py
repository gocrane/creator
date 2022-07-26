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
def max_get_estimator(data,sample_interval,cycle_duration,*args):
    args = args[0]
    margin = args[0]["margin"]
    sample_rate = 1.0/sample_interval
    result = pd.DataFrame(columns=['sample_rate','sample'])
    result['sample_rate'] = sample_rate
    n_samples_per_cycle = int(cycle_duration*sample_rate)
    samples = np.zeros(n_samples_per_cycle)
    n_samples = len(data)
    n_cycles = int(n_samples/n_samples_per_cycle)
    index = 0
    for i in np.arange(n_samples-n_samples_per_cycle,n_samples,1):
        max_value = data[i]
        # get max value in all cycles.
        for j in np.arange(1,n_cycles,1):
            if max_value < data[i-n_samples_per_cycle*j]:
                max_value = data[i-n_samples_per_cycle*j]
        samples[index] = max_value*(1.0+margin)
        index += 1
    
    result['sample'] = samples
    
    return result
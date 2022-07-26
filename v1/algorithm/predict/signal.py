'''
Crane v0.3.0 fft and max prediction.
'''

import logging
import numpy as np
import pandas as pd
import math
import sys
from fft_predict import fft_get_estimator
from max_predict import max_get_estimator

# default estimator is fft estimator with different parameters
# min_spectrum_items_nums low_amplitude_threshould margin
# 3  1.0  0.01-0.20
# 50 0.05 0.01-0.20

def update_aggregate_signals(data, sample_interval, cycle_duration,last_timestamp,*args):
# no need for double check signal fit double cycle_duration, already check in is_periodicity
    args = args[0]
    sample_rate = 1.0 / sample_interval
    n = int(cycle_duration * sample_rate)
    m = 0
    i = len(data)
    while (i-n >=0):
        i-=n
        m += 1
    data = data[i:]
    if m < 2:
        return None
    sample_per_cycle = int(len(data)/m)
    history = data[:(m-1)*sample_per_cycle]
    actual = data[(m-1)*sample_per_cycle:]
    min_pe = sys.float_info.max
    best_estimator = {}
    for i in range(len(args)):
        estimator = args[i]["estimator"]
        if estimator == "fft":
            estimated = fft_get_estimator(data,sample_interval,cycle_duration,args[i:i+1])
        elif estimator == "max":
            estimated = max_get_estimator(data,sample_interval,cycle_duration,args[i:i+1])
        else:
            return None
        
        if not estimated.empty:
            estimated = estimated['sample']
            pe = predict_error(actual,estimated)
            logging.info("Testing estimators ...", "estimator", estimator, "pe", pe)
            if pe < min_pe:
                min_pe = pe
                best_estimator = args[i]
    result = pd.DataFrame(columns=['timestamp', 'sample'])    
    if best_estimator:
        if best_estimator['estimator'] == "fft":
            estimated = fft_get_estimator(data,sample_interval,cycle_duration,args[i:i+1])
        elif estimator == "max":
            estimated = max_get_estimator(data,sample_interval,cycle_duration,args[i:i+1])
        next_timestamp = last_timestamp
        cycles = 1
        if cycle_duration == 60*60:
            cycles = 24
        n = len(estimated)
        samples = np.zeros(n*cycles)
        timestamps = np.zeros(n*cycles)
        for c in range(cycles):
            for i in range(n):
                samples[i+c*n] = estimated['sample'][i]
                next_timestamp += sample_interval
                timestamps[i+c*n] = int(next_timestamp)
        
        result['timestamp'] =  timestamps
        result['sample'] = samples
        
    return result

# Amplify x (0.0 < x < 1.0). The bigger x the greater the degree of amplification.
# For example, amplify(0.1) = 0.47 (+370%), amplify(0.5) = 3.1 (+520%)
def amplify(x):
    return -math.log(1.0-x)/math.log(1.25)
    
# from sklearn.metrics import mean_absolute_percentage_error 

def mean_absolute_percentage_error(actual, predict):
    if len(actual) != len(predict):
        raise ValueError("actual and predict signal length is not same")
    
    epsilon = 1e-3
    length = len(actual)
    actual = actual[:length]
    predict = predict[:length]
    err = 0.0
    for i in range(length):
        if actual[i] < epsilon:
            print("actual value is almost 0")
            return 0
        err += abs((predict[i] - actual[i]) / actual[i])
    err = err/length
    return err

# mape with experience
def predict_error(actual, predict):
    if len(actual) != len(predict):
        raise ValueError("actual and predict signal length is not same")
    
    epsilon = 1e-3
    length = len(actual)
    actual = actual[:length]
    predict = predict[:length]
    err = 0.0
    for i in range(length):
        if actual[i] < epsilon:
            print("actual value is almost 0")
            return 0
        if predict[i]<actual[i]:
            err += amplify((actual[i] - predict[i]) / actual[i])
        else:
            err += (predict[i] - actual[i]) / actual[i]
    err = err/length
    #err = mean_absolute_percentage_error(actual, predict)
    return err

from scipy.fft import fft  
import pandas as pd
import numpy as np
import matplotlib as plt
'''
Crane v0.3.0 periodic check func.
'''
# crane v0.3.0 
# PredictorManager(realtimeDataSources,historyDataSource), default all is prom data source
# Default algrithm is dsp and percentile, for dsp model update interval default is 12h
# periodicSignalPrediction(DSP) Run 
    # goroutinue for loop to watch QueryExprWithCaller request channel
        # goroutinue updateAggregateSignalsWithQuery, include dsp/percentile config like sample internal, history length etc.
            # query history time series from history data source proxy
            # updateAggregateSignals
                # default history resolution 1 minutes, duration is 15d, resoultion can`t more 1 hour, duration can`t less 2d.
                # set estimator, max(need margin)、fft(margin、highFrequencyThreshold、lowAmplitudeThreshold、min/maxNumOfSpectrumItems)、
                # isPeriodicTimeSeries
                    # change samples to signals and set sample rate via history resolution
                        # sample rate is 1/resolution(s)
                    # isPeriodic
                        # history resolution while is signal length at least double of period
                        # get frequencies from signals via fft
                        # if cycle time(1/freq) less than period, is not periodic
                        # if cycle time almost equal(epsilon<1e-3), think it is periodic
                    
# crane dsp fft is_periodicity
from scipy.fft import fft  

# fft algorithm to check the signal is or not is periodic signal.
def is_periodicity(data, sample_interval, cycle_duration,show_pic=False):
    """
    :param data:  检测数据，ndarray 类型
    :param sample_interval: 采样数据的时间,单位 s
    :param cycle_duration: 预测周期,单位 s
    :param show_pic: 是否展示图片
    :return: is_cycle 为是否周期性, cycles 为可能的周期列表
    """
    is_cycle = False
    sample_rate = 1.0 / sample_interval
    n = int(cycle_duration * sample_rate)
    m = 0
    i = len(data)
    while (i-n >=0):
        i-=n
        m += 1
    data = data[i:]
    if m < 2 : return is_cycle, None
    sample_length = len(data)
    result = pd.DataFrame(columns=['amp', 'freq'])
    fft_y = fft(data)
    result['amp'] = np.abs(fft_y)/sample_length*2
    result['freq'] = sample_rate*np.arange(sample_length)/len(fft_y)
    length = int(len(result['freq'])/2)
    result = result[:][1:length]
    if show_pic is True:
        fig,axs = plt.subplots(1,2,figsize=(8,2),dpi=100)
        x=np.arange(sample_length -1)
        axs[0].plot(x,result['amp'])
        axs[0].set_title('幅值归一化')
        axs[1].plot(x,result['freq'])
        axs[1].set_title('频率')
        plt.show()
        
    # 按照幅值强弱程度降序排列
    result = result.sort_values(by='amp', ascending=False)
    # pd.options.display.float_format = '{:.2f}'.format
    # result.head()
    # 频率转换为周期
    cycle_list = 1 / result['freq'].values
    #print(cycle_list)
    is_cycle = False
    cycles = []
    for cycle in cycle_list:
        # 判断是不是整数
        if cycle > cycle_duration:
            return is_cycle, cycles  
        m = cycle_duration/cycle
        epsilon = abs(m - float(int(m)))
        # optimization： set hyper-parameter
        if epsilon < 1e-3:
            is_cycle = True
            cycles.append(cycle)
            return is_cycle, cycles
    return is_cycle, cycles

def test_is_periodicity(show_pic):
    epsilon = 1e-15
    frequency = 5 # hz
    sample_interval = 0.001 # 采样 0.001s
    sample_rate = 1.0/sample_interval # 采样频率 Hz
    
    x = np.arange(0.0,1.0,sample_interval,dtype=float)
    
    freqs = [frequency,frequency,frequency,frequency,frequency]
    growth_ratio = 0.1
    signals = [np.sin(freqs[0]*2*np.pi*x) + 1.0,
               np.sin(freqs[1]*2*np.pi*x+np.random.random_sample())+1.0,
               np.sin(2.0*freqs[2]*np.pi*x)+0.5*np.sin(2.0*freqs[2]*4*np.pi*x)+3.0,
               np.sin(2.0*freqs[3]*np.pi*x) + 2*np.random.random_sample(),
               (1.0+np.floor(x/(1/freqs[4])*growth_ratio))* np.sin(2.0*freqs[4]*np.pi*x)]
    
    for i in range(len(freqs)):
        y = signals[i]
        cycle_duration = 1.0/freqs[i] # s
        if show_pic is True:
            plt.plot(x,y)
            plt.show()
        is_cycle, cycles = is_periodicity(y, sample_interval, cycle_duration,show_pic=False)
        
        if not is_cycle:
            raise ValueError("test error")
        else:
            print("is cycle")
        
        if len(cycles) == 0:
            raise ValueError("no cycles error")
        print(cycles)
        assert (cycles[0]-cycle_duration < epsilon)
    return
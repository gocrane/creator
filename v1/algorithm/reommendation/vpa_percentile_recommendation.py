import math
from histogram_option import LinearHistogramOptions
from histogram import Histogram
# container request 推荐 cpu 和 memory
# percentile 算法
# crane v0.3.0 percentile 算法 with margin

# recommendation reconcile, period or once, inspector will check you need recommand hpa or resource request, and advisor will give recommandation.
# doRecommend -> recommendation.Offer -> ResourceRequestAdvisor.Advise -> get percentile predictor -> makeCpuConfig/makeMemConfig -> 
# default_cpu(sample_interval=1m,percentile=0.99,margin=0.15,histogram(half_life=24h,bucket_size=0.25,max_value=100))
# default_memory(sample_interval=1m,percentile=0.99,margin=0.15,histogram(half_life=48h,bucket_size=104857600,max_value=104857600000))
# QueryRealtimePredictedValuesOnce -> if no registed signals, we first fetch history data to construct the histogram model, then get estimation. -> process
# makeInternalConfig configure the histogram configuration,for resource request is LinearHistogramOptions
# default configuration for cpu （epsilon:1e-10, max_value: 100, bucket_size: 0.25, num_buckets: int(math.Ceil(maxValue/bucketSize)) + 1） 
# default configuration for memory （epsilon:1e-10, max_value: 104857600000,ucket_size: 104857600, num_buckets: int(math.Ceil(maxValue/bucketSize)) + 1） 
# create a dry-run proposal, 



# when init controller, will init aggregateSignals in forloop.
# Reconcile TimeSeriesPrediction object
# syncTimeSeriesPrediction -> syncPredictionStatus
    # check if needed(no predict data、end_timestamp of window out of prev predict time range) update prediction status
    # predict double times of PredictionWindowSeconds of spec
    # percentilePrediction.QueryPredictedTimeSeries
        # getPredictedValues 100ms timeout, vpa.Histogram Percentile(e.percentile)*(1+margin)

# set default config of percentile in makeInternalConfig
default_min_sample_weight = 1e-5
        
# 假设 data 是已经存在的 aggregateSignals, 保存的是一组容器聚合信号，作为推荐的输入
# 输出的是指定分布的百分位数
# crane cpu 和 memory 分布默认是线性直方图 ,可选衰减直方图 decaying histograms
# 参考：https://github.com/kubernetes/autoscaler/blob/d509cf0f1a9513e89dae20a69a581ce11ba4c0b0/vertical-pod-autoscaler/pkg/recommender/model/aggregate_container_state.go#L91


# ContainerNameToAggregateStateMap map[container_name]*AggregateContainerState
# samples is same container name in same pod and namespace cpu/memory usage collections
# In crane, named aggragateSignal
def new_aggregate_container_state_cpu(samples):
    '''vpa default
    # num_buckets first_bucket_size ratio epsilon from default vpa config
    # cpu_num_buckets = int(math.ceil(math.log(math.log(1000.0 * (1.0+0.05 - 1) / 0.01 + 1),1.+0.05)) + 1
    # cpu_histogram_options = ExponentialHistogramOptions(cpu_num_buckets,0.01,1.+0.05,0.001*0.1)
    '''
    # In crane will use LinearHistogram, from newAggregateSignal
    # default configuration for cpu （epsilon:1e-10, max_value: 100, bucket_size: 0.25, num_buckets: int(math.Ceil(maxValue/bucketSize)) + 1） 
    # num_buckets,bucket_size, epsilon
    cpu_num_buckets = int(math.ceil(100/0.25)) + 1
    cpu_histogram_options = LinearHistogramOptions(cpu_num_buckets,0.25,1e-10)
    
    '''vpa default
    # half_life,total_weight,min_bucket,max_bucket, histogram_options
    # half_life default is 24h
    # aggregate_cpu_usage = DecayingHistogram(24*60*60,0.0,cpu_histogram_options.num_bucket(),0,cpu_histogram_options)
    '''
    # default sample_interval=1m,percentile=0.99,margin=0.15,history length default is 7d for crane, but now sample_interval is 30s
    # total_weight ,min_bucket ,max_bucket , histogram_options
    aggregate_cpu_usage = Histogram(0.0,cpu_histogram_options.num_bucket()-1,0,cpu_histogram_options)
    for i in range(len(samples)):
        sample = samples[i]
        # origin vpa will use this,diff from crane
        '''vpa default
        针对 CPU 和 Memory 资源使用数据，AggregateContainerState 实现了不同的处理逻辑。
        例如向半衰指数直方图导入数据时，CPU 使用量样本对应的权重是基于容器 CPU request 值确定的。
        当 CPU request 增加时，对应的权重也随之增加。旧的样本数据权重将相对减少，有助于推荐模型快速应对 CPU 使用“尖刺”问题，减缓 CPU“饥饿等待”几率。
        而 Memory 使用量样本对应的权重固定为 1.0。
        由于内存为不可压缩资源，Recommender 划分了 memory 使用量统计窗口，默认为 24h。
        在当前窗口内只关注资源使用量峰值，添加到对应的半衰指数直方图中。
        同时这也表示，针对 memory 每 24h Recommender 中只保存一个采样点。
        # aggregate_cpu_usage.add_sample(sample['cpu_usage'],max(sample['request'], 0.1),i*30) # sample duration is 30s
        '''
        # value: float, weight: float, time: float):
        aggregate_cpu_usage.add_sample(sample, max(default_min_sample_weight,sample),i)
    return aggregate_cpu_usage
        
    
    
def new_aggregate_container_state_memory(samples):
    '''vpa default
    # num_buckets first_bucket_size ratio epsilon from default vpa config
    memory_num_buckets = int(math.ceil(math.log(math.log(1e12 * (1.0+0.05 - 1) / 1e7 + 1),1.+0.05)) + 1
    memory_historgram_options = ExponentialHistogramOptions(memory_num_buckets, 1e7,1.+0.05,0.001*0.1)
    '''
                          
    # num_buckets,bucket_size, epsilon
    # default configuration for memory （epsilon:1e-10, max_value: 104857600000,bucket_size: 104857600, num_buckets: int(math.Ceil(maxValue/bucketSize)) + 1） 
    memory_num_buckets = int(math.ceil(104857600000/104857600)) + 1
    memory_histogram_options = LinearHistogramOptions(memory_num_buckets,104857600,1e-10)
    '''
    # half_life,total_weight,min_bucket,max_bucket, histogram_options
    # half_life default is 24h
    aggregate_memory_peaks = DecayingHistorgam(24*60*60,0.0,memory_histogram_options.num_bucket(),0,memory_histogram_options)
    '''
    # total_weight ,min_bucket ,max_bucket , histogram_options
    aggregate_memory_peaks = Histogram(0.0,memory_histogram_options.num_bucket()-1,0,memory_histogram_options)
    for i in range(len(samples)):
        sample = samples[i]
        # origin vpa will use this,diff from crane
        '''vpa default
        # aggregate_memory_peaks.add_sample(sample['memory_usage'],max(sample['request'], 0.1),i*30) # sample duration is 30s
        '''
        # value: float, weight: float, time: float):
        aggregate_memory_peaks.add_sample(sample, max(default_min_sample_weight,sample),i)
    return aggregate_memory_peaks
    

# container metrics data
# container_name, pod_name, pod_namespace, usage(cpu, memory), time, window.duration
# data is offline container metrics
# AggregateContainerState
def percentile_predict(data, percentile: float,aggregated: bool,predict_type: str,margin,*args):
    default_margin = margin
    if predict_type=='cpu':
        aggregate_usage = new_aggregate_container_state_cpu(data)
    elif predict_type == 'memory':
        aggregate_usage = new_aggregate_container_state_memory(data)
    else:
        raise ValueError("type is not supported for predict")
    result = []
    if aggregated:
        value = (1+default_margin)*aggregate_usage.percentile(percentile)
        result.append(value)
    else:
        for sample in data:
            value = (1+default_margin)*aggregate_usage.percentile(percentile)
            result.append(value)
    return result
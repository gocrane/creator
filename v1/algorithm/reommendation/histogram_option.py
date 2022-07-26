# crane vpa percentile algorithm
# 使 CPU 和 Memory 资源消耗量低于该推荐值的部分占总体时间的比重保持在某个阈值以上

from typing import Dict,Type,Any
import collections
class HistogramOptions(object):
    def __init__(self):
        pass
    def num_bucket(self) -> int:
        pass
    def find_bucket(self, value: float) -> int:
        pass
    def get_bucket_start(self, bucket: int) -> float:
        pass
    def get_epsilon(self) -> float:
        pass
# 线性直方图
class LinearHistogramOptions(HistogramOptions):
    def __init__(self, num_buckets: int, bucket_size: float, epsilon: float):
        self.num_buckets = num_buckets
        self.bucket_size = bucket_size
        self.epsilon = epsilon
    def num_bucket(self) -> int:
        return self.num_buckets
    def find_bucket(self, value: float) -> int:
        bucket = int(value/self.bucket_size)
        if bucket < 0:
            return 0
        if bucket > self.num_buckets:
            return self.num_buckets -1
        return bucket
    def get_bucket_start(self, bucket: int) -> float:
        if bucket <0 | bucket >= self.num_buckets:
            raise ValueError("index out of range")
        return float(bucket) * self.bucket_size
        
    def get_epsilon(self) -> float:
        return self.epsilon

import math
# 衰减直方图，指数桶
class ExponentialHistogramOptions(HistogramOptions):
    def __init__(self, num_buckets: int, first_bucket_size: float,ratio: float, epsilon: float):
        self.num_buckets = num_buckets
        self.first_bucket_size = first_bucket_size
        self.ratio = ratio
        self.epsilon = epsilon
    def num_bucket(self) -> int:
        return self.num_buckets
    def find_bucket(self, value: float) -> int:
        if value < self.first_bucket_size:
            return 0
        
        bucket = int(math.log(value*(self.ratio-1)/self.first_bucket_size+1,self.ratio))
        if bucket > self.num_buckets:
            return self.num_buckets -1
        return bucket
    def get_bucket_start(self, bucket: int) -> float:
        if bucket <0 | bucket >= self.num_buckets:
            raise ValueError("index out of range")
        if bucket == 0:
            return 0.0
        return self.first_bucket_size * math.pow(self.ratio, float(bucket))
        
    def get_epsilon(self) -> float:
        return self.epsilon
 
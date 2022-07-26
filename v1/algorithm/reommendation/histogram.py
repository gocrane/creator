# crane vpa percentile algorithm
# 使 CPU 和 Memory 资源消耗量低于该推荐值的部分占总体时间的比重保持在某个阈值以上

from typing import Dict,Type,Any
import collections 
import numpy as np

class Histogram:
    """
    Histogram represents an approximate distribution of some variable.
    https:#github.com/kubernetes/autoscaler/blob/master/vertical-pod-autoscaler/pkg/recommender/util/histogram.go
    """
    bucket_weights: Dict[int, float]
    total_weight: float
    def __init__(self, total_weight: float,min_bucket: int,max_bucket: int, histogram_options: Type[HistogramOptions]):
        self.bucket_weights = collections.defaultdict(float)
        self.total_weight = total_weight
        self.min_bucket = min_bucket
        self.max_bucket = max_bucket
        self.options = histogram_options
    def add_sample(self, value: float, weight: float, time: float):
        if weight < 0.0:
            raise ValueError("sample weight must be non-negative")
        bucket = self.options.find_bucket(value)
        self.bucket_weights[bucket] += weight
        self.total_weight += weight
        if (bucket < self.min_bucket) & (self.bucket_weights[bucket] >= self.options.get_epsilon()):
            self.min_bucket = bucket
        if (bucket > self.max_bucket) & (self.bucket_weights[bucket] >= self.options.get_epsilon()):
            self.max_bucket = bucket
        return
    def safe_subtract(self, value: float, sub: float, epsilon: float) -> float:
        value -= sub
        if value < epsilon:
            return 0.0
        return value
    def subtract_sample(self, value: float, weight: float, time: float):
        if weight < 0.0:
            raise ValueError("sample weight must be non-negative")
        bucket = self.options.FindBucket(value)
        epsilon = self.options.get_epsilon()
        self.total_weight = self.safe_subtract(self.total_weight,weight,epsilon)
        self.bucket_weights[bucket] = self.safe_subtract(self.bucket_weights[bucket],weight,epsilon)
        self.update_min_and_max_bucket()
        return
    
    def merge(self, other: 'Histogram'):
        o = self.__class__(other)
        if self.options != o.options:
            raise ValueError("can't merge histograms with different options")
        for bucket in np.arange(o.min_bucket,o.max_bucket,1):
            self.bucket_weights[bucket] += o.bucket_weights[bucket]
        
        self.total_weight += o.total_weight
        if o.min_bucket < self.min_bucket :
            self.min_bucket = o.min_bucket
        if o.max_bucket > self.max_bucket:
            self.max_bucket = o.max_bucket
        return
    def scale(self, factor: float):
        if factor < 0.0:
            raise ValueError("scale factor must be non-negative")
        for i, v in self.bucket_weights.items():
            self.bucket_weights[i] = v * factor
        self.total_weight *= factor
        self.update_min_and_max_bucket()
    def update_min_and_max_bucket(self):
        epsilon = self.options.get_epsilon()
        last_bucket = self.options.num_bucket() -1 
        while (self.bucket_weights[self.min_bucket] < epsilon & self.min_bucket < last_bucket):
            self.min_bucket += 1
        while (self.bucket_weights[self.max_bucket] < epsilon & self.max_bucket > 0):
            self.min_bucket -= 1
    def percentile(self, percentile: float) -> float:
        if self.is_empty():
            return 0.0
        partial_sum = 0.0
        threshold = percentile * self.total_weight
        bucket = self.min_bucket
        for i, w in sorted(self.bucket_weights.items()):
            partial_sum += w
            if partial_sum >= threshold:
                bucket = i
                break
        if bucket < self.options.num_bucket() -1:
            # last bucket
            return self.options.get_bucket_start(bucket+1)
        # Return the end of the bucket.
        return self.options.get_bucket_start(bucket)
    def is_empty(self) -> bool:
        return (
            self.bucket_weights[self.min_bucket] < self.options.get_epsilon()
        )
    def string(self):
        lines = ["minBucket: %d, maxBucket: %d, totalWeight: %.3f".format(self.min_bucket,self.max_bucket,self.total_weight),"%-tile\tvalue"]
        for i in np.arange(0,100,5):
            lines.append("%d\t%.3f".format(i, self.percentile(0.01*float(i))))
        return "\n".join(lines)
    def equal(self, other: 'Histogram'):
        pass
    def get_checkpoint(self) -> Dict[str, Any]:
        return {
            "total_weight": self.total_weight,
            "bucket_weights": {
                b: w for b, w in self.bucket_weights.items() if w > self.options.get_epsilon()
            }
        }
    def from_checkpoint(self, checkpoint: Dict[str, Any]):
        total_weight = checkpoint["total_weight"]
        if total_weight < 0.0:
            raise ValueError(
                f"Invalid checkpoint data with negative weight {total_weight}"
            )
        for bucket_str, weight in checkpoint["bucket_weights"].items():
            # JSON keys are always strings, convert to int
            bucket = int(bucket_str)
            self.bucket_weights[bucket] += weight
        self.total_weight += total_weight

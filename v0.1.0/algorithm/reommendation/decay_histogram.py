# crane vpa percentile algorithm
# 使 CPU 和 Memory 资源消耗量低于该推荐值的部分占总体时间的比重保持在某个阈值以上

from typing import Dict,Type,Any
from histogram import Histogram
'''
直方图赋予新样本比旧样本更高的权重，逐渐衰减（“忘记”）过去的样本。
为每个样本数据权重乘上指数2^((sampleTime - referenceTimestamp) / halfLife)，以保证较新的样本被赋予更高的权重，而较老的样本随时间推移权重逐步衰减。
默认情况下，每 24h 为一个半衰期，即每经过 24h，直方图中所有样本的权重（重要性）衰减为原来的一半。
这意味着信号在每个半衰期都会失去一半的权重（“重要性”）
由于只有样本的相对（而非绝对）权重很重要，因此 referenceTimestamp 可以随时移动，这相当于将所有权重乘以一个常数。
在实践中，只要指数变得太大，referenceTimestamp 就会向前移动，以避免浮点算术溢出。
'''

'''
场景延伸：不同半衰期对推荐值的影响
在 VPA Recommender CPU 和 Memory 推荐模型中，半衰期设置会严重影响到容器预测指标与真实指标的拟合度
例如半衰期设置较长可能导致指标预测值偏向于平直，这种情况更倾向于反应容器长周期的资源利用率情况，半衰期设置较短可能导致指标预测值偏向于波峰波谷明显，这种情况更倾向于反应容器短周期的资源利用率情况。
总结来说，不同长度的半衰期配置适用于不同的场景：
1. 半衰期较长的指标预测比较适合私用云场景下的用户资源申请量推荐、动态调度、垂直伸缩等场景，这些场景的特点是基于指标预测值完成一次决策后应用负载在较长时间内保持稳定；
2. 半衰期较短的指标预测比较适合私用云场景下的在离线混部等场景，这些场景的特点是系统对应用负载指标数据的波峰波谷比较敏感，期望通过削峰填谷来实现降本增效；

短半衰期引入的问题：
1. 原生的 Vpa Recommender 在部署时是一个中心单体结构，它会对集群中全量的 pod 进行指标预测，并更新至 vpa status 资源中。
半衰期长度的设置可能诱发性能瓶颈，例如较短的半衰期设置会导致短周期内大量 vpa status 状态的变更，这些变更会更新至 etcd 中，此时有可能会给 apiserver 和 etcd 带来较大的压力。

指标预测值拟合有以下设计要点：

在实践中，我们采取以下措施缓解半衰期长度设置带来的性能问题：
1. 拉长 VPA Recommender 执行周期(recommender-interval)；
2. 限制 VPA Recommender 的 qps(kube-api-qps)；
'''

MAX_DECAY_EXPONENT = 100
class DecayingHistogram(Histogram):
    def __init__(self, half_life: float,total_weight: float,min_bucket: int,max_bucket: int, histogram_options: Type[HistogramOptions]):
        super().__init__(total_weight,min_bucket,max_bucket, histogram_options)
        self.half_life = half_life
        self.reference_time = 0
    def percentile(self, percentile: float):
        return super().percentile(percentile)
    def shift_reference_time(self, new_reference_time: float):
        # Make sure the decay start is an integer multiple of halfLife.
        new_reference_time = int(
            (new_reference_time // self.half_life) * self.half_life
        )
        exponent = round((self.reference_time - new_reference_time) / self.half_life)
        self.scale(2 ** exponent)  # Scale all weights by 2^exponent.
        self.reference_time = new_reference_time
    def decay_factor(self, time: float):
        max_allowed_timestamp = self.reference_time + (self.half_life * MAX_DECAY_EXPONENT)
        if time > max_allowed_timestamp:
            # The exponent has grown too large. Renormalize the histogram by
            # shifting the referenceTimestamp to the current timestamp and rescaling
            # the weights accordingly.
            self.shift_reference_time(time)
        decay_factor = 2 ** ((time - self.reference_time) / self.half_life)
        return decay_factor
    def add_sample(self, value: float, weight: float, time: float):
        super().add_sample(value, weight*self.decay_factor(time), time)
        return
    def subtract_sample(self, value: float, weight: float, time: float):
        super().subtract_sample(value, weight*self.decay_factor(time),time)
        return
    def merge(self, other: 'DecayingHistogram'):
        o = self.__class__(other)
        if self.half_life != o.half_life:
            raise ValueError("can't merge decaying histograms with different half life periods")
        if self.reference_time < o.reference_time:
            self.shift_reference_time(o.reference_time)
        elif o.reference_time < self.reference_time:
            o.shift_reference_time(self.reference_time)
        super().merge(o)
    def is_empty(self) -> bool:
        return super().is_empty()
    def string(self) -> str:
        return "referenceTimestamp: %f, halfLife: %f\n%s".format(self.reference_time,self.half_life,super().string())
    def get_checkpoint(self) -> Dict[str, Any]:
        return {
            "total_weight": self.total_weight,
            "bucket_weights": {
                b: w for b, w in super().bucket_weights.items() if w > super().get_epsilon()
            },
            "reference_time": self.reference_time,
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
            super().bucket_weights[bucket] += weight
        super().total_weight += total_weight
        self.reference_time = checkpoint["reference_time"]
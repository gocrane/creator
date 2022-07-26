The algorithm and evaluation module of v1 accomplish the following:
1. The three main algorithms of crane v0.3.0 are reproduced to provide support for later algorithm optimization:
     - Predict periodicity based on dsp fft
     - Predict periodic signals based on dsp fft, max algorithm for resource planning
     - Implement request recommendation algorithm based on percentile

2. Precipitate offline evaluation pipeline to provide support for later algorithm effectiveness evaluation
     - Data acquisition (es + prometheus python utils)
     - Data cleaning
     - Algorithm evaluation metrics

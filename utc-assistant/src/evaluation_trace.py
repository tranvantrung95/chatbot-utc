import time
import math
from contextlib import contextmanager

class StageTimer:
    def __init__(self, clock=time.time):
        self.clock = clock
        self.timings = {}

    @contextmanager
    def stage(self, name):
        start = self.clock()
        try:
            yield
        finally:
            end = self.clock()
            duration = end - start
            self.timings[f"{name}_sec"] = round(duration, 4)

def summarize_latencies(values):
    if not values:
        return {
            "count": 0,
            "avg_latency_sec": 0.0,
            "p50_latency_sec": 0.0,
            "p95_latency_sec": 0.0,
            "max_latency_sec": 0.0
        }
    
    count = len(values)
    avg = sum(values) / count
    
    sorted_vals = sorted(values)
    
    if count % 2 == 1:
        p50 = sorted_vals[count // 2]
    else:
        p50 = (sorted_vals[count // 2 - 1] + sorted_vals[count // 2]) / 2.0
        
    p95_idx = int(math.ceil(0.95 * count)) - 1
    p95 = sorted_vals[max(0, p95_idx)]
    
    maximum = max(values)
    
    return {
        "count": count,
        "avg_latency_sec": round(avg, 2),
        "p50_latency_sec": round(p50, 2),
        "p95_latency_sec": round(p95, 2),
        "max_latency_sec": round(maximum, 2)
    }

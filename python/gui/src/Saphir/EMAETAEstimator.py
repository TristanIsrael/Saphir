class EMAETAEstimator:

    def __init__(self, total_iterations, alpha=0.3):
        self.alpha = alpha
        self.total = total_iterations
        self.ema = None
        self.completed = 0
        self.eta = 0.0

    def update(self, iter_duration):
        if self.ema is None:
            self.ema = iter_duration
        else:
            self.ema = self.alpha * iter_duration + (1 - self.alpha) * self.ema

        self.completed += 1
        remaining = self.total - self.completed
        self.eta = self.ema * remaining

        return self.eta
    
    def remaining_time(self) -> float:
        return self.eta
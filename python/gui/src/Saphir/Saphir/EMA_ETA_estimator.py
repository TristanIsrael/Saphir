class EMAETAEstimator:

    def __init__(self):
        self.__alpha = 0
        self.__total = 0
        self.__ema = None
        self.__completed = 0
        self.__eta = 0.0
    
    def setup(self, total_iterations:int, alpha=0.3):
        self.__alpha = alpha
        self.__total = total_iterations
        self.__ema = None
        self.__completed = 0
        self.__eta = 0.0

    def update(self, iter_duration:float):
        if self.__ema is None:
            self.__ema = iter_duration
        else:
            self.__ema = self.__alpha * iter_duration + (1 - self.__alpha) * self.__ema

        self.__completed += 1
        remaining = self.__total - self.__completed
        self.__eta = self.__ema * remaining

        return self.__eta
    
    def remaining_time(self) -> float:
        return self.__eta
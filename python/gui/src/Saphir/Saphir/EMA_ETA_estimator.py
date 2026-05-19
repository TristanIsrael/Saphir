class EMAETAEstimator:
    """ The EMA ETA estimator is designed to provide an estimation of the remaining
    time for a work divided into iterations.
    
    There is no unit for the duration, the caller is responsible of converting the duration
    in any unit. The time unit is consistent inside the estimator.
    """

    def __init__(self):
        self.__alpha = 0
        self.__total = 0
        self.__ema = None
        self.__completed = 0
        self.__eta = 0.0
    
    def setup(self, total_iterations:int, alpha=0.3):
        """ Setup the estimator with the total number of iterations 
        
        The alpha value is a factor for the linearization of the gaps between durations which means
        that when there are big differences between the duration of iterations, this difference
        will be lowered to minimize its impact.
        """

        self.__alpha = alpha
        self.__total = total_iterations
        self.__ema = None
        self.__completed = 0
        self.__eta = 0.0

    def update(self, iter_duration:float):
        """ Indicates that an iteration has been done and provides the duration """

        if self.__ema is None:
            self.__ema = iter_duration
        else:
            self.__ema = self.__alpha * iter_duration + (1 - self.__alpha) * self.__ema

        self.__completed += 1
        remaining = self.__total - self.__completed
        self.__eta = self.__ema * remaining

        return self.__eta
    
    def remaining_time(self) -> float:
        """ Returns the remaining time needed to achieve the rest of the iterations """

        return self.__eta

import math

class EMAETAEstimator:
    """ The EMA ETA estimator is designed to provide an estimation of the remaining
    time for a work divided into iterations.
    
    There is no unit for the duration, the caller is responsible of converting the duration
    in any unit. The time unit is consistent inside the estimator.

    The estimation is done by calculating a data rate.
    """

    def __init__(self):
        self.__total_size = 0
        self.__done_size = 0
        self.__weighted_speed_sum = 0.0
        self.__weight_sum = 0.0
    
    def setup(self, total_size:int, alpha=0.3):
        """ Setup the estimator with the total size of the data
        
        The alpha value is a factor for the linearization of the gaps between durations which means
        that when there are big differences between the duration of iterations, this difference
        will be lowered to minimize its impact.
        """

        self.__total_size = total_size
        self.__done_size = 0

        self.__weighted_speed_sum = 0.0
        self.__weight_sum = 0.0

    def speed(self):
        if self.__weight_sum == 0:
            return 0.0
        return self.__weighted_speed_sum / self.__weight_sum

    def update(self, iter_duration:float, filesize:int):
        """ Indicates that an iteration has been done and returns the remaining time """
        
        if iter_duration <= 0:
            return
        
        instant_speed = filesize / iter_duration

        w = filesize / (filesize + 1e6)

        self.__weighted_speed_sum += w * instant_speed
        self.__weight_sum += w

        self.__done_size += filesize
    
    def remaining_time(self) -> float:
        """ Returns the remaining time needed to achieve the rest of the iterations """

        remaining = self.__total_size - self.__done_size

        if remaining <= 0:
            return 0.0
        
        spd = self.speed()
        if spd <= 0:
            return math.inf
        
        return remaining / spd

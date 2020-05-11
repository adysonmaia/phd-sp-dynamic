from abc import ABC, abstractmethod


class Estimator(ABC):
    """Estimator Abstract Class
    """

    def __call__(self, *args, **kwargs):
        """Call the estimator as a function

        See :py:meth:`Estimator.calc`

        Args:
            *args:  args
            **kwargs: kwargs
        Returns:
            object: estimation result
        """
        return self.calc(*args, **kwargs)

    @abstractmethod
    def calc(self, *args, **kwargs):
        """Calculate the estimation

        Args:
            *args: args
            **kwargs: kwargs
        Returns:
            object: estimation result
        """
        pass


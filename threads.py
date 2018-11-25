import threading
import time


class StoppableThread(threading.Thread):
    """Thread class that implements a stop function"""

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None):
        self.target = target
        self.args = args
        self.kwargs = kwargs                 
        super(StoppableThread, self).__init__(group=group, target=target, name=name, 
            args=args, kwargs=kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()
        print("Thread stopped")

    def join(self, *args, **kwargs):
        self.stop()
        super(StoppableThread, self).join(*args, **kwargs)


class DroneThread(StoppableThread):
    """
    Stoppable thread that runs a target function in a loop
    """

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None):
        self._loopdelay = kwargs.pop('LoopDelay', 0)

        super(DroneThread, self).__init__(group=group, target=target, name=name,
                 args=args, kwargs=kwargs)
        
    def run(self):
        if self.target:
            while not self._stop_event.is_set():
                self.target(*self.args, **self.kwargs)   # run the target function
                time.sleep(self._loopdelay)

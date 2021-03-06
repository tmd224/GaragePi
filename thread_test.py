import time
from threads import DroneThread

def drone_func(name="Noodles"):
    print("Hello %s Drone Thread"%name)



if __name__=="__main__":

    d1 = DroneThread(target=drone_func, args=("Noody",), kwargs={'LoopDelay':2})
    try:
        d1.start()
        time.sleep(10)
    except KeyboardInterrupt:
        print("Stopping Thread")
        d1.stop()

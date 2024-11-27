import threading
import time
import socket
print("\033cStart")
a = 0

def count() :
    global a
    a +=1
    
def worker() :
    while True :
        count()
        if event.is_set() :
            print(threading.current_thread().name)
            break


event = threading.Event()
print(threading.current_thread().name)


for i in range (10000):
    event.clear()
    threading.Thread(target=worker).start()
    event.set()
    time.sleep(0.01)


print("End")
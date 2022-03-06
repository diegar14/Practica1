from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
from random import random, randint


N = 100
NPROD = 5



def delay(factor = 1000):  #Velocidad del proceso
    sleep(random()/factor)


def add_data(buffer, pid, data, mutex):  #Carga de datos al buffer
    
    mutex.acquire()  
    try:
        
        if buffer[pid] == 0:   #Si la celda está vacía
            buffer[pid] = data  #Cargamos el dato en la celda que corresponde al productor
            print(f"apilamos {data}")
            print([i for i in buffer])
        else:      
            print("se ha intentado añadir en una celda llena")
        
    finally:
        mutex.release()


def get_data(buffer, mutex, non_empty):
    
    mutex.acquire()
    try:
        idx = 0  #Este bucle saca la posición del mínimo ignorando los -1
        for i, c in enumerate(buffer):
            if c != -1 and  (c < buffer[idx] or buffer[idx]==-1):
                idx = i
               
        data = buffer[idx]
        
        if data == -1:  #Si es cierto, toda la lista es -1 y se ha terminado
            return [idx, data]
        
        buffer[idx] = 0  #Vacía la celda
        
        print(f"desapilamos {data}")
        print([i for i in buffer])
            
        delay()
                       
    finally:
        mutex.release()
        
    return [idx, data]


def producer(buffer, empty, non_empty, mutex):
    
    dato = 0
    pid = int(current_process().name.split('_')[1])
    
    for v in range(N):
        print (f"producer {current_process().name} produciendo")
        d = randint(1,5)
        dato += d  #Produce números de forma creciente
        delay()
        
        empty[pid].acquire()  #Marca que se está ocupando su celda
        add_data(buffer, pid, dato, mutex)  #Carga el dato
        non_empty[pid].release() #Marca que está ocupada la celda
        
        print (f"producer {current_process().name} almacenado {dato}")
       
    empty[pid].acquire()
    add_data(buffer, pid, -1, mutex) #Al acabar, carga el -1
    
    print (f"producer {current_process().name} finalizado")
    non_empty[pid].release()


def consumer(l, buffer, empty, non_empty, mutex):
    
    while True:
            
        print (f"consumer {current_process().name} desalmacenando")
        for i in range(len(buffer)):
            non_empty[i].acquire()  #Recibe cuando se llena el buffer
            
        [idx, dato] = get_data(buffer, mutex, non_empty)
        
        if dato == -1: #Todo el buffer el -1, para
            break
        
        for i in range(len(buffer)):
            if i == idx:
                empty[i].release() #Marca que está vacía la celda desapilada
            else: 
                non_empty[i].release() #Marca que siguen llenas las demás
        
        
        print (f"consumer {current_process().name} consumiendo {[idx,dato]}")
        l.append(dato) #Añade el dato al output
        
    print(l)
    print(len(l))
    if l == sorted(l) and len(l) == N*NPROD: #Verifica que l está ordenada y es del tamaño esperado
        print("Success")
    

def main():
    
    NCONS = 1
    K = NPROD
    
    buffer = Array('i', K)
    l = []
    
    for i in range(K):
        buffer[i] = 0
    print ("buffer inicial", buffer[:])

    #empty[i] es 0 cuando esta llena la celda i
    #non_empty[i] es 1 cuando esta llena la celda i
    non_empty = [Semaphore(0) for i in range (NPROD)]
    empty = [Semaphore(1) for i in range (NPROD)]
    mutex = Lock()
    
    prodlst = [ Process(target=producer,
                    name=f'prod_{i}',
                    args=(buffer, empty, non_empty, mutex))
                for i in range(NPROD) ]

    conslst = [ Process(target=consumer,
                    name=f'cons_{i}',
                    args=(l, buffer, empty, non_empty, mutex))
                for i in range(NCONS) ]
    
    for p in prodlst + conslst:
        p.start()


    for p in prodlst + conslst:
        p.join()
        
        

if __name__ == '__main__':
    main()

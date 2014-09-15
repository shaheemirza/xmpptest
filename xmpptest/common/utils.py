from threading import Thread
from multiprocessing import Process, Manager
import logging
import time


def run(client, worker_num, thread_num, results_dict):
    client.set_worker_num(worker_num)
    client.set_thread_num(thread_num)
    client.set_results_dict(results_dict)
    if client.connect():
        client.process(block=True)

def make_threads(clients, worker_num, results_dict):
    logger = logging.getLogger()
    threads = []
    for client in clients:
        thread = Thread(target=run, args=(client, worker_num, len(threads),
                                          results_dict, ))
        # thread.daemon = True
        thread.start()
        threads.append(thread)
    logger.info("Make %s threads" % len(threads))
    for thread in threads:
        thread.join()
        logger.info("Joined thread %s" % thread)

# {workder id: clients array}
def make_processes(clients):
    manager = Manager()
    results_dict = manager.dict()
    logger = logging.getLogger()
    logger.debug(clients)
    procs = []
    for wid, clients in clients.items():
        proc = Process(target=make_threads, args=(clients, len(procs),
                                                  results_dict, ))
        proc.daemon = False
        procs.append(proc)
    logger.info("Make %s processes" % len(procs))
    return procs, results_dict
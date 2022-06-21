import concurrent.futures as futures

class ThreadPool(futures.ThreadPoolExecutor):
    __instance = None

    def __init__(self):
        if ThreadPool.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__(None)
            ThreadPool.__instance = self
        

    @staticmethod
    def getInstance():
        if ThreadPool.__instance == None:
            ThreadPool()
        return ThreadPool.__instance

from jobshop_preprocess import Preprocess
import random

class JobShop:
    def __init__(self, preprocess_):
        self.iter = 0
        self.n = len((preprocess_.jobID))
        self.preprocess = preprocess_
        self.preJobDict = {}
        

    def init(self):
        self.iter = 0

    def step(self, path):
        step_list = []
        while len(step_list) < 5:
            r = str(random.randint(0,9))
            j = preprocess.jobID[random.randrange(0,self.n)]
            step_list.append((r,j))
        print(f"step_list={step_list}")
        for i in range(self.n):
            if i not in path:
                yield path[:] + [i]

    def score(self, path):
        """total distance of path"""
        total_waste = 0
        for jobInfo in path:
            total_waste += jobInfo[3]
        return total_waste

    def count(self):
        self.iter += 1

    def terminate(self):
        return self.iter >= self.n

if __name__ == '__main__':
    preprocess = Preprocess(str(1))
    
import os
import pandas as pd
from gurobipy import *
from typing import Dict, List
# import random
import heapq
import datetime
import plotly.express as px
import plotly.io as pio

# random.seed(0)
datasetDir = os.path.join("..","dataset")
# datasetDir = "big_dataset"

class Preprocess:
    
    # manHour: Dict[str, int] = {}
    # jobID: List[str] = []
    # jobOrder = set()
    # machineID: List[str] = []
    # prefixedOutput = [] # start_time, id
    # resultDict = {} # jobID, (machineID, start, end)
    
    dirpath = "data_prob1"
    logDirpath = "log1"
    
    allData = True
    testFlag = False
    timeRange = int(800)
    
    eraseZero = False
    
    # caseNum:string
    def __init__(self,_classNum):
        self.classNum = _classNum
        self.manHour: Dict[str, int] = {}
        self.jobID: List[str] = []
        self.jobOrder = set()
        self.machineID: List[str] = []
        self.prefixedOutput = [] # start_time, id
        self.resultDict = {} # jobID, (machineID, start, end)
        self.assignableList = {} # jobID, machineID, assignable
    
    def makeChart(self):
        resultName = f"result_{self.classNum}.txt"
        resultPath = os.path.join(self.dirpath,resultName)
        with open(resultPath, 'r') as f:
            data = f.readlines()
            for i, line in enumerate(data):
                if i>0:
                    jID, mID, st, ed = line.split(',')
                    self.resultDict[str(jID)] = (str(mID), int(st), int(ed))
        print(f"self.resultDict={self.resultDict}")
        
        dt = datetime.datetime(2024,6,1)
        if self.allData:
            df = pd.DataFrame([
                dict(Task=f"{self.classNum}_job_{jID}", Start=dt+datetime.timedelta(days=st-1), Finish=dt+datetime.timedelta(days=ed), Resource=f"machine_{mID}") for jID, (mID, st, ed) in self.resultDict.items()
            ])
        else:
            idSet = set()
            for i, (preID, postID) in enumerate(self.jobOrder):
                idSet.add(preID)
                idSet.add(postID)
                if i>10:
                    break
                
            df = pd.DataFrame([
                dict(Task=f"{self.classNum}_job_{jID}", Start=dt+datetime.timedelta(days=self.resultDict[jID][1]-1), Finish=dt+datetime.timedelta(days=self.resultDict[jID][2]), Resource=f"machine_{self.resultDict[jID][0]}") for jID in idSet
            ])
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Resource")
        # plt.title(f"result_{self.classNum}")
        gantopath = os.path.join(self.dirpath,"ganto",f"{self.classNum}.html")
        pio.write_html(fig,file=gantopath)
        
    
    def fixResult(self):
        preResultName = f"preResult_{self.classNum}.txt"
        preResultPath = os.path.join(self.dirpath,preResultName)
        with open(preResultPath, 'r') as f:
            data = f.readlines()
            for i,line in enumerate(data):
                if i>0:
                    id, t = line.split(',')
                    self.prefixedOutput.append((int(t),str(id)))
        
        self.prefixedOutput.sort()
        print(f"self.prefixedOutput={self.prefixedOutput}")
        
        hList = []
        for id in self.machineID:
            heapq.heappush(hList,(1,id))
        
        print(f"hList={hList}")
        
        resultName = f"result_{self.classNum}.txt"
        resultPath = os.path.join(self.dirpath,resultName)
        with open(resultPath, 'w') as f:
            print("jobID,machineID,start,end",file=f)
            for t, jID in self.prefixedOutput:
                now_t,mID = heapq.heappop(hList)
                print(f"{jID},{mID},{t},{t+self.manHour[jID]-1}",file=f)
                heapq.heappush(hList,(t+self.manHour[jID], mID))

    
    def readInput(self):
        self.readResource()
        self.readJobN()
        self.readPreJobID()
        self.readAssignable()
    
    def readResource(self):
        filePath = os.path.join(datasetDir,"resources.csv")
        df = pd.read_csv(filePath)
        machineID = df["machineID"].tolist()
        for id in machineID:
            self.machineID.append(str(id))
    
    def readAssignable(self):
        
        filePath = os.path.join(datasetDir,f"assignable_new_{self.classNum}.csv")
        df = pd.read_csv(filePath)
        for row in df.T:
            jobID = str(df.T[row]["jobID"])
            machineID = str(df.T[row]["machineID"])
            if int(df.T[row]["assignable"])==1:
                assignable = True
            else:
                assignable = False
            self.assignableList[jobID,machineID] = assignable
    
    def readJobN(self):
        
        filePath = os.path.join(datasetDir,f"jobs_{self.classNum}.csv")
        df = pd.read_csv(filePath)
        df = df.set_index("jobID")
        jobID, manHour = multidict(df.T)
        
        for id in jobID:
            if self.eraseZero and int(manHour[id])==0:
                self.jobID.append(str(id))
                self.manHour[str(id)] = int(1)
            else:
                self.jobID.append(str(id))
                self.manHour[str(id)] = int(manHour[id])
                
        # if self.testFlag==True:
        #     testFilePath = os.path.join(self.dirpath,f"jobs_{self.classNum}.csv")
        #     with open(testFilePath,"w") as f:
        #         for id in self.jobID:
        #             self.manHour[str(id)] = random.randint(1,5)
        #             print(f"{id},{self.manHour[str(id)]}",file=f)
                
    
    def readPreJobID(self):
        filePath = os.path.join(datasetDir,f"precedence_{self.classNum}.csv")
        df = pd.read_csv(filePath)
        for jobOrder in df.T:
            preJobID = str(df.T[jobOrder]["preJobID"])
            postJobID = str(df.T[jobOrder]["postJobID"])
            self.jobOrder.add((preJobID,postJobID))
        
if __name__ == '__main__':
    preprocess = Preprocess("36")
    preprocess.readInput()
    print(preprocess.assignableList)
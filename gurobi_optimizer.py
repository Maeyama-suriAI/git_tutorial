from gurobipy import *
from typing import Dict, List
import os
from UnionFind import UnionFind
import numpy as np
import random

# solve：問０
# solve_resource：問１

class job_UnionFind:
    
    def __init__(self,jobID_) -> None:
        self.uf = UnionFind(len(jobID_))
        self.jobOrder = jobID_
        self.jobIndex = {}
        for i,id in enumerate(jobID_):
            self.jobIndex[id] = i
    
    def union(self,x,y):
        self.uf.union(self.jobIndex[x],self.jobIndex[y])
    
    def all_group_members(self):
        job_group =[]
        for key,val in self.uf.all_group_members().items():
            gr = []
            for i in val:
                gr.append(self.jobOrder[i])
            job_group.append(gr)
        return job_group

# https://qiita.com/ookamikujira/items/809dda14787c900e7059 の丸パクリ
def solve_pulp(preprocess):
    
    print("solve_pulp start")

    # preprocessが持つ変数
    # manHour: Dict[str, int] = {}
    # jobID: List[str] = []
    # jobOrder = set()
    # machineID: List[str] = []
    # assignableList[jobID,machineID] = assignable
    
    manHour = preprocess.manHour
    jobID = preprocess.jobID
    jobOrder = preprocess.jobOrder
    machineID = preprocess.machineID
    prefixedOutput = preprocess.prefixedOutput
    resultDict = preprocess.resultDict
    assignableList = preprocess.assignableList
    
    #モデルインスタンスの作成
    # model = LpProblem("jobshop",sense=LpMinimize)
    model = Model("jobshop")

    #変数の設定
    #作業員wにおいて作業iが作業jより先行するか否か
    # x = LpVariable.dicts("x",[(i,j,k) for i in task for j in task for k in workers], cat="Binary" )
    x = model.addVars([(i,j,k) for i in jobID for j in jobID for k in machineID],name="x",vtype=GRB.BINARY)
    #作業員wにおいて作業iが実施されるか否か
    # y = LpVariable.dicts("y",[(i,k) for i in task for k in workers], cat="Binary" )
    y = model.addVars([(i,k) for i in jobID for k in machineID],name="y",vtype=GRB.BINARY)
    #作業iの完了時間
    # z = LpVariable.dicts("z",[(i) for i in task],cat="Continuous", lowBound=0)
    z = model.addVars([(i) for i in jobID],name="z",vtype=GRB.CONTINUOUS,lb=0)
    #すべてのタスクが完了する時間
    fintime = model.addVar(vtype=GRB.CONTINUOUS)
    QQQ = 9999
    
    # 資源制約
    # for (j,r),val in assignableList.items():
    #     if val==False:
    #         model.addConstr(y[j,r]==0)
    #         for k in jobID:
    #             model.addConstr(x[j,k,r] == 0)
    #             model.addConstr(x[k,j,r] == 0)
    
    #必ず作業が誰かに割り当てられる
    for i in jobID:
        model.addConstr(quicksum(y[i,k]  for k in machineID) == 1)
        # model += lpSum(y[i,k]  for k in machineID) == 1

    #作業iが作業jに先行するとき1、そうでないとき0
    for k in machineID:
        for i in jobID:
            for j in jobID:
                if i != j:
                    #ijの両方のJobを行う時のみ先行関係が発生する
                    #どちらかのJobが先行するとき、もう片方のJobは必ず後行するためijの関係が分かればjiの関係もわかる
                    #作業i,jともに後先の関係が無ければ作業員wは作業i,jを両方とも担当していない#
                    # model += 2*(x[i,j,k] + x[j,i,k])+1 >= y[i,k] + y[j,k]
                    # model += 2*(x[i,j,k] + x[j,i,k])   <= y[i,k] + y[j,k]
                    model.addConstr(2*(x[i,j,k] + x[j,i,k])+1 >= y[i,k] + y[j,k])
                    model.addConstr(2*(x[i,j,k] + x[j,i,k])   <= y[i,k] + y[j,k])
                elif i == j:
                    # model += x[i,j,k] == 0 #同一のJobに先行の関係はない
                    model.addConstr(x[i,j,k] == 0)

    #作業jが完了する時間z[i]
    for j in jobID:
        for k in machineID:
            model.addConstr(quicksum(manHour[i] * x[i,j,k] for i in jobID) + manHour[j] <= z[j])
            # model += lpSum(manHour[i] * x[i,j,k] for i in jobID) + manHour[j] <= z[j]

    #仕事iと仕事jの終了時間の関係式
    for k in machineID:
        for i in jobID:
            for j in jobID:
                if i != j:
                    # model += z[i] <= z[j] - manHour[j] + QQQ * (1-x[i,j,k])
                    model.addConstr(z[i] <= z[j] - manHour[j] + QQQ * (1-x[i,j,k]))

    #冷却作業は対応する焼き作業より必ず後に行う
    for i, j in jobOrder:
        model.addConstr(z[i] <= z[j] - manHour[j])

    #z[i]の最大を最小化
    for i in jobID:
        model.addConstr(z[i] <= fintime)
        # model += z[i] <= fintime 

    #目的関数
    # model.objective = fintime
    model.setObjective(fintime,GRB.MINIMIZE)
    
    model.optimize()
    
    def saveResult():
        # y = model.addVars([(i,k) for i in jobID for k in machineID]
        # filename = f"preResult_{preprocess.classNum}.txt"
        filename = f"result_{preprocess.classNum}.txt"
        filepath = os.path.join(preprocess.dirpath, filename)
        with open(filepath, "w") as f:
            print("jobID,machineID,start,end",file=f)
            for j in jobID:
                for r in machineID:
                    if y[j,r].x==True:
                        print(f"{j},{r},{z[j].x-manHour[j]},{z[j].x}",file=f)
                            
    # 計算結果出力
    def printSolution():
        if model.Status==GRB.Status.OPTIMAL:
            print("solved!")
            print(f"Opt. Value={model.ObjVal}")
            saveResult()
            
        elif model.Status==GRB.Status.TIME_LIMIT:
            filename = "timelimit.txt"
            filepath = os.path.join(preprocess.logDirpath,filename)
            with open(filepath,'a') as f:
                print(preprocess.classNum,file=f)
            print("time over")
            saveResult()
        else:
            filename = "nosolution.txt"
            filepath = os.path.join(preprocess.logDirpath,filename)
            with open(filepath,'a') as f:
                print(preprocess.classNum,file=f)
            print("No solution")
    
    printSolution()




def solve_resource(preprocess):
    
    # preprocessが持つ変数
    # manHour: Dict[str, int] = {}
    # jobID: List[str] = []
    # jobOrder = set()
    # machineID: List[str] = []
    
    INF = 2000 # INF
    
    jsModel = Model("jobshop")
    
    T = jsModel.addVars(preprocess.jobID, name="T", vtype=GRB.INTEGER)
    varList = []
    for j in preprocess.jobID:
        for r in preprocess.machineID:
            varList.append((j,r))
    X = jsModel.addVars(varList, name="X", vtype=GRB.BINARY)
    Z = jsModel.addVar(name="Z")
    jsModel.addConstrs(Z >= X[j,r]*(T[j]+preprocess.manHour[j]) for j in preprocess.jobID for r in preprocess.machineID)
    
    jsModel.setObjective(Z, GRB.MINIMIZE)
    
    # 可能なリソース指定（問１のみ）
    
    
    # 順序
    jsModel.addConstrs(T[postJ] - T[preJ] >= preprocess.manHour[preJ] for preJ, postJ in preprocess.jobOrder)
    
    # 資源制約
    F = {}
    for j in preprocess.jobID:
        for k in preprocess.jobID:
            for r in preprocess.machineID:
                F[j,k,r] = jsModel.addVar(vtype=GRB.BINARY)
                jsModel.addConstr(T[k] - T[j] - preprocess.manHour[j] + INF*(1-X[j,r]*X[k,r]) >= -INF*(1-F[j,k,r]))
    
    jsModel.addConstrs(
        F[j,k,r] + F[k,j,r] >= 1
        for j in preprocess.jobID
        for k in preprocess.jobID
        for r in preprocess.machineID
    )
    # jsModel.addConstrs(
    #     T[j] - T[k] - preprocess.manHour[k] + INF*(1-X[j,r]*X[k,r]) >= -INF(1-(T[j]-T[k])/(T[k]-T[j])) # T_k <= T_jのとき
    #     for j in preprocess.jobID
    #     for k in preprocess.jobID
    #     for r in preprocess.machineID
    # )
    
    # 任意のジョブが一回は行われる
    jsModel.addConstrs(quicksum(X[j,r] for r in preprocess.machineID)==1 for j in preprocess.jobID)
        
    # 最適化する時間を指定
    time_limit = 100
    jsModel.Params.TimeLimit = time_limit
    
    jsModel.setParam(GRB.Param.Threads, 20) # 計算に使うスレッド数？
    
    # 最適化計算
    jsModel.optimize()
    
    def saveResult():
        filename = f"preResult_{preprocess.classNum}.txt"
        filepath = os.path.join(preprocess.dirpath, filename)
        with open(filepath, "w") as f:
            print("id,start_time",file=f)
            for j in preprocess.jobID:
                for r in preprocess.machineID:
                    if X[j,r].x==True:
                        print(f"{j},{T[j].x},{r}",file=f)
                            
    # 計算結果出力
    def printSolution():
        if jsModel.Status==GRB.Status.OPTIMAL:
            print("solved!")
            print(f"Opt. Value={jsModel.ObjVal}")
            saveResult()
            
        elif jsModel.Status==GRB.Status.TIME_LIMIT:
            filename = "timelimit.txt"
            filepath = os.path.join(preprocess.logDirpath,filename)
            with open(filepath,'a') as f:
                print(preprocess.classNum,file=f)
            print("time over")
            saveResult()
        else:
            filename = "nosolution.txt"
            filepath = os.path.join(preprocess.logDirpath,filename)
            with open(filepath,'a') as f:
                print(preprocess.classNum,file=f)
            print("No solution")
    
    printSolution()    
    
    jsModel.close()


#時間添え字の手法
def solve(preprocess):
    
    # preprocessが持つ変数
    # manHour: Dict[str, int] = {}
    # jobID: List[str] = []
    # jobOrder = set()
    # machineID: List[str] = []
    
    timeRange = preprocess.timeRange
    print(f"timeRange={timeRange}")        
    jsModel = Model(f"jobshop_{preprocess.classNum}")
        
    # 決定変数作成
    # X[j,t]：ジョブjがt期に始まるか否か
    varlist = []
    for id in preprocess.jobID:
        for t in range(1,timeRange+2):
            varlist.append((id,t))
    print(f"len varlist={len(varlist)}")
    
    X = jsModel.addVars(varlist, name="X", ub=1, vtype=GRB.INTEGER) # id,t期に開始したか否か
    
    S = jsModel.addVars(preprocess.jobID, name="S") # 開始時刻
    jsModel.addConstrs((quicksum((t-1)*X[id,t] for t in range(2, timeRange+2)) == S[id] for id in preprocess.jobID), name="start time")
    
    Z = jsModel.addVar(name="Z")
    
    # 目的関数
    jsModel.addConstrs(Z >= S[id]+preprocess.manHour[id] for id in preprocess.jobID)
    jsModel.setObjective(Z, GRB.MINIMIZE)
    
    # ジョブ制約１：各ジョブが全体で一回行われる
    for idf in preprocess.jobID:
        jsModel.addConstr((quicksum(X[idf,tf] for tf in range(1, timeRange-preprocess.manHour[id]+2)) == 1), name="jobC1")
        jsModel.addConstr((quicksum(X[idf,tf] for tf in range(timeRange-preprocess.manHour[id]+2, timeRange+2)) == 0), name="jobC1")

    # ジョブ制約２：
    jsModel.addConstrs((
            S[postID] - S[preID] >= preprocess.manHour[preID]
            for preID, postID in preprocess.jobOrder
        ), name="jobC2"
    )
    
    # 資源制約
    jsModel.addConstrs(
        ((quicksum(X[jID,s] for jID in preprocess.jobID for s in range(
                # max(1, int(t - preprocess.manHour[jID] + 1)), min(t+1 ,timeRange-preprocess.manHour[jID] + 2)
                max(1, int(t - preprocess.manHour[jID] + 1)), t+1
            )
        ) <= len(preprocess.machineID)) for t in range(1, timeRange+2)),
        name=f"rcC_t"
    )
    
    print(f"len(preprocess.machineID))={len(preprocess.machineID)}")
    
    # 境界条件調整のため
    jsModel.addConstrs((timeRange >= S[id] + preprocess.manHour[id] for id in preprocess.jobID),"C_timerange")
    
    # 最適化する時間を指定
    time_limit = 100
    jsModel.Params.TimeLimit = time_limit
    
    jsModel.setParam(GRB.Param.Threads, 4) # 計算に使うスレッド数？
    
    # 最適化計算
    jsModel.optimize()
    
    def saveResult():
        filename = f"preResult_{preprocess.classNum}.txt"
        filepath = os.path.join(preprocess.dirpath, filename)
        with open(filepath, "w") as f:
            print("id,start_time",file=f)
            for t in range(1,timeRange+2):
                for id in preprocess.jobID:
                    if X[id,t].x==1:
                        print(f"{id},{t}",file=f)
    
    # 計算結果出力
    def printSolution():
        if jsModel.Status==GRB.Status.OPTIMAL:
            print("solved!")
            print(f"Opt. Value={jsModel.ObjVal}")
            saveResult()
            
        elif jsModel.Status==GRB.Status.TIME_LIMIT:
            filename = "timelimit.txt"
            filepath = os.path.join(preprocess.logDirpath,filename)
            with open(filepath,'a') as f:
                print(preprocess.classNum,file=f)
            print("time over")
            saveResult()
        else:
            filename = "nosolution.txt"
            filepath = os.path.join(preprocess.logDirpath,filename)
            with open(filepath,'a') as f:
                print(preprocess.classNum,file=f)
            print("No solution")
    
    printSolution()    
    
    jsModel.close()

if __name__ == '__main__':
    
    jobOrder=["4","6","3","2","10"]
    
    uf = job_UnionFind(jobOrder)
    
    
    uf.union("4","6")
    uf.union("10","4")
    for val in uf.all_group_members():
        print(f"val:{val}")
    # key:0,val:[0]
    # key:1,val:[1, 2]
    # key:3,val:[3]
    # key:4,val:[4]
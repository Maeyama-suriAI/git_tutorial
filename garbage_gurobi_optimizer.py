from gurobipy import *
from typing import Dict, List
import os

def sumJobHour(preprocess):
    
    sumHour = 0
    for key, mH in preprocess.manHour.items():
        # print(key,mH)
        sumHour += mH
        
    return sumHour

def solve(preprocess):
    
    # preprocessが持つ変数
    # manHour: Dict[str, int] = {}
    # jobID: List[str] = []
    # jobOrder = set()
    # machineID: List[str] = []
    
    timeRange = preprocess.timeRange
    print(f"timeRange={timeRange}")
    
    print("start gurobi_optimize!")
        
    jsModel = Model(f"jobshop_{preprocess.classNum}")
        
    # 決定変数作成
    # X[j,t]：ジョブjがt期に始まるか否か
    varlist = []
    for t in range(1,timeRange+2):
        for id in preprocess.jobID:
            varlist.append((id,t))
    print(f"len varlist={len(varlist)}")
    
    X = jsModel.addVars(varlist, name="X", vtype=GRB.BINARY)
    Z = jsModel.addVar(name="Z", vtype=GRB.INTEGER)
    
    # 目的関数
    jsModel.addConstrs(Z >= (t+preprocess.manHour[id]-1) * X[id,t] for id,t in varlist)
    jsModel.setObjective(Z, GRB.MINIMIZE)
    
    # ジョブ制約１：各ジョブが全体で一回行われる
    # jsModel.addConstrs(((X.sum(id, "*") == 1) for id in preprocess.jobID),name="jobC1")
    for idf in preprocess.jobID:
        # print(f"idf={idf}")
        # for tf in range(1, timeRange - preprocess.manHour[idf] - 1 + 1):
        #     print(f"tf={tf}")
        # return
        jsModel.addConstr((quicksum(X[idf,tf] for tf in range(1, timeRange - preprocess.manHour[idf] + 1 + 1)) == 1), name="jobC1")
        # jsModel.addConstr((quicksum(X[idf,tf] for tf in range(1, timeRange - preprocess.manHour[idf] - 1 + 1)) == 1), name="jobC1")
        
        # jsModel.addConstr((quicksum(X[idf,tf] for tf in range(1, timeRange + 1)) == 1), name="jobC1")
    
    # ジョブ制約２：
    jsModel.addConstrs((
            X[preID, t] + quicksum(
                X[postID, s] for s in range(1, (t+preprocess.manHour[preID]-1) +1)
            ) <= 1
            for preID, postID in preprocess.jobOrder
            for t in range(1, (timeRange-preprocess.manHour[preID]+1) +1)
        ), name="jobC2"
    )
    
    # 資源制約
    jsModel.addConstrs(
        ((quicksum(X[jID,s] for jID in preprocess.jobID for s in range(
                max(1, int(t - preprocess.manHour[jID] + 1)), min(t,timeRange-preprocess.manHour[jID] + 1)+1
            )
        ) <= len(preprocess.machineID)) for t in range(1, timeRange+1)),
        name=f"rcC_t"
    )
    
    print(f"len(preprocess.machineID))={len(preprocess.machineID)}")
    
    # 最適化計算
    jsModel.optimize()
    
    # 計算結果出力
    def printSolution():
        
        if jsModel.Status==GRB.Status.OPTIMAL:
            print("solved!")
            print(f"Opt. Value={jsModel.ObjVal}")
            
            filename = f"preResult_{preprocess.classNum}.txt"
            filepath = os.path.join(preprocess.dirpath, filename)
            with open(filepath, "w") as f:
                print("id,start_time",file=f)
                for t in range(1,timeRange):
                    for id in preprocess.jobID:
                        if X[id,t].x==True:
                            print(f"{id},{t}",file=f)
        else:
            
            print("No solution")
    
    printSolution()
    
    jsModel.close()


if __name__ == '__main__':
    
    jobID, man_hour = multidict({
        "0":75,
        "1":75,
    })
    
    solve(jobID, man_hour)
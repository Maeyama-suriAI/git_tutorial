from gurobipy import *
from typing import Dict, List
import os
from UnionFind import UnionFind
import numpy as np
import random

# solve：問０
# solve_resource：問１

graph_flag = False

class job_UnionFind:
    
    def __init__(self,jobID_) -> None:
        self.uf = UnionFind(len(jobID_))
        self.jobID = jobID_
        self.jobIndex = {}
        for i,id in enumerate(jobID_):
            self.jobIndex[id] = i
    
    def union(self,x,y):
        # print(self.jobIndex)
        # print(f"x={x}")
        # print(f"y={y}")
        self.uf.union(self.jobIndex[x],self.jobIndex[y])
    
    def all_group_members(self):
        job_group =[]
        for key,val in self.uf.all_group_members().items():
            gr = []
            for i in val:
                gr.append(self.jobID[i])
            job_group.append(gr)
        return job_group

def solve_highSpeed(preprocess):
    
    classNum = preprocess.classNum
    jobID = preprocess.jobID
    jobOrder = preprocess.jobOrder
    machineID = preprocess.machineID
    prefixedOutput = preprocess.prefixedOutput
    resultDict = preprocess.resultDict
    assignableList = preprocess.assignableList
    
    ansDict = {} # jobID: (machineID, start, end)
    
    # ufでジョブをグループでくくる
    # 50ジョブずつ、計10グループに分ける
    # print(f"jobID={jobID}")
    uf = job_UnionFind(jobID)
    for pre,post in jobOrder:
        uf.union(pre,post)
    
    # print(uf.all_group_members())
    # print(f"{classNum}:{len(uf.all_group_members())}")
    
    n_clasterID = 2
    
    ############################### 
    random.seed(0)
    g_clasterID = [i for i in range(len(uf.all_group_members()))] # この順列をランダムに入れ替えたら、何か起こる？
    random.shuffle(g_clasterID)
    #############################  
    
    g_clasterID = np.array_split(g_clasterID, n_clasterID)
    # 
    # g_claster = [for i in range()]
    # print(g_clasterID)
    g_claster = []
    for cl in g_clasterID:
        gr = []
        for cl_idx in cl:
            for jID in uf.all_group_members()[cl_idx]:
                gr.append(jID)
        g_claster.append(gr)
    
    print(g_claster)
    
    # return
    
    for job_group in g_claster:
        
        # breakpoint()
        
        #モデルインスタンスの作成
        # model = LpProblem("jobshop",sense=LpMinimize)
        model = Model("jobshop")
        
        #変数の設定
        #すべてのタスクが完了する時間
        fintime = model.addVar(vtype=GRB.CONTINUOUS)
        QQQ = 9999
        
        ######################特例ロジック###############################
        #作業員wにおいて作業iが作業jより先行するか否か
        # x = LpVariable.dicts("x",[(i,j,k) for i in task for j in task for k in workers], cat="Binary" )
        x = model.addVars([(i,j,k) for i in job_group for j in job_group for k in machineID],name="x",vtype=GRB.BINARY)
        
        #作業員wにおいて作業iが実施されるか否か
        # y = LpVariable.dicts("y",[(i,k) for i in task for k in workers], cat="Binary" )
        y = model.addVars([(i,k) for i in job_group for k in machineID],name="y",vtype=GRB.BINARY)
        
        #作業iの完了時間
        # z = LpVariable.dicts("z",[(i) for i in task],cat="Continuous", lowBound=0)
        z = model.addVars([(i) for i in job_group],name="z",vtype=GRB.CONTINUOUS,lb=0)
        
        # print(x)
        # print(y)
        # print(z)
        # breakpoint()
        
        # job_group、探索済みジョブ以外の所要時間を0とする
        manHour = {id:0 for id in job_group}
        for j in job_group:
            manHour[j] = preprocess.manHour[j]
        
        # 各リソースにおいて、asnDictの最大値よりも大きな値を取ること
        # jobID: (machineID, start, end)
        last_time = {r:0 for r in machineID}
        for j,(r,st,ed) in ansDict.items():
            last_time[r] = max(last_time[r], ed)
        for j in job_group:
            for r in machineID:
                model.addConstr(y[j,r]*last_time[r] <= z[j]-manHour[j])
        
        # すでに探索済みのジョブについては決定変数を定数化する
        # ansDict = {} # jobID: (machineID, start, end)
        # for j,val in ansDict.items():
        #     r,start,end = val
        #     model.addConstr(z[j]==end)
        #     model.addConstr(y[j,r]==1)
        # print(f"manHour={manHour}")
        ######################ここからは同様のロジック###############################

        # 資源制約
        # for (j,r),val in assignableList.items():
        for j in job_group:
            for r in machineID:
                if assignableList[j,r]==False:
                    model.addConstr(y[j,r]==0)
                    for k in job_group:
                        model.addConstr(x[j,k,r] == 0)
                        model.addConstr(x[k,j,r] == 0)


        #必ず作業が誰かに割り当てられる
        for i in job_group:
            model.addConstr(quicksum(y[i,k]  for k in machineID) == 1)
            # model += lpSum(y[i,k]  for k in machineID) == 1

        #作業iが作業jに先行するとき1、そうでないとき0
        for k in machineID:
            for i in job_group:
                for j in job_group:
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
        for j in job_group:
            for k in machineID:
                model.addConstr(quicksum(manHour[i] * x[i,j,k] for i in job_group) + manHour[j] <= z[j])
                # model += lpSum(manHour[i] * x[i,j,k] for i in jobID) + manHour[j] <= z[j]

        #仕事iと仕事jの終了時間の関係式
        for k in machineID:
            for i in job_group:
                for j in job_group:
                    if i != j:
                        # model += z[i] <= z[j] - manHour[j] + QQQ * (1-x[i,j,k])
                        model.addConstr(z[i] <= z[j] - manHour[j] + QQQ * (1-x[i,j,k]))

        #冷却作業は対応する焼き作業より必ず後に行う
        for i, j in jobOrder:
            if i in job_group:
                model.addConstr(z[i] <= z[j] - manHour[j])

        #z[i]の最大を最小化
        for i in job_group:
            model.addConstr(z[i] <= fintime)
            # model += z[i] <= fintime 

        #目的関数
        # model.objective = fintime
        model.setObjective(fintime,GRB.MINIMIZE)

        model.optimize()
        
        # jobID: (machineID, start, end)
        for j in job_group:
            for r in machineID:
                if y[j,r].x==True:
                    ansDict[j] = (r, z[j].x-manHour[j], z[j].x)
    
    # print(f"ansDict={ansDict}")
    optVal = 0
    filename = f"result_{preprocess.classNum}.txt"
    filepath = os.path.join(preprocess.dirpath, filename)
    with open(filepath, "w") as f:
        print("jobID,machineID,start,end",file=f)
        for j, (r, st, ed) in ansDict.items():
            print(f"{j},{r},{st},{ed}",file=f)
            optVal = max(optVal,ed)
    
        # print("id,start_time",file=f)
        # for j, (r, st, ed) in ansDict.items():
        #     print(f"{j},{r},{st},{ed}",file=f)
    
    if graph_flag:
        from datetime import datetime, timedelta
        import plotly.express as px
        import plotly.io as pio
        import pandas as pd
        def add_minutes_to_datetime(minute_to_add):
            # 指定された日時をdatetimeオブジェクトに変換
            dt = datetime(2023, 1, 1, 10, 00)
            # 指定された分数を加算
            later = dt + timedelta(minutes=minute_to_add)
            # 結果を返す
            return later
        #各作業者の作業一覧とその作業完了時間
        result = {"作業者":[],"作業":[],"作業開始時間":[],"作業完了時間":[]}
        for j, (r, st, ed) in ansDict.items():
                # print(f"{j},{r},{st},{ed}",file=f)
                result["作業者"].append(r)
                result["作業"].append(j)
                result["作業開始時間"].append(st)
                result["作業完了時間"].append(ed)
        #データフレームの作成
        data = []
        for i in range(len(result["作業"])):
            data.append(dict(
                Worker     = result["作業者"][i], 
                Start      = add_minutes_to_datetime(result["作業開始時間"][i]), 
                Finish     = add_minutes_to_datetime(result["作業完了時間"][i]), 
                Task       = result["作業"][i])
        )
        df = pd.DataFrame(data)
        #ガントチャートの描画
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Worker", color="Task")
        fig.update_yaxes(autorange="reversed")
        fig.show()
    
    return optVal

def solve_bigData(preprocess):
    
    classNum = preprocess.classNum
    jobID = preprocess.jobID
    jobOrder = preprocess.jobOrder
    machineID = preprocess.machineID
    prefixedOutput = preprocess.prefixedOutput
    resultDict = preprocess.resultDict
    assignableList = preprocess.assignableList
    
    ansDict = {} # jobID: (machineID, start, end)
    
    # ufでジョブをグループでくくる
    # 50ジョブずつ、計10グループに分ける
    uf = job_UnionFind(jobID)
    for pre,post in jobOrder:
        uf.union(pre,post)
    
    # print(uf.all_group_members())
    print(f"{classNum}:{len(uf.all_group_members())}")
    
    n_clasterID = 2
    
    
    ############################### 
    random.seed(0)
    g_clasterID = [i for i in range(len(uf.all_group_members()))] # この順列をランダムに入れ替えたら、何か起こる？
    random.shuffle(g_clasterID)
    #############################  
    
    g_clasterID = np.array_split(g_clasterID, n_clasterID)
    # 
    # g_claster = [for i in range()]
    print(g_clasterID)
    g_claster = []
    for cl in g_clasterID:
        gr = []
        for cl_idx in cl:
            for jID in uf.all_group_members()[cl_idx]:
                gr.append(jID)
        g_claster.append(gr)
    
    print(g_claster)
    
    # return
    
    for job_group in g_claster:
        
        
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
        
        
        ######################特例ロジック###############################
        # job_group、探索済みジョブ以外の所要時間を0とする
        manHour = {id:0 for id in jobID}
        for j in job_group:
            manHour[j] = preprocess.manHour[j]
        for j,val in ansDict.items():
            manHour[j] = preprocess.manHour[j]
        
        # すでに探索済みのジョブについては決定変数を定数化する
        # ansDict = {} # jobID: (machineID, start, end)
        for j,val in ansDict.items():
            r,start,end = val
            model.addConstr(z[j]==end)
            model.addConstr(y[j,r]==1)
        print(f"manHour={manHour}")
        ######################ここからは同様のロジック###############################

        # 資源制約
        for (j,r),val in assignableList.items():
            if val==False:
                model.addConstr(y[j,r]==0)
                for k in jobID:
                    model.addConstr(x[j,k,r] == 0)
                    model.addConstr(x[k,j,r] == 0)


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
        
        # jobID: (machineID, start, end)
        for j in job_group:
            for r in machineID:
                if y[j,r].x==True:
                    ansDict[j] = (r, z[j].x-manHour[j], z[j].x)
    
    # print(f"ansDict={ansDict}")
from gurobi_optimizer import *
from jobshop_preprocess import Preprocess
from highSpeed_optimizer import *

def test():
    
    # manHour: Dict[str, int] = {}
    # jobID: List[str] = []
    # jobOrder = set()
    # machineID: List[str] = []
    
    preprocess = Preprocess("19")
    preprocess.readInput()
    
    print(f"manHour={preprocess.manHour}")
    print(f"jobID={preprocess.jobID}")
    print(f"jobOrder={preprocess.jobOrder}")
    print(f"machineID={preprocess.machineID}")
    
    # for i in range(48):
    #     strI = str(i)
    #     preprocess = Preprocess(strI)
    #     preprocess.readInput()
    #     sumJob = sumJobHour(preprocess)
    #     print(f"ID:{strI} sumJob:{sumJob}")

def calculation():
    # preprocess = Preprocess("1")
    # preprocess.readInput()
    # 
    # solve(preprocess)
    # 
    # preprocess.fixResult()
    # preprocess.makeChart()
    
    # wrong_list = [20]
    wrong_list = [i for i in range(0,48)]
    # wrong_list = [4,7,9,10,12,18,34,36,39,45,47]
    # wrong_list = [20]
    # for i in range(0,48):
    optval_list = []
    for i in wrong_list:
        if i == 20:
            optval_list.append(10000)
            continue
        preprocess = Preprocess(str(i))
        preprocess.readInput()

        # solve(preprocess)
        # solve_resource(preprocess)
        opval = solve_pulp(preprocess)
        # solve_bigData(preprocess)
        # opval = solve_highSpeed(preprocess)
        optval_list.append(opval)

        # preprocess.fixResult()
        # preprocess.makeChart()
        # print(f"preprocess.manHour={preprocess.manHour}")
    print(optval_list)
    with open("optVal.txt", "w") as f:
        for i,ov in enumerate(optval_list):
            print(f"{i}:{ov}",file=f)

def big_calc():
    preprocess = Preprocess("big")
    preprocess.readInput()
    # solve(preprocess)
    # solve_resource(preprocess)
    # solve_pulp(preprocess)
    # solve_bigData(preprocess)
    solve_highSpeed(preprocess)

def graph():
    wrong_list = [20]
    # wrong_list = [i for i in range(1,48)]
    
    for i in wrong_list:
    # for i in wrong_list:
        preprocess = Preprocess(str(i))
        preprocess.readInput()
        preprocess.fixResult()
        preprocess.makeChart()
        print(f"preprocess.manHour={preprocess.manHour}")

# def graph_fromResult():
#     wrong_list = [20]
#     # wrong_list = [i for i in range(1,48)]
#     
#     for i in wrong_list:
#     # for i in wrong_list:
#         # preprocess = Preprocess(str(i))
#         # preprocess.readInput()
#         # preprocess.fixResult()
#         makeChart()
#         print(f"preprocess.manHour={preprocess.manHour}")

def test():
    import plotly.express as px
    import plotly.io as pio
    import pandas as pd
    df = pd.DataFrame([
        dict(Task="Job A", Start='2009-01-01', Finish='2009-02-28', Resource="Alex"),
        dict(Task="Job B", Start='2009-03-05', Finish='2009-04-15', Resource="Alex"),
        dict(Task="Job C", Start='2009-02-20', Finish='2009-05-30', Resource="Max")
    ])  

    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Resource")
    fig.update_yaxes(autorange="reversed")
    pio.write_html(fig,file="./6-2.html")
    # fig.write_image('table.png')
    # breakpoint()
    # fig.close()
    # fig.show()

def show_graph(dirpath,classNum):
    ansDict = {}
    optVal = 0
    filename = f"result_{classNum}.txt"
    filepath = os.path.join(dirpath, filename)
    with open(filepath, "r") as f:
        data = f.readlines()
        for i,line in enumerate(data):
            if i==0:
                continue
            j,r,st,ed = line.split(',')
            st = float(st)
            ed = float(ed)
            optVal = max(optVal,ed)
            ansDict[j] = (r,st,ed)
    
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
    # fig.show()
    # gantopath = os.path.join("ganto1",f"{classNum}.html")
    #Bpio.write_html(fig,file=gantopath)
    print(classNum,optVal)

if __name__ == '__main__':
    # calculation()
    # big_calc()
    # graph()
    # test()
    # git_tutorial
    # git check
    dirpath = "data_prob1_hSp"
    for i in range(47):
        show_graph(dirpath,i)

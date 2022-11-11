import argparse
import pandas as pd
import glob
import sys
import json
import numpy as np
sys.path.append('../')
from periodicity_classification.fft import is_periodicity

parser = argparse.ArgumentParser()
parser.add_argument("--data_dir",type=str,help="数据地址")
parser.add_argument("--sample_interval",type=int,help="数据样本采样的时间")
parser.add_argument("--cycle_duration",type=int,help="预测周期")
parser.add_argument("--format",type=str,help="数据类型")
args = parser.parse_args()

def parse_data(file, first_indexs):
    result_map={}
    json_data=json.load(open(file))['data']['result']
    for data in json_data:
        index=data['metric']['pod']
        if index in first_indexs:
            timsp_datas = data['values']
            datas = []
            for timesp_data in timsp_datas:
                datas.append(timesp_data[1])
            result_map[index]=datas
        else:
            continue
    return result_map

def main():
    # load data
    listglob = glob.glob('{}/*.{}'.format(args.data_dir,args.format))
    listglob.sort()
    data = pd.DataFrame()
    datas_map={}
    intersection_indexs=[]
    i=0
    for file in listglob:
        indexs=[]
        data=json.load(open(file))['data']['result']
        
        for data in data:
            indexs.append(data['metric']['pod'])
        
        if i==0:
            intersection_indexs = indexs
        else:
            intersection_indexs = set(intersection_indexs).intersection(indexs)
        i +=1

    for file in listglob:
        if args.format == "json":
            file_map = parse_data(file, intersection_indexs)
            datas_map[file] = file_map
            print(file)
        else:
            raise NotImplementedError

    # concat data
    print('{} data'.format(len(intersection_indexs)))
    for index in intersection_indexs:
        datas=[]
        for key in datas_map:
            data=datas_map[key][index]
            datas=np.hstack((datas,data))
        is_period, cycles = is_periodicity(datas, args.sample_interval, args.cycle_duration)
        if is_period:
            print("{} is period signal,cycle maybe {}".format(index,cycles))

if __name__ == "__main__":
    main()

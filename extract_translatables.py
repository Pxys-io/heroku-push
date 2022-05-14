import csv
import json
import sys
import re
arg=sys.argv[1:]
print(arg)
path=arg[0]

starter=arg[1]
langs=arg[2].split(",")
delimiter=arg[3]
lines=[]
with open(path,"r") as f:
    pattern1=re.compile(starter+r"\"(.*?)\"")
    pattern2=re.compile(starter+r"'(.*?)'")
    m1=pattern1.findall(f.read())
    m2=pattern2.findall(f.read())
    m=m1+m2
    print(len(m))
    # c=csv.writer(open("locales.csv","w"),dialect="excel",delimiter=delimiter)
    data={}
    for match in m:
        text_field={}
        for i,lang in enumerate(langs):
            if i==0:text_field[lang]=match
            else:text_field[lang]="NULL"
        data[match]=text_field
    print(data)
    _temp={
        "langs":langs,
        "data":data
    }
    with open("locales.json","w") as o:
        json.dump(_temp,o)
    
    # c.writerows(rows)
            
    
    
    
    
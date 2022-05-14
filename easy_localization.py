import json

import csv
class EasyLocalization:
    # data={}
    def __init__(self,json_path) -> None:
        with open(json_path,"r") as f:
            _temp=json.load(f)
            # self.available_langs=_temp["langs"]
            _langs={}
            for l in _temp["langs"]:
                splitted=l.split("_")
                # print(splitted)
                if len(splitted)>1:
                    _langs[splitted[0]]=splitted[1]
                else:
                    _langs[l] = l
            self.available_langs=_langs
            self.data=_temp["data"]
        # pass
    # def __init__(self,csv_path,deli="^") -> None:
    #     """Deprecated, use json 

    #     Args:
    #         csv_path (_type_): path to csv file
    #         deli (str, optional): "delimeter ". Defaults to "^".
    #     """
    #     data_path=csv_path
    #     with open(data_path, "r") as f:
    #         csv.reader(f,dialect="excel",delimiter=deli)
            
    #         text=f.read().splitlines()
    #         _data={}
    #         __langs=text[0].split(deli)
    #         langs=[]
    #         available_langs={}
    #         for _l in __langs:
    #             splitted=_l.split("_")
    #             if len(splitted)>1:
    #                 langs.append(splitted[0])
    #                 available_langs[splitted[0]]=splitted[1]
    #             else:
    #                 langs.append(_l)
    #                 available_langs[_l]=_l
                
    #         self.available_langs=available_langs
    #         for t in text[1:]:
    #             texts=t.split(deli)
    #             _temp={}
    #             _langs=langs[:len(t)] + [""]*(len(t) - len(langs))
    #             for i,s in enumerate(texts):
                    
    #                 _temp[_langs[i]]=s.strip()
    #             _data[texts[0].strip()]=_temp
    #     self.data=_data
    def translate(self,text:str,lang:str):
        text=text.strip()
        if text not in self.data.keys():return text
        available:dict=self.data[text]
        if lang not in available.keys() or available[lang]=="" or available[lang]=="NULL" or available[lang]=="\\" :return text
        return str(available[lang])
    def export(self,file_name):
        with open(file_name, "w") as f:
            _temp={"langs":self.available_langs,"data":self.data}
            json.dump(self.data,f)
            

        
        
                
            
            
        
        
    
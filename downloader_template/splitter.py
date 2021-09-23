import csv
import os
import shutil

with open('urllist.csv') as f:
    reader=csv.DictReader(f)
    partnumber=0
    for num,cand in enumerate(reader):
        if num%5==0:
            partnumber+=1
            foldername=f'part{partnumber}/'
            # if not os.path.exists(foldername):
            #     os.mkdir(foldername)
            shutil.copytree('barebone',foldername)
            currentfile=open(foldername+'urllist.csv','w')
            currentfile.write('name'+','+'website\n')
        currentfile.write(cand['name']+','+cand['website']+'\n')

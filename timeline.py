import datetime
import re
from sys import argv
from lxml import objectify
from collections import OrderedDict 
import math
import numpy as np


def outliers_modified_z_score(ys):
    threshold = 3.5

    median_y = np.median(ys)
    median_absolute_deviation_y = np.median([np.abs(y - median_y) for y in ys])
    modified_z_scores = [0.6745 * (y - median_y) / median_absolute_deviation_y
                         for y in ys]
    outliers = set(np.where(np.abs(modified_z_scores) > threshold)[0])
    print(outliers)
    max_norm = min(set(ys) - outliers) - 1.5 * np.std(list(set(ys) - outliers))
    new_list = list(map(lambda x: max_norm if np.abs(modified_z_scores)[ys.index(x)] > threshold else x, ys))
    mini = min(new_list)
    return list(map(lambda x: x - mini, new_list))

#Constants
monthNames = ["January", "Feburary", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"]

#Data
dates = []
description = []
lengthOfLine = 10

#Input of the form string "yyyy-mm-dd"
def dashedToDate(dashed):
    dateArray = dashed.split('-')
    year = int(dateArray[0])
    month = int(dateArray[1])
    day = int(dateArray[2])
    return datetime.date(year,month,day)

if len(argv) > 1:
    data = open(argv[1],'r')
else:
    data = open('knowledge.xml', 'rb')

dates = {}
xml = data.read().decode('utf-8').encode('ascii')
root = objectify.fromstring(xml)
for i in root.entity:
    if "hasDate" in i.attrib:
        try:
            dates[i.attrib['link']] = datetime.datetime.strptime(i.attrib['hasDate'], "%Y-%m-%d")
        except:
            dates[i.attrib['link']] = datetime.datetime.strptime(i.attrib['hasDate'], "%Y")

data.close()

# create file to put the TeX/Tikz code

texfile = open('picture.tex','w')
texfile.writelines("\\begin{tikzpicture}")

# Styles used
texfile.writelines("[datemarker/.style={circle,draw=black,fill=white,radius=4pt},\n")
texfile.writelines("textlabel/.style={anchor=west,text height=1.7ex,text depth=.25ex}]\n")

# Draw the background
texfile.writelines("\\draw (0,0) -- (0,"+ str(lengthOfLine)+ ");\n")

order = OrderedDict(sorted(dates.items(), key=lambda t: t[1]))
ordered = list(order.items())
startDate = order[ordered[0][0]]
#print(order)
endDate = order[ordered[-1][0]]
span = (endDate - startDate).days

# Draw the dates
diffs = []
labels = []
for x in range(len(dates)):
    diff = (ordered[x][1] - startDate).days
    diffs.append(diff)
    labels.append(ordered[x])
#    print(diff)
prev = -10000
modified = outliers_modified_z_score(diffs)
for i, x in enumerate(modified):
    print(x)
    tmp = x
    if x - prev < 300:
        x = x + 300
    prev = tmp
    month = monthNames[labels[i][1].month-1]
    dateText = month+" "+str(labels[i][1].day)+", "+str(labels[i][1].year)
    yCoordOnLine = (x*lengthOfLine)/max(modified)
#    print(yCoordOnLine)
    textToPrint = dateText +": "+ labels[i][0].split("/")[-1].replace('_'," ")
    texfile.writelines("\\node at (0, "+ str(yCoordOnLine)+ ") [datemarker] {};\n")
    texfile.writelines("\\draw (0.1, "+ str(yCoordOnLine)+ ") node [textlabel] {"+textToPrint+"};\n")


texfile.writelines("\\end{tikzpicture}")
texfile.close()


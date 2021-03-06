#!/usr/bin/python3
# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np
import cv2
import matplotlib.pyplot as plt
import argparse
import os
import shutil
import projectMethod as pm
import sys
import csv


def createFileList(myDir, format='.png'):
    fileList = []
    print(myDir)
    for root, dirs, files in os.walk(myDir, topdown=False):
        for name in files:
            if name.endswith(format):
                fullName = os.path.join(root, name)
                fileList.append(fullName)
    return fileList

def main():
    kbdinput = input('Select File : ')
    cntimagetillnow = 0
    inputImg = cv2.imread("Docs/{}".format(kbdinput))
    binimg = pm.preprocess(inputImg)
    dest = 'testingImgs'
    pm.horizontal_cut(binimg,dest)
    cntimagetillnow = pm.vertical_cutTraining(dest,cntimagetillnow)
    print('{}'.format(cntimagetillnow),' images now loaded.')
    listname = []
    with open('CsvData/TestBook.csv', mode='r', encoding='utf-8-sig') as outfile:
        reader = csv.reader(outfile)
        for rows in reader:
            listname.append(rows[0])
    #print(listname)
    myFileList = createFileList('testingImgs/verticalcutoutput')
    res = []
    index = 0
    for file in myFileList:
        print(file)
        img_file = Image.open(file)
        # img_file.show()

        # get original image parameters...
        width, height = img_file.size
        format = img_file.format
        mode = img_file.mode

        # Make image Greyscale
        img_grey = img_file.convert('L')
        #img_grey.save('result.png')
        #img_grey.show()

        # Save values
        value = np.asarray(img_grey.getdata(), dtype=np.int).reshape((img_grey.size[1], img_grey.size[0]))
        #value = np.select([value <= 127, value>127], [np.zeros_like(value), np.ones_like(value)])
        value = np.where(value > 127 , 1, 0)
        name = listname[index]
        value = value.flatten()
        last = np.array([name])
        value = np.concatenate((value, last))
        res.append(value)
        print(value)
        index +=1
    with open("CsvData/testdata.csv", 'w' , newline='',encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(res)


if __name__ == "__main__":
    main()

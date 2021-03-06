from PIL import Image
import numpy as np
import cv2
import matplotlib.pyplot as plt
import argparse
import os
import shutil

def imreadUnicode(imgDirectory): #reads image with unicode chars
    readimg = cv2.imdecode(np.fromfile(u'{}'.format(imgDirectory), np.uint8), cv2.IMREAD_UNCHANGED)
    return readimg

def imreadUnicodeGray(imgDirectory): #reads image with unicode chars
    readimg = cv2.imdecode(np.fromfile(u'{}'.format(imgDirectory), np.uint8), cv2.IMREAD_GRAYSCALE)
    return readimg

def imwriteUnicode(img,imgDir,imgName): #writes image to a file with unicode char name
    cv2.imwrite('{}/tempimg.png'.format(imgDir), img)
    os.rename(r'{}/tempimg.png'.format(imgDir),r'{}/{}.png'.format(imgDir,imgName))

def color_cut(img):
    kernel = np.ones((2,2),np.uint8)
    # Convert BGR to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # define range of black color in HSV
    lower_val = np.array([0,0,0])
    upper_val = np.array([179,100,130])

    # Threshold the HSV image to get only black colors
    mask = cv2.inRange(hsv, lower_val, upper_val)

    # Bitwise-AND mask and original image
    res = cv2.bitwise_and(img,img, mask= mask)
    # invert the mask to get black letters on white background
    res2 = cv2.bitwise_not(mask)
    '''
    # display image
    cv2.imshow("img", res)
    cv2.imshow("img2", res2)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    '''
    return res2

def image_deskew(image):
    # convert the image to grayscale and flip the foreground
    # and background to ensure foreground is now "white" and
    # the background is "black"
    #gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(image)
    # threshold the image, setting all foreground pixels to
    # 255 and all background pixels to 0
    thresh = cv2.threshold(gray, 0, 255,
        cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    # grab the (x, y) coordinates of all pixel values that
    # are greater than zero, then use these coordinates to
    # compute a rotated bounding box that contains all
    # coordinates
    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]
    # the `cv2.minAreaRect` function returns values in the
    # range [-90, 0); as the rectangle rotates clockwise the
    # returned angle trends to 0 -- in this special case we
    # need to add 90 degrees to the angle
    if angle < -45:
        angle = -(90 + angle)
    # otherwise, just take the inverse of the angle to make
    # it positive
    else:
        angle = -angle
    # rotate the image to deskew it
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h),
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    '''
    # draw the correction angle on the image so we can validate it
    cv2.putText(rotated, "Angle: {:.2f} degrees".format(angle),
        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    '''
    # show the output image
    print("[INFO] angle: {:.3f}".format(angle))
    return rotated

def preprocess(img): #recieve input image and turns it into clean binary
    img = cv2.fastNlMeansDenoisingColored(img,None,10,10,7,21) 
    img = cv2.resize(img, (1240,1754), interpolation = cv2.INTER_AREA)
    '''height,width ,channel= img.shape
    for x in range(height):
        for y in range(width):
            color = img[x,y]
            if not (color[0] == color[1] == color[2]):
                img[x,y] = [255,255,255]'''
    grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #colorgut = color_cut(img)
    #img = image_deskew(colorgut)
    #ret,binimg = cv2.threshold(img,125,255,cv2.THRESH_BINARY) #turns image into binary
    binimg = cv2.adaptiveThreshold(grayimg,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
    #binimg = cv2.bitwise_not(binimg)
    #inverts image
    #binimg = cv2.cvtColor(binimg, cv2.COLOR_GRAY2RGB)
    return binimg

def normalize(img,dimensioncrop): #extend image with black spaces to the desired dimension
    blank_image = np.zeros((dimensioncrop,dimensioncrop,3), np.uint8)
    blank_image = cv2.bitwise_not(blank_image) #inverts image
    #blank_image = Image.new('1', (dimensioncrop, dimensioncrop), color = 255)
    width,height,channel = img.shape
    if width > dimensioncrop or height > dimensioncrop:
        return blank_image
    for x in range(width):
        for y in range(height):
            blank_image[x,y,0] = img[x,y,0]
            blank_image[x,y,1] = img[x,y,1]
            blank_image[x,y,2] = img[x,y,2]
    return blank_image

def normalize_byresize(img,dimensioncrop): #extend image by scaling to the desired dimension: loses scale property
    blank_image = np.zeros((dimensioncrop,dimensioncrop,3), np.uint8)
    blank_image = cv2.bitwise_not(blank_image) #inverts image
    #blank_image = Image.new('1', (dimensioncrop, dimensioncrop), color = 255)
    width,height,channel = img.shape
    dim = (dimensioncrop,dimensioncrop)
    if width > dimensioncrop or height > dimensioncrop:
        return blank_image
    blank_image = cv2.resize(img, dim, interpolation = cv2.INTER_NEAREST)
    return blank_image

def comparison(baseimg,comparator): #recieve 2 image outputs matching percentage by pixel
    width,height,channel = baseimg.shape
    width2,height2,channel2 = comparator.shape
    if width == width2 and height == height2:
        print('image dimension matched')
    else:
        print('invalid dimension')
        return 0
    matchingpix = 0
    pixdetected = 3600
    for x in range(width):
        for y in range(height):
            if comparator[x,y,0] == baseimg[x,y,0]:
                matchingpix += 1
    match_percent = matchingpix/pixdetected
    match_percent = str(round(match_percent, 2))
    return match_percent

def comparison_split4x4(baseimg,comparator): #recieve 2 image and blocksize returns error percent
    width,height,channel = baseimg.shape
    width2,height2,channel2 = comparator.shape
    splitsize = 8
    if width == width2 and height == height2:
        #print('image dimension matched')
        pass
    else:
        print('invalid dimension')
        return 0
    if width % splitsize != 0 or height % splitsize != 0:
        print('indivisible to {} block'.format(splitsize))
        return 0
    blocksize = width//splitsize
    blockMatrix = (splitsize,splitsize)
    splitbase = np.zeros(blockMatrix)
    splitcompare = np.zeros(blockMatrix)
    for x in range(splitsize):
        for y in range(splitsize):
            for h in range(blocksize):
                for k in range(blocksize):
                    if baseimg[(x*blocksize)+h,(y*blocksize)+k,0] == 255:
                        splitbase[x,y] += 1
                    if comparator[(x*blocksize)+h,(y*blocksize)+k,0] == 255:
                        splitcompare[x,y] += 1
    error = np.zeros(blockMatrix)
    for x in range(splitsize):
        for y in range(splitsize):
            if splitcompare[x,y] == 0:
                if splitbase[x,y] == 0:
                    error[x,y] = 0
                else:
                    error[x,y] = 100
            else:
                error[x,y] = abs((splitcompare[x,y]-splitbase[x,y])/splitcompare[x,y])*100
    error_percent = 0
    for x in range(splitsize):
        for y in range(splitsize):
            error_percent += error[x,y]
    error_percent = error_percent/(splitsize*splitsize)
    return error_percent

def comparison_split4x4_getleast_error(baseimg,comparefolderPath): #recieve base image to compare to most fit img in folderPath
    leastError = 100
    fileWithLeastErrror = None
    errorPercent = 0
    for file in os.listdir(comparefolderPath):
        if file.endswith(".png"):
            pass
        else:
            continue
        compimg = imreadUnicode('{}/{}'.format(comparefolderPath,file))
        errorPercent = comparison_split4x4(baseimg,compimg)
        if errorPercent < leastError:
            leastError = errorPercent
            fileWithLeastErrror = '{}'.format(file)
    leastErrorImgComparedto = fileWithLeastErrror
    if fileWithLeastErrror == 'blank.png':
        leastErrorImgComparedto = 'X'
    else:
        leastErrorImgComparedto = leastErrorImgComparedto[0]
    return leastErrorImgComparedto

def crop_image_only_outside(img): #crop image to reduce all blackspace outside
    height,width,channel = img.shape
    top = 0
    bottom = 0
    left = 0
    right = 0
    for x in range(height):
        for y in range(width):
            if img[x,y,0] == 0:
                top = x
                break
        if top != 0:
            break
    Cropimg = img[top:height,0:width]
    height,width,channel = Cropimg.shape
    for y in range(width):
        for x in range(height):
            if Cropimg[x,y,0] == 0:
                left = y
                break
        if left != 0:
            break
    Cropimg = Cropimg[0:height,left:width]
    height,width,channel = Cropimg.shape
    for x in range(height):
        for y in range(width):
            if Cropimg[height-x-1,width-y-1,0] == 0:
                bottom = height-x
                break
        if bottom != 0:
            break
    Cropimg = Cropimg[0:bottom,0:width]
    height,width,channel = Cropimg.shape
    for y in range(width):
        for x in range(height):
            if Cropimg[height-x-1,width-y-1,0] == 0:
                right = width-y
                break
        if right != 0:
            break
    Cropimg = Cropimg[0:height,0:right]
    return Cropimg

def horizontal_cut(binimg,dest): #cuts binary image into folder 'horizontalcutoutput' by row to dest folder
    
    #finding horizontal partition
    height,width = binimg.shape
    lines = []

    blotcount = 0
    beginsignal = 1

    shutil.rmtree('{}/horizontalcutoutput'.format(dest),ignore_errors=True)
    os.makedirs('{}/horizontalcutoutput'.format(dest),exist_ok=True)

    for x in range(height):
        for y in range(width):
            if binimg[x,y] == 0:
                blotcount += 1
        if blotcount > 0 and beginsignal == 1:
            lines.append(x)
            beginsignal = 0
        elif blotcount == 0 and beginsignal == 0:
            lines.append(x)
            beginsignal = 1
        blotcount = 0


    #print(lines_begin[0])
    #discarding close lines
    margin = 3
    linebefore = 0
    thisline = 0

    filteredlines = []

    for x in lines:
        if linebefore == 0 and thisline == 0:
            thisline = x
        elif thisline != 0 and linebefore == 0:
            filteredlines.append(thisline)
            linebefore = thisline
            thisline = x
        else:
            if thisline - linebefore >= margin and x - thisline >= margin:
                filteredlines.append(thisline)
            linebefore = thisline
            thisline = x
    filteredlines.append(thisline)
    #results are stored in filteredlines
    '''
    for x in filteredlines:
        cv2.line(img,(0,x),(width,x),(250,0,0),1)
    '''
    cropbegin = 0
    cnt = 0
    for x in filteredlines:
        if cropbegin == 0:
            cropbegin = x
        else:
            imgCrop = binimg[cropbegin-1:x+1,0:width]
            flag = cv2.imwrite('{}/horizontalcutoutput/cropimage_{}.png'.format(dest,cnt), imgCrop)
            #print(cnt,'H')
            #print(flag)
            cnt += 1
            cropbegin = 0
    #cv2.imwrite('testfile/paragraphs_out.png',img)

    #cv2.imshow('image',img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return dest

def vertical_cut(horizontalcutfolder_path): #cuts horizontal cuts outputs into small chars by line into same directory

    cntimg = 0
    path = '{}/horizontalcutoutput'.format(horizontalcutfolder_path)
    shutil.rmtree('{}/verticalcutoutput/'.format(horizontalcutfolder_path),ignore_errors=True)
    for file in os.listdir(path):
        if file.endswith(".png"):
            pass
        else:
            break
        #image preprocessing
        shutil.rmtree('{}/verticalcutoutput/line{}'.format(horizontalcutfolder_path,cntimg),ignore_errors=True)

        os.makedirs('{}/verticalcutoutput/line{}'.format(horizontalcutfolder_path,cntimg),exist_ok=True)
        binimg = cv2.imread('{}/horizontalcutoutput/cropimage_{}.png'.format(horizontalcutfolder_path,cntimg))
        height,width = binimg.shape

        #finding vertical partition
        lines = []
        blotcount = 0
        beginsignal = 1

        for y in range(width):
            for x in range(height):
                if binimg[x,y] == 0:
                    blotcount += 1
            if blotcount > 0 and beginsignal == 1:
                lines.append(y)
                beginsignal = 0
            elif blotcount == 0 and beginsignal == 0:
                lines.append(y)
                beginsignal = 1
            blotcount = 0


        #print(lines_begin[0])
        #discarding close lines
        margin = 0
        linebefore = 0
        thisline = 0

        filteredlines = []

        for x in lines:
            if linebefore == 0 and thisline == 0:
                thisline = x
            elif thisline != 0 and linebefore == 0:
                filteredlines.append(thisline)
                linebefore = thisline
                thisline = x
            else:
                if thisline - linebefore >= margin and x - thisline >= margin:
                    filteredlines.append(thisline)
                linebefore = thisline
                thisline = x
        filteredlines.append(thisline)
        #results are stored in filteredlines
        '''
        for x in filteredlines:
            cv2.line(binimg,(x,0),(x,height),(250,0,0),1)
        '''
        cropbegin = 0
        cnt = 0
        for x in filteredlines:
            if cropbegin == 0:
                cropbegin = x
            else:
                imgCrop = binimg[0:height,cropbegin-1:x+1]
                imgCrop = crop_image_only_outside(imgCrop)
                imgCrop = normalize(imgCrop,36)
                if len(str((cnt+1))) == 1:
                    fill = 'n000' + str((cnt+1))
                elif len(str((cnt+1))) == 2:
                    fill = 'n00' + str((cnt+1))
                elif len(str((cnt+1))) == 3:
                    fill = 'n0' + str((cnt+1))
                else:
                    fill = 'n' + str((cnt+1))                
                flag = cv2.imwrite('{}/verticalcutoutput/line{}/{}.png'.format(horizontalcutfolder_path,cntimg,fill), imgCrop)
                #print(cnt,'V')
                #print(flag)
                cnt += 1
                cropbegin = 0
        cv2.imwrite('testfile/paragraphs_out.png',binimg)

        #cv2.imshow('image',binimg)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        cntimg += 1
    return '{}/verticalcutoutput'.format(horizontalcutfolder_path)

def vertical_cutTraining(horizontalcutfolder_path,cntallimgtilnow = 0): #cuts horizontal cuts outputs into small chars by line into same directory

    cntimg = 0
    cntallimg = cntallimgtilnow
    path = '{}/horizontalcutoutput'.format(horizontalcutfolder_path)
    if cntallimgtilnow == 0:
        shutil.rmtree('{}/verticalcutoutput'.format(horizontalcutfolder_path),ignore_errors=True)
        os.makedirs('{}/verticalcutoutput'.format(horizontalcutfolder_path),exist_ok=True)
    for file in os.listdir(path):
        if file.endswith(".png"):
            pass
        else:
            break
        #image preprocessing
        binimg = cv2.imread('{}/horizontalcutoutput/cropimage_{}.png'.format(horizontalcutfolder_path,cntimg))
        height,width,chanel = binimg.shape

        #finding vertical partition
        lines = []

        blotcount = 0
        beginsignal = 1

        for y in range(width):
            for x in range(height):
                if binimg[x,y,0] == 0:
                    blotcount += 1
            if blotcount > 0 and beginsignal == 1:
                lines.append(y)
                beginsignal = 0
            elif blotcount == 0 and beginsignal == 0:
                lines.append(y)
                beginsignal = 1
            blotcount = 0


        #print(lines_begin[0])
        #discarding close lines
        margin = 0
        linebefore = 0
        thisline = 0

        filteredlines = []

        for x in lines:
            if linebefore == 0 and thisline == 0:
                thisline = x
            elif thisline != 0 and linebefore == 0:
                filteredlines.append(thisline)
                linebefore = thisline
                thisline = x
            else:
                if thisline - linebefore >= margin and x - thisline >= margin:
                    filteredlines.append(thisline)
                linebefore = thisline
                thisline = x
        filteredlines.append(thisline)
        #results are stored in filteredlines
        '''
        for x in filteredlines:
            cv2.line(binimg,(x,0),(x,height),(250,0,0),1)
        '''
        cropbegin = 0
        for x in filteredlines:
            if cropbegin == 0:
                cropbegin = x
            else:
                imgCrop = binimg[0:height,cropbegin-1:x+1]
                imgCrop = crop_image_only_outside(imgCrop)
                imgCrop = normalize(imgCrop,36)
                if len(str((cntallimg+1))) == 1:
                    fill = 'n000' + str((cntallimg+1))
                elif len(str((cntallimg+1))) == 2:
                    fill = 'n00' + str((cntallimg+1))
                elif len(str((cntallimg+1))) == 3:
                    fill = 'n0' + str((cntallimg+1))
                else:
                    fill = 'n' + str((cntallimg+1))
                flag = cv2.imwrite('{}/verticalcutoutput/{}.png'.format(horizontalcutfolder_path,fill), imgCrop)
                #print(cnt,'V')
                #print(flag)
                cntallimg += 1
                cropbegin = 0
        cv2.imwrite('testfile/paragraphs_out.png',binimg)

        #cv2.imshow('image',binimg)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        cntimg += 1
    return cntallimg

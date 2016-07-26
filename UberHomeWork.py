#!/usr/bin/env python
# coding: utf-8
__author__      = "Siyu Zhu"
__copyright__ = "Copyright 2016, Uber Homework"
__version__ = "0.0.1"
__email__ = "junesiyu@gmail.com"

get_ipython().magic(u'matplotlib inline')
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches
import matplotlib.animation as animation
from subprocess import check_output, STDOUT
from PIL import Image
import numpy as np

def rgb2gray(rgb):
    return np.dot(rgb[...,:3], [0.299, 0.587, 0.114])

def createFileList(dirname, targetname, lengthn, maxn):
    '''
    Create file list to feed in the darknet/yolo validation mode

    Input:
    dirname: dir contains image files
    targetname: target text filename contains file list

    '''
    with open(targetname, 'wb') as f:
        for i in range(1, maxn):
            filename = str(i).zfill(lengthn)+'.jpg' + '\n'
            fullname = os.path.join(dirname, filename)
            f.write(fullname)
            #print fullname,
    return


def getConfDict(infofile, ):
    ''' read detection file and find most confident detection for each frame
    Input:
        infofile: text file generated by yolo with car confidence and bounding boxes
    Output:
        dictionary: {key: image file name}, {value: (confidence, xmin, ymin, xmax, ymax)}
    '''
    with open(infofile) as f:
        confdict = dict()
        lines = f.readlines()
        for line in lines:
            line = line.split(' ')
            imageno = line[0]
            crate = float(line[1])
            if imageno not in confdict or crate > confdict[imageno][0]:
                    xmin, ymin, xmax, ymax = [float(x) for x in line[2:]]
                    confdict[imageno] = [crate, xmin, ymin, xmax, ymax]
    return confdict


def generateBB(confdict, targetfilename, dirname, lengthn, maxn, ):
    '''generate bounding box movie for detection results
    Input:
        confdict: confidence and bounding box dictionary from getConfDict
        targetfilename: movie file name to save
        dirname: dir contains original image sequences
        lengthn: image file name length
        maxn: total number of jpg files'''

    # create writer for dumping movie content
    FFMpegWriter = animation.writers['ffmpeg']
    metadata = dict(title='Movie Test', artist='Matplotlib',
                    comment='Movie support!')
    writer = FFMpegWriter(fps=15, metadata=metadata)

    # initialize first frame
    # load image
    filename = '00000001.jpg'
    fullname = os.path.join(dirname, filename)
    im = mpimg.imread(fullname)
    # show image
    fig1 = plt.figure(figsize = (6.40, 2.72))
    fig1.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
    ax1 = fig1.add_subplot(111)
    im1 = plt.imshow(im)

    with writer.saving(fig1, targetfilename, 100):
        # iterate over all image frames
        for i in range(1, maxn):
            key = str(i).zfill(lengthn)

            # get image plot
            filename = key +'.jpg'
            fullname = os.path.join(dirname, filename)
            im = mpimg.imread(fullname)
            im1.set_data(im)

            # add bounding box
            xmin, ymin, xmax, ymax = confdict[key][1:]
            xmin, ymin, w, h = xmin, ymin, xmax-xmin, ymax-ymin
            rect1 = patches.Rectangle((xmin, ymin), w, h, fill=False, edgecolor = 'r')
            ax1.add_patch(rect1)
            ax1.axis('off')
            #plt.show()

            writer.grab_frame()
            rect1.remove()

def cropBB(confdict, dirname, lengthn, maxn, ):
    '''grop bounding box region for semantic segmentations
    Input:
        confdict: confidence and bounding box dictionary from getConfDict
        dirname: dir contains original image sequences
        lengthn: image file name length
        maxn: total number of jpg files

    Output:
        color image containing segmentation maps are saved to files with 'crop....jpg'
        '''
    import numpy as np
    # iterate over all image frames
    for i in range(1, maxn):
        key = str(i).zfill(lengthn)
        filename = key +'.jpg'
        fullname = os.path.join(dirname, filename)
        im = mpimg.imread(fullname)

        xmin, ymin, xmax, ymax = confdict[key][1:]
        w, h = xmax - xmin, ymax - ymin
        xmin, ymin, xmax, ymax = max(1, xmin - w/2), max(1, ymin - h/2), min(im.shape[1], xmax + w/2), min(im.shape[0], ymax + h/2)
        im = im[ymin:ymax, xmin:xmax]
        im = Image.fromarray(np.uint8(im))
        im.thumbnail((250, 250), Image.ANTIALIAS)
        im = np.array(im.getdata(), np.uint8).reshape(im.size[1], im.size[0], 3)
        plt.imsave(os.path.join(dirname, 'crop_'+filename), im)
    return

def pixSegmentor(confdict, dirname, lengthn, maxn):
    imheight, imwidth = 272, 640
    # detection threshold is 0.9
    dthre = 0.9

    for i in xrange(1, maxn):
        key = str(i).zfill(lengthn)
        filename = 'new_'+key +'.png'
        fullname = os.path.join(dirname, filename)
        print fullname
        im = mpimg.imread(fullname)

        # embed segmentation map into original image
        xmin, ymin, xmax, ymax = [int(x) for x in confdict[key][1:]]
        w, h = xmax - xmin, ymax - ymin
        xmin, ymin, xmax, ymax = max(1, xmin - w/2), max(1, ymin - h/2), min(imwidth, xmax + w/2), min(imheight, ymax + h/2)

        im = Image.fromarray(np.uint8(im*255))
        im = im.resize(( xmax - xmin, ymax - ymin))
        im = np.array(im.getdata(), np.uint8).reshape(im.size[1], im.size[0], 3)
        canvas = np.zeros((imheight, imwidth, 3))
        canvas[ymin:ymax, xmin:xmax, :] = im


        # find target region
        canvas = np.float32(canvas) / 255
        canvas = canvas[:,:,0]*255 + canvas[:,:,1]*255*255 + canvas[:,:,2]
        xmin, ymin, xmax, ymax = confdict[key][1:]
        roi = canvas[ymin:ymax, xmin:xmax]

        # count labels precision for each segment
        totallabels = np.unique(canvas)
        roilabels = np.unique(roi)
        roidict = dict()
        for i in roilabels:
            roidict[i] = np.count_nonzero(roi == i)
        for i in totallabels:
            p = 0
            if i in roidict: p = roidict[i]
            if float(p) / np.count_nonzero(canvas == i) < dthre:
                canvas[canvas == i] = 0

        # binarize segmentation map
        canvas = np.uint8(canvas > 0)*255
        # save image
        plt.imsave(os.path.join(dirname, 'seg_'+filename), canvas)

def saliencyMovie (targetfilename, rawdirname, mapdirname, lengthn, maxn):
    '''generate saliency movie for pixel detection results
    Input:
        targetfilename: movie file name to save
        rawdirname: dir contains original image sequences
        mapdirname: dir contains segmentation map sequences
        lengthn: image file name length
        maxn: total number of jpg files'''

    targetfilename = 'pixSeg.mp4'
    rawdirname = '/Users/siyuzhu/yolo/darknet/car/'
    mapdirname = '/Users/siyuzhu/jupyter/uber/segmap/'

    # create writer for dumping movie content
    FFMpegWriter = animation.writers['ffmpeg']
    metadata = dict(title='Movie Test', artist='Matplotlib',
                    comment='Movie support!')
    writer = FFMpegWriter(fps=15, metadata=metadata)

    # initialize first frame
    # load image
    filename = '00000001.jpg'
    fullname = os.path.join(rawdirname, filename)
    im = mpimg.imread(fullname)

    filename = 'seg_new_00000001.png'
    fullname = os.path.join(mapdirname, filename)
    smap = mpimg.imread(fullname)
    im[:,:,0] = im[:,:,0]+smap[:,:,0]*255

    # show image
    fig1 = plt.figure(figsize = (6.40, 2.72))
    fig1.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
    ax1 = fig1.add_subplot(111)
    im1 = plt.imshow(im)


    with writer.saving(fig1, targetfilename, 100):
        # iterate over all image frames
        for i in range(1, maxn):
            key = str(i).zfill(lengthn)

            # get image plot
            filename = key +'.jpg'
            fullname = os.path.join(rawdirname, filename)
            im = mpimg.imread(fullname)

            filename = 'seg_new_'+key+'.png'
            fullname = os.path.join(mapdirname, filename)
            smap = mpimg.imread(fullname)
            im[:,:,0] = im[:,:,0]+smap[:,:,0]*255

            im1.set_data(im)
            writer.grab_frame()


def SegMovie (targetfilename, rawdirname, lengthn, maxn):
    '''generate color segmentation movie for pixel detection results
    Input:
        targetfilename: movie file name to save
        rawdirname: dir contains segmentation color image sequences
        lengthn: image file name length
        maxn: total number of jpg files'''



    # create writer for dumping movie content
    FFMpegWriter = animation.writers['ffmpeg']
    metadata = dict(title='Movie Test', artist='Matplotlib',
                    comment='Movie support!')
    writer = FFMpegWriter(fps=15, metadata=metadata)

    # initialize first frame
    # load image
    filename = 'new_00000001.png'
    fullname = os.path.join(rawdirname, filename)
    im = mpimg.imread(fullname)


    # show image
    fig1 = plt.figure()
    fig1.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
    ax1 = fig1.add_subplot(111)
    ax1.axis('off')
    im1 = plt.imshow(im)
    plt.show()
    raw_input()


    with writer.saving(fig1, targetfilename, 100):
        # iterate over all image frames
        for i in range(1, maxn):
            key = str(i).zfill(lengthn)

            # get image plot
            filename = 'new_'+key +'.png'
            fullname = os.path.join(rawdirname, filename)
            im = mpimg.imread(fullname)

            im1.set_data(im)
            writer.grab_frame()


if __name__ == '__main__':
    lengthn = 8
    maxn = 253
    dirname = '/Users/siyuzhu/yolo/darknet/car/' # change this to point to car image sequence
    segdirname = '/Users/siyuzhu/jupyter/uber/segmap/' # change this to point to segmentation map produced by GBS with random color.
    tmpdirname = '/Users/siyuzhu/work/src/github.com/miguelfrde/image-segmentation/tmp'
    # change this to point to segmentation map produced by GBS
    filelist = 'pascal.2014.test.txt'
    infofile = '/Users/siyuzhu/yolo/darknet/results/comp4_det_test_car.txt'
    # change this to your yolo directry containing output file from valid mode.

    # create file list to feed yolo
    createFileList(dirname, filelist, lengthn, maxn)

    # Run yolo in a subroutine
    curdir = os.getcwd()
    yolodir = '/Users/siyuzhu/yolo/darknet/'
    os.chdir(yolodir)
    check_output('./darknet yolo valid cfg/yolo.cfg yoloweights/yolo.weights', stderr=STDOUT, shell=True)
    os.chdir(curdir)

    # create bounding box dictionary from yolo detection
    dic = getConfDict(infofile, )

    # create movie
    generateBB(dic, 'detBB.mp4', dirname, lengthn, maxn, )
    cropBB(dic, dirname, lengthn, maxn, )

    # create movie for pixel segmentation
    pixSegmentor(dic, segdirname, lengthn, maxn,)
    saliencyMovie ('pixSeg.mp4', dirname, mapdirname, lengthn, maxn)

    targetfilename = 'colorSeg.mp4'
    SegMovie ('colorSeg.mp4', tmpdirname, lengthn, maxn)

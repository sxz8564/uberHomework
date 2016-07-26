#### This is the code for Uber homework.

****
It perform detection on a video sequence to predict bounding box of a moving car. It perform pixel segmentation to the same car. The detection is performed using YOLO. The segmentation is performed using GBS. 

#### Prerequisites
****
To run the code, first, download prerequisite packages, including YOLO and GBS. 

Follow this instructions to download darknet and YOLO. 
<http://pjreddie.com/darknet/yolo/>

Follow this instructions to download Google Go and GBS.
<https://github.com/miguelfrde/image-segmentation>

For GBS, you need to replace the code in /src/github.com/miguelfrde/image-segmentation/main.go with the code in this repository. 

#### Running the Code
****
You need to change the directory name in the test Harness (__main__) UberHomeWork.py to the actural directory that you installed yolo and GBS. 

Please also notice that you need to download data from PASCAL and weight for YOLO. 

UberHomeWork.py is the main code. This code will produce videos as final prediction output.


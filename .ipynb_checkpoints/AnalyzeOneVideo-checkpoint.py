
# coding: utf-8

# In[ ]:


import numpy as np
import cv2
import time
import os
import os.path
import glob
from multiprocessing import Pool, Process
import math
import gc
import datetime
import sys
sys.path.append('/home/gravishlab/Documents/Python/')
sys.path.append('/home/gravishlab/Documents/Python/Tracker/')
sys.path.append('/home/gravishlab/Documents/Python/Tracker/Tracker/')
from Tracker import Tracker
from Tracker.Tracker import Tracker


print("Imported videos")

    
    
def loadendframes(vname, sep):
    
    # capture video, and find number of frames
    n_sub_frames = 3
    cap = cv2.VideoCapture(vname)
    vFr = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#     print('---N_Frames', vFr)
    
    frames = np.zeros((n_sub_frames, h, w), np.uint8)
    
    for kk,fr in enumerate(np.linspace(sep, vFr-sep, n_sub_frames).astype(int)):
        cap.set(1,fr) # define frame (must be between 0 and 1)
        tru, ret = cap.read(1)

        # check if video frames are being loaded
        if not tru:
            print('Codec issue: cannot load frames.')
            break
            
        frames[kk,:,:] = ret[:,:,0]

#         cv2.imshow('raw',ret)
#         cv2.waitKey(250)
#         cv2.destroyAllWindows()
            
    cap.release()
    return frames


def subtractframes(frames, buffer):
    fdiff = np.max(np.abs(np.diff(frames.astype(np.int16), n=1, axis = 0)), axis=0)
    bigdiff = (fdiff < -10) | (fdiff > 10)
    bigdiff = bigdiff[:,:,np.newaxis] # to work with more than 2 frames making work for imshow
    #bigdiff = np.swapaxes(np.swapaxes(bigdiff,0,1),1,2) # make 3rd axis singular so works for imshow
    
    # open the image
    kernel = cv2.getStructuringElement( cv2.MORPH_RECT, (3,3))
    opening = cv2.morphologyEx(bigdiff.astype(np.uint8), cv2.MORPH_OPEN, kernel)
    # do not include point close to wall
    h, w, _ = bigdiff.shape
    ndiff = opening[buffer:h-buffer, :].sum();
    #temp = bigdiff[buffer:h-buffer, buffer:w-buffer].sum()
    #print(temp, ndiff)
    #cv2.imshow('not opened',bigdiff.astype(np.uint8)*255)
    im2show = opening.copy()*255; 
    cv2.rectangle(im2show, (0, buffer), (w, h-buffer), (255,0,0), 1)
    cv2.imshow('raw', im2show)
    cv2.waitKey(1000)
    cv2.destroyAllWindows()
    
    return ndiff


def deleteantvids(vname):
    temp = vname.split('/')
    vbase = temp[-1].split('.')[0][0:-7]
    dbase = temp[-1].split('.')[0].split('_')[0]
    tbase = temp[-1].split('.')[0].split('_')[1]
    c_num = temp[-1].split('-')[0][-2:]
    
    # delete videos
    # os.remove(vname) # delete permanently
    os.system('gvfs-trash \'' + vname + '\'')  # move to trash

    # webcam pic
    vtime1 = (datetime.datetime.strptime(tbase,'%H%M%S') - datetime.timedelta(seconds=2)).strftime('%H%M%S')
    vtime2 = (datetime.datetime.strptime(tbase,'%H%M%S') - datetime.timedelta(seconds=3)).strftime('%H%M%S')
    vtime3 = (datetime.datetime.strptime(tbase,'%H%M%S') - datetime.timedelta(seconds=4)).strftime('%H%M%S')
    vname1 = dbase + '_' + vtime1 + '_Cam' + c_num + '.jpg'
    vname2 = dbase + '_' + vtime2 + '_Cam' + c_num + '.jpg'
    vname3 = dbase + '_' + vtime3 + '_Cam' + c_num + '.jpg'
    if os.path.exists(('/').join(temp[:-1]) + '/' + vname1):
        #os.remove(('/').join(temp[:-1]) + '/' + vname1) # delete permanently
        os.system('gvfs-trash \'' + ('/').join(temp[:-1]) + '/' + vname1 + '\'')
    if os.path.exists(('/').join(temp[:-1]) + '/' + vname2):
        #os.remove(('/').join(temp[:-1]) + '/' + vname2) # delete permanently
        os.system('gvfs-trash \'' + ('/').join(temp[:-1]) + '/' + vname2 + '\'')
    if os.path.exists(('/').join(temp[:-1]) + '/' + vname3):
        #os.remove(('/').join(temp[:-1]) + '/' + vname2) # delete permanently
        os.system('gvfs-trash \'' + ('/').join(temp[:-1]) + '/' + vname3 + '\'')

#     print('---**Videos deleted**')
    return;


def movevids(vname, sub_orders, cams, subs, recording_days):
    temp = vname.split('/')
    dbase = temp[-1].split('.')[0].split('_')[0]
    tbase = temp[-1].split('.')[0].split('_')[1]
    day = dbase[-2:]
    c_num = temp[-1].split('-')[0][-2:]
    #if vname.split('.')[-1] == 'avi':
    #    c_num = temp[-1].split('-')[0][-2:]
    #elif vname.split('.')[-1] == 'mp4':
    #    c_num = temp[-1].split('.')[0][-2:]
    #else:
    #        print('do not recognize video file type')
    
    # which colony was it
    colony = [kk for kk, c in enumerate(recording_days) if int(day) in c][0]
    
    # which substrate is it
    sub_id = sub_orders[colony][cams.index(int(c_num))]-1
    sub = subs[sub_id]
    if type(sub)==int:
        sub = str(sub) + 'mm'
    
    # what is recording session destination folder based on day of recording
    session_days = [c for c in recording_days if int(day) in c]
    temp2 = '-'.join([str(c) for c in session_days[0]])
    dfolder = ('/media/gravishlab/SeagateExpansionDrive/AntTrack/Tunnel_' + 
                dbase[:-2] + temp2)
    
    # what is specific susbtrate subfolder and new name of video
    new_vname = dfolder + '/' + sub + '/' + temp[-1]
    #print(new_vname)
    os.rename(vname, new_vname)

    # webcam pic
    vtime1 = (datetime.datetime.strptime(tbase,'%H%M%S') - datetime.timedelta(seconds=2)).strftime('%H%M%S')
    vtime2 = (datetime.datetime.strptime(tbase,'%H%M%S') - datetime.timedelta(seconds=3)).strftime('%H%M%S')
    vtime3 = (datetime.datetime.strptime(tbase,'%H%M%S') - datetime.timedelta(seconds=4)).strftime('%H%M%S')
    vname1 = dbase + '_' + vtime1 + '_Cam' + c_num + '.jpg'
    vname2 = dbase + '_' + vtime2 + '_Cam' + c_num + '.jpg'
    vname3 = dbase + '_' + vtime3 + '_Cam' + c_num + '.jpg'
    if os.path.exists(('/').join(temp[:-1]) + '/' + vname1):
#         print(dfolder + '/' + vname1)
        os.rename(('/').join(temp[:-1]) + '/' + vname1, dfolder + '/' + str(sub) + '/' + vname1)
    if os.path.exists(('/').join(temp[:-1]) + '/' + vname2):
        os.rename(('/').join(temp[:-1]) + '/' + vname2, dfolder + '/' + str(sub) + '/' + vname2)
    if os.path.exists(('/').join(temp[:-1]) + '/' + vname3):
        os.rename(('/').join(temp[:-1]) + '/' + vname3, dfolder + '/' + str(sub) + '/' + vname3)

    return new_vname, sub;


def deleteormove(vname, sep, buffer, s_order, cams, subs, recording_days):
    t = time.time()
    new_vname = [];
    
    frames = loadendframes(vname, sep)
    ndiff = subtractframes(frames, buffer)
    if ndiff<10:
        deleteantvids(vname)
        print(vname, ' -- DELETED -- %.2f s -- %i pix diff' % (time.time()-t, ndiff))
    else:
        (new_vname, sub) = movevids(vname, s_order, cams, subs, recording_days)
        print(vname, ' -- MOVED to ' + str(sub) + ' -- %.2f s' % (time.time()-t))
        
    return new_vname;


def trackvid(filename, min_osize, thresh_val):
    # contours tracking etc.
    video = Tracker(filename, min_object_size= min_osize)
    try:
        if video.file_exists == False:

            video.threshold_val = thresh_val
            video.load_video()
            video.compute_background()          # form background image
            video.remove_background()           # remove background
            video.threshold()                   # threshold to segment features
            video.find_distance()               # takes, dist tranform, finds peaks, associates to ants, finds head/gaster
            video.morpho_closing()
            video.find_objects()
            video.draw_contours()
            video.save_JSON()
            video.associate_contours(max_covariance=10,
                             max_velocity=100,
                             n_covariances_to_reject=20, 
                             max_tracked_objects=100,
                             kalman_state_cov=1,
                             kalman_init_cov=0.2,
                             kalman_measurement_cov=1)
            video.save_association_JSON()

            print('---Contours and tracks saved')
        else:
            print('---Tracked files already exist')
    except:
        print('---error! ') #, filename)
        
        
def compressvid(filename):
    ## define new name for compressed video
    
    # if don't want "-000" --> messed up tracker
    #temp = filename.split('/')
    #file = temp[-1]
    #new_file = file.split('-')[0]
    #dname = '/'.join(temp[:-1])
    #outname = dname + '/' + new_file + '.mp4' 
    
    # if want to keep "-000"
    outname = filename.split('.')[0] + '.mp4'
    
    
    try:
    
        # compress video using CRF 14 and very slow compression speed (becomes 1/100 of original size)
        commandline = 'ffmpeg -i \'%s\' -vcodec libx264 -preset veryslow -crf 14 \'%s\';' % (filename, outname);
        #commandline = 'ffmpeg -i \'%s\' -vcodec libx264 -preset slow -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -pix_fmt yuv420p \'%s\';'% (filename, outname);
        os. system(commandline)
        print('---Video file compressed: %s'%outname)

        # move old file to trash
        os.system('gvfs-trash \'' + filename + '\'')  # move to trash
        
    except:
        print('---Couldn\'t compress video')
    
#%% Imports

import math
import numpy as np
import os
import pandas as pd
import os
import random
from datetime import datetime
import traceback 
import matplotlib.pyplot as plt

##### Dataframe joining and reach filtering


### Set parameters
pthresh = 0.6 
diff_thresh = 10
euc_travel_thresh = 11
num_frames_thresh = 5
digit_count_thresh = 3 

y_buffer1 = 25
#buffer for y coord of GA
x_buffer1 = 30
#x_buffer1 for x coord of GA. Added to both sides 

y_buffer2 = 20
x_buffer2 = 0





dlc_path = 'C:\\DLCModels\\Model_2\\Analysis\\Python\\Analysis_Outputs\\Redoing\\DLC'
#path containing date folders that each contain DLC h5 output files
yolo_path = 'C:\\DLCModels\\Model_2\\Analysis\\Python\\Analysis_Outputs\\Redoing\\YOLO'
#path to folder containing date folders with YOLO output pkl files

dlc_dates = sorted(os.listdir(dlc_path))
yolo_dates = sorted(os.listdir(yolo_path))
#makes sorted list of the date folders


main = 'C:\\DLCModels\\Model_2\\Analysis\\Python\\Analysis_Outputs\\Redoing'
#path where the errors texfile will be made
timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_')
errors_file_path = os.path.join(main, f'{timestamp}errors.txt')
#this file path will be used to make a textfile with a list of all encounterd
    #errors if there are any






def __DLC_H5toDataFrame__(file_path):
    # changes column titles and makes rows start at index 0
    df = pd.read_hdf(file_path)
    df.columns = df.columns.get_level_values(1) + '_' + df.columns.get_level_values(2)
    # gets rid of scorer, gets rid of multiindex
    df = df.astype('float')
    # converts all columns to float type
    return df

    

for i, j in zip(dlc_dates, yolo_dates):
    #loops through date folders for dlc and yolo
        
    #makes sure that the yolo folder and dlc folder are from same date
    if i != j:
        raise ValueError(f'folder name not equal \n DLC: {i} \n YOLO: {j}')
        
        
        
        

dates = {}
#dictionary that will contain filtered data from each date

for l, j in zip(dlc_dates, yolo_dates):
    #loops through one date at a time, drawing from both yolo and 
        #dlc date folders 
    
    try:
        
        #path for reach dataframes to be saved into
        reaches_path = 'C:\\DLCModels\\Model_2\\Analysis\\Python\\Analysis_Outputs\\Redoing\\Reaches'
        reach_date_path = os.path.join(reaches_path, f'{l}')
        os.mkdir(reach_date_path)
    
        #paths for the specific yolo and dlc date folders
        yolo_date_path = os.path.join(yolo_path, j)
        dlc_date_path = os.path.join(dlc_path, l)
        
        
        #makes list of all the files in the date folders
        yolo_files = os.listdir(yolo_date_path)
        dlc_files = os.listdir(dlc_date_path)
        yolo_files = [x for x in yolo_files if x.endswith('.pkl') and x.startswith('SESSION') == False ]
        #filters out non pkl files and SESSION files that may be in folders
        dlc_files = [x for x in dlc_files if x.endswith('.h5')]
        #filters out non h5 files
        
        
        #checks to make sure there are the same amount of dlc and yolo files
            #for the date. If not, adds this error to the textfile and 
            #moves on to next date
        if len(yolo_files) != len(dlc_files):
            error = (f'{l} number of yolo files different than number of dlc files')
            with open(errors_file_path, "a") as file:
              file.write(error + "\n" + '############' + '\n')
              #adds this error to the textfile, creates a new textfile if one doesn't already exist
            continue
        
        
        
        
        yolo_preds = []
        #list containing yolo predictions for the date in question
        os.chdir(yolo_date_path)
        cwd = os.getcwd()
        
        #loops through yolo files and gets rid of low confidence predictions
        for file in yolo_files:
            
            dataframe = pd.read_pickle(file)
            #reads yolo output file and creates dataframe
            
            
            ##replaces low confidence yolo_preds with the closest subsequent box
                #that has a high confidence
            box_conf_thresh = 0.6  
            left = dataframe.iloc[:,0:6]
            #left frame
            Lconf_mask = left.loc[:,'LGAconf'] > box_conf_thresh
            #mask where values are above thresh
            left = left.where(Lconf_mask)
            #fills below threshold values with nan
            left = left.bfill()
            #fills nan values with closest subsequent non-nan value
            
            right = dataframe.iloc[:,6:12]
            Rconf_mask = right.loc[:,'RGAconf'] > box_conf_thresh
            right = right.where(Rconf_mask)
            right = right.bfill()
            
            dataframe = pd.concat([left,right], axis = 1)
            #combines left and right
            
            #creates metadata columns
            string_list = file.split('_')
            dataframe['mouse'] = string_list[0]
            dataframe['test'] = string_list[1]
            dataframe['date'] = string_list[2]
            dataframe['camera'] = string_list[3]
            dataframe['treatment'] = string_list[4]
            
            if '.mp4' in file:
                dataframe['yolo_file_name'] = file.split('.mp4')[0]
                
            else: 
                dataframe['yolo_file_name'] = file
            
            yolo_preds.append(dataframe)
            #appends yolo dataframe to yolo prediction list
            
            
                
    
        dlc_preds = []
        #list containing dlc predictions for the date in question
        os.chdir(dlc_date_path)
        cwd = os.getcwd()
        
        #same idea as the yolo df block above but for dlc output for the date
        for file in dlc_files:
            df = __DLC_H5toDataFrame__(file)
            string_list = file.split('_')
            
            #metadata columns
            df['mouse'] = string_list[0]
            df['test'] = string_list[1]
            df['date'] = string_list[2]
            df['camera'] = string_list[3]
            df['treatment'] = string_list[4]
            dlc_preds.append(df)
        #makes a list of DLC dataframes from a directory of h5 files and adds columns with info based on their file names
        
        
        
        def merge(boxes, labels):   
            dataframes = []
            
            for l, b in zip(labels, boxes):
                #goes through 2 lists, one containing dlc labels for a date and one containing boxes
                if (len(l) == len(b)) and (l.loc[0,'mouse'] == b.loc[0,'mouse']):
                    #checks that the files are from the same video by comparing number of frames and mouseID
                    boxes = b
                    
                    dataframe = (pd.concat([l.drop(columns = ['mouse', 'test', 'date', 'camera', 'treatment']), b], axis = 1))
                    #concatates the two dataframes and removes duplicate identification columns 
                    dataframes.append(dataframe)
                    
            
            return dataframes 
        #returns a list of combined DLC and boxes dataframes 
                
            

        merged = merge(yolo_preds , dlc_preds)
        #list of merged dataframes 



        ################ Filtering
        reaches_list = []

        for k in merged: 
            
            
            ### Getting digit labels that are in the primary (bigger) GA
                #the goal of this box is to locate all of the digits that are in the 
                #general vicinity of the grabbing area. These points will be 
                #filtered further
            df = k.copy()
    
    
            ycolumns = [('leftdigit1_y', 'leftdigit1_likelihood'),('leftdigit2_y', 'leftdigit2_likelihood'), 
                        ('leftdigit3_y', 'leftdigit3_likelihood'),('leftdigit4_y', 'leftdigit4_likelihood'), 
                        ('rightdigit1_y', 'rightdigit1_likelihood'), ('rightdigit2_y', 'rightdigit2_likelihood'),
                        ('rightdigit3_y', 'rightdigit3_likelihood'), ('rightdigit4_y', 'rightdigit4_likelihood')]
            #columns for y coord masking
    
            xcolumns = [('leftdigit1_x', 'leftdigit1_likelihood'), ('leftdigit2_x', 'leftdigit2_likelihood'), 
                        ('leftdigit3_x', 'leftdigit3_likelihood'), ('leftdigit4_x', 'leftdigit4_likelihood'), 
                        ('rightdigit1_x', 'rightdigit1_likelihood'), ('rightdigit2_x', 'rightdigit2_likelihood'),
                        ('rightdigit3_x', 'rightdigit3_likelihood'), ('rightdigit4_x', 'rightdigit4_likelihood')]
            #columns for x coord masking
    
    
                
    
    
    
            leftGAxmask = pd.concat([ 
                (df['LGAx1'] - x_buffer1 < df[x_col]) & (df[x_col] < df['LGAx2'] + x_buffer1) & (df[l_col] > pthresh)
                for x_col, l_col in xcolumns
                ], axis = 1)
            '''left grabbing area mask for x coords. makes a dataframe with where each column is one 
            of the conditions in the xcolumns list. A row of this dataframe contains
            all of the true or false values for whether each digit is in x boundaries of the GA
             and whether it is above the conf p value'''
    
            leftGAymask = pd.concat([ 
                (df[y_col]>df['LGAy2'] - y_buffer1) & (df[l_col] > pthresh)
                for y_col, l_col in ycolumns
                ], axis = 1)
            #same but for y coord
    
    
            leftGAmask = (leftGAxmask & leftGAymask).any(axis = 1)
            '''complete left GA mask. Is true if there is any digit between both the x and y
            bounds of the left GA''' 
    
    
            rightGAxmask = pd.concat([ 
                (df['RGAx1'] - x_buffer1 < df[x_col]) & (df[x_col] < df['RGAx2'] + x_buffer1) & (df[l_col] > pthresh)
                for x_col, l_col in xcolumns
                ], axis = 1)
            #same but for right GAx
    
            rightGAymask = pd.concat([ 
                (df[y_col]>df['RGAy2'] - y_buffer1) & (df[l_col] > pthresh)
                for y_col, l_col in ycolumns
                ], axis = 1)
            #same but for right GAy
    
            rightGAmask = (rightGAxmask & rightGAymask).any(axis = 1)
    
    
            reachmask = leftGAmask | rightGAmask
            #is true if there is any digit in left or right GA 
            reaches = df[reachmask].copy()
    
    
    
    
            ### Filtering by number of frames between 'reaches'
    
            reaches.loc[:,'diff'] = reaches.index.diff()
            #creates column with number of frames that have elapsed between each "reach"
            diff_thresh_mask = reaches.loc[:,'diff'] >= diff_thresh
            diff_thresh_mask = diff_thresh_mask.rename('diff_thresh')
            #filters based on a minimum diff threshold. at least x frames must have elapsed 
                #for the reach to pass the filter. If labelling drops out in the middle of
                #the reach for a few frames it will still be one reach 
            reaches = pd.concat([reaches, diff_thresh_mask], axis = 1)
            #adds diffthreshmask to the end of reaches 
    
    
    
            ### Filtering by number of frames in the reach
    
            ##counts the number of frames in a "reach"
            reaches.loc[:,'num_frames'] = None
            #makes a number of frames column
            num_frames_idx = reaches.columns.get_loc('num_frames')
            #gets index of the new column
            threshyes = reaches[diff_thresh_mask]
            #dataframe where the diff threshold is satisfied. Each row corresponds 
                #to the beginning of a reach
            for i in range(len(threshyes.index)):
                #loops through threshyes index
                if i == len(threshyes.index) -2:
                    break
                #stops out of range error
                
                frame1 = threshyes.index[i]
                frame2 = threshyes.index[i +1]
                #gets frame number values of 2 adjacent reaches
                idx1 = int(reaches.index.get_loc(frame1))
                idx2 = int(reaches.index.get_loc(frame2)) -1
                #gets index of those frame numbers in reaches df
                
    
                num_frames = int(reaches.index[idx2]) + 1 - int(reaches.index[idx1])
                reaches.iloc[idx1,num_frames_idx] = num_frames
                #calculates the number of frames in the reach and enters the info into 
                    #numframes column 
            '''labels the reaches with their length in frames'''
    
    
            num_frames_mask = (reaches.loc[:,'num_frames'] > num_frames_thresh)
    
    
    
            ### Filtering by distance travelled in the reach
    
            ##euclidian distance from 2 points
            def euc_dist(x1, y1, x2, y2):
                distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                return distance
    
    
            ##gets coordinates of all digits above pthresh for a given frame
            def getcoords(df, frame_number):
                LD1 = []   
                LD2 = []
                LD3 = []
                LD4 = []
                RD1 = []
                RD2 = []
                RD3 = []
                RD4 = []
                #each of these lists will contain x and y coordinates for a digit
                    
                series = df.iloc[frame_number, :]
                #takes a row of the df corresponding to the desired frame
                if series['leftdigit1_likelihood'] > pthresh:
                    LD1.append(series['leftdigit1_x'])
                    LD1.append(series['leftdigit1_y'])
                if series['leftdigit2_likelihood'] > pthresh:
                    LD2.append(series['leftdigit2_x'])
                    LD2.append(series['leftdigit2_y'])
                if series['leftdigit3_likelihood'] > pthresh:
                    LD3.append(series['leftdigit3_x'])
                    LD3.append(series['leftdigit3_y'])
                if series['leftdigit4_likelihood'] > pthresh:
                    LD4.append(series['leftdigit4_x'])
                    LD4.append(series['leftdigit4_y'])
    
                if series['rightdigit1_likelihood'] > pthresh:
                    RD1.append(series['rightdigit1_x'])
                    RD1.append(series['rightdigit1_y'])
                if series['rightdigit2_likelihood'] > pthresh:
                    RD2.append(series['rightdigit2_x'])
                    RD2.append(series['rightdigit2_y'])
                if series['rightdigit3_likelihood'] > pthresh:
                    RD3.append(series['rightdigit3_x'])
                    RD3.append(series['rightdigit3_y'])
                if series['rightdigit4_likelihood'] > pthresh:
                    RD4.append(series['rightdigit4_x'])
                    RD4.append(series['rightdigit4_y'])
                #these blocks check for the p cutoff and output the xy coords for labels that are above p
                    
                coords = [LD1, LD2, LD3, LD4, RD1, RD2, RD3, RD4]
                #makes list of coordiantes
                return coords 
    
    
    
    
    
    
            reaches.loc[:,'euc_travel'] = None
            #creates column for euclidian distance between minx,miny and maxx, maxy for 
                #a given frame
            #y_travel_idx = reaches.columns.get_loc('y_travel')
            euc_travel_idx = reaches.columns.get_loc('euc_travel')
            #gets index of euc travel
    
            for i in range(len(threshyes.index)):
                #loops through threshyes index
                if i == len(threshyes.index) -2:
                    break
                #stops out of range error
                
                frame1 = threshyes.index[i]
                frame2 = threshyes.index[i +1]
                #gets frame number values of 2 adjacent reaches
                idx1 = int(reaches.index.get_loc(frame1))
                idx2 = int(reaches.index.get_loc(frame2)) -1
                #gets index of those frame numbers in reaches df
                
                y_coords =[]
                x_coords =[]
                #lists with x and y_cords of reach coords
                ## loops through every frame in the reach
                    #fills the above  lists with all x_cords and y_cords 
                for j in range(idx1, idx2 +1, 1):
                
                    coords = getcoords(reaches, j)
                    coords = [n for n in coords if len(n) >0]
                    coords_y = [n[1] for n in coords]
                    coords_x = [n[0] for n in coords]
                    for k in coords_y:
                        y_coords.append(k)
                    for k in coords_x:
                        x_coords.append(k)
                    
                    
                    
                    
                y_min = min(y_coords)
                y_max = max(y_coords)
                x_min = min(x_coords)
                x_max = max(x_coords)
                #calculates max and mins 
                
                #y_travel = y_max - y_min
                #reaches.iloc[idx1, y_travel_idx] = y_travel
                
                euc_travel = euc_dist(x_min, y_min, x_max, y_max)
                reaches.iloc[idx1, euc_travel_idx] = euc_travel
                #calculates the euclidian distacne of the reach and enters the info into 
                    #euc_travel
            euc_travel_mask = reaches.loc[:, 'euc_travel'] > euc_travel_thresh
            #creates mask for min euc travel
    
    
    
            ### Filtering by maximum number of digits visible in the reach 
    
    
            ##counts number of labelled digits for each paw for a given frame 
            def countdigits(df, frame_number):
                
                leftpaw = []
                rightpaw = []
                
                #each of these lists will contain a list of which digits are labelled
                    #for a given paw
                    
                series = df.iloc[frame_number, :]
                #takes a row of the df corresponding to the desired frame
                if series['leftdigit1_likelihood'] > pthresh:
                    leftpaw.append('1')
                if series['leftdigit2_likelihood'] > pthresh:
                    leftpaw.append('2')
                if series['leftdigit3_likelihood'] > pthresh:
                    leftpaw.append('3')
                if series['leftdigit4_likelihood'] > pthresh:
                    leftpaw.append('4')
    
                if series['rightdigit1_likelihood'] > pthresh:
                    rightpaw.append('1')
                if series['rightdigit2_likelihood'] > pthresh:
                    rightpaw.append('2')
                if series['rightdigit3_likelihood'] > pthresh:
                    rightpaw.append('3')
                if series['rightdigit4_likelihood'] > pthresh:
                    rightpaw.append('4')
                #these blocks check each digit for the p cutoff and updates the leftpaw and 
                    #rightpaw lists if they pass
                    
                left_count = len(leftpaw)
                right_count = len(rightpaw)
                #number of labelled digits for each paw 
                return left_count, right_count
    
    
            reaches.loc[:,'max_digit_count'] = None
            #creates column for max_digit_count for a given frame
            max_digit_count_idx = reaches.columns.get_loc('max_digit_count')
            #gets index of max dig count travel
    
    
            for i in range(len(threshyes.index)):
                #loops through threshyes index
                if i == len(threshyes.index) -2:
                    break
                #stops out of range error
                
                frame1 = threshyes.index[i]
                frame2 = threshyes.index[i +1]
                #gets frame number values of 2 adjacent reaches
                idx1 = int(reaches.index.get_loc(frame1))
                idx2 = int(reaches.index.get_loc(frame2)) -1
                #gets index of those frame numbers in reaches df
                
                leftcounts = []
                rightcounts = []
                #these lists will be filled with the digit counts for each frame in
                    #the reach
                for j in range(idx1, idx2 +1, 1):
                
                    leftcount, rightcount  = countdigits(reaches, j)
                    #counts the digits in the frame
                    leftcounts.append(leftcount)
                    rightcounts.append(rightcount)
                    #adds the counts to the lists above
                    
                max_left =  max(leftcounts)
                #maximum number of left digits simultaneously visible
                max_right = max(rightcounts)
                #maximum number of right digits simultaneously visible
                max_both = max(max_left, max_right)
                #takes max of right and left 
                
                reaches.iloc[idx1, max_digit_count_idx] = max_both
                #labels the reach 
                
    
            digit_count_mask = reaches.loc[:,'max_digit_count'] >= digit_count_thresh
            #mask where only reaches that meet the minimum number of visible digits 
                #are included
    
    
    
    
    
            ###Filtering by secondary (smaller) grabbing area 
                #the goal of this box is to filter out non-reach points that are in the 
                #primary grabbing area. Should reduce false positives
            reaches.loc[:,'GA_t/f'] = None
            #creates column for whether or not there is a digit in the grabbing area at
                #some point in the reach
            GA_tf_idx = reaches.columns.get_loc('GA_t/f')
            #gets index of GA-tf column
    
            #gets column index numbers for the different GA coordinate columns
            LGAx1_idx = reaches.columns.get_loc('LGAx1')
            LGAx2_idx = reaches.columns.get_loc('LGAx2')
            LGAy2_idx = reaches.columns.get_loc('LGAy2')
            RGAx1_idx = reaches.columns.get_loc('RGAx1')
            RGAx2_idx = reaches.columns.get_loc('RGAx2')
            RGAy2_idx = reaches.columns.get_loc('RGAy2')
    
    
    
    
            for i in range(len(threshyes.index)):
                #loops through threshyes index (reaches)
                if i == len(threshyes.index) -2:
                    break
                #stops out of range error
                
                frame1 = threshyes.index[i]
                frame2 = threshyes.index[i +1]
                #gets frame number values of 2 adjacent reaches
                idx1 = int(reaches.index.get_loc(frame1))
                idx2 = int(reaches.index.get_loc(frame2)) -1
                #gets index of those frame numbers in reaches df
                
                reachcoords = []
                #list with x and y_cords of plotted points in the reach
               
                ## loops through every frame in the reach
                    #fills the above list with all x_cords and y_cords 
                for j in range(idx1, idx2 +1, 1):
                    #loops through the frames of the reach reach
                
                    coords = getcoords(reaches, j)
                    #gets coordinates for p>pthresh digits in the frame
                    coords = [n for n in coords if len(n) >0]
                    #only uses lists that aren't empty
                    for k in coords:
                        reachcoords.append(k)
                        #adds the digit coordinates from this frame to the coordinate
                        #list for the reach
                    
                LGA_tf = None
                RGA_tf = None 
                #true/false tokens for whether or not a "reach" passses into the left
                    #or right GA
                
                
                for j in reachcoords:
                    #loops through all digit coordinates of reach
                    
                    
                    
                    if (
                    reaches.iloc[idx1, LGAx1_idx] - x_buffer2 < j[0]
                    and j[0] < reaches.iloc[idx1, LGAx2_idx] + x_buffer2
                    and j[1] > reaches.iloc[idx1, LGAy2_idx] - y_buffer2
                    ):
                        LGA_tf = True
                        
                    #checks if reach passed through right secondary GA
                    if (
                    reaches.iloc[idx1, RGAx1_idx] - x_buffer2 < j[0] 
                    and j[0] < reaches.iloc[idx1, RGAx2_idx] + x_buffer2
                    and j[1] > reaches.iloc[idx1, RGAy2_idx] - y_buffer2
                    ):
                        RGA_tf = True
                        
                if LGA_tf or RGA_tf:
                    reaches.iloc[idx1, GA_tf_idx] = True
                    #if either GA has been entered the reach will be marked true for 
                        #GA_tf
                else:
                    reaches.iloc[idx1, GA_tf_idx] = False
                
                    
            GA_mask = reaches.loc[:,'GA_t/f'] == True
            #masks based on whether the reach has passed into one of the secondary GAs 
             
    
            
            reaches = reaches [diff_thresh_mask & num_frames_mask & euc_travel_mask & digit_count_mask & GA_mask]
            #this is the df with all of the masks combined
            
                
            
            reaches_list.append(reaches)
            
            date_idx = reaches.columns.get_loc('date')
            mouse_id_idx = reaches.columns.get_loc('mouse')
            yolo_name_idx = reaches.columns.get_loc('yolo_file_name')
            
            print(f'DONE date: {df.iloc[0,date_idx]} mouse: {df.iloc[0,mouse_id_idx]}')
            
            
            #reach_file_name = f'{df.iloc[0,date_idx]}_{df.iloc[0,mouse_id_idx]}.csv' 
            reach_file_name = f'{df.iloc[0, yolo_name_idx]}.csv' 
            #new file name will have same name as corresponding yolo file name
            reach_file_path = os.path.join(reach_date_path, reach_file_name)
            reaches.to_csv(reach_file_path)
            #saves reaches df in reaches date folder
                
            
    
    
    

    #if an error is thrown for a date the error is added to the textfile and
        #the program moves to the next date 
    except Exception:
        error_traceback = traceback.format_exc()
        error = f'An error occurred for {l} \n Error {error_traceback}'
        with open(errors_file_path, "a") as file:
          file.write(error + "\n" + '############' + '\n')
          #adds this error to the textfile, creates a new textfile if one doesn't already exist
        print(error)
    
    
    


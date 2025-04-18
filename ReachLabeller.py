#%%
import os
import pandas as pd
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image 
import cv2
import subprocess
import sys 
import traceback
import time









##### Functions



#replaces missing data (nan) in desired slice with 'none'
def fill_w_none(dataframe, desiredslice):
    x, y = desiredslice.split(':')
    x = int(x)
    y = int(y)
    for index,row in dataframe.loc[x:y].iterrows():
    #iterates over desired slice of the df
        if pd.isna(dataframe.loc[index, 'reach_type']):
        #here the specific column being iterated over is 'reach_type'
            dataframe.at[index, 'reach_type'] = 'none'



#counts number of total reaches that have been labelled in a given dataframe
def count_reaches(dataframe):
    prev = 'none'
    next = 'none'
    reaches = 0
    for index, row in dataframe.loc[:].iterrows():
        next = row['reach_type']
        if (next != prev) and (next != 'none') and (pd.isna(row['reach_type']) == False):
            reaches += 1
            prev = row['reach_type']
        else:
            prev = row['reach_type']
    return reaches




#takes specific frame of an mp4 and its dataframe and plots the frame
def frameplot(video_path, frame_number, df, show):
    
    
    
    video_folder = os.path.dirname(video_path)
    #containing folder of video
    video = cv2.VideoCapture(video_path)
    #captures Mp4
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    #sets desired frame
    success, frame = video.read()
    #reads the set video and outputs boolean of success/fail and the extracted frame
    
    if success:
        output_path = os.path.join(video_folder ,f'frame{frame_number}.jpg')
        cv2.imwrite(output_path, frame)
        #print(output_path)
    else:
        print('unable to extract frame')
    #if extraction was successful the frame is saved 
        
    
    image = Image.open(output_path)
    #opens saved image
    image_array = np.array(image)
    #converts t0 np array
    fig, ax = plt.subplots()
    #creates a figure and a subplot (ax)
    
    ax.imshow(image_array)

    
    

    ax.set_title(frame_number)
    #plots the two GAs 
    #ax.add_patch(tbox)
    #print(series)
    
    
    if show == True:
        plt.show()
        #plots the image
        
    try:
        os.remove(output_path)
        #deletes the jpg after it has been plotted
    except Exception:
        error_traceback = traceback.format_exc()
        current_date = datetime.now()
        error = f'{current_date}\nAn error occurred for Folder: {i} \n Error: {error_traceback}'
        with open(errors_file_path, "a") as file:
            file.write(error + "\n" + '############' + '\n')
            #adds this error to the textfile, creates a new textfile if one doesn't already exist
        print(error)
    
        
        
#uses frameplot function to plot all the frames in the reach
def reach(reach_df, frame_number, video_path, buff_length):
    
    #pre and post buffers are frames added onto the beginning and end
        #of the frame
    if buff_length in ['long', 'beginning', 'end']:
        pre_buff = 50
        post_buff = 50
    elif buff_length == 'short':
        pre_buff = 10
        post_buff = 10
    
    
    
    start_frame = frame_number
    #start frame
    reach_number = reach_df.index.get_loc(frame_number)
    #nth reach in the list of reaches
    num_frames = reach_df.loc[start_frame, 'num_frames']
    #number of frames in the reach
    end_frame = start_frame + num_frames
    #end frame based on the start frame and the num_frames column of the df
    
   
    #finds the start and end frames of the previous reach
    if reach_number != 0:
        prev_reach = reach_df.index[reach_number - 1]
        prev_num_frames = reach_df.loc[prev_reach, 'num_frames']
        prev_reach_end = prev_reach + prev_num_frames
    else:
        prev_reach_end = 0
    
    #finds the start frame of the next reach 
    if reach_number < len(reach_df) - 1:
        next_reach = reach_df.index[reach_number + 1]
    else: 
        next_reach = reach_df.index[reach_number]
    
    
    #we check to see if the desired pre and post buff values results in
        #plotting frames that overlap into
        #another reach. If not, we use long or short as the value. If there 
        #is overlap the pre and post buffs are set to be as large as 
        #possible without overlap 
    if start_frame - pre_buff > prev_reach_end:
        pre_buff = pre_buff
    else:
        pre_buff = start_frame - prev_reach_end 
    if end_frame + post_buff < next_reach:
        post_buff = post_buff
    else:
        post_buff = next_reach - end_frame
    
    
    #plots all the desire frames including the buffers
    num_frames = reach_df.loc[frame_number, 'num_frames']
    
    if buff_length in ['long', 'short']:
        for i in range(start_frame - pre_buff, end_frame + post_buff , 1):
            frameplot(video_path, i, reach_df, show = True)
    
    elif buff_length == 'beginning':
        end = end_frame + post_buff
        start = start_frame - pre_buff
        start = int(start)
        length = (end - start)/2 
        end = start + length
        end = int(end)
        
        for i in range(start, end, 1):
            frameplot(video_path, i, reach_df, show = True)
    
    elif buff_length == 'end':
        end = end_frame + post_buff
        end = int(end)
        start = start_frame - pre_buff
        length = (end - start)/2 
        start = end - length
        start = int(start)
        
        
        for i in range(start, end, 1):
            frameplot(video_path, i, reach_df, show = True)
        
    
    
    

    

        
#plays a video clip of a specific reach. Takes a path to a video and 
    #its corresponding reach dataframe. Reach number is the nth reach starting
    #from 0. Playback speed: 1 is normal, 0.5 is double, 2 is half, etc.         
def play_reach(ffmpeg_bin, video_path, reach_df, reach_number, playback_speed):
    
    
    apps = os.listdir(ffmpeg_bin)
    #list of exe files in ffmpeg bin
    
    #creates path to ffmpeg exe
    ffmpeg = [x for x in apps if x == 'ffmpeg.exe']
    ffmpeg = ffmpeg[0]
    ffmpeg_path = os.path.join(ffmpeg_bin, ffmpeg)
    
    ##creates path to ffplay exe
    ffplay = [x for x in apps if x == 'ffplay.exe']
    ffplay = ffplay[0]
    ffplay_path = os.path.join(ffmpeg_bin, ffplay)
    
    
    output_folder = os.path.dirname(video_path)
    #clip will be saved here 
    output_path = os.path.join(output_folder, 'clip.mp4')
    #name of clip to be saved

    
    total_reaches = len(reach_df)
    start_frame = reach_df.index[reach_number]
    num_frames = reach_df.loc[start_frame, 'num_frames']
    #number of frames in the reach
    end_frame = start_frame + num_frames
    
    #these are frames that are added to the beginning or the end of the 
        #reach to make it easier to see. Initialized at 0.
    pre_buff = 0
    post_buff = 0
    
    
    #finds the start and end frames of the previous reach
    if reach_number != 0:
        prev_reach = reach_df.index[reach_number - 1]
        prev_num_frames = reach_df.loc[prev_reach, 'num_frames']
        prev_reach_end = prev_reach + prev_num_frames
    else:
        prev_reach_end = 0
        pre_buff = 50
    
    if reach_number < len(reach_df) - 1:
        next_reach = reach_df.index[reach_number + 1]
    #finds the start frame of the next reach 
    else: 
        next_reach = reach_df.index[reach_number]
    
    
    #ideal pre and post buff values are 50 so we check to see if 
        #using those values will result in a clip that overlaps into
        #another reach. If not, we use 50 as the value. If there is overlap 
        #the pre and post buffs are set to be as large as possible without 
        #overlap 
    if start_frame - 50 > prev_reach_end:
        pre_buff = 50
    else:
        pre_buff = start_frame - prev_reach_end 
    if end_frame + 50 < next_reach:
        post_buff = 50
    else:
        post_buff = next_reach - end_frame
        
    
    
    #Start and end times for the video clip in seconds. Videos are all 
        #100 frames/second so just divide the frame numbers by 100
    start_time = str(float((start_frame - pre_buff)/100))
    end_time = str(float((end_frame + post_buff)/100))



    #subprocess commands for ffmpeg to save the clip
    ffmpeg_cmd = [
        
        ffmpeg_path,
        #program that will be used in the subprocess
        "-i", video_path,  
        #input for ffmpeg
        "-ss", start_time,   
        #start time
        "-to", end_time,  
        #end time
        "-c", "copy", '-y', 
        #Will save the clip and will overwrite if necessary        
        output_path   
        #output path        
    ]
    
    #commands for ffplay to play the clip
    ffplay_cmd = [
        ffplay_path,
        #ffplay plays th clip
        '-fs',
        #fullscreen
        '-autoexit', 
        #exits after plaing
        '-vf', f'setpts={playback_speed}*PTS', 
        #varaible playing speed
        output_path
        #output path 
        
        ]

    #ffmpeg commands
    try:
        
        subprocess.run(ffmpeg_cmd, check=True)
        #saves the video clip using ffmpeg subprocess
        print(f'\n\n\n\n\nreach {reach_number +1} of {total_reaches} (frames {start_frame}-{end_frame})')
        subprocess.run(ffplay_cmd)
        #plays the saved clip and autoexits the window. 
        try:
            os.remove(output_path)
            #deletes the clip after it has been plotted
        except Exception:
            error_traceback = traceback.format_exc()
            current_date = datetime.now()
            error = f'{current_date}\nAn error occurred for Folder: {i} \n Error: {error_traceback}'
            with open(errors_file_path, "a") as file:
                file.write(error + "\n" + '############' + '\n')
                #adds this error to the textfile, creates a new textfile if one doesn't already exist
            print(error)
        
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        
        




#function for labelling the reaches in a reach df
    #plays a video of the reach for the user and takes user input to
    #label the reach . ffmpeg bin is the path to ffmpeg bin which contains
    #ffmpeg and ffplay exe files
    #min_valid can equal 'no_min' or an integer 
def label_reaches (ffmpeg_bin, video_path, reaches_path, output_folder, playback_speed, min_valid):
    
    
    
    #min_valid is the desired number of valid reach attempts to be labelled
        #before program moves to the next file
    try: 
        if type(min_valid) == str:
            min_valid = np.nan
        
        reach_df = pd.read_csv(reaches_path, index_col=0)
        #sets the reach dataframe
        
        #creates a success_level column if there isn't one there
            #this is where the labels will go 
        if 'success_level' not in reach_df.columns:
            
            #creates a success level column that can hold float and string 
                #dtypes. Default is nan
            reach_df['success_level'] = pd.Series(dtype='object')
            
            
            
       #these are labelling speed columns that can be used for estimating
           #time for future labelling 
        if 'labels_per_hr' not in reach_df.columns:
            reach_df['labels_per_hr'] = np.nan
        
        labels_per_hr_idx = reach_df.columns.get_loc('labels_per_hr')
            
        if 'avg_labels_per_hr' not in reach_df.columns:
            reach_df['avg_labels_per_hr'] = np.nan
            
        
            
        
        #This is used when the reach_df is a partially labelled dataframe
            #unlabelled entries are np.nan so this creates a dataframe 
            #with just nan in the labelled column and looks at its first member
            #to see where labelling should begin for this session
        unlabelled_mask = (reach_df['success_level']).isna()
        unlabelled = reach_df[unlabelled_mask]
        first_unlabelled = unlabelled.index[0]
        first_unlabelled_idx = reach_df.index.get_loc(first_unlabelled)
        
        #this prompt is displayed after the reach is played. The user inputs
            #one of the selections 
        prompt = (
            f'{reaches_path}'
            #shows which file is being labeled
            '\n'
            '\n'
            'Input success level \n'
            "1: didn't touch \n"
            '2: touched pellet, did not bring through slit \n'
            '3: brought into enclosure but not to mouth \n'
            '4: brought to mouth \n'
            'i: irregular attempt \n'
            '     -pellet was not in the well \n'
            '     -tweezers were touching pellet at beginning of reach \n'
            '     -more than 2 pellets in the well \n'
            '     -fewer than 2 pellets in the well \n'
            'x: other \n'
            '     -hard to determine \n' 

            '     -clip was not a reach \n'
            'r: replay clip \n'
            'f: generate the first frame of the clip \n'
            'c: generate all frames of a short version of the clip \n'
            'lc: long clip -- bc: beginning of clip -- ec: end of clip \n'
            'pr: go to previous reach \n'
            'nr: go to next reach \n'
            's: save \n'
            'sq: save and quit \n'
            )
            
       
        
        success_level_idx = reach_df.columns.get_loc('success_level')
        #index of the success level column
        i = first_unlabelled_idx
        #initializes i as the first unlabelled reach in the dataframe
        
        num_labelled = 0
        #number of labelled reaches for the file, will be updated
            #every reach
        
        start = time.time()
        #this is used to keep track of how long the current session has taken
            #for updating the labelling speed columns
        
        #counts how many valid reaches are in the success level column
            #when numvalid is at desired level we move to the next file
        valid_mask = reach_df['success_level'].isin(['1', '2', '3', '4'])
        num_valid = valid_mask.sum()
        
        
        
        #loops through each reach 
        while i < len(reach_df.index):
            
            try: 
                
            
                
                #gets the current label of the reach
                    #useful if the user wants to go back and see previous labels
                current_label = reach_df.iloc[i, success_level_idx]
                if current_label == np.nan:
                    label_status = 'unlabelled'
                else:
                    label_status = current_label
                
                
                reach_frame = reach_df.index[i]
                #this is the frame number of the beginning of the reach
                
                
                if i == first_unlabelled_idx:
                    level = ('')   
                if not level in ('f', 'c', 'lc', 'ec', 'bc'):
                    play_reach(ffmpeg_bin, video_path, reach_df, i, playback_speed)
                #plays the reach for the user
                print(f'current label: {label_status}\ncurrent num_valid: {num_valid}')
                #prints label status
                
                #takes user input based on prompt and cleans it up
                level = input(prompt)
                level = level.lower()
                level = level.strip()
                
                #checks to make sure the input is one of the options
                while (level not in ('1', '2', '3', '4', '5', 'r', 'i', 's', 'sq', 
                                     'x', 'f', 'c','lc', 'bc', 'ec', 'nr', 'pr'
                                     )):
                    level = input('proper input please \n').lower().strip()
                
                #play the whole reach with short buffer option
                if level == 'r':
                    continue
                elif level == 'c':
                    reach(reach_df, reach_frame, video_path, 'short')
                
                #plays the whole reach with long buffer option
                elif level == 'lc': 
                    reach(reach_df, reach_frame, video_path, 'long')
                    
                elif level == 'bc': 
                    reach(reach_df, reach_frame, video_path, 'beginning')
                    
                elif level == 'ec': 
                    reach(reach_df, reach_frame, video_path, 'end')
                    
                 #plots the starting frame
                elif level == 'f':
                    frameplot(video_path, reach_frame, reach_df, show = True)
                
                #saves the partially labelled dataframe to the output folder
                    #overwrites if one is already there
                elif level == 's':
                    base = os.path.basename(reaches_path)
                    #file name
                    base = base.replace('notdone_', '')
                    #gets rid of notdone prefix if current df is a 
                        #part labelled df
                    new_name = 'notdone_' + base
                    #new name
                    new_path = os.path.join(output_folder, new_name)
                    #new path
                    
                    #attempts to save the file and prompts user to close
                        #excel file if it is open so that it can be overwritten
                    try:
                        reach_df.to_csv(new_path)
                        print('PROGRESS HAS BEEN SAVED')
                    except PermissionError:
                        print('COULD NOT SAVE. CLOSE THE EXCEL FILE IF IT IS OPEN')
                
                #does the same as saving but also exits the console 
                elif level == 'sq':
                    
                    #these blocks calculate average labelling times and
                        #updates the columns
                    end = time.time()
                    elapsed_min = end - start
                    elapsed_hr = elapsed_min/3600
                    
                    if num_labelled > 0:
                        
                        labels_per_hr = num_labelled/elapsed_hr
                        reach_df.iloc[first_unlabelled_idx:i , labels_per_hr_idx] = labels_per_hr
                    
                    speed_mask = pd.isna(reach_df.loc[:, 'labels_per_hr']) == False 
                    speeds = reach_df.loc[:, 'labels_per_hr'][speed_mask]
                    avg_labels_per_hr = speeds.mean()
                    reach_df.loc[:, 'avg_labels_per_hr'] = avg_labels_per_hr    
                    
                    
                    
                    
                    base = os.path.basename(reaches_path)  
                    base = base.replace('notdone_', '')                        
                    new_name = 'notdone_' + base
                    new_path = os.path.join(output_folder, new_name)
                    try:
                        reach_df.to_csv(new_path)
                        print(f'labels are saved to {new_path}')
                        sys.exit()
                    except PermissionError:
                        print('COULD NOT SAVE. CLOSE THE EXCEL FILE IF IT IS OPEN')
                    
        
                #this block edits the success_level column depending on user input
                    #and updates i to move to next reach
                if level == '1':
                    reach_df.loc[reach_frame, 'success_level'] = '1'
                    print('edited')
                    i += 1
                    num_labelled +=1
                    
                    if min_valid != 'no_min':
                        num_valid += 1
                elif level == '2':
                    reach_df.loc[reach_frame, 'success_level'] = '2'
                    print('edited')
                    i += 1
                    num_labelled +=1
                    if min_valid != 'no_min':
                        num_valid += 1
                elif level == '3':
                    reach_df.loc[reach_frame, 'success_level'] = '3'
                    print('edited')
                    i += 1
                    num_labelled +=1
                    if min_valid != 'no_min':
                        num_valid += 1
                elif level == '4':
                    reach_df.loc[reach_frame, 'success_level'] = '4'
                    print('edited')
                    i += 1
                    num_labelled +=1
                    if min_valid != 'no_min':
                        num_valid += 1
                elif level == 'i':
                    reach_df.loc[reach_frame, 'success_level'] = 'i'
                    print('edited')
                    i += 1
                    num_labelled +=1
                elif level == 'x':
                    reach_df.loc[reach_frame, 'success_level'] = 'x'
                    print('edited')
                    i += 1
                    num_labelled +=1
                
                #these update i to mover to previous reach or next reach and do not 
                    #edit the success column 
                elif level == 'pr':
                    i -= 1 
                    continue 
                elif level == 'nr':
                    i += 1
                    continue
                
                
                
                    
                     
                #saves the df with the done prefix to the output folder once all reaches
                    #have been labelled or min valid labels have been done
                    #overwrites unlabelled file if it is there
                
                if i == len(reach_df) or num_valid >= min_valid:
                    
                    #these blocks calculate average labelling times and
                        #updates the columns
                    end = time.time()
                    elapsed_min = end - start
                    elapsed_hr = elapsed_min/3600
                    
                    if num_labelled > 0: 
                        labels_per_hr = num_labelled/elapsed_hr
                        last_frame_idx = len(reach_df) - 1
                        reach_df.iloc[first_unlabelled_idx: last_frame_idx , labels_per_hr_idx] = labels_per_hr
                        
                    
                    speed_mask = pd.isna(reach_df.loc[:, 'labels_per_hr']) == False 
                    speeds = reach_df.loc[:, 'labels_per_hr'][speed_mask]
                    avg_labels_per_hr = speeds.mean()
                    reach_df.loc[:, 'avg_labels_per_hr'] = avg_labels_per_hr                           
                    
                    base = os.path.basename(reaches_path)  
                    base = base.replace('notdone_', '')                        
                    new_name = 'notdone_' + base
                    
                    if i == len(reach_df):
                        new_new_name = 'done_' +base
                    elif num_valid >= min_valid:
                        new_new_name = 'done_' +base.split('.')[0] + f'_minV{min_valid}.csv'
                    new_new_path = os.path.join(output_folder, new_new_name)
                    new_path = os.path.join(output_folder, new_name)
                    try:
                        reach_df.to_csv(new_path)
                        os.rename(new_path, new_new_path)
                        print('Current mouse complete. Moving to next \n\n\n\n\n\n')
                    except Exception:
                        new_name = 'done_' + '(1)' + base
                        new_path = os.path.join(output_folder, new_name)
                        reach_df.to_csv(new_path)
                        
                    
                    return True
                    #this is for when we are looping through multiple files
                    
                    break
            except Exception:
                reach_df.loc[reach_frame, 'success_level'] = 'error'
                error_traceback = traceback.format_exc()
                current_date = datetime.now()
                error = f'{current_date}\nAn error occurred for file: {reaches_path} frame: {reach_frame} \n Error: {error_traceback}'
                with open(errors_file_path, "a") as file:
                    file.write(error + "\n" + '############' + '\n')
                    #adds this error to the textfile, creates a new textfile if one doesn't already exist
                print(error)
                i += 1

                
        
       
        
# loops through video folder and deletes leftover files 
        files = os.listdir(video_path)
        for file in files:
            if file.endswith('jpg') or file.endswith('clip.mp4'):
                file_path = os.path.join(video_path, file)
        
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                    
    
    except Exception:
        error_traceback = traceback.format_exc()
        current_date = datetime.now()
        error = f'{current_date}\nAn error occurred for File: {reaches_path}\n Error: {error_traceback}'
        with open(errors_file_path, "a") as file:
            file.write(error + "\n" + '############' + '\n')
            #adds this error to the textfile, creates a new textfile if one doesn't already exist
        print(error)
        base = os.path.basename(reaches_path)  
        base = base.replace('notdone_', '')                        
        new_name = 'error_' + base
        new_path = os.path.join(output_folder, new_name)
        reach_df.to_csv(new_path)
        return True







##### Labelling 


ffmpeg_bin = r'C:\DLCModels\Model_2\Analysis\Python\Reach_labeller\ffmpeg-7.1-full_build\bin'
#path to ffmpeg bin which contains ffmpeg.exe and ffplay.exe

video_folder = r'C:\DLCModels\Model_2\Analysis\Python\Videos_dates'
#folder containing date folders that contain videos
video_dates = os.listdir(video_folder)
#list of the date folders

reaches_folder = r'C:\DLCModels\Model_2\Analysis\Python\Analysis_Outputs\Reaches'
#folder containing date folders containing reach dataframes
reaches_dates = os.listdir(reaches_folder)
#list of the date folders

output_folder = r'C:\DLCModels\Model_2\Analysis\Python\Analysis_Outputs\Labelled_reaches'
#folder containing date folders where labelled dataframes will go
output_dates = os.listdir(output_folder)
#list of the date folders 

errors_file_path = os.path.join(output_folder, 'errors.txt')
#errors file that will be updated over time 

shared_dates = [x for x in reaches_dates if x in video_dates]
#these are the date folders that are in the videos 
    #folder and the reaches folder

#Loops through each shared date and then each file in the date folders. If 
    #partially labelled dataframes are present the labelling will start 
    #with them 


for i in shared_dates:
    
    
    
    try:
        
        
        
        video_date_path = os.path.join(video_folder, i)
        #video folder path
        date_videos = os.listdir(video_date_path)
        #list of videos in the date folder 
        
        reaches_date_path = os.path.join(reaches_folder, i)
        #reaches date foldr 
        date_reaches = os.listdir(reaches_date_path)
        #list of reaches in date folder 
        
        
        output_date_path = os.path.join(output_folder, i)
        #output date folder path 
        
        
        
        #makes a date folder in output folder if it doesn't exist
        if i not in(output_dates):
            os.mkdir(output_date_path)
         
        date_outputs = os.listdir(output_date_path)
        #list of previous outputs in the output date folder 
        
        #loops through list of reaches
        for j in date_reaches:
            
            try:
                video_name = [x for x in date_videos if x.split('_')[0] == j.split('_')[0]]
                #finds the corresponding video for the reach df by checking the 
                    #mouse id. FILE NAMES MUST FOLLOW THE SAME FORMAT
                if len(video_name) == 1:
                    #will be true if there was a corresponding video
                    video_name = video_name[0]
                    #creates video name
                    print(f'labelling {video_name}')
                else:
                    print(f'could not find corresponding video for {j} ')
                    continue 
                
                done = False
                skip = False
                reach_mouse_id = j.split('_')[0]
                #mouse id for reach file
                
                #treatment variable makes sure that the correct corresponding
                    #video is used for the reaches file. If there is 
                    #treatment metadata in the file name it checks the two. If
                    #not it only checks date and mouse id
                treatment = [x for x in j.split('_') if x.startswith('j60') or x.startswith('control') or x.startswith('chronicj60')]
                if len(treatment) > 0:
                    treatment = treatment[0]
                
                if type(treatment) == str:
                    if treatment.startswith('control'):
                        reach_mouse_treatment = 'control'
                    elif treatment.startswith('j60'):
                        reach_mouse_treatment = 'j60'
                    elif treatment.startswith('chronicj60'):
                        reach_mouse_treatment = 'chronicj60'
                else:
                    reach_mouse_treatment = np.nan
                
                #loops through outputs
                date_outputs_clean = [x for x in date_outputs if x.endswith('.csv')]
                for k in date_outputs_clean:
                    
                    
                    treatment = [x for x in k.split('_') if x.startswith('j60') or x.startswith('control') or x.startswith('chronicj60')]
                    if len(treatment) > 0:
                        treatment = treatment[0]
                    else: 
                        treatment = np.nan
                    
                    if type(treatment) == str:
                        if treatment.startswith('control'):
                            output_mouse_treatment = 'control'
                        elif treatment.startswith('j60'):
                            output_mouse_treatment = 'j60'
                        elif treatment.startswith('chronicj60'):
                            output_mouse_treatment = 'chronicj60'
                    else:
                        reach_mouse_treatment = np.nan
                    
                    output_mouse_id = k.split('_')[1]
                    #mouse id for the output
                    output_completion = k.split('_')[0]
                    #completion status (done or notdone) of the output file
                    
                    if type(reach_mouse_treatment ) == str and type(output_mouse_treatment == str):
                        
                        if reach_mouse_id == output_mouse_id and reach_mouse_treatment == output_mouse_treatment and output_completion == 'notdone':
                            #will use this file if this is true
                            
                            video_path = os.path.join(video_date_path, video_name)
                            reaches_path = os.path.join(output_date_path, k)
                            done = label_reaches(ffmpeg_bin, video_path, reaches_path, output_date_path, 1, 16)
                            #done is set to ture once the label_reaches
                                #function has labelled all the reaches in the df
                    else: 
                        if reach_mouse_id == output_mouse_id and output_completion == 'notdone':
                            #will use this file if this is true
                            
                            video_path = os.path.join(video_date_path, video_name)
                            reaches_path = os.path.join(output_date_path, k)
                            done = label_reaches(ffmpeg_bin, video_path, reaches_path, output_date_path, 1, 16)
                            #done is set to ture once the label_reaches
                                #function has labelled all the reaches in the df
                    
                    if type(reach_mouse_treatment ) == str and type(output_mouse_treatment == str):
                        if reach_mouse_id == output_mouse_id and reach_mouse_treatment == output_mouse_treatment and output_completion == 'done':
                            skip = True
                            #we skip this file if it is done
                            break
                    else:
                        if reach_mouse_id == output_mouse_id and output_completion == 'done':
                            skip = True
                            #we skip this file if it is done
                            break
                
                if skip or done:
                    #skips current j if it is already done or has just been completed
                    continue
                
                #labels reach df if it hasn't been done and there was no partial df
                video_path = os.path.join(video_date_path, video_name)
                reaches_path = os.path.join(reaches_date_path, j)
                label_reaches(ffmpeg_bin, video_path, reaches_path, output_date_path, 1, 16)
                
            except Exception:
                error_traceback = traceback.format_exc()
                current_date = datetime.now()
                error = (
                    
                    f'{current_date}\nAn error occurred for Date: {i} File: {j} \n Error: {error_traceback}'
                    )
                with open(errors_file_path, "a") as file:
                    file.write(error + "\n" + '############' + '\n')
                    #adds this error to the textfile, creates a new textfile if one doesn't already exist
                print(error)
        
        if i == shared_dates[len(shared_dates) - 1]:
            print ('All files complete')
    
    
    except Exception:
        
        error_traceback = traceback.format_exc()
        current_date = datetime.now()
        error = f'{current_date}\nAn error occurred for Date: {i} \n Error: {error_traceback}'
        with open(errors_file_path, "a") as file:
            file.write(error + "\n" + '############' + '\n')
            #adds this error to the textfile, creates a new textfile if one doesn't already exist
        print(error)

   
        

    























    



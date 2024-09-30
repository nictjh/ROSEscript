from datetime import datetime
from genericpath import isdir
import pandas as pd
from os import listdir
from os.path import isfile, join
import re
import os
import shutil
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import style
# import mpld3
import plotly.express as px
import plotly.offline as pyo
import plotly.graph_objects as go
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import ImageTk, Image

def compile_defect_history(defect_history_path):

    """Reading all defect_history files and compiling necessary rows into one file"""

    # global defect_df

    defect_df = pd.DataFrame(columns=[
        "Tail",
        "Date",
        'Time',
        "Filename",
        "Defect",
        "Rect Date",
        "Rect Time",
        "Rect Text",
        "Object Type Text",
        "Characteristics",
        "FL",
        "FL description",
        "Notification",
        "Utilization Value",
        "Workcenter",
        "Man Hour",
        "Symp",
        "Symptom Code Text",
        "Cir.Code Text",
        "Fair/Gair",
        "Effect Code Text",
        "ACModel"
    ])

    defect_index_count = 0
    dropped_rows = 0
    defect_history_datetime_format = '%d.%m.%Y %H:%M:%S'
    rect_format = '%d.%m.%Y %H:%M:%S'

    onlyfiles = [file_item for file_item in listdir(defect_history_path) if isfile(join(defect_history_path, file_item))]
    for filename in onlyfiles:
        file_path = defect_history_path + "\\" + filename
        print("Processing {}".format(filename))

        df = pd.read_excel(file_path,sheet_name="Sheet1", header=0)
        # Clean Column headers
        df = df.rename(columns=lambda x: x.strip())

        for index, row in df.iterrows():
            try:
                long_text = row["Long Text"].strip()
            except:
                # Empty Row condition
                continue

            try:
                defect_datetime_string = long_text[0:19]
                defect_datetime_object = datetime.strptime(defect_datetime_string, defect_history_datetime_format)
            except:
                # if no Timestamp avail,
                dropped_rows += 1
                continue

            defect_tail_number = row["AC"]
            defect_FL = row['FL']
            defect_FLDesc = row["FL description"]
            defect_char = row["Characteristics"]
            defect_notif = row["Notification"]
            defect_util = row["Utilization Value"]
            defect_wc = row["Workcenter"]
            defect_mh = row["Man Hour"]
            defect_symp = row["Symp"]
            defect_symCode = row["Symptom Code Text"]
            defect_cirCode = row["Cir.Code Text"]
            defect_FG = row["Fair/Gair"]
            defect_effect = row["Effect Code Text"]
            defect_obj_text = row["Object Type Text"]
            defect_model = row["ACModel"]

            #Assumes every entry has an NRIC
            long_text_cut = long_text[long_text.find(')') + 2: len(long_text)]

            if long_text.find("Phone") != -1:
                long_text_cut = long_text_cut[16:len(long_text_cut)]

            # Strips all whitespaces
            long_text_cut = long_text_cut.strip()

            # Reading Rectification Text Value
            try:
                rect_text = row["Rect Description"].strip()
            except:
                # Empty row, skip
                continue

            if not re.search(r"\d+\.\d+\.\d+",rect_text[:11]):
                continue

            rect_datetime = rect_text[:19]
            print(rect_datetime)
            rect_datetime_obj = datetime.strptime(rect_datetime, rect_format)

            rect_text_cut = rect_text[rect_text.find(')') +2:]
            if rect_text.find("Phone") != -1:
                rect_text_cut = rect_text_cut[16:]

            # Strip all whitespaces
            rect_text_cut = rect_text_cut.strip()

            new_defect = {
                "Tail" : int(defect_tail_number),
                "Date" : defect_datetime_object.strftime("%d/%m/%y"),
                "Time" : defect_datetime_object.strftime("%H:%M:%S"),
                "Filename" : filename,
                "Defect" : long_text_cut,
                "Rect Date" : rect_datetime_obj.strftime("%d/%m/%y"),
                "Rect Time" : rect_datetime_obj.strftime("%H:%M:%S"),
                "Rect Text" : rect_text_cut,
                "Object Type Text" : defect_obj_text,
                "Characteristics" : defect_char,
                "FL" : defect_FL,
                "FL description" : defect_FLDesc,
                "Notification" : defect_notif,
                "Utilization Value" : defect_util,
                "Workcenter" : defect_wc,
                "Man Hour" : defect_mh,
                "Symp" : defect_symp,
                "Symptom Code Text" : defect_symCode,
                "Cir.Code Text" : defect_cirCode,
                "Fair/Gair" : defect_FG,
                "Effect Code Text" : defect_effect,
                "ACModel" : defect_model,
            }

            new_df = pd.DataFrame(new_defect, index=[defect_index_count])
            defect_index_count += 1
            defect_df = pd.concat([defect_df,new_df])

    defect_df.to_csv("defect_history.csv", index=False)
    print("Dropped Rows: {}".format(dropped_rows))

    return(defect_df)



def compile_CVFDR(CVFDR_path):

    """
    Reads all txt files and compiles into a single index file.
    Splits all the different flights in single txt file and saves as individual csv files
    """

    # global index_df

    index_df = pd.DataFrame(columns=[
        "Tail",
        "Date",
        "Time",
        "Type",
        "Filename"
    ])

    datetime_format_1 = '%m/%d/%Y %I:%M:%S %p'
    datetime_format_2 = '%b %d %H:%M:%S %Y'
    row_count = 0
    file_counter = 0
    only_folders = [file_item for file_item in listdir(CVFDR_path) if isdir(join(CVFDR_path, file_item))]

    for file in only_folders:
        tail_number = file # Assigns the name of folder to tail number
        dir_path = CVFDR_path + "\\" + file
        only_files = [file_item for file_item in listdir(dir_path) if isfile(join(dir_path, file_item))]

        for filename in only_files:
            file_path = dir_path + "\\" + filename

            # Read first line date and delimiters in txt file
            with open(file_path) as f:
                first_line =  f.readline().strip()

            if first_line[-1] == ',':
                file_type = 'A'
            elif first_line[-1] == ';':
                file_type = 'B'
            else:
                file_type = "Error"

            if file_type != "Error":
                if file_type == 'A':
                    sep = ','
                    i = first_line.find(sep)
                    datetime_string = first_line[i+1 : -1]
                elif file_type == 'B':
                    sep = ';'
                    i = first_line.find(sep)
                    datetime_string = first_line[i+1 : -1]
                    i = datetime_string.find(sep)
                    datetime_string = datetime_string[0:i]

            datetime_object_1 = datetime.strptime(datetime_string, datetime_format_1)

            first_row =  {
                "Tail" : tail_number,
                "Date" : datetime_object_1.strftime("%d/%m/%y"),
                "Time" : datetime_object_1.strftime("%H:%M:%S"),
                "Type" : file_type,
                "Filename" : filename
            }

            first_row_df = pd.DataFrame(first_row, index=[row_count])
            row_count += 1
            index_df = pd.concat([index_df, first_row_df])

            # Read txt files into csv files so as to extract the remaining dates
            df = pd.read_csv(file_path, sep=sep, skiprows=1, header=[0,1])
            df.columns =  df.columns.map(" ".join)
            df = df.drop(index=0, axis=0) # Drops units row
            df = df.iloc[:,:-1]
            df.columns = df.columns.str.strip()
            df.columns = df.columns.str.replace(" ", "")

            # Retrieving Flight Date & Time and creating separate Date column
            df["UTCTimeInternaltorecorder"] = df["UTCTimeInternaltorecorder"].str.strip()
            df["DateofFlights"] = df["UTCTimeInternaltorecorder"].str.slice_replace(0,4,"").str[:7] + df["UTCTimeInternaltorecorder"].str.slice_replace(0,4,"").str[-4:]

            # Drop Duplicates to get unique dates only
            df_index = df.drop_duplicates(subset=["DateofFlights"])
            df_index = df_index.drop(columns="DateofFlights", axis=1) # removes this column after use

            for index, row in df_index.iterrows():
                # Strip the date column so as to extract
                longtext_date = row["UTCTimeInternaltorecorder"].strip()
                longtext_date = longtext_date[4:] # Slice till Month First letter
                datetime_object = datetime.strptime(longtext_date, datetime_format_2)

                # Add this new row of dates into the index_df
                new_row = {
                    "Tail" : tail_number,
                    "Date" : datetime_object.strftime("%d/%m/%y"),
                    "Time" : datetime_object.strftime("%H:%M:%S"),
                    "Type" : file_type,
                    "Filename" : filename
                }

                new_df = pd.DataFrame(new_row, index=[row_count])
                row_count += 1
                index_df = pd.concat([index_df, new_df])

            # Split of flights into different files
            for index, row in df.iterrows():
                date = row["DateofFlights"].strip()
                datetime_obj = datetime.strptime(date, "%b %d %Y")
                df.at[index, "DateofFlights"] = datetime_obj.strftime("Y%yM%mD%d")

            # Saving all unique dates
            dict_counter = 1
            date_dict = {}
            for i in range(1, len(df)):
                if df.loc[i, "DateofFlights"] in date_dict.keys():
                    df.loc[i, "Reference Flight Number"] = date_dict[df.loc[i, "DateofFlights"]]
                else:
                    date_dict[str(df.loc[i, "DateofFlights"])] = dict_counter
                    df.loc[i, "Reference Flight Number"] = date_dict[df.loc[i, "DateofFlights"]]
                    dict_counter += 1

            # Invert the dictionary
            # inverted_dict = dict(zip(date_dict.values(), date_dict.keys()))
            inverted_dict = dict((v,k) for k, v in date_dict.items())

            for i in inverted_dict.keys():
                trial_df = df[df["Reference Flight Number"] == int(i)]
                trial_df = trial_df.drop(columns="Reference Flight Number", axis=1)
                os.makedirs("Datasets/trial", exist_ok=True) #Update
                trial_df.to_csv("Datasets/trial/{0}_{1}.csv".format(tail_number, inverted_dict[i]), index=False) #Update
                print("Saved {0}_{1} into Datasets/trial folder".format(filename, inverted_dict[i])) 

            file_counter += 1
            print("Opening file number {}".format(file_counter))

    index_df.to_csv("index.csv", index=False)
    print("Collated index file")
    return(index_df)

### not working tested 5 times....
# def match_df(index_df, defect_df):

#     """
#     Match resulting dataframes of compile functions
#     """

#     # global matched_df


#     # Used left join so as to retain info in index, and add on necessary if matched on defect file
#     matched_df = index_df.merge(defect_df, how="left", left_on=["Tail", "Date"], right_on=["Tail", "Date"])
#     # matched_df = pd.merge(index_df, defect_df, on=["Tail", "Date"], how="left")
#     matched_df = matched_df.drop(["Time_x", "Time_y"], axis=1)
#     matched_df.to_csv("matched.csv", index=False)


#     return(matched_df)

# This somehow works... only difference is the dataframe
def match_df(index, defect):
    """Match the resulting csv files of the compiled functions"""

    # global matched_df

    # Read the files
    index_df = pd.read_csv(index, header=0)
    defect_df = pd.read_csv(defect, header=0)
    # Use left join to retain the info in index file and add on the necessary info
    matched_df = index_df.merge(defect_df, how="left", left_on=["Tail", "Date"], right_on=["Tail", "Date"])
    matched_df = matched_df.drop(["Time_x", "Time_y"], axis=1)
    matched_df.to_csv("matched.csv", index=False)

    # Run separator after match
    sep_defects(r"Datasets\trial")
    return(matched_df)



def sep_defects(extracted_filespath):
    """Differentiate the files into defects and non defects"""
    df = pd.read_csv("matched.csv")
    df = df.dropna()
    df = df.reset_index(drop=True)

    onlyfiles = [file_item for file_item in listdir(extracted_filespath) if isfile(join(extracted_filespath, file_item))]
    for index, row in df.iterrows():
        date = row["Date"]
        datet_obj = datetime.strptime(date, "%d/%m/%y")
        df.loc[index, "defectFile"] = str(row["Tail"]) + "_" + str(datet_obj.strftime("Y%yM%mD%d")) + ".csv"

    matched_files = df["defectFile"].values.tolist()
    matched_files = list(set(matched_files)) # Remove duplicate dates and convert to list

    # Check files (remove those that do not have any data)
    files_noData = []
    for i in matched_files:
        if i not in onlyfiles:
            print("Files with no flight data: {}".format(i))
            files_noData.append(i)

    # Collate matched_files list without the no data files
    matched_files = [file_item for file_item in matched_files if file_item not in files_noData]

    for i in matched_files:
        os.makedirs("Datasets/defects_test", exist_ok=True) # Update
        shutil.move("Datasets/trial/{}".format(i), "Datasets/defects_test/{}".format(i))


def flight_grnd_sep(norm_folder_path, defect_folder_path):
    """Separate files into in flight or on ground based on 2 conditions"""

    file_paths = [norm_folder_path, defect_folder_path]
    for paths in file_paths:
        grounds = []
        flights = []
        files = [file_item for file_item in listdir(paths) if isfile(join(paths, file_item))]
        for file in files:
            # Get filepath for each file
            filepath = paths + "\\" + file
            print("Opening file: {}".format(file))
            df = pd.read_csv(filepath)
            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

            # Strip again just in case for the column headers
            df_obj = df.select_dtypes(["object"])
            df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
            replacements = {
                "******" : "0"
            }
            df["PresAlt"] = df["PresAlt"].replace(replacements)
            df = df.astype({"PresAlt":float}) # Assign column type to float so can be used in ifelse statement

            # Params for while loop
            flag = True
            yeet = True
            startSlice = 0
            endSlice = 5
            count = 0

            while flag:
                if yeet == False:
                    print("Breaking the loop")
                    break
                if endSlice > len(df):
                    print("{} is a ground flight".format(file))
                    grounds.append(file)
                    yeet=False

                print("Count: {}".format(count))
                df_cut = df.iloc[startSlice:endSlice, :]
                print(df_cut[["DCU1_Dscrt_In_1-4Weight_on_Wheels_LH", "PresAlt"]])

                for i in range(len(df_cut)):
                    if (str(df_cut.iloc[i, 12]) == '.') and (df_cut.iloc[i, 15] >= 100):
                        count += 1
                        print("Fulfilled condition counter: {}".format(count))
                    if count == 5:
                        print("{} is a flight file".format(file))
                        flights.append(file)
                        yeet = False
                        break

                startSlice += 5
                endSlice += 5
                count = 0

        for i in flights:
            os.makedirs(paths + "\\" + "flights", exist_ok=True)
            shutil.move(paths + "\\" + "{}".format(i), paths + "\\" + "flights" + "\\" + "{}".format(i))
            print("Moved Flight file: {}".format(i))
        for i in grounds:
            os.makedirs(paths + "\\" + "ground", exist_ok=True)
            shutil.move(paths + "\\" + "{}".format(i), paths + "\\" + "ground" + "\\" + "{}".format(i))
            print("Moved Ground file: {}".format(i))
    return("Transfers of all files are done")



def plot_overallBar(norm_folderpath, defect_folderpath):
    """Plot overview bar chart to show performance of aircraft"""

    only_folder_norm = [file_item for file_item in listdir(norm_folderpath) if isdir(join(norm_folderpath, file_item))]
    only_folder_defect = [file_item for file_item in listdir(defect_folderpath) if isdir(join(defect_folderpath, file_item))]

    ### Working on the normal files
    for file in only_folder_norm:
        if file == "flights":
            dir_path = norm_folderpath + "\\" + file
            normflight_files = [file_item for file_item in listdir(dir_path) if isfile(join(dir_path,file_item))]
        elif file == "ground":
            dir_path = norm_folderpath + "\\" + file
            normground_files = [file_item for file_item in listdir(dir_path) if isfile(join(dir_path, file_item))]

    ###  Defect files
    for file in only_folder_defect:
        if file == "flights":
            dir_path = defect_folderpath + "\\" + file
            defFlight_files = [file_item for file_item in listdir(dir_path) if isfile(join(dir_path, file_item))]
        elif file == "ground":
            dir_path = defect_folderpath + "\\" + file
            defGround_files = [file_item for file_item in listdir(dir_path) if isfile(join(dir_path, file_item))]

    # Count the tail numbers for each file in non defects folder
    df_flights = pd.DataFrame(normflight_files, columns=["Flights"])
    df_ground  = pd.DataFrame(normground_files, columns=["Ground"])

    df_flights_def = pd.DataFrame(defFlight_files, columns=["Flights"])
    df_ground_def  = pd.DataFrame(defGround_files, columns=["Ground"])

    # Adding a Tail Column
    for index, rows in df_flights.iterrows():
        df_flights.loc[index, "Tail"] = rows["Flights"][0:3]

    for index, rows in df_ground.iterrows():
        df_ground.loc[index, "Tail"] = rows["Ground"][0:3]

    for index, rows in df_flights_def.iterrows():
        df_flights_def.loc[index, "Tail"] = rows["Flights"][0:3]

    for index, rows in df_ground_def.iterrows():
        df_ground_def.loc[index, "Tail"] = rows["Ground"][0:3]

    # Different Tails in the file
    tails = list(df_flights["Tail"].unique())
    tails_def = list(df_flights_def["Tail"].unique())
    tails = sorted(list(set(tails + tails_def)))

    # Counting the files based on tail number
    normalFiles_FL = {}
    normalFiles_GND = {}
    for tail in tails:
        count = len(df_flights.loc[df_flights["Tail"] == tail])
        normalFiles_FL[tail] = count
        counts = len(df_ground.loc[df_ground["Tail"] == tail])
        normalFiles_GND[tail] = counts

    defFiles_FL = {}
    defFiles_GND = {}
    for tail in tails_def:
        count = len(df_flights_def.loc[df_flights_def["Tail"] == tail])
        defFiles_FL[tail] = count
        counts = len(df_ground_def.loc[df_ground_def["Tail"] == tail])
        defFiles_GND[tail] = counts

    ## Plotting of graphs
    style.use("ggplot")
    xpos = np.arange(len(tails)) # to plot multiple stacked bar charts based on x position
    bar_width = 0.4 # bar width
    plt.bar(xpos, list(normalFiles_FL.values()), bar_width, label="Flights", color="royalblue")
    plt.bar(xpos, list(defFiles_FL.values()), bar_width, bottom=list(normalFiles_FL.values()), label="Flights with Defect", color="red")
    plt.bar(xpos+bar_width+0.01, list(normalFiles_GND.values()), bar_width, label="Ground", color="darkgoldenrod")
    plt.bar(xpos+bar_width+0.01, list(defFiles_GND.values()), bar_width, bottom=list(normalFiles_GND.values()), label="Ground w Defect", color="red")

    font = {
        "weight" : "bold",
        "size" : 12
    }

    for i,v in enumerate(list(normalFiles_FL.values())):
        plt.text(i,v,str(v), ha='center', va="bottom", fontdict=font)
    for i, v in enumerate(list(defFiles_FL.values())):
        plt.text(i, list(normalFiles_FL.values())[i] + v, str(v), ha='center', va='bottom', fontdict=font)
    for i, v in enumerate(list(normalFiles_GND.values())):
        plt.text(i + bar_width + 0.01, v, str(v), ha='center', va='bottom', fontdict=font)
    for i, v in enumerate(list(defFiles_GND.values())):
        plt.text(i + bar_width + 0.01, list(normalFiles_GND.values())[i] + v, str(v), ha='center', va='bottom', fontdict=font)

    plt.xticks(xpos+bar_width/2, tails)
    plt.xlabel("a/c Tail Number")
    plt.ylabel("Count of Flights")
    plt.title("Number of Flight recordings vs Tail Number")
    plt.legend()

    # Saving plot into IMG and Displaying
    figure = plt.gcf()
    figure.set_size_inches(17.45,9.82)
    plt.savefig("barplot.jpg", bbox_inches='tight')
    plt.show()



# left normal plotting of time series graph and GUI
def plot_TSgraphs(file_path):
    """Plot Time series graphs: Airspeed, Altitude, Engine Torque & Weight on Wheels"""

    # Read and convert time into timeseries
    df = pd.read_csv(file_path)
    # Convert "RelativeTime" column to datetime format
    df["RelativeTime"] = pd.to_datetime(df["RelativeTime"], format="%H:%M:%S")
    df["UTCTimeInternaltorecorder"] = pd.to_datetime(df['UTCTimeInternaltorecorder'], format='%a %b %d %H:%M:%S %Y')
    df.set_index('UTCTimeInternaltorecorder', inplace=True)


    def create_graph(yaxis):
        """Create Time series graph"""
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df[yaxis], mode="lines"))
        fig.update_layout(
            xaxis_title = "Time",
            yaxis_title = yaxis,
            title = "Time Series Graph for {}".format(yaxis)
        )
        fig.update_xaxes(range=[df.index.min(), df.index.max()])
        pyo.plot(fig, filename="TimeSeries_{}.html".format(yaxis))

    create_graph("TAS")
    create_graph("PresAlt")
    create_graph("DCU1_Dscrt_In_1-4Weight_on_Wheels_LH")


    # For Engine Torque
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df["RelativeTime"], y=df["Eng1_TQDCU1_1"], name="Engine 1"))
    fig3.add_trace(go.Scatter(x=df["RelativeTime"], y=df["Eng2_TQ_ALTDCU1_1"], name="Engine 2"))
    fig3.update_xaxes(title="RelativeTime")
    fig3.update_yaxes(title="EngineTorque")
    fig3.update_layout(title="Time Series Graph for Engine Torque")
    pyo.plot(fig3, filename="TimeSeries_EngTorq.html")


    return("Plot saved in html file")


#Done
# defect_df = compile_defect_history(r"C:\Users\Nicho\OneDrive\Desktop\Airforce MATTERS\Attachment to LDAB\Chinook AD project\CH_defect_history")
#Done
# index_df = compile_CVFDR(r"C:\Users\Nicho\OneDrive\Desktop\Airforce MATTERS\Attachment to LDAB\Chinook AD project\CH47 CVFDR Y2022 (CSV)")

# matched_df = match_df("index.csv", "defect_history.csv")

# print(defect_df.head())
# print(index_df.head())
# print(matched_df.head())

# sep_defects(trial_filepath)

# flight_grnd_sep(r"C:\Users\Nicho\OneDrive\Desktop\Airforce MATTERS\Attachment to LDAB\Chinook AD project\Datasets\trial", r"C:\Users\Nicho\OneDrive\Desktop\Airforce MATTERS\Attachment to LDAB\Chinook AD project\Datasets\defects_test")

# plot_overallBar(r"C:\Users\Nicho\OneDrive\Desktop\Airforce MATTERS\Attachment to LDAB\Chinook AD project\Datasets\trial", r"C:\Users\Nicho\OneDrive\Desktop\Airforce MATTERS\Attachment to LDAB\Chinook AD project\Datasets\defects_test")

# plot_TSgraphs(r"C:\Users\Nicho\OneDrive\Desktop\Airforce MATTERS\Attachment to LDAB\Chinook AD project\Datasets\test\flights\189_Y21M11D03.csv")



### Root widget, creating the window
root = tk.Tk()
root.title("GUI for Processing of files")

### Functions
defect_folderpath = r"Path"
CVFDR_folderpath = r"Path"

def askDir_defect():
    """For search directory (Process Defect Files)"""
    global defect_folderpath
    defect_folderpath =  filedialog.askdirectory()
    defect_history_path_label.config(text=defect_folderpath, bg="lightgreen")
    defect_history_path_button.config(bg="#f0f0f0")
    process_defects_button.config(bg="yellow", state="normal")

import threading

def runDefectProcess():
    """To process defect files using compile_defect_history""" # Took 1-2mins
    filepath = defect_folderpath
    # Disable button
    process_defects_button.config(state="disabled", bg="#f0f0f0")
    # Create window
    loading_window = create_loadingbar()

    def background_process():
        compile_defect_history(defect_history_path=filepath)
        close_loadingbar(loading_window)
        messagebox.showinfo("Update", "defect_history file created")

    thread = threading.Thread(target=background_process)
    thread.start()



def askDir_CVFDR():
    """For search directory (Process downloaded txt)"""
    global CVFDR_folderpath
    CVFDR_folderpath = filedialog.askdirectory()
    CVFDR_path_label.config(text=CVFDR_folderpath, bg="lightgreen")
    CVFDR_path_button.config(bg="#f0f0f0")
    process_CVFDR_button.config(bg="yellow", state="normal")


def runExtractprocess():
    """To process the txt files and split into the different flights""" # Took 4mins
    filepath = CVFDR_folderpath
    #Disable the button
    process_CVFDR_button.config(bg="#f0f0f0", state="disabled")
    loading_window = create_loadingbar()
    def background_process():
        compile_CVFDR(CVFDR_path=filepath)
        close_loadingbar(loading_window)
        messagebox.showinfo("Update", "index file created")
    thread = threading.Thread(target=background_process)
    thread.start()



def create_loadingbar():
    """Creates a loading window to display in order to show that the files are processing"""
    loading_window = tk.Toplevel(root)
    loading_window.title("Loading...")
    loading_window.geometry("300x100")
    progress = ttk.Progressbar(loading_window, orient=tk.HORIZONTAL, length=200, mode="indeterminate")
    progress.pack(pady=20)
    progress.start(10)
    return(loading_window)

def close_loadingbar(loading_window):
    """Destroys the created window"""
    loading_window.destroy()


def run_match(file1, file2):

    """Run eveything the rest of the script in one button"""

    def background_process(file1, file2):
        match_df(file1,file2)
        flight_grnd_sep(r"Datasets/trial", r"Datasets/defects_test")
        close_loadingbar(loading_window)

    try:
        loading_window = create_loadingbar()
        # Disable the button after one use
        match_button.config(bg="#f0f0f0", state="disabled")
        thread = threading.Thread(target=background_process, args=(file1,file2))
        thread.start()

    except:
        file1 = filedialog.askopenfilename(title="Open the INDEX file", filetypes=(("CSV Files", "*.csv"),))
        file2 = filedialog.askopenfilename(title="Open the DEFECT_HISTORY file", filetypes=(("CSV Files", "*.csv"),))
        loading_window = create_loadingbar()
        match_button.config(bg="#f0f0f0", state="disabled")
        thread = threading.Thread(target=background_process, args=(file1,file2))
        thread.start()


def run_barButton(filepath1, filepath2):
    loading_window = create_loadingbar()
    def background_process():
        plot_overallBar(filepath1, filepath2)
        close_loadingbar(loading_window)
    thread = threading.Thread(target=background_process)
    thread.start()


### Widgets
eg1_label = tk.Label(root, text="E.g. of Structure of folder", font=("Helevetica", 12))
# frame1 = tk.Frame(root, width=210, height=133)
img = ImageTk.PhotoImage(Image.open("step1pic.jpg"))
panel = tk.Label(root, image=img)

## Second Section
step1 = tk.Label(root, text="Step 1: Select defect_history folder directory", font=("Helvetica", 15, "bold"))
defect_history_path_button = tk.Button(root, text="Select directory", font=22, bg="yellow", command=askDir_defect)
defect_history_path_label = tk.Label(root, text=defect_folderpath, bg="red", font=18)
process_defects_button = tk.Button(root, text="Start", font=22, command=runDefectProcess, state="disabled")

## Third Section
eg2_label = tk.Label(root, text="E.g. of Structure of folder", font=("Helevetica", 12))
img2 = ImageTk.PhotoImage(Image.open("step2pic.jpg"))
panel2 = tk.Label(root, image=img2)
step2 = tk.Label(root, text="Step 2: Select CVFDR folder directory", font=("Helvetica", 15, "bold"))
CVFDR_path_button = tk.Button(root, text="Select directory", font=22, bg="yellow", command=askDir_CVFDR)
CVFDR_path_label = tk.Label(root, text=CVFDR_folderpath, bg="red", font=18)
process_CVFDR_button  = tk.Button(root, text="Start", font=22, command=runExtractprocess, state="disabled")


## Fourth Section
match_label = tk.Label(root, text="Step 3: Match > Separate > Differentiate", font=("Helvetica", 15, "bold"))
match_button = tk.Button(root, text="Start", font=22, bg="orange", command=lambda: run_match("index.csv", "defect_history.csv"))

##Fifth Section
other_func_label = tk.Label(root, text="Other functions:", font=("Helvetica", 15, "bold"))
bar_label = tk.Label(root, text="Plot Overview Bar graph", font=("Helvetica", 12, "bold"))
bargraph_button = tk.Button(root, text="Plot", bg="orange", font=22, command=lambda: run_barButton(r"Datasets/trial", r"Datasets/defects_test"))
TS_label = tk.Label(root, text="Plot Time Series Graphs", font=("Helvetica", 12, "bold"))
TS_dir_button = tk.Button(root, text="Select File", font=22, bg="orange" )
tsplot_button = tk.Button(root, text="Plot", font=22, bg="orange" )


### Positioning
# header.pack() #Shove it into the window
# Grid positions are relative, you need to add another label/text
##
eg1_label.grid(row=0, column=0, pady=(20,0))
panel.grid(row=0, column=1, pady=(20,0))

##
step1.grid(row=1, column=0, columnspan=2, pady=5)
defect_history_path_button.grid(row=1, column=3, pady=5, padx=(5,5))
defect_history_path_label.grid(row=2, column=0, columnspan=2, padx=2)
process_defects_button.grid(row=2, column=3, pady=5)
separator_1 = ttk.Separator(root, orient="horizontal").grid(row=3, sticky="ew", columnspan=4)

##
eg2_label.grid(row=4, column=0, pady=(20,0))
panel2.grid(row=4, column=1, pady=(20,0))
step2.grid(row=5, column=0, columnspan=2, pady=5)
CVFDR_path_button.grid(row=5, column=3, pady=5, padx=(5,5))
CVFDR_path_label.grid(row=6, column=0, columnspan=2, padx=2)
process_CVFDR_button.grid(row=6, column=3, pady=5)
separator_2 = ttk.Separator(root, orient="horizontal").grid(row=7, sticky="ew", columnspan=4)

## 4th section
warning_1 = tk.Label(root, text="Warning: Only proceed once you finish step 1 & 2", font=10).grid(row=8, column=0, pady=(5,0))
match_label.grid(row=9, column=0, columnspan=2, pady=50)
match_button.grid(row=9, column=3, pady=50)
separator_3 = ttk.Separator(root, orient="horizontal").grid(row=10, sticky="ew", columnspan=4)

##  5th section
other_func_label.grid(row=11, column=0, padx=0, sticky="W")

## 6th section
bar_label.grid(row=12, column=0, pady=5)
TS_label.grid(row=12, column=1, pady=5)
bargraph_button.grid(row=13, column=0, pady=2)
TS_dir_button.grid(row=13, column=1, pady=2)
tsplot_button.grid(row=13, column=1, pady=2, sticky="E")


### Event Loop
root.mainloop()

### GUI Progress Update
# Loading window to try (Done)
# Left TS function to link
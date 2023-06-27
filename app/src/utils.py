from pathlib import Path
import pandas as pd
import numpy as np
import os
import openpyxl
import streamlit as st
import tkinter as tk
from tkinter.filedialog import askdirectory
from natsort import natsorted
import pdb


def sort_measurements_df(
    dir_path,
    xlsx_fname,
    df_list,
    sample_type,
    measures,
    chronic=False,
    animal_id=None,
):
    sheetname_list = [
        "Blank-subtracted DeltaFF(%)",
        "Blank sub AUC",
        "Latency (s)",
        "Time to peak (s)",
    ]

    odors_list = [f"Odor {x}" for x in range(1, 8)]

    for df_ct, df in enumerate(df_list):
        measure = measures[df_ct]
        if chronic is True:
            df = df.reset_index().set_index(["Date", sample_type])
        else:
            df = df.reset_index().set_index(["Animal ID", "ROI", sample_type])
        df.sort_index(inplace=True)
        df = df.reindex(sorted(df.columns), axis=1)
        df.drop(columns=[(measure, "Odor 2")], inplace=True)

        # Manually add back empty/non-sig odor columns to reduce confusion
        for odor in odors_list:
            if (measure, odor) not in df.columns:
                df[(measure, odor)] = np.nan

        # Drop odor 8/blank from df
        if (measure, "Odor 8") in df.columns:
            df.drop(columns=[(measure, "Odor 8")], inplace=True)
        columns_list = [(f"{measure}", f"Odor {x}") for x in range(1, 8)]

        df = df[columns_list]  # Reorders Odor columns list
        sheetname = sheetname_list[df_ct]
        save_to_excel(dir_path, sheetname, xlsx_fname, df, animal_id)


def save_to_excel(dir_path, sheetname, xlsx_fname, df, animal_id=None):
    """
    Saves measurement dfs as one sheet per measurement type into Excel file
    """

    # xlsx_fname = f"compiled_dataset_analysis.xlsx"
    xlsx_path = Path(dir_path, xlsx_fname)

    if os.path.isfile(xlsx_path):  # if it does, write to existing file
        # if sheet already exists, overwrite it
        with pd.ExcelWriter(
            xlsx_path, mode="a", if_sheet_exists="replace"
        ) as writer:
            df.to_excel(writer, sheetname)
    else:  # otherwise, write to new file
        df.to_excel(xlsx_path, sheetname)

    format_workbook(xlsx_path, animal_id)


def format_workbook(xlsx_path, animal_id=None):
    """
    Adds borders to Excel spreadsheets
    """
    wb = openpyxl.load_workbook(xlsx_path)

    # Initialize formatting styles
    no_fill = openpyxl.styles.PatternFill(fill_type=None)
    side = openpyxl.styles.Side(border_style="thin")
    border = openpyxl.styles.borders.Border(
        left=side,
        right=side,
        top=side,
        bottom=side,
    )

    # Loop through all cells in all worksheets
    for sheet in wb.worksheets:
        if animal_id:
            sheet["A1"] = animal_id
        for row in sheet:
            for cell in row:
                # Apply colorless and borderless styles
                cell.fill = no_fill
                cell.border = border

    # Save workbook
    wb.save(xlsx_path)


def flatten(arg):
    """
    Flattens nested list of sig odors
    """
    if not isinstance(arg, list):  # if not list
        return [arg]
    return [x for sub in arg for x in flatten(sub)]  # recurse and collect


def make_pick_folder_button():
    """
    Makes the "Pick folder" button and checks whether it has been clicked.
    """
    clicked = st.button("Pick folder")
    return clicked


def pop_folder_selector():
    """
    Pops up a dialog to select folder. Won't pop up again when the script
    re-runs due to user interaction.
    """
    # Set up tkinter
    root = tk.Tk()
    root.withdraw()

    # Make folder picker dialog appear on top of other windows
    root.wm_attributes("-topmost", 1)

    dir_path = askdirectory(master=root)

    return dir_path

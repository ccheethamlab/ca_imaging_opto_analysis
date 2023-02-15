import streamlit as st
import pandas as pd
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import plotly.io as pio

pio.templates.default = "plotly_white"

from stqdm import stqdm
import pdb


def set_webapp_params():
    """
    Sets the name of the Streamlit app along with other things
    """
    st.set_page_config(page_title="Plot Multiple Acute Imaging Data")
    st.title("Plot data from multiple acute imaging sessions")

    st.markdown(
        "Please select the .xlsx files containing the response properties that you "
        "want to plot. The files should be named in the format "
        "YYMMDD--123456-7-8_ROIX_analysis.xlsx."
    )


def initialize_states():
    """
    Initializes session state variables
    """

    # # # --- Initialising SessionState ---
    # makes the avg_means data persist
    if "files" not in st.session_state:
        st.session_state.files = False
    # checks whether Load data was clicked
    if "load_data" not in st.session_state:
        st.session_state.load_data = False
    if "sig_data" not in st.session_state:
        st.session_state.sig_data = False
    if "sig_odors" not in st.session_state:
        st.session_state.sig_odors = False
    if "nosig_exps" not in st.session_state:
        st.session_state.no_sig_exps = False

    if "plots_list" not in st.session_state:
        st.session_state.plots_list = False
    if "selected_odor" not in st.session_state:
        st.session_state.selected_odor = False

    # measures to plot
    st.session_state.measures = [
        "Blank-subtracted DeltaF/F(%)",
        "Area under curve",
        "Latency (s)",
        "Time to peak (s)",
    ]

    st.session_state.files = st.file_uploader(
        label="Choose files",
        label_visibility="collapsed",
        accept_multiple_files=True,
    )


def import_data():
    """
    Loads data from uploaded .xlsx files, drops non-significant response data,
    and returns only significant data and list of significant odors
    """

    # makes list to hold exp names with no significant data
    nosig_exps = []
    # makes list to hold all significant odors
    all_sig_odors = []

    # makes dict to hold data from all significant odors
    sig_data_dict = {}

    # adds progress bar
    load_bar = stqdm(st.session_state.files, desc="Loading ")
    for file in load_bar:
        # reads avg means into dict, with sheet names/sample # as keys, df
        # as values
        exp_name = (
            file.name.split("_")[0]
            + "_"
            + file.name.split("_")[1]
            + "_"
            + file.name.split("_")[2]
        )
        load_bar.set_description(f"Loading data from {exp_name}", refresh=True)

        data_dict = pd.read_excel(
            file,
            sheet_name=None,
            header=1,
            index_col=0,
            na_values="FALSE",
            dtype="object",
        )

        sig_data_df = pd.DataFrame()

        # drop non-significant colums from each df using NaN values
        for data_df in data_dict.values():
            data_df.dropna(axis=1, inplace=True)

            # extracts measurements to plot
            data_df = data_df.loc[
                [
                    "Blank-subtracted DeltaF/F(%)",
                    "Area under curve",
                    "Latency (s)",
                    "Time to peak (s)",
                ]
            ]

            sig_data_df = pd.concat([sig_data_df, data_df], axis=1)

            # gets list of remaining significant odors
            sig_odors = data_df.columns.values.tolist()

            all_sig_odors.append(sig_odors)

        sig_data_dict[exp_name] = sig_data_df
        if sig_data_df.empty:
            nosig_exps.append(exp_name)

    return nosig_exps, all_sig_odors, sig_data_dict


def main():
    set_webapp_params()
    initialize_states()

    if st.session_state.files or st.session_state.load_data:
        if st.button("Load data"):
            st.session_state.load_data = True

            (
                st.session_state.nosig_exps,
                odors_list,
                st.session_state.sig_data,
            ) = import_data()

            st.info(
                f"Response data loaded successfully for "
                f"{len(st.session_state.files)} experiments."
            )

            # flatten list of odors
            flat_odors_list = [
                odor for sublist in odors_list for odor in sublist
            ]

            if len(st.session_state.nosig_exps) == len(st.session_state.files):
                st.error(
                    "None of the uploaded experiments have significant "
                    " odor responses. Please upload data for experiments with "
                    " significant responses to plot the response measurements."
                )
                # st.session_state.load_data = False
            else:
                # gets unique significant odors and puts them in order
                st.session_state.sig_odors = list(
                    dict.fromkeys(flat_odors_list)
                )
                st.session_state.sig_odors.sort()

            # if load data is clicked again, doesn't display plots/slider
            st.session_state.plots_list = False

        # if data has been loaded, always show plotting buttons
        if st.session_state.load_data and len(
            st.session_state.nosig_exps
        ) != len(st.session_state.files):
            if st.button("Plot data"):
                # plots_list = {}
                plots_list = defaultdict(dict)

                line_color_scale = [
                    "#D00000",
                    "#FFBA08",
                    "#3F88C5",
                    "#032B43",
                    "#136F63",
                ]

                fill_color_scale = [
                    "#FF5C5C",
                    "#FFE299",
                    "#A1C5E3",
                    "#B1DFFC",
                    "#85EADD",
                ]

                # adds progress bar

                odor_bar = stqdm(st.session_state.sig_odors, desc="Plotting ")

                for odor in odor_bar:
                    # makes list of experiments that have sig responses for
                    # the odor

                    sig_odor_exps = []
                    for exp_ct, experiment in enumerate(
                        st.session_state.sig_data.keys()
                    ):
                        if odor in st.session_state.sig_data[experiment]:
                            sig_odor_exps.append(experiment)

                    for measure in st.session_state.measures:
                        measure_fig = go.Figure()

                        for exp_ct, sig_experiment in enumerate(sig_odor_exps):
                            exp_odor_df = st.session_state.sig_data[
                                sig_experiment
                            ][odor]
                            # if odor == "Odor 4":
                            #     pdb.set_trace()

                            measure_fig.add_trace(
                                go.Box(
                                    x=[sig_experiment]
                                    * len(exp_odor_df.loc[measure].values)
                                    if isinstance(
                                        exp_odor_df.loc[measure], pd.Series
                                    )
                                    else [sig_experiment],
                                    y=exp_odor_df.loc[measure].values.tolist()
                                    if isinstance(
                                        exp_odor_df.loc[measure], pd.Series
                                    )
                                    else [exp_odor_df.loc[measure]],
                                    line=dict(color="rgba(0,0,0,0)"),
                                    fillcolor="rgba(0,0,0,0)",
                                    boxpoints="all",
                                    pointpos=0,
                                    marker_color=fill_color_scale[exp_ct],
                                    marker=dict(
                                        line=dict(
                                            color=line_color_scale[exp_ct],
                                            width=2,
                                        ),
                                        size=12,
                                    ),
                                    name=sig_experiment,
                                ),
                            )

                            # add horizontal line for mean
                            line_width = (1 / len(sig_odor_exps)) / 2

                            interval = (1 / len(sig_odor_exps)) / 2

                            start = (1 / len(sig_odor_exps)) / 4

                            # only adds mean line if there is more than one pt
                            if isinstance(exp_odor_df.loc[measure], pd.Series):
                                measure_fig.add_shape(
                                    type="line",
                                    line=dict(
                                        color=line_color_scale[exp_ct],
                                        width=4,
                                    ),
                                    xref="x domain",
                                    x0=start
                                    if exp_ct == 0
                                    else start
                                    + exp_ct * (interval + line_width),
                                    x1=start + line_width
                                    if exp_ct == 0
                                    else start
                                    + exp_ct * (interval + line_width)
                                    + line_width,
                                    # xref="paper",
                                    # x0=0 if exp_ct == 0 else (exp_ct * line_width),
                                    # x1=start + (exp_ct * line_width) + line_width,
                                    y0=exp_odor_df.loc[measure].values.mean(),
                                    y1=exp_odor_df.loc[measure].values.mean(),
                                )

                            #  below is code from stack overflow to hide duplicate legends
                            names = set()
                            measure_fig.for_each_trace(
                                lambda trace: trace.update(showlegend=False)
                                if (trace.name in names)
                                else names.add(trace.name)
                            )

                            measure_fig.update_xaxes(showticklabels=False)

                            measure_fig.update_yaxes(
                                title_text=measure,
                            )

                            if measure == "Time to peak (s)":
                                measure_fig.update_yaxes(
                                    rangemode="tozero",
                                )

                            measure_fig.update_layout(
                                boxgap=0.4,
                                title={
                                    "text": measure,
                                    "x": 0.4,
                                    "xanchor": "center",
                                },
                                legend_title_text="Experiment ID<br />",
                                showlegend=True,
                            )

                            plots_list[odor][measure] = measure_fig

                    odor_bar.set_description(f"Plotting {odor}", refresh=True)
                    # plots_list[odor] = odor_fig

                st.info("All plots generated.")
                if len(st.session_state.nosig_exps) != 0:
                    st.warning(
                        "No plots have been generated for the "
                        "following experiments due to the lack of significant "
                        "odor responses: \n"
                        f"{st.session_state.nosig_exps}"
                    )

                st.session_state.plots_list = plots_list

            # display slider and plots if plots have already been generated
            # even if Plot data isn't clicked again
            if st.session_state.plots_list:
                st.session_state.selected_odor = st.selectbox(
                    "Select odor number to display its corresponding plots:",
                    options=st.session_state.sig_odors,
                )

                if st.session_state.selected_odor:
                    for measure in st.session_state.measures:
                        st.plotly_chart(
                            st.session_state.plots_list[
                                st.session_state.selected_odor
                            ][measure]
                        )


if __name__ == "__main__":
    main()

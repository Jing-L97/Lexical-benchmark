import numpy as np
import pandas as pd
import math
from scipy.special import comb
from scipy.stats import norm
from collections import Counter
from collections import defaultdict
from typing import List
import matplotlib.pyplot as plt
from tqdm import tqdm
import random
from .utils import *


################################################################################################
# function to load csv data#
#################################################################################################
def load_csv(file_path, left_header, right_header):
    # Read the CSV file
    df = pd.read_csv(file_path)
    df.set_index('word', inplace=True)
    # Get the index of the start column
    df = df.loc[:, left_header:right_header]
    # Convert column headers to integers
    df.columns = df.columns.astype(int)
    return df


def apply_threshold(df, threshold):
    return df.applymap(lambda x: 1 if x > threshold else 0)


def to_tc_df(df, month, threshold):
    """convert the monthly df into the TC df"""
    # select the corresponding month
    df_frame = df[[month]]
    # remove words not produced/generated by this month
    df_frame = df_frame[df_frame[month] != 0]
    # apply the threshold on the generated words
    score_frame = apply_threshold(df_frame, threshold)
    score_frame.columns = ['count']
    # convert the result into freq_m
    score_frame['freq_m'] = score_frame['count'] / score_frame['count'].sum() * 1000000
    score_frame = score_frame.reset_index()
    score_frame['correct'] = score_frame['word'].apply(is_word)
    return score_frame


def dict2df(score_dict, header):
    """convert the dict into df for plotting rates in E1.3 figs"""
    df = pd.DataFrame(list(score_dict.items()), columns=['month', header])
    df = df.T
    df.columns = df.iloc[0]
    df = df.drop(df.index[0])
    return df


def month2model(model_dict, value):
    """convert the month into the corresponding trained model"""
    for key, value_range in model_dict.items():
        # Check if the value falls within the range
        if len(value_range) == 1 and value == value_range[0]:
            return key
        elif len(value_range) == 2 and value_range[0] <= value <= value_range[1]:
            return key
    return None


#################################################################################################
# Summary statistics for Token Counts
#################################################################################################

## custom numerical format
def custom_format(num):
    if (not np.isnan(num)) and num == int(num):  # Check if the number is effectively an integer
        return f"{int(num)}"
    elif 0.001 < abs(num) < 1000:  # Check if the number is between 0 and 0.001
        return f"{num:.3g}"
    else:  # For all other cases, print in scientific notation
        return f"{num:.3e}"


### defining summary statistics over tc and comparison functions
def tc_summary(data, figures=False):
    """Returns basic statistics about a list of token_counts (as defined in the TokenCount Class)
    the output is a dataframe with statistics as columns and corpora as lines
    """
    if type(data) == TokenCount:
        data = [data]
    if type(data) == list:
        listofdic = [tc.stats() for tc in data]
    tc_stats = pd.DataFrame(listofdic)
    tc_stats.set_index('name', inplace=True)
    return tc_stats


def prop_zero(ref_count: TokenCount, gen_count: TokenCount):
    """ computes a plot of differences"""
    refdf = ref_count.df
    gendf = gen_count.df

    missing_count = ref_count.difference(gen_count)


def tc_compare(ref_count: TokenCount, gen_count_list: List[TokenCount], figures=False):
    """Compare two token counts; the first one is the reference, the second one the generated (or test)
     from the reference, one can compute the missing words (words in ref not in gen)
     and the oovs (words in gen not in ref)
     the function retuns two dataframes, one with stats for the missing and one with stats from the oovs"""
    listofdic = []
    for gen_count in gen_count_list:
        missing_count = ref_count.difference(gen_count)
        m = missing_count.stats()
        m["prop_missing"] = missing_count.nb_of_types() / ref_count.nb_of_types()
        m["name"] = gen_count.name
        listofdic.append(m)
    missing_stats = pd.DataFrame(listofdic)
    missing_stats.set_index('name', inplace=True)

    listofdic = []
    for gen_count in gen_count_list:
        oov_count = gen_count.difference(ref_count)
        m = oov_count.stats()
        m["prop_oovs"] = oov_count.nb_of_types() / gen_count.nb_of_types()
        m["name"] = gen_count.name
        listofdic.append(m)
    oov_stats = pd.DataFrame(listofdic)
    oov_stats.set_index('name', inplace=True)

    listofdic = []
    for gen_count in gen_count_list:
        try:
            oov_count = gen_count.difference(ref_count)
            nword_count = oov_count.nonword()
            m = nword_count.stats()
            m["prop_nwords"] = nword_count.nb_of_types() / oov_count.nb_of_types()
            m["name"] = gen_count.name
            listofdic.append(m)
        except:
            pass
    nword_stats = pd.DataFrame(listofdic)
    nword_stats.set_index('name', inplace=True)

    return missing_stats, oov_stats, nword_stats


def calculate_miss_scores(group):
    """function used in a groupby bin; computes various scores for the missing items (from the point of view of ref_count)"""
    dfreq_score = (group['gen_count'] < group['ref_count']).mean() * -1 + (
                group['gen_count'] > group['ref_count']).mean()
    pmiss = (group['gen_count'] == 0).mean()
    nb = group.shape[0]
    medcount = (group['ref_count']).median()
    result = pd.Series([medcount, dfreq_score, pmiss, nb], index=['medcount', 'dfreq_score', 'pmiss', 'nb'])
    return result


def calculate_oov_scores(group):
    """function used in a groupby bin; computes various scores for the oov items"""
    poov = (group['ref_count'] == 0).mean()
    nb = group.shape[0]
    medcount = (group['gen_count']).median()
    result = pd.Series([medcount, poov, nb], index=['medcount', 'poov', 'nb'])
    return result


def calculate_word_scores(group):
    """function used in a groupby bin; computes various scores for the oov items"""
    pnonword = (group['correct'] == False).mean()
    nb = group.shape[0]
    medcount = (group['gen_count']).median()
    result = pd.Series([medcount, pnonword, nb], index=['medcount', 'pnword', 'nb'])
    return result


def build_bins(df, count_header: str, groupbin: int):
    """bin data into groups"""
    nblines = len(df)
    num_bins = groupbin  # int(nblines/groupbin)
    df['rnd'] = df[count_header] + np.random.normal(loc=0, scale=0.1, size=nblines)
    df['ranks'] = df['rnd'].rank().astype(int)
    df['bin'] = pd.qcut(df['ranks'], q=num_bins, labels=[f"Bin_{i + 1}" for i in range(num_bins)])
    return df


def tc_compute_miss_oov_rates(ref_count: TokenCount, gen_count: TokenCount, groupbin=20):
    """from two token counts (one reference and one generated or test),
     computes miss rate and oov rate curves
     (probability as a function of token count, grouped by bins of groupbin size)
     """
    # set the word column as index
    ref_count_frame = ref_count.df[['word', 'count', 'correct']]
    gen_count_frame = gen_count.df[['word', 'count', 'correct']]
    ref_count_frame.set_index('word', inplace=True)
    gen_count_frame.set_index('word', inplace=True)
    # remove the index with na
    ref_count_frame = ref_count_frame[~ref_count_frame.index.isna()]
    gen_count_frame = gen_count_frame[~gen_count_frame.index.isna()]
    # make a joint dataframe of counts for ref and gen (missing words are indicated by nans)
    newdf = pd.concat([ref_count_frame, gen_count_frame], axis=1, join='outer')
    # renaming the columns
    newdf.columns = ["ref_count", 'ref_correct', "gen_count", 'correct']
    # merge the spelling check columns
    newdf['correct'].fillna(newdf['ref_correct'], inplace=True)
    newdf = newdf.drop('ref_correct', axis=1)  # remove the duplicated spelling check column
    newdf.fillna(0, inplace=True)

    # this is a df where the oovs have been removed (to compute missing rates)
    missingdf = newdf.copy(deep=True)[newdf["ref_count"] != 0]
    # building bins of 200 tokens for the missing rate curve
    missingdf = build_bins(missingdf, 'ref_count', groupbin)
    mscores = missingdf.groupby('bin').apply(calculate_miss_scores).reset_index()

    # this is a df where the missed words have been removed (to compute oov rates)
    oovdf = newdf.copy(deep=True)[newdf["gen_count"] != 0]
    oovdf = build_bins(oovdf, 'gen_count', groupbin)
    oscores = oovdf.groupby('bin').apply(calculate_oov_scores).reset_index()

    # this is a df where only oov words are preserved (to reduce the nonword prop in train)
    oovdf = newdf.copy(deep=True)[newdf["gen_count"] != 0]
    nonworddf = oovdf[oovdf["ref_count"] == 0]
    nonworddf = nonworddf.reset_index()
    nonworddf = build_bins(nonworddf, 'gen_count', groupbin)
    nscores = nonworddf.groupby('bin').apply(calculate_word_scores).reset_index()

    return mscores, oscores, nscores


#################################################################################################
# E1 plotting functions
#################################################################################################

def plot_score(df, label, xlim=[0, 36], ylim=[0, 1], xlabel='(Pseudo) month', ylabel='Proportion of acquired words', color=False):
    """plot the thresholded counts"""
    # Convert column headers to integers
    df.columns = df.columns.astype(int)
    # Calculate average values across rows for each column
    average_values = df.mean()
    # Plot the curve
    plt.xlabel(xlabel)  # Label for the x-axis
    plt.ylabel(ylabel)  # Label for the y-axis
    plt.xlim(xlim)
    plt.ylim(ylim)
    if not color:
        plt.plot(average_values.index, average_values.values, label=label)
    else:
        plt.plot(average_values.index, average_values.values, label=label,color=color,linewidth=3.5)
    plt.grid(True)  # Show grid lines
    plt.legend()  # Show legend


#################################################################################################
# E2 plotting functions
#################################################################################################

def line_plot(data, xlog=True, ylim=[0, 1]):
    """Generic line plotting function; data is a dictionnary associating a name with a dataframe with two columns
    (the first one for x, the second one for y)
    """
    plt.figure(figsize=(10, 5))  # Set the size of the plot

    for key in data:
        df = data[key]
        xname = df.columns[0]
        yname = df.columns[1]
        aggregated_df = df.groupby(xname)[yname].mean().reset_index()
        plt.plot(aggregated_df[xname], aggregated_df[yname], label=key)
    # plt.title('prob of missing as a function of Token Count for the accumulator model')  # Title of the plot
    plt.xlabel(xname)  # Label for the x-axis
    plt.ylabel(yname)  # Label for the y-axis
    plt.ylim(ylim)
    plt.axhline(y=0, color='red', linestyle='--', label='y = 0')
    if xlog:
        plt.xscale("log")
    plt.grid(True)  # Show grid lines
    plt.legend()  # Show legend
    plt.show()  # Display the plot


def bar_plot(values, names, lower_bounds=None, upper_bounds=None, colors=None, ytitle=None, title=None, showval=True):
    """
    Creates a bar plot with optional confidence intervals.

    Parameters:
    - values: list or array of mean values (center of error bars)
    - lower_bounds: list or array of lower bounds of the confidence intervals
    - upper_bounds: list or array of upper bounds of the confidence intervals
    - names: list of names for each bar

    The lengths of all inputs must match.
    """
    # Calculate the error margins from the values
    if (not lower_bounds is None) and (not upper_bounds is None):
        error_lower = [value - lower for value, lower in zip(values, lower_bounds)]
        error_upper = [upper - value for value, upper in zip(values, upper_bounds)]
        error_bars = [error_lower, error_upper]
    else:
        error_bars = None
    # Set the positions of the bars
    positions = range(len(values))
    # Default color
    if colors is None:
        colors = ['skyblue'] * len(values)

    # Create the bar plot
    plt.figure(figsize=(10, 5))  # Set the figure size
    bars = plt.bar(positions, values, yerr=error_bars, capsize=5, color=colors, alpha=0.75, label='Values')

    if showval:
        for bar in bars:
            yval = bar.get_height()  # Get the height of each bar
            plt.text(bar.get_x() + bar.get_width() / 2, yval, f"{yval:.3g}", ha='center', va='bottom')

    plt.xticks(positions, names)  # Set the names on the x-axis
    plt.ylabel(ytitle)
    plt.title(title)
    # plt.legend()

    # Show the plot
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()


def plot_miss_oov_rates(ref_count: TokenCount, gen_count_list: List[TokenCount], groupbin=50):
    """
     Plots three curves regarding missing words and oovs

    :param ref_count: a reference TokenCount
    :param gen_count_list: a list of generated or test TokenCount
    :param groupbin:
    :return: nothing
    """
    pmiss = {}
    poov = {}
    dfreqscore = {}
    pnonword = {}
    for gen_count in gen_count_list:  # TODO: change the format into the desired one
        try:
            msc, osc, nsc = tc_compute_miss_oov_rates(ref_count, gen_count, groupbin=groupbin)
            pmiss[gen_count.name] = msc[["medcount", "pmiss"]]
            dfreqscore[gen_count.name] = msc[["medcount", "dfreq_score"]]
            poov[gen_count.name] = osc[["medcount", "poov"]]
            pnonword[gen_count.name] = nsc[["medcount", "pnword"]]
        except:
            print(gen_count.name)

    line_plot(pmiss)
    line_plot(dfreqscore, ylim=[-1, 1])
    line_plot(poov)
    line_plot(pnonword)


#################################################################################################
# Exploratory plotting functions
#################################################################################################
def tc_stats_plot(tc_stats, keyword):
    """ plotting as barplot particular statistics from tc_stats
    (tc stats is a simple dataframe with columns (keywords) as type of statistics and lines as corpora(token counts))
    """
    values = tc_stats[keyword]
    names = tc_stats.index
    bar_plot(values, names, ytitle=keyword)

def tc_plot_miss_oov_rates(ref_count: TokenCount, gen_count_list: List[TokenCount], groupbin=50):
    """
     Plots three curves regarding missing words and oovs

    :param ref_count: a reference TokenCount
    :param gen_count_list: a list of generated or test TokenCount
    :param groupbin:
    :return: nothing
    """
    pmiss = {}
    poov = {}
    dfreqscore = {}
    pnonword = {}
    for gen_count in gen_count_list:
        try:
            msc, osc, nsc = tc_compute_miss_oov_rates(ref_count, gen_count, groupbin=groupbin)
            pmiss[gen_count.name] = msc[["medcount", "pmiss"]]
            dfreqscore[gen_count.name] = msc[["medcount", "dfreq_score"]]
            poov[gen_count.name] = osc[["medcount", "poov"]]
            pnonword[gen_count.name] = nsc[["medcount", "pnword"]]
        except:
            print(gen_count.name)
        
    line_plot(pmiss)
    line_plot(dfreqscore, ylim=[-1, 1])
    line_plot(poov)
    line_plot(pnonword)

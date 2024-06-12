from typing import List
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
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
    #df = df.sort_values(by='count').reset_index(drop=True)
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

def merge_score(df):
    """merge rows of df"""
    df.columns = df.columns.astype(int)
    average_values = df.mean()
    merged = pd.DataFrame(average_values).T
    return merged 

def get_equal_quantity(data_frame, col_header:str, n_bins:int):
    # sort the df based on the selected column
    data_frame.dropna()
    data_frame[col_header] = data_frame[col_header].astype(int)
    data_frame = data_frame.sort_values(by=[col_header]).reset_index(drop=True)
    data = data_frame[col_header]
    size = len(data)
    assert n_bins <= size, "too many bins compared to data size"
    bin_indices = np.linspace(1, len(data), n_bins + 1) - 1  # indices to edges in sorted data
    data_sorted = np.sort(data)
    bins = [data_sorted[0]]  # left edge inclusive
    bins = np.append(bins, [(data_sorted[int(b)] + data_sorted[int(b + 1)]) / 2 for b in bin_indices[1:-1]])
    bins = np.append(bins, data_sorted[-1])  # this is because the extreme right edge is inclusive in plt.hits
        # computing bin membership for the original data; append bin membership to stat
    bin_membership = np.zeros(size, dtype=int)
    for i in range(0, len(bins)-1):
        bin_membership[(data_sorted >= bins[i]) & (data_sorted < bins[i + 1])] = i
    data_frame['group'] = bin_membership
    return data_frame

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
    tc_stats = tc_stats.sort_values(by='name')
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
def plot_score(df, label, xlim=[0, 36], ylim=[0, 1], xlabel='(Pseudo) month', ylabel='Proportion of acquired words'
               , color=False, error_bar=False, linewidth=2):
    """Plot the thresholded counts with color range for variability."""
    # Convert column headers to integers
    df.columns = df.columns.astype(int)
    # Calculate average values across rows for each column
    average_values = df.mean()
    # Calculate standard deviation across rows for each column
    std_dev_values = df.std()
    # Plot the curve with color range
    plt.xlabel(xlabel, fontsize=14)  # Label for the x-axis
    plt.ylabel(ylabel, fontsize=14)  # Label for the y-axis
    plt.xlim(xlim)
    plt.ylim(ylim)

    if not color:
        # Fill the area between the average values +/- standard deviation
        plt.plot(average_values.index, average_values.values, label=label, linewidth=linewidth)
        if error_bar:
            plt.fill_between(average_values.index,
                             average_values.values - std_dev_values.values,
                             average_values.values + std_dev_values.values,
                             alpha=0.3)
    else:
        plt.plot(average_values.index, average_values.values, label=label, color=color, linewidth=linewidth)
        if error_bar:
            plt.fill_between(average_values.index,
                             average_values.values - std_dev_values.values,
                             average_values.values + std_dev_values.values,
                             color=color, alpha=0.3)

    plt.legend()  # Show legend


def fit_sigmoid(score_df: pd.DataFrame, target_y, label):
    """fit sigmoid curve of extrapolated exp vocab"""
    def sigmoid(x, a, b):
        return 1 / (1 + np.exp(-(a * x + b)))

    x_data = score_df.columns.to_list()
    x_data = np.array(x_data)  # month array
    y_data = score_df.iloc[0].to_list()

    # Fit the sigmoid function to the scatter plot data
    popt, pcov = curve_fit(sigmoid, x_data, y_data, maxfev=100000, method='trf')
    # Generate x values for the fitted curve
    x_fit = np.linspace(0, max(x_data), 40)
    # Use the optimized parameters to generate y values for the fitted curve
    y_fit = sigmoid(x_fit, *popt)
    # first find the target x in the given scatter plots
    if max(y_data) < target_y:
        # Use the optimized parameters to generate y values for the fitted curve
        y_fit = sigmoid(x_fit, *popt)
        while y_fit[-1] < target_y:
            x_fit = np.append(x_fit, x_fit[-1] + 1)
            y_fit = np.append(y_fit, sigmoid(x_fit[-1], *popt))
            # Break the loop if the condition is met
            if y_fit[-1] >= target_y:
                break

    # Generate x values for the fitted curve
    # Find the index of the target y-value
    target_y_index = np.argmin(np.abs(y_fit - target_y))
    # Retrieve the corresponding x-value
    target_x = x_fit[target_y_index]

    plt.scatter(x_data, y_data)
    # plot until it has reached the target x
    plt.plot(x_fit, y_fit, linewidth=3.5, label=label + f': {target_x:.2f}')
    plt.legend()
    plt.ylim(0, 1)
    # Marking the point where y reaches the target value
    plt.axvline(x=int(target_x), linestyle='dotted')
    header_lst = ['Group', "Month", "Slope", "Weighted_offset"]
    # return the optimized parameters of the sigmoid function
    para_frame = pd.DataFrame([label, target_x, popt[0], popt[1]]).T
    para_frame.columns = header_lst
    return para_frame


def fit_log(x_data, y_data, label):
    """Fit a logarithmic curve to the data and plot it."""

    def log_curve(x, a, b):
        return a * np.log2(x) + b

    try:
        # Fit the logarithmic function to the scatter plot data
        popt, _ = curve_fit(log_curve, x_data, y_data, maxfev=100000, method='trf')
        # Generate x values for the fitted curve
        x_fit = np.linspace(min(x_data), max(x_data), 40)
        # Use the optimized parameters to generate y values for the fitted curve
        y_fit = log_curve(x_fit, *popt)
        # Plot the original scatter plot data
        plt.scatter(x_data, y_data)
        # Plot the fitted curve
        plt.plot(x_fit, y_fit, linewidth=3.5, label=label)
        plt.xlabel('Median freq', fontsize=15)
        plt.ylabel('Estimated months', fontsize=15)
        plt.tick_params(axis='both', labelsize=10)
        plt.legend()

    except Exception as e:
        print(f"An error occurred while fitting data for {label}: {e}")



#################################################################################################
# E2 plotting functions
#################################################################################################

def line_plot(data,fig_path,xlog=True, ylim=[0, 1]):
    """Generic line plotting function; data is a dictionnary associating a name with a dataframe with two columns
    (the first one for x, the second one for y)
    """
    #plt.figure(figsize=(10, 5))  # Set the size of the plot

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
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
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


def plot_bars(df_values, color_dict: dict, fig_path, df_single=False, df_shades=False, ytitle=None, title=None,
              showval=True):
    """
    Creates a grouped bar plot with shaded regions within each bar based on another DataFrame.

    Parameters:
    - df_values: pandas DataFrame where columns are group labels and index are the names for each group of bars (x labels)
    - df_shades: if plot, pandas DataFrame with the same structure as df_values, representing the proportion of the shaded regions within each bar
    - color_dict: dictionary where keys are group_labels (column names) and values are colors for the main bars
    - ytitle: string for the y-axis title
    - title: string for the plot title
    - showval: boolean to show the value on top of the bars
    """
    names = df_values.index
    group_labels = df_values.columns
    grouped_values = df_values.values

    # Initialize bar plot settings
    plt.figure(figsize=(10, 5))

    num_groups = len(names)
    num_bars = len(group_labels)
    bar_width = 0.8 / num_bars  # Width of each bar within a group
    indices = np.arange(num_groups)  # The x locations for the groups

    # Plot single df if there is any
    if isinstance(df_single, pd.DataFrame):
        single_values = df_single.values.flatten()
        single_names = df_single.index

        single_color = color_dict.get('single', 'grey')  # Default to blue if 'single' not found in color_dict
        single_positions = np.linspace(0, -0.8, len(single_values))  # Positions for single bars
        single_bars = plt.bar(single_positions, single_values, width=bar_width, color=single_color, alpha=0.75)
        # Set x tick label in the middle of each single bar

        if showval:
            for bar, value, pos in zip(single_bars, single_values, single_positions):
                yval = bar.get_height()
                plt.text(pos + bar_width / 2, yval, f"{yval:.2g}", ha='center', va='bottom')

    # Loop through each bar in the group
    for i in range(num_bars):
        values = grouped_values[:, i]
        color = color_dict.get(group_labels[i], 'grey')  # Default to grey if label not found
        # Bar positions for this group
        positions = indices + (i + 2) * bar_width
        bars = plt.bar(positions, values, width=bar_width, color=color, alpha=0.75, label=group_labels[i])

        # Annotate main bar values if showval is True
        if showval:
            for bar, position, value in zip(bars, positions, values):
                yval = bar.get_height()  # Get the height of each bar
                plt.text(position, yval, f"{value:.2g}", ha='center', va='bottom')

        # Plot shaded regions and annotate with proportions
        if isinstance(df_shades, pd.DataFrame):  # only plot the result if there is df input
            grouped_shades = df_shades.values
            shades = grouped_shades[:, i]

            for pos, val, shade in zip(positions, values, shades):
                shade_value = val * shade
                plt.bar(pos, shade_value, width=bar_width, color='lightgrey', alpha=0.5)
                # Annotate with the proportion value below the shaded region
                # plt.text(pos, 0, f"{shade:.3g}", ha='center', va='bottom', color='black')

    all_pos = np.concatenate((single_positions, indices + (num_bars + 3) * bar_width / 2), axis=None)
    all_names = list(single_names) + (list(names))
    plt.xticks(all_pos, all_names, fontsize=10)
    plt.ylabel(ytitle, fontsize=15)
    plt.title(title)
    plt.legend()
    # Show the plot
    plt.grid(True, linestyle='--', alpha=0.6)
    # save the figure to the fig_path
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
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


#### token count plots
def tc_plot(tokcount: TokenCount):
    """Three diagnostic plots from a token count:
           - Cumulative types as a function of token counts (starting with hapaxes)
           - Cumulative tokens as a function of token counts (starting with the highest frequency word)
           - Zipf law plot
    """
    # cumulative freq plot
    sorted_data = np.sort(tokcount.df["count"])
    nbpoints = sorted_data.shape[0]

    # Compute ranks
    fraction_types = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    # Plotting
    plt.figure(figsize=(8, 5))
    plt.plot(sorted_data, fraction_types, marker='o')
    plt.title('Fraction of Types with less or equal a Token Count')
    plt.xlabel('Token Counts')
    plt.ylabel('Fraction of Total Types')
    plt.grid(True)
    plt.xscale("log")
    plt.show()

    # Compute cumulative fractions
    cumulative_counts = np.cumsum(sorted_data[::-1])[::-1]
    total_counts = cumulative_counts[0]
    fractions = cumulative_counts / total_counts

    plt.figure(figsize=(8, 5))
    plt.plot(sorted_data, fractions, marker='o')
    plt.title('Fraction of Total Tokens for Types with more of equal Token Count')
    plt.xlabel('Token Counts')
    plt.ylabel('Fraction of Total Tokens')
    plt.grid(True)
    plt.xscale("log")
    plt.show()

    # Zipf law plot
    x = np.arange(1, (nbpoints + 1))  # ranks
    y = sorted_data[::-1]  # counts
    # log_x = np.log(x)
    # log_y = np.log(y)
    # Fit a linear regression model in the log-log space
    # weights = 1 / x
    # wls_model = sm.WLS(log_y, sm.add_constant(log_x), weights=weights)
    # results = wls_model.fit()
    # intercept = results.params[0]
    # slope = results.params[1]
    # log_y_fit=results.fittedvalues
    log_x, log_y_fit, intercept, slope = tokcount.zipf_coef()
    #plt.figure(figsize=(8, 5))
    plt.plot(x, y, marker='o')
    plt.plot(np.exp(log_x), np.exp(log_y_fit), 'r-',
             label=f'Regression Line: y = {slope:.2f}x + {intercept:.2f}')  # Regression line
    plt.title('Zipf plot')
    plt.xlabel('Rank')
    plt.ylabel('Count')
    plt.grid(True)
    plt.xscale("log")
    plt.yscale("log")
    plt.legend()
    plt.show()



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


def tc_plot_miss_oov_rates(ref_count: TokenCount, gen_count_list: List[TokenCount], fig_path: str, groupbin=50):
    """
     Plots three curves regarding missing words and oovs

    :param ref_count: a reference TokenCount
    :param gen_count_list: a list of generated or test TokenCount
    :param groupbin:
    :return: dataframe containing different scores
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

    # save figures respectively
    line_plot(pmiss, fig_path + 'M.png')
    line_plot(dfreqscore, fig_path + 'F.png', ylim=[-1, 1])
    line_plot(poov, fig_path + 'O.png')
    line_plot(pnonword, fig_path + 'N.png')
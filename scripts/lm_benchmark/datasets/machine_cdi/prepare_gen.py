import pandas as pd

model_dict = {'50h':[1],'100h':[1],'200h':[2,3],'400h':[4,8],'800h':[9,18]
    ,'1600h':[19,28],'3200h':[29,36],'4500h':[46,54],'7100h':[66,74]}


model_dict = {'50h':[1],'100h':[1],'200h':[2,3],'400h':[4,8],'800h':[10,18]
    ,'1600h':[19,28],'3200h':[29,36],'4500h':[46,54],'7100h':[66,74]}

df = pd.read_csv('/Users/jliu/PycharmProjects/Lexical-benchmark/datasets/raw/CHILDES_child.csv'
                   ,usecols = ['month','content','num_tokens'])

month_lst = ['3200h']
for month in month_lst:
    selected = df[(df['month'] >= model_dict[month][0]) & (df['month'] <= model_dict[month][1])]
    selected.columns = ['train','month','num_tokens']
    selected.to_csv('/Users/jliu/PycharmProjects/freq_bias_benchmark/data/train/train_utt/' + month[:-1] + '_child1.csv')


# segment the dataframes
import os
import numpy as np

month = '800h'
# Load the DataFrame from the CSV file
df = pd.read_csv('/Users/jliu/PycharmProjects/freq_bias_benchmark/data/train/train_utt/' + month[:-1] + '.csv')

# Define the number of splits and directories
num_splits = 30
num_dirs = 3
files_per_dir = num_splits // num_dirs

# Calculate the size of each split
split_size = int(np.ceil(len(df) / num_splits))

# Create directories
for i in range(1, num_dirs + 1):
    os.makedirs(f'dir_{i}', exist_ok=True)

# Split the DataFrame and save to files
for i in range(num_splits):
    start_idx = i * split_size
    end_idx = min((i + 1) * split_size, len(df))
    split_df = df.iloc[start_idx:end_idx]

    # Determine the directory for the current file
    dir_idx = (i // files_per_dir) + 1
    file_name = f'dir_{dir_idx}/data_{i + 1}.csv'

    # Save the split DataFrame to a CSV file
    split_df.to_csv(file_name, index=False)


def segment_sentences(file_path):
    """prepare for prompts"""

    segments = []

    with open(file_path, 'r') as file:
        for line in file:
            words = line.lower().strip().split()
            length = len(words)

            # Process the sentence if it has more than 3 words
            if length > 3:
                i = 0
                while i < length:
                    # If remaining words are less than 3, take them as they are
                    if length - i <= 3:
                        segments.append(' '.join(words[i:]))
                        break
                    else:
                        segments.append(' '.join(words[i:i + 3]))
                        i += 3
            else:
                # If the sentence is 3 words or less, take it as it is
                segments.append(' '.join(words))

    return segments



# prepare crp gen by segmenting into intermediate sets
raw_ROOT = f'{ROOT}/datasets/raw/3200.csv'
count = pd.read_csv(raw_ROOT)

month_lst = [15]
for month in month_lst:
    threshold = count['num_tokens'].sum()/18*month
    # Step 2: Compute the cumulative sum
    count['cum_sum'] = count['num_tokens'].cumsum()
    index_threshold = count[count['cum_sum'] <= threshold].index
    subframe = count.loc[index_threshold]
    wordcount = TokenCount.from_df(subframe,'train')
    wordcount.df.to_csv(f'{ROOT}/datasets/processed/freq/{str(month)}.csv',index=None)
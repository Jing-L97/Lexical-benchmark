#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
script to evaluate hyperparameters
1.compare entropy and log prob distr of the train data and genrated prompts
2. count the numbwer of generated words 
@author: jliu
"""


import os
import pandas as pd
from plot_entropy_util import plot_single_para, plot_distance, mean_KL,match_seq,lemmatize
import collections




def parseArgs(argv):
    # Run parameters
    parser = argparse.ArgumentParser(description='Generate tokens from decoder models')
    
    
    parser.add_argument('--number', default = '1',
                        help='a list of top-k or top_p candidates')
    
    parser.add_argument('--root_path', default = 'KL/KL_material/',
                        help='a list of temperature parameters for optimization')
    
    parser.add_argument('--output_path', default = 'KL/KL_eval/',
                        help='the output path of the calculated scores')
    
    parser.add_argument('--KL', type=bool, default = True,    # to be modified later!!!
                        help='a list of temperature parameters for optimization')
    
    parser.add_argument('--gpu', type=bool, default = True,
                        help= 'whether to use gpu')
   
    return parser.parse_args(argv)




def get_distr(root_path,gpu,KL):
    
    '''
    get the entropy distr and KL divergence with the reference data for each type 
    
    input: the root directory containing all the generated files adn train reference
    output: 1.the info frame with all the generarted tokens
            2.the reference frame with an additional column of the month info
            3.vocab size frame with the seq word and lemma frequencies
    '''
    
    # load the rerference data
    frame_all = []
    seq_all = []
    month_lst = []
    prompt_lst = []
    h_all = []
    prob_all =[]
    strategy_lst = []
    beam_lst = []
    topk_lst = []
    topp_lst = []
    random_lst = []
    temp_lst = []
    h_dist_lst = []
    prob_dist_lst = []
    directory_lst = []
    reference_frame = pd.DataFrame()
    
    # go over the generated files recursively
    
    for month in os.listdir(root_path): 
        if not month.endswith('.csv') and not month.endswith('.ods'): 
            train_distr = pd.read_csv(root_path + '/' + month + '/train_distr.csv')
            train_distr['month'] = month
            reference_frame = pd.concat([reference_frame,train_distr])
                    
            
            for prompt_type in os.listdir(root_path + '/' + month): 
                
                
                if not prompt_type.endswith('.csv') and not prompt_type.endswith('.ods'):                    
                    for strategy in os.listdir(root_path + '/' + month+ '/' + prompt_type): 
                        
                        for file in os.listdir(root_path + '/' + month+ '/' + prompt_type+ '/' + strategy):
                                  # in the case that entroyp and prob are not calculated yet
                                # load decoding strategy information
                                
                                data = pd.read_csv(root_path + '/' + month+ '/' + prompt_type + '/' + strategy + '/' + file)
                                
                                if not file.startswith('.'):
                                    
                                    try:
                                        
                                        # calculate the KL divergence between the reference and generated distr                                       
                                        #if KL:
                                        try:
                                            h_dist = mean_KL(data['LSTM_generated_h'].tolist(),train_distr['entropy'].tolist(),gpu)
                                            prob_dist = mean_KL(data['LSTM_generated_prob'].tolist(),train_distr['prob'].tolist(),gpu)
                                            
                                            h_dist_lst.append(h_dist)
                                            prob_dist_lst.append(prob_dist)
                                            
                                            prob_all.append(data['LSTM_generated_prob'].tolist())
                                            h_all.append(data['LSTM_generated_h'].tolist())
                                            print('SUCCESSFUL KL')
                                        except:
                                    
                                            h_dist_lst.append(1)
                                            prob_dist_lst.append(1)
                                            
                                            prob_all.append(data['LSTM_generated_prob'].tolist())
                                            h_all.append(data['LSTM_generated_h'].tolist())
                                            print('FAILED KL')
                                            
                                        # count words
                                        seq = []
                                        n = 0
                                        while n < data.shape[0]:
                                            generated = data['LSTM_segmented'].tolist()[n].split(' ')
                                            seq.extend(generated)
                                            n += 1
                                        
                                        # get freq lists
                                        frequencyDict = collections.Counter(seq)  
                                        freq_lst = list(frequencyDict.values())
                                        word_lst = list(frequencyDict.keys())
                                        fre_table = pd.DataFrame([word_lst,freq_lst]).T
                                        
                                        col_Names=["Word", "Freq"]
                                        
                                        fre_table.columns = col_Names
                                        seq_all.extend(seq)
                                        
                                        
                                        if strategy == 'beam':
                                            beam_lst.append(file.split('_')[0])
                                            topk_lst.append('0')
                                            topp_lst.append('0')
                                            random_lst.append('0')
                                            strategy_lst.append(strategy)
                                            fre_table['BEAM'] = file.split('_')[0]
                                            fre_table['TOPK'] ='0'
                                            fre_table['TOPP'] ='0'
                                            fre_table['RANDOM'] ='0'
                                            
                                            
                                        elif strategy == 'sample_topk':
                                            topk_lst.append(file.split('_')[0])
                                            beam_lst.append('0')
                                            topp_lst.append('0')
                                            random_lst.append('0')
                                            strategy_lst.append(strategy.split('_')[1])
                                            fre_table['TOPK'] = file.split('_')[0]
                                            fre_table['BEAM'] ='0'
                                            fre_table['TOPP'] ='0'
                                            fre_table['RANDOM'] ='0'
                                            
                                            
                                            
                                        elif strategy == 'sample_topp':
                                            topp_lst.append(file.split('_')[0])
                                            beam_lst.append('0')
                                            topk_lst.append('0')
                                            random_lst.append('0')
                                            strategy_lst.append(strategy.split('_')[1])
                                            fre_table['TOPP'] = file.split('_')[0]
                                            fre_table['BEAM'] ='0'
                                            fre_table['TOPK'] ='0'
                                            fre_table['RANDOM'] ='0'
                                            
                                            
                                        elif strategy == 'sample_random':
                                            random_lst.append('1')
                                            topk_lst.append('0')
                                            beam_lst.append('0')
                                            topp_lst.append('0')
                                            strategy_lst.append(strategy.split('_')[1])
                                            fre_table['RANDOM'] = file.split('_')[0]
                                            fre_table['BEAM'] ='0'
                                            fre_table['TOPP'] ='0'
                                            fre_table['TOPK'] ='0'
                                        
                                        # concatnete all the basic info regarding the genrated seq
                                        fre_table['MONTH'] = month
                                        fre_table['PROMPT'] = prompt_type
                                        prompt_lst.append(prompt_type)
                                        month_lst.append(month)
                                        temp_lst.append(float(file.split('_')[1]))
                                        directory_lst.append(month+ '/' + prompt_type + '/' + strategy + '/' + file)
                                        frame_all.append(fre_table)
                                        
                                        print('SUCCESS: ' + month+ '/' + prompt_type + '/' + strategy + '/' + file)    
                                    
                                    
                                    except:
                                        print('FAILURE: ' + month+ '/' + prompt_type + '/' + strategy + '/' + file)
                                
                                else:
                                    print(file)
    
    
    
    info_frame = pd.DataFrame([month_lst,prompt_lst,strategy_lst,beam_lst,topk_lst,topp_lst,random_lst,temp_lst,h_all,prob_all,prob_dist_lst,h_dist_lst,directory_lst]).T
    
    # rename the columns
    info_frame.rename(columns = {0:'month', 1:'prompt',2:'decoding', 3:'beam', 4:'topk', 5:'topp',6:'random', 7:'temp',8:'entropy',9:'prob',10:'prob_dist',11:'entropy_dist',12:'location'}, inplace = True)
    # remove the row with NA values
    
    info_frame = info_frame.dropna()
    info_frame = info_frame[(info_frame['random'] != '.') & (info_frame['topp'] != '.') & (info_frame['topk'] != '.') & (info_frame['prob'] != '[]')]
    
    
    # sort the result based on temperature to get more organized legend labels
    info_frame = info_frame.sort_values(by='temp', ascending=True)
    
    
    # # get word count and lemma count frames
    seq_lst = list(set(seq_all))
    
    seq_frame = match_seq(seq_lst,frame_all)
    
    word_lst, lemma_dict = lemmatize(seq_lst)
    
    word_lst.extend(['MONTH','PROMPT','BEAM','TOPK','TEMP','TOPP','RANDOM'])
    word_frame = seq_frame[word_lst]
    
    # reshape the lemma frame based onthe word_frame: basic info, lemma, total counts
    lemma_frame = seq_frame[['MONTH','PROMPT','BEAM','TOPK','TEMP','TOPP','RANDOM']]
    for lemma, words in lemma_dict.items():
        
        # Merge columns in the list by adding their values
        lemma_frame[lemma] = word_frame[words].sum(axis=1)
    
    return info_frame, reference_frame, seq_frame, word_frame, lemma_frame




'''
start evaluation
'''




def main(argv):
    
    
    # Args parser
    args = parseArgs(argv)
        
    gpu = args.gpu  
    KL = args.KL
    number = args.number
    output_path = args.output_path
    root_path = args.root_path + 'eval' + number
    
    
    info_frame, reference_frame, seq_frame, word_frame, lemma_frame = get_distr(root_path,gpu,KL)

    info_frame.to_csv(output_path + 'Info_frame' + number + '.csv')
    reference_frame.to_csv(output_path + 'Reference_frame' + number + '.csv')
    seq_frame.to_csv(output_path + 'seq_frame'+ number + '.csv')
    word_frame.to_csv(output_path + 'word_frame'+ number + '.csv')
    lemma_frame.to_csv(output_path + 'lemma_frame'+ number + '.csv')
    
    
    
if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
    


'''
def plot_distr(info_frame, reference_frame, month_lst, var_lst,decoding_lst,prompt_lst,KL): 
    
    for month in month_lst:
        for var in var_lst:
            # load the reference data based on the month and the investigated variable
            reference = reference_frame[reference_frame['month']==month][var].tolist()
            for prompt in prompt_lst:
                
                for decoding in decoding_lst:
                    
                    if KL:
                        target = info_frame[(info_frame['month']==month) & (info_frame['decoding']==decoding) & (info_frame['prompt']==prompt)]
                        
                        # sort the parameters 
                        decoding_val_lst = []
                        temp_val_lst = []
                        n = 0
                        while n < target.shape[0]:
                            
                            decoding_val = int(target[decoding].tolist()[n])
                            temp_val = float(target['temp'].tolist()[n])
                            
                            decoding_val_lst.append(decoding_val)
                            temp_val_lst.append(temp_val)
                            n += 1
                        
                        target[decoding] = decoding_val_lst
                        target['temp'] = temp_val_lst
                        
                        
                        # plot the KL divergence between the generated tokens and reference
                        plot_distance(target,var,decoding,prompt,month)
                        
                    
                    # get the decoding-specific parameters
                    decoding_para_lst = list(set(info_frame[(info_frame['month']==month) & (info_frame['decoding']==decoding) 
                                              & (info_frame['prompt']==prompt)][decoding].tolist()))
                    for decoding_para in decoding_para_lst:
                        
                        # plot the entropy and 
                        plot_single_para(info_frame,reference,decoding,decoding_para,month,prompt,var)
                 


root_path = 'eval'
gpu = True
KL = True

info_frame, reference_frame = get_distr(root_path,gpu,KL)

var_lst = ['prob']
decoding_lst = ['topp']
prompt_lst = ['unprompted']
#month_lst = ['1','3','12','36']
month_lst = ['36']
plot_distr(info_frame, reference_frame, month_lst, var_lst,decoding_lst,prompt_lst,KL)
    




column_lst = ['MONTH','PROMPT','BEAM','TOPK','TEMP','TOPP','RANDOM']
vocab_size_frame = get_score(threshold,word_frame,column_lst)




# plot the vocab size figures based on the results
for month in month_lst:
    for var in var_lst:
        for prompt in prompt_lst:
            
            for decoding in decoding_lst:
                
                
                # get the decoding-specific parameters
                decoding_para_lst = list(set(info_frame[(info_frame['month']==month) & (info_frame['decoding']==decoding) 
                                          & (info_frame['prompt']==prompt)][decoding].tolist()))
                
                
                
                
                
                    selected_frame = condition[condition['TEMP']==decode_para]
                    selected_frame['HOUR'] = selected_frame['HOUR'].astype(int)
                    selected_frame['Pseudo-month'] = selected_frame['HOUR']/89
                    # Sort the DataFrame based on the 'Column_Name'
                    selected_frame = selected_frame.sort_values('HOUR')
                    
                    
                    average_y_values = selected_frame.groupby('Pseudo-month')['vocab_size'].mean().reset_index()
                    
                    # convert back to month
                    
                    plt.figure(figsize=(8, 6))  # Optional: specify the figure size
                    sns.lineplot(data=average_y_values, x='Pseudo-month', y='vocab_size', marker='o')
                    
                    plt.ylim(20,100)
                    plt.xlabel('Pseudo-month')  # Label for x-axis
                    plt.ylabel(y_label)  # Label for y-axis (average)
                    plt.title(prompt +': ' + 'topk_' + decode_para)  # Title of the plot
                    plt.grid(True)  # Optional: add gridlines
                    plt.show()

'''



    
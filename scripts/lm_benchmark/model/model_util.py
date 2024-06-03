import numpy as np
import math
import pandas as pd
from pathlib import Path
from scipy.special import comb
from scipy.stats import norm
from collections import Counter
from collections import defaultdict
from tqdm import tqdm
import random
from lm_benchmark.utils import TokenCount

#################################################################################################
# function definitions useful for estimating theoretical probabilities of generations in the accumulator model
#################################################################################################
## custom numerical format
def custom_format(num):
    if (not np.isnan(num)) and num == int(num):  # Check if the number is effectively an integer
        return f"{int(num)}"
    elif 0.001 < abs(num) < 1000:  # Check if the number is between 0 and 0.001
        return f"{num:.3g}"
    else:  # For all other cases, print in scientific notation
        return f"{num:.3e}"

def p_miss(p, n):
    """Computes the probability of observing zero instances of an event with probability p after n draws
    Application: probability of not seeing a word with probability p in a corpus of size n words
    """
    return (1 - p) ** n


def p_obs_k_e(k, p, n):
    """
    Computes the probability of observing k instances of an event with probability p after n draws
    Exact formula using Bernouilli coefficients; crashes for k>50 and large n
    prob= C(n,k) * p^k * (1-p)^(n-k)
    """
    prob = np.nan
    if (k < 50) or (k > n - 50) or (n < 1000000):
        prob = comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
    return prob


def p_obs_k_p(k, p, n):
    """
    Approximates the probability of observing k instances of an event with probability p after n draws
    Poisson approximation, crashes for k>150; valid only for p small, n large, np moderate
    prob= (l^k) * e^-l / n!   with l=n*p
    """
    lambd = p * n
    prob = np.nan
    # print(lambd,k)
    if (k < 150) and (np.log10(lambd) * k < 300):
        prob = (lambd ** k) * np.exp(-lambd) / math.factorial(k)
    return prob


def p_obs_k_ps(k, p, n):
    """
    Approximates the probability of observing k instances of an event with probability p after n draws
    Poisson approximation with Stirling approximation for factorial, crashes for k>800; valid only for p small, n large, np moderate
    prob= ((l/k*e)^k) * e^-l / sqrt(2k*pi)   with l=n*p
    """
    lambd = p * n
    prob = np.nan
    if (k > 0) and (np.log10(lambd / k * np.e) * k < 300):
        prob = ((lambd / k * np.e) ** k) * np.exp(-lambd) / np.sqrt(2 * k * np.pi)
    return prob


def phi(mu, sd, x):
    """Cumulative function for a gaussian of mean mu and standard deviation sd"""
    return norm.cdf((x - mu) / sd)


def p_obs_k_g(k, p, n):
    """
    Approximates the probability of observing k instances of an event with probability p after n draws
    Gaussian approximation, never crashes; valid only for np>5 and n(1-p)>5
    prob==phi(k+0.5)-phi(k-0.5); where phi(x)=unitnormalCDF((x-mu)/sd), mu=n*p, sd=np.sqrt(n*p*(1-p))
    """
    mu = n * p
    sd = np.sqrt(n * p * (1 - p))
    return phi(mu, sd, k + 0.5) - phi(mu, sd, k - 0.5)


def p_obs_k(k, p, n):
    """Computes the probability of observing k instances of an event with probability p after n draws
    Application: probability of seeing a word k times, assuming it has probability p, in a corpus of size n words
    Uses various approximations to avoid crashing, and being approx correct
    """

    prob = p_obs_k_e(k, p, n)  # exact bernouilli
    if np.isnan(prob):
        prob = p_obs_k_p(k, p, n)  # Poisson Approx
    if np.isnan(prob):
        prob = p_obs_k_ps(k, p, n)  # Poisson Stirling Approx
    if np.isnan(prob):
        prob = p_obs_k_g(k, p, n)  # Gaussian Approx
    return prob


def p_obs_less_than_k(k, p, n):
    """Computes the probability of observing strictly less than k instances of an event with probability p after n draws
    Application: probability of seeing a word k times, assuming it has probability p, in a corpus of size n words
    Uses various approximations to avoid crashing, and being approx correct
    """
    pless = 0
    for i in range(k):
        pless += p_obs_k(i, p, n)
    return pless


def p_obs_k_list(k, p, n):
    """function used to debug"""
    return {'exact': p_obs_k_e(k, p, n), 'Poisson': p_obs_k_p(k, p, n), 'PoissonStir': p_obs_k_ps(k, p, n),
            'Gaussian': p_obs_k_g(k, p, n), 'total': p_obs_k(k, p, n)}


def accu_model_tok_stats(token_count, ref_corpus_size, gen_corpus_size=None):
    """Token Frequency stats for a token observed token_count times in the reference corpus (of size ref_corpus_size)
    in new corpus generated by an accumulator model with perfect memory trained on the reference corpus.
    The generated corpus size (gen_corpus_size) by default is of the same size as the reference, but can differ.
    Returned values:
       p_miss: probability of missing the word in the generated corpus
       p_once: probability of observing the word once
       p_same: probability of observing the word with the expected count (taking into account differences in corpus size)
       p_less: probability of observing the word with less than the expected count (including zero)
       p_more: probability of observing the word with more than the expected count
       score: expected score where score=1 if observed count is seen more than expected and -1 if less
    """
    if gen_corpus_size is None:
        gen_corpus_size = ref_corpus_size

    prob_token = token_count / ref_corpus_size
    gen_token_count = int(round(1.0 * token_count / ref_corpus_size * gen_corpus_size))

    pmiss = p_miss(prob_token, gen_corpus_size)
    ponce = p_obs_k(1, prob_token, gen_corpus_size)
    psame = p_obs_k(gen_token_count, prob_token, gen_corpus_size)
    pless = p_obs_less_than_k(gen_token_count, prob_token, gen_corpus_size)
    pmore = 1 - psame - pless
    score = pless * -1 + pmore
    return {'p_miss': pmiss, 'p_once': ponce, 'p_same': psame, 'p_less': pless, 'p_more': pmore, 'score': score}



###########################################################################################
## Defining nonparametric memory models
###########################################################################################

### defining an accumulator model based on a reference corpus

def make_accu(ref_count:TokenCount)->TokenCount:
   """Make a corpus from an accumulator model based on ref_count. Returns a TokenCount."""
   accucountarray=np.random.multinomial(ref_count.nb_of_tokens(), ref_count.df["count"]/ref_count.nb_of_tokens())
   accuwords=ref_count.df['word']
   accu_count=TokenCount(dict(zip(accuwords,accucountarray)),name="accu")
   accu_count.df=accu_count.df[accu_count.df["count"]!=0]
   return accu_count


#

def segment_into_chunks(input_file, num_chunks):
    """get the accumulator model from the largest training set"""
    # Read the text file into a DataFrame
    df = pd.read_csv(input_file)
    total_words = df['num_tokens'].sum()
    # Calculate the approximate number of words per chunk
    words_per_chunk = math.ceil(total_words / num_chunks)

    # Initialize variables
    current_chunk_number = 1
    current_chunk_word_count = 0
    chunk_numbers = []

    # Assign chunk numbers to each sentence
    for _, row in df.iterrows():
        sentence_word_count = row['count']
        if current_chunk_word_count + sentence_word_count > words_per_chunk and current_chunk_number < num_chunks:
            current_chunk_number += 1
            current_chunk_word_count = 0
        chunk_numbers.append(current_chunk_number)
        current_chunk_word_count += sentence_word_count

    # Add the chunk numbers to the DataFrame
    df['month'] = chunk_numbers
    return df



### defining an simple ngram model for words (used in CRP)


def generate_ngrams(word, n=2):
    """Extract ngrams from a word"""
    # Add beginning and end symbols
    word = '^' * (n - 1) + word + '$' * (n - 1)
    # Generate n-grams
    ngrams = [word[i:i + n] for i in range(len(word) - n + 1)]
    return ngrams


def build_ngram_model(words, n=2):
    """Build an ngram model for a list of words (they start with a series of ^ and end with a list of $) """
    ngrams = []
    # Collect n-grams from all words
    for word in words:
        ngrams.extend(generate_ngrams(word, n))

    # Count the occurrences of each n-gram
    ngram_counts = Counter(ngrams)

    # Calculate probabilities
    model = defaultdict(dict)
    for ngram, count in ngram_counts.items():
        prefix = ngram[:-(n - 2)]
        last_char = ngram[-(n - 2)]
        if prefix not in model:
            # Create a counter for this prefix if it does not exist
            model[prefix] = Counter()
        model[prefix][last_char] += count

    # Convert counts to probabilities
    for prefix, counts in model.items():
        total = sum(counts.values())
        for char in counts:
            counts[char] /= total

    return dict(model)

# sampling one word from the word ngram model
def sample_word(model, n=3, start_symbol='^', end_symbol='$'):
    """sample one word from an existing ngram model"""
    # Start with an appropriate number of start symbols based on n
    word = ''
    current = start_symbol * (n - 1)  # Adjust to start with n-1 start symbols

    while True:
        probabilities = model.get(current)
        if not probabilities:
            break
        next_char = random.choices(list(probabilities.keys()), weights=probabilities.values())[0]
        if next_char == end_symbol:
            break
        word += next_char
        # Update the current prefix by sliding to the right: include the latest character
        current = current[1:] + next_char  # Adjust to keep the length of 'current' as n-1

    return word


## chinese restaurant process model
def make_crp(ref_count: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """Make a chinese restaurant process based on ref_count with concentration param alpha
    Alpha should be scaled to correspond to the desired oov rate (alpha~oov_rate*total_token_count)
    Attention, not optimized for speed: for large corpora, this is EXTREMELY SLOW (30min for a 1M word corpus)
    Also, the process does not check that by accident an existing word could be generated
    """
    # make a 3-gram lm for words
    ngram_model = build_ngram_model(ref_count['word'], 3)
    # nb of tokens in the reference token count
    nbtoks = ref_count['count'].sum()
    # initialize an empty generated token count; convert into df
    gen_count = ref_count
    gen_count.columns = ['word','PseudoCount','freq_m','correct']   # only preserve the
    gen_count["count"] = 0

    # set word as index and only preserve the pseudo and true word count
    gen_frame = gen_count[['word','PseudoCount',"count"]]
    gen_frame.set_index('word', inplace=True)

    # make a new corpus with the same nb of tokens as the reference one
    for i in tqdm(range(1, nbtoks + 1)):
        # fist decide whether we should sample a new table (word)
        p_new_table = alpha / (nbtoks + i - 1 + alpha)
        if np.random.rand() < p_new_table:
            # Start a new table (word, by using the ngram model)
            new_word = sample_word(ngram_model, 3)
            if new_word in gen_frame.index:
                # if the word already existed, increment its count
                gen_frame["count"].loc[new_word] += 1
            else:
                # create a new word (with pseudo count of 0)
                gen_frame.loc[new_word] = [0, 1]
        else:
            # sample from existing tables
            adjusted_probs = gen_frame["count"] + gen_frame["PseudoCount"]
            ntables = len(adjusted_probs)
            probs = adjusted_probs / np.sum(adjusted_probs)
            # print(i,adjusted_probs,ntables,probs)
            table_choice = np.random.choice(np.arange(ntables), p=probs)
            gen_frame["count"].iloc[table_choice] += 1
    del gen_frame["PseudoCount"]  # removing the extra pseudocount column
    gen_frame = gen_frame[gen_frame["count"] != 0]  # removing missed words
    #gen_count.df.set_index('Word', inplace=True)
    gen_frame = gen_frame.reset_index()
    return gen_frame


def get_crp_score(crp_path:Path,CDI_ROOT:str,lang:str,memory_threshold:int)->dict:
    """get crp scores based on the machine CDI"""
    test_filename = lang + '_exp_machine.csv'
    test_frame = pd.read_csv(Path(CDI_ROOT)/test_filename)
    test_lst = test_frame['word'].tolist()
    overlap_words = {}
    for file in crp_path.iterdir():
        if file.name.endswith('csv'):
            frame = pd.read_csv(file)
            count = frame[frame['word'].isin(test_lst)]
            merged_df = pd.merge(count, test_frame, on='word', how='outer')
            merged_df = merged_df.fillna(0)
            # apply thresholds on the results
            merged_df = merged_df[['word','count_x']]
            merged_df.columns = ['word','count']
            merged_df['score'] = merged_df['count'].apply(lambda x: 1 if x > memory_threshold else 0)
            score = merged_df['score'].mean()
            overlap_words[int(file.name[:-4])] = score
            # sort the dictionay based on months(key)
            overlap_words = {key: overlap_words[key] for key in sorted(overlap_words)}
    return overlap_words

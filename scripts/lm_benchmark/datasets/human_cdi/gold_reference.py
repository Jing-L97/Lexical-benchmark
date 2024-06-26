"""
This is a loader and extractor for Human CDI

"""

import enum
from pathlib import Path
import pandas as pd
from ..utils import word_cleaning, word_to_pos, segment_synonym, remove_exp, merge_word


CONTENT_POS = {'ADJ', 'NOUN', 'VERB', 'ADV', 'PROPN'}
CATEGORY = {'connecting_words','helping_verbs','pronouns','quantifiers','prepositions','sounds','locations','question_words'}
WORD = {'now','dont','hi'}

class POSTypes(str, enum.Enum):
    """ Categories for Part of speech (PoS)

    """
    all = "all"
    content = "content"
    function = "function"

    def __str__(self) -> str:
        return self.value


class GoldReferenceCSV:
    """
    Download from the wordbank website : https://wordbank.stanford.edu/data?name=item_data
    This CSV contains ... TODO add brief description
    More info: docs/datasets/human_cdi (TODO: add correct documentation file)

    Column definitions:
        - downloaded: a date corresponding to the date it was downloaded
        - item_id: the id of the utterance
        - item_definition: the definition of the utterance
        - category: the category of the utterance
        - [16 - 30] these columns correspond to the month of the child
            - the cell values correspond to score based on knowledge of the word


    Gold<pd.DataFrame>:
        - word<str>: (the word)
        - word_length<int>: the length of the utterance in characters
        - POS<str>: a string representing the part of speech the utterance belongs to (see docs/... TODO)
        - category: string representing the category of the utterance
        - [16 - 30] these columns correspond to the month of the child
            - the cell values correspond to score based on knowledge of the word
    """

    @property
    def df(self) -> pd.DataFrame:
        """ Get the data as a Pandas DataFrame """
        if self._src_df is None:
            self._src_df = self.__load__()
        return self._src_df

    @property
    def gold(self) -> pd.DataFrame:
        """ Get the Gold data as a Pandas DataFrame """
        if self._target_df is None:
            self._target_df = self.__build_gold__()
        return self._target_df

    def __init__(self, age_min, age_max,raw_csv: Path,
                 pos_filter_type: POSTypes = POSTypes.content,
                 ):

        if not raw_csv.is_file():
            raise ValueError(f'Given file ::{raw_csv}:: does not exist !!')

        self._raw_csv_location = raw_csv
        self.pos_filter_type = pos_filter_type
        self.age_min = age_min
        self.age_max = age_max

        # Zero init
        self.download_date = None
        self._src_df = None
        self._target_df = None

        self.columns = [
            "word", "word_length", "POS", "category",
            *[str(a) for a in range(age_min, age_max + 1)]
        ]

    def __load__(self) -> pd.DataFrame:
        """ Load the dataset into a dataframe """
        df = pd.read_csv(self._raw_csv_location)
        self.dl_date = df['downloaded'].iloc[0]
        df = df.drop(["downloaded"], axis=1)
        return df

    def __build_gold__(self) -> pd.DataFrame:
        """ Build the gold dataframe from the given src """
        df = self.df.copy()

        # segment lines with synonyms
        df = segment_synonym(df,'item_definition')
        # Create a clean version of item_definition
        df['word'] = df['item_definition'].apply(word_cleaning)
        # remove expressions
        df = remove_exp(df,'word')
        # Calculate Word length
        df['word_length'] = df['word'].apply(len)

        # Build POS for the list of words
        df['POS'] = df['word'].apply(word_to_pos)

        # Filter words by PoS
        if self.pos_filter_type == POSTypes.content:
            # filter out all PoS that is not in CONTENT_POS
            df = df[df['POS'].isin(CONTENT_POS)]
        
        elif self.pos_filter_type == POSTypes.function:
            # Filter out all PoS that is in CONTENT_POS
            df = df[~df['POS'].isin(CONTENT_POS)]
        
        # Filter polysemous words by annotations from original data
        df = df[~df['category'].isin(CATEGORY)]
        df = df[~df['item_definition'].isin(WORD)]

        # merge different word senses by adding the prop
        df = merge_word(df,'word')
        df = df.drop(["item_id"], axis=1)

        return df[self.columns].copy()

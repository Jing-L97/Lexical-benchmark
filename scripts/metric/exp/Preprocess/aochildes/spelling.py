string2w = {
	'coca cola': 'cocacola',
	'g_i joe': 'gijoe',
	'don\'t cha': 'don\'t you',

}

w2string = {

	# probe words used by Philip Huebner
	'c_d': 'cd',
	'd_v_d': 'dvd',
	't+shirt': 'shirt',
	't_shirt': 'shirt',
	'dump+truck': 'dumptruck',
	'dump+trucks': 'dumptrucks',
	'head+phones': 'headphones',
	'coca_cola': 'cocacola',
	'coca+cola': 'cocacola',
	'g_i_joe': 'gijoe',
	'm_and_m': 'm&m',

	# split into pieces
	'everytime': 'every time',
	'lets': 'let us',
	'djou': 'do you',
	'dyou': 'do you',
	'didjou': 'did you',
	'wouldjou': 'would you',
	'wouldja': 'would you',
	'whadyou': 'what do you',
	'whaddya': 'what do you',
	'whadda': 'what do',
	'whaddaya': 'what do you',
	'whatcha': 'what are you',
	'whadya': 'what do you',
	'whada': 'what do',
	'didja': 'did you',
	'gimme': 'give me',
	'lemme': 'let me',
	'comere': 'come here',
	'cmere': 'come here',
	'camere': 'come here',
	'comon': 'come on',
	'cmon': 'come on',
	'oughta': 'ought to',
	'dontcha': 'do not you',
	'getcha': 'get you',
	'howbout': 'how about',
	'havta': 'have to',
	'hafta': 'have to',
	'byebye': 'bye bye',
	'nono': 'no no',
	'dunno': 'do not know',
	'hahaha': 'ha ha ha',
	'hehehe': 'he he he',
	'waimit': 'wait a minute',
	'betcha': 'bet you',
	'willn\'t': 'will not',
	'wherz': 'where is',
	'meetcha': 'meet you',
	'outa': 'out of',
	'knockknock': 'knock knock',
	'whadoes': 'what does',
	'whatchamacallit': 'what should we call it',
	'thankyou': 'thank you',

	# spelling
	'lookee': 'look',
	'looka': 'look',
	'lookit': 'look',
	'look_it': 'look',
	'mkay': 'okay',
	'mmkay': 'okay',
	'mm+kay': 'okay',
	'ya': 'you',
	'til': 'until',
	'untill': 'until',
	'goin': 'going',
	'doin': 'doing',
	'aroun': 'around',
	'scuse': 'excuse',
	'play+dough': 'playdoh',
	'playdoh': 'playdoh',
	'play_doh': 'playdoh',  # in case actual word is upper-cased
	'ninight': 'night night',
	'whad': 'what',
	'bandaid': 'band_aid',
	'babys': 'babies',
	'alrighty': 'alright',
	'alrigthy': 'alright',
	'grocerys': 'groceries',
	'seatbelt': 'seat belt',
	'earring': 'ear ring',
	'earrings': 'ear rings',
	'playroom': 'play room',
	'playrooms': 'play rooms',
	'woofwoof': 'woof woof',
	'woof+woof': 'woof woof',
	'woof+woof+woof': 'woof woof woof',
	'woof_woof': 'woof woof',
	'woof_woof_woof': 'woof woof woof',
	'woof_woof_woof_woof': 'woof woof woof woof',
	'snowman': 'snow man',
	'snow_man': 'snow man',
	'dere': 'there',
	'potatoe': 'potato',
	'potatoes': 'potatos',

	# diminutive
	'doggy': 'doggie',
	'puppys': 'puppies',
	'birdy': 'birdie',
	'kitty': 'kittie',
	'kittys': 'kitties',

	# contraction
	'what\'dya': 'what do you',
	'wha\'dyou': 'what do you',
	'wha\'does': 'what does',
	'cann\'t': 'can not',
	'whyn\'t': 'why do not you',
	'd\'you': 'do you',
	'c\'mon': 'come on',
	'c\'mere': 'come here',
	'com\'ere': 'come here',
	'd\'ya': 'do you',
	'y\'know': 'you know',
	'\'cause': 'because',
	's\'more': 'some more',
	'y\'wanna': 'you want to',
	'mommy\'ll': 'mommy will' ,
	'you\'ve': 'you have' ,
	'daddy\'ll': 'daddy will' ,
	'you\'re': 'you are' ,
	'this\'ll':  'this will' ,
	'that\'ll':  'that will' ,
	'that\'s': 'that is',
	'let\'s': 'let us',
    'is\'nt': 'is not',
	'it\'s': 'it is',
	'don\'t': 'do not',
    'doesn\'t': 'does not',
    'there\'s': 'there is',
    'what\'s': 'what is',
	'where\'s': 'where is',
    'they\'re': 'they are',
    'didn\'t': 'did not',
    'i\'m': 'i am',
    'i\'ve': 'i have',
    'we\'ve': 'we have',
    'haven\'t': 'have not',
	# underscore
	# underscore
	'have_to': 'have to',
	'has_to': 'has to',
	'got_to': 'got to',
	'lots_of': 'lots of',
	'a_lot_of': 'a lot of',
	'a_lot': 'a lot',
	'all_gone': 'all gone',
	'so_that': 'so that',
	'next_to': 'next to',
	'no_no': 'no no',
	'each_other': 'each other',
	'as_soon_as': 'as soon as',
	'ought_to': 'ought to',
	'come_on': 'come on',
	'oink_oink': 'oink oink',
	'oh_no': 'oh no',
	'all_done': 'all done',
	'quack_quack': 'quack quack',
	'how_about': 'how about',
	'because_of': 'because of',
	'peep_peep': 'peep peep',
	'laa_laa': 'laa laa',
	'what_about': 'what about',
	'sort_of': 'sort of',

	# aha
	'uhoh': 'aha',
	'uhuh': 'aha',
	'ahhah': 'aha',
	'uhhum': 'aha',
	'ummhm': 'aha',
	'umhum': 'aha',
	'hmhm': 'aha',
	'uhhuh': 'aha',
}

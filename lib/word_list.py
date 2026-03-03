"""Crossword fill word list with pattern matching."""

import os
import re


# Common crossword fill words — curated for quality and solvability.
# Mix of 3-15 letter words frequently seen in NYT-style crosswords.
_CURATED_WORDS = [
    # 3-letter words
    'ACE', 'ACT', 'ADD', 'AGE', 'AGO', 'AID', 'AIM', 'AIR', 'ALE', 'ALL',
    'AND', 'ANT', 'APE', 'ARC', 'ARE', 'ARK', 'ARM', 'ART', 'ATE', 'AWE',
    'AXE', 'BAD', 'BAG', 'BAN', 'BAR', 'BAT', 'BED', 'BET', 'BIG', 'BIT',
    'BOW', 'BOX', 'BOY', 'BUD', 'BUG', 'BUS', 'BUT', 'BUY', 'CAB', 'CAN',
    'CAP', 'CAR', 'CAT', 'COP', 'COT', 'COW', 'CRY', 'CUB', 'CUP', 'CUR',
    'CUT', 'DAD', 'DAM', 'DAY', 'DEN', 'DEW', 'DID', 'DIG', 'DIM', 'DIP',
    'DOC', 'DOG', 'DOT', 'DRY', 'DUB', 'DUE', 'DUG', 'DUO', 'DYE', 'EAR',
    'EAT', 'EEL', 'EGG', 'EGO', 'ELF', 'ELK', 'ELM', 'EMU', 'END', 'ERA',
    'ERR', 'EVE', 'EWE', 'EYE', 'FAN', 'FAR', 'FAT', 'FAX', 'FED', 'FEW',
    'FIG', 'FIN', 'FIR', 'FIT', 'FIX', 'FLU', 'FLY', 'FOB', 'FOE', 'FOG',
    'FOR', 'FOX', 'FRY', 'FUN', 'FUR', 'GAB', 'GAG', 'GAP', 'GAS', 'GEL',
    'GEM', 'GET', 'GNU', 'GOB', 'GOD', 'GOT', 'GUM', 'GUN', 'GUT', 'GUY',
    'GYM', 'HAD', 'HAM', 'HAS', 'HAT', 'HAY', 'HEN', 'HER', 'HEW', 'HID',
    'HIM', 'HIP', 'HIS', 'HIT', 'HOG', 'HOP', 'HOT', 'HOW', 'HUB', 'HUE',
    'HUG', 'HUM', 'HUT', 'ICE', 'ICY', 'ILL', 'IMP', 'INK', 'INN', 'ION',
    'IRE', 'IRK', 'IVY', 'JAB', 'JAG', 'JAM', 'JAR', 'JAW', 'JAY', 'JET',
    'JIG', 'JOB', 'JOG', 'JOT', 'JOY', 'JUG', 'JUT', 'KEG', 'KEN', 'KEY',
    'KID', 'KIN', 'KIT', 'LAB', 'LAD', 'LAG', 'LAP', 'LAW', 'LAY', 'LED',
    'LEG', 'LET', 'LID', 'LIE', 'LIT', 'LOG', 'LOT', 'LOW', 'LUG', 'MAD',
    'MAN', 'MAP', 'MAR', 'MAT', 'MAW', 'MAX', 'MAY', 'MEN', 'MET', 'MIX',
    'MOB', 'MOM', 'MOP', 'MOW', 'MUD', 'MUG', 'NAB', 'NAG', 'NAP', 'NET',
    'NEW', 'NIL', 'NIT', 'NOD', 'NOR', 'NOT', 'NOW', 'NUB', 'NUN', 'NUT',
    'OAK', 'OAR', 'OAT', 'ODD', 'ODE', 'OFF', 'OFT', 'OIL', 'OLD', 'ONE',
    'OPT', 'ORB', 'ORE', 'OUR', 'OUT', 'OWE', 'OWL', 'OWN', 'PAD', 'PAL',
    'PAN', 'PAT', 'PAW', 'PAY', 'PEA', 'PEG', 'PEN', 'PEP', 'PER', 'PET',
    'PEW', 'PIE', 'PIG', 'PIN', 'PIT', 'PLY', 'POD', 'POP', 'POT', 'PRY',
    'PUB', 'PUG', 'PUN', 'PUP', 'PUS', 'PUT', 'RAG', 'RAM', 'RAN', 'RAP',
    'RAT', 'RAW', 'RAY', 'RED', 'REF', 'RIB', 'RID', 'RIG', 'RIM', 'RIP',
    'ROB', 'ROD', 'ROT', 'ROW', 'RUB', 'RUG', 'RUN', 'RUT', 'RYE', 'SAC',
    'SAD', 'SAG', 'SAP', 'SAT', 'SAW', 'SAY', 'SEA', 'SET', 'SEW', 'SHE',
    'SHY', 'SIN', 'SIP', 'SIS', 'SIT', 'SIX', 'SKI', 'SKY', 'SLY', 'SOB',
    'SOD', 'SON', 'SOP', 'SOT', 'SOW', 'SOY', 'SPA', 'SPY', 'STY', 'SUB',
    'SUM', 'SUN', 'SUP', 'TAB', 'TAD', 'TAG', 'TAN', 'TAP', 'TAR', 'TAT',
    'TAX', 'TEA', 'TEN', 'THE', 'TIE', 'TIN', 'TIP', 'TOE', 'TON', 'TOO',
    'TOP', 'TOT', 'TOW', 'TOY', 'TUB', 'TUG', 'TWO', 'URN', 'USE', 'VAN',
    'VAT', 'VET', 'VIA', 'VIE', 'VOW', 'WAD', 'WAG', 'WAR', 'WAX', 'WAY',
    'WEB', 'WED', 'WET', 'WHO', 'WIG', 'WIN', 'WIT', 'WOE', 'WOK', 'WON',
    'WOO', 'WOW', 'YAK', 'YAM', 'YAP', 'YAW', 'YEA', 'YES', 'YET', 'YEW',
    'YIN', 'YOU', 'ZAP', 'ZEN', 'ZIP', 'ZIT', 'ZOO',
    # 4-letter words
    'ABLE', 'ACHE', 'ACID', 'ACME', 'ACRE', 'AGED', 'AIDE', 'AISLE',
    'AJAR', 'AKIN', 'ALAS', 'ALLY', 'ALSO', 'ALTO', 'AMID', 'ARCH',
    'AREA', 'ARIA', 'ARMY', 'ASEA', 'ATOM', 'ATOP', 'AUTO', 'AVID',
    'AXLE', 'BABE', 'BACK', 'BAIL', 'BAIT', 'BAKE', 'BALD', 'BALE',
    'BALL', 'BAND', 'BANE', 'BANK', 'BARE', 'BARN', 'BASE', 'BATH',
    'BEAD', 'BEAM', 'BEAN', 'BEAR', 'BEAT', 'BEEF', 'BEEN', 'BEER',
    'BELL', 'BELT', 'BEND', 'BENT', 'BEST', 'BILE', 'BILL', 'BIND',
    'BIRD', 'BITE', 'BLADE', 'BLOW', 'BLUE', 'BLUR', 'BOAR', 'BOAT',
    'BODY', 'BOLD', 'BOLT', 'BOMB', 'BOND', 'BONE', 'BOOK', 'BOOM',
    'BORE', 'BORN', 'BOSS', 'BOTH', 'BOWL', 'BULK', 'BULL', 'BUMP',
    'BURN', 'BURR', 'BUST', 'BUSY', 'CAFE', 'CAGE', 'CAKE', 'CALF',
    'CALL', 'CALM', 'CAME', 'CAMP', 'CANE', 'CAPE', 'CARD', 'CARE',
    'CART', 'CASE', 'CASH', 'CAST', 'CAVE', 'CELL', 'CHAT', 'CHIN',
    'CHIP', 'CITE', 'CITY', 'CLAD', 'CLAM', 'CLAN', 'CLAP', 'CLAY',
    'CLIP', 'CLOD', 'CLOG', 'CLOT', 'CLUB', 'CLUE', 'COAL', 'COAT',
    'CODE', 'COIL', 'COIN', 'COLD', 'COLE', 'COLT', 'COMB', 'COME',
    'CONE', 'COOK', 'COOL', 'COPE', 'COPY', 'CORD', 'CORE', 'CORK',
    'CORN', 'COST', 'COZY', 'CRAB', 'CREW', 'CROP', 'CROW', 'CUBE',
    'CULT', 'CURB', 'CURE', 'CURL', 'DALE', 'DAME', 'DAMP', 'DARE',
    'DARK', 'DARN', 'DART', 'DASH', 'DATA', 'DATE', 'DAWN', 'DAYS',
    'DEAD', 'DEAF', 'DEAL', 'DEAN', 'DEAR', 'DEBT', 'DECK', 'DEED',
    'DEEM', 'DEEP', 'DEER', 'DEMO', 'DENT', 'DENY', 'DESK', 'DIAL',
    'DICE', 'DIED', 'DIET', 'DINE', 'DIRE', 'DIRT', 'DISC', 'DISH',
    'DISK', 'DOCK', 'DOES', 'DOME', 'DONE', 'DOOM', 'DOOR', 'DOSE',
    'DOVE', 'DOWN', 'DOZE', 'DRAB', 'DRAG', 'DRAW', 'DRIP', 'DROP',
    'DRUM', 'DUAL', 'DUEL', 'DUFF', 'DUKE', 'DULL', 'DUMB', 'DUMP',
    'DUNE', 'DUSK', 'DUST', 'DUTY', 'EACH', 'EARL', 'EARN', 'EASE',
    'EAST', 'EASY', 'ECHO', 'EDGE', 'EDIT', 'EELS', 'ELSE', 'EMIT',
    'ENDS', 'EPIC', 'EVEN', 'EVER', 'EVIL', 'EXAM', 'EXEC', 'EXIT',
    'EYED', 'EYES', 'FACE', 'FACT', 'FADE', 'FAIL', 'FAIR', 'FAKE',
    'FALL', 'FAME', 'FANG', 'FARE', 'FARM', 'FAST', 'FATE', 'FAWN',
    'FEAR', 'FEAT', 'FEED', 'FEEL', 'FEET', 'FELL', 'FELT', 'FEND',
    'FERN', 'FEST', 'FILE', 'FILL', 'FILM', 'FIND', 'FINE', 'FIRE',
    'FIRM', 'FISH', 'FIST', 'FLAG', 'FLAIR', 'FLAP', 'FLAT', 'FLAW',
    'FLEA', 'FLED', 'FLEE', 'FLEW', 'FLEX', 'FLIP', 'FLIT', 'FLOCK',
    'FLOG', 'FLOW', 'FOAL', 'FOAM', 'FOIL', 'FOLD', 'FOLK', 'FOND',
    'FONT', 'FOOD', 'FOOL', 'FOOT', 'FORD', 'FORE', 'FORK', 'FORM',
    'FORT', 'FOUL', 'FOUR', 'FREE', 'FROG', 'FROM', 'FUEL', 'FULL',
    'FUME', 'FUND', 'FUSE', 'FUSS', 'GAIT', 'GALE', 'GALL', 'GAME',
    'GANG', 'GAPE', 'GARB', 'GATE', 'GAVE', 'GAZE', 'GEAR', 'GENE',
    'GIFT', 'GILD', 'GILL', 'GILT', 'GIST', 'GIVE', 'GLAD', 'GLEE',
    'GLEN', 'GLIB', 'GLOW', 'GLUE', 'GLUM', 'GLUT', 'GNAT', 'GNAW',
    'GOAD', 'GOAL', 'GOAT', 'GOES', 'GOLD', 'GOLF', 'GONE', 'GOOD',
    'GORE', 'GRAB', 'GRAD', 'GRAM', 'GRAY', 'GREW', 'GRID', 'GRIM',
    'GRIN', 'GRIP', 'GRIT', 'GROW', 'GULF', 'GULL', 'GULP', 'GURU',
    'GUST', 'GUTS', 'HACK', 'HAIL', 'HAIR', 'HALE', 'HALF', 'HALL',
    'HALT', 'HAND', 'HANG', 'HARE', 'HARK', 'HARM', 'HARP', 'HASH',
    'HASTE', 'HATE', 'HAUL', 'HAVE', 'HAZE', 'HAZY', 'HEAD', 'HEAL',
    'HEAP', 'HEAR', 'HEAT', 'HEED', 'HEEL', 'HELD', 'HELM', 'HELP',
    'HERB', 'HERD', 'HERE', 'HERO', 'HIDE', 'HIGH', 'HIKE', 'HILL',
    'HILT', 'HIND', 'HINT', 'HIRE', 'HIVE', 'HOARD', 'HOAX', 'HOLD',
    'HOLE', 'HOME', 'HONE', 'HOOD', 'HOOK', 'HOPE', 'HORN', 'HOSE',
    'HOST', 'HOUR', 'HOWL', 'HUGE', 'HULL', 'HUMP', 'HUNG', 'HUNT',
    'HURL', 'HURT', 'HUSH', 'HYMN', 'IDEA', 'IDLE', 'IDOL', 'INCH',
    'INTO', 'IRON', 'ISLE', 'ITEM', 'JADE', 'JAIL', 'JAPE', 'JAVA',
    'JAZZ', 'JEAN', 'JEST', 'JILT', 'JINX', 'JIVE', 'JOIN', 'JOKE',
    'JOLT', 'JOWL', 'JUDO', 'JUMP', 'JUNE', 'JUNK', 'JURY', 'JUST',
    'KEEN', 'KEEP', 'KELP', 'KEPT', 'KICK', 'KILL', 'KIND', 'KING',
    'KITE', 'KNACK', 'KNEE', 'KNEW', 'KNIT', 'KNOB', 'KNOT', 'KNOW',
    'LACE', 'LACK', 'LACY', 'LAID', 'LAIR', 'LAKE', 'LAME', 'LAMP',
    'LAND', 'LANE', 'LARD', 'LARK', 'LASH', 'LASS', 'LAST', 'LATE',
    'LAWN', 'LEAD', 'LEAF', 'LEAK', 'LEAN', 'LEAP', 'LEFT', 'LEND',
    'LENS', 'LENT', 'LESS', 'LEVY', 'LIAR', 'LICE', 'LICK', 'LIED',
    'LIEU', 'LIFE', 'LIFT', 'LIKE', 'LILY', 'LIMB', 'LIME', 'LIMP',
    'LINE', 'LINK', 'LINT', 'LION', 'LIST', 'LIVE', 'LOAD', 'LOAF',
    'LOAM', 'LOAN', 'LOCK', 'LODE', 'LOFT', 'LONE', 'LONG', 'LOOK',
    'LOOM', 'LOOP', 'LOOT', 'LORD', 'LORE', 'LOSE', 'LOSS', 'LOST',
    'LOUD', 'LOVE', 'LUCK', 'LULL', 'LUMP', 'LUNG', 'LURE', 'LURK',
    'LUSH', 'LUST', 'LYNX', 'MACE', 'MADE', 'MAID', 'MAIL', 'MAIN',
    'MAKE', 'MALE', 'MALL', 'MALT', 'MANE', 'MANY', 'MARE', 'MARK',
    'MARS', 'MASH', 'MASK', 'MASS', 'MAST', 'MATE', 'MATH', 'MAZE',
    'MEAD', 'MEAL', 'MEAN', 'MEAT', 'MEEK', 'MEET', 'MELD', 'MELT',
    'MEMO', 'MEND', 'MENU', 'MESA', 'MESH', 'MESS', 'MICA', 'MICE',
    'MILD', 'MILE', 'MILK', 'MILL', 'MIME', 'MIND', 'MINE', 'MINT',
    'MIRE', 'MISS', 'MIST', 'MITE', 'MITT', 'MOAN', 'MOAT', 'MOCK',
    'MODE', 'MOLD', 'MOLE', 'MOLT', 'MONK', 'MOOD', 'MOON', 'MOOR',
    'MOPE', 'MORE', 'MORN', 'MOSS', 'MOST', 'MOTH', 'MOVE', 'MUCH',
    'MUCK', 'MUFF', 'MULE', 'MULL', 'MURK', 'MUSE', 'MUSH', 'MUST',
    'MUTE', 'MYTH', 'NAIL', 'NAME', 'NAPE', 'NAVE', 'NAVY', 'NEAR',
    'NEAT', 'NECK', 'NEED', 'NEST', 'NEWS', 'NEXT', 'NICE', 'NINE',
    'NODE', 'NONE', 'NOON', 'NORM', 'NOSE', 'NOTE', 'NOUN', 'NUDE',
    'NUMB',
    # 5-letter words
    'ABODE', 'ABORT', 'ABOUT', 'ABOVE', 'ADAPT', 'ADEPT', 'ADMIT',
    'ADOPT', 'ADORE', 'ADULT', 'AFTER', 'AGAIN', 'AGENT', 'AGILE',
    'AGREE', 'AHEAD', 'AISLE', 'ALARM', 'ALBUM', 'ALERT', 'ALGAE',
    'ALIEN', 'ALIGN', 'ALIKE', 'ALIVE', 'ALLEY', 'ALLOT', 'ALLOW',
    'ALONE', 'ALONG', 'ALOOF', 'ALTER', 'AMAZE', 'AMPLE', 'ANGEL',
    'ANGER', 'ANGLE', 'ANGRY', 'ANIME', 'ANKLE', 'ANNEX', 'ANTIC',
    'APPLE', 'APPLY', 'ARENA', 'ARISE', 'ARMOR', 'AROMA', 'ASIDE',
    'ATLAS', 'ATONE', 'ATTIC', 'AUDIO', 'AUDIT', 'AVAIL', 'AVERT',
    'AVOID', 'AWAKE', 'AWARD', 'AWARE', 'BACON', 'BADGE', 'BARON',
    'BASIC', 'BASIN', 'BASIS', 'BATCH', 'BEACH', 'BEARD', 'BEAST',
    'BEGIN', 'BEING', 'BELOW', 'BENCH', 'BIRTH', 'BLACK', 'BLADE',
    'BLAME', 'BLAND', 'BLANK', 'BLAST', 'BLAZE', 'BLEAK', 'BLEED',
    'BLEND', 'BLESS', 'BLIND', 'BLISS', 'BLOCK', 'BLOND', 'BLOOD',
    'BLOOM', 'BLOWN', 'BOARD', 'BOAST', 'BONUS', 'BOOTH', 'BOUND',
    'BRAIN', 'BRAND', 'BRASS', 'BRAVE', 'BREAD', 'BREAK', 'BREED',
    'BRICK', 'BRIDE', 'BRIEF', 'BRINK', 'BRISK', 'BROAD', 'BROKE',
    'BROOK', 'BROOD', 'BROTH', 'BROWN', 'BRUSH', 'BUILD', 'BUILT',
    'BUNCH', 'BURST', 'BUYER', 'CABIN', 'CABLE', 'CAMEL', 'CANAL',
    'CANDY', 'CARGO', 'CARRY', 'CATCH', 'CATER', 'CAUSE', 'CEDAR',
    'CHAIN', 'CHAIR', 'CHALK', 'CHANT', 'CHARM', 'CHART', 'CHASE',
    'CHEAP', 'CHEAT', 'CHECK', 'CHEEK', 'CHEER', 'CHESS', 'CHEST',
    'CHIEF', 'CHILD', 'CHILL', 'CHINA', 'CHOIR', 'CHORD', 'CHOSE',
    'CHUNK', 'CLAIM', 'CLASH', 'CLASP', 'CLASS', 'CLEAN', 'CLEAR',
    'CLERK', 'CLICK', 'CLIFF', 'CLIMB', 'CLING', 'CLOCK', 'CLONE',
    'CLOSE', 'CLOTH', 'CLOUD', 'CLOWN', 'COACH', 'COAST', 'COLOR',
    'COMET', 'COMIC', 'CORAL', 'COUNT', 'COUCH', 'COULD', 'COURT',
    'COVER', 'CRACK', 'CRAFT', 'CRANE', 'CRASH', 'CRAWL', 'CRAZE',
    'CRAZY', 'CREAK', 'CREAM', 'CREST', 'CRIME', 'CRISP', 'CROSS',
    'CROWD', 'CROWN', 'CRUEL', 'CRUSH', 'CRUST', 'CUBIC', 'CURVE',
    'CYCLE', 'DAILY', 'DANCE', 'DEATH', 'DEBUT', 'DECAY', 'DECOR',
    'DECOY', 'DELAY', 'DELTA', 'DEMON', 'DENSE', 'DEPOT', 'DEPTH',
    'DERBY', 'DESKS', 'DETER', 'DIARY', 'DIGIT', 'DINER', 'DIRTY',
    'DISCO', 'DITCH', 'DIZZY', 'DODGE', 'DONOR', 'DOUBT', 'DOUGH',
    'DRAFT', 'DRAIN', 'DRAKE', 'DRAMA', 'DRANK', 'DRAPE', 'DRAWN',
    'DREAD', 'DREAM', 'DRESS', 'DRIED', 'DRIFT', 'DRILL', 'DRINK',
    'DRIVE', 'DROIT', 'DRONE', 'DROOL', 'DROPS', 'DROWN', 'DRUNK',
    'DRYER', 'DULLY', 'DWARF', 'DWELL', 'DYING', 'EAGER', 'EAGLE',
    'EARLY', 'EARTH', 'EASEL', 'EATEN', 'EATER', 'EDICT', 'EIGHT',
    'ELBOW', 'ELDER', 'ELECT', 'ELITE', 'ELUDE', 'EMAIL', 'EMBER',
    'EMPTY', 'ENDED', 'ENDOW', 'ENEMY', 'ENJOY', 'ENTER', 'ENTRY',
    'ENVOY', 'EQUAL', 'EQUIP', 'ERASE', 'ERODE', 'ERROR', 'ESSAY',
    'ETHER', 'ETHIC', 'EVADE', 'EVENT', 'EVERY', 'EVICT', 'EXACT',
    'EXALT', 'EXCEL', 'EXERT', 'EXILE', 'EXIST', 'EXPEL', 'EXTRA',
    'FABLE', 'FACET', 'FAITH', 'FALSE', 'FANCY', 'FATAL', 'FAUNA',
    'FEAST', 'FENCE', 'FERRY', 'FETCH', 'FEVER', 'FIBER', 'FIELD',
    'FIEND', 'FIFTY', 'FIGHT', 'FINAL', 'FINER', 'FIRST', 'FLAME',
    'FLANK', 'FLARE', 'FLASH', 'FLASK', 'FLEET', 'FLESH', 'FLICK',
    'FLIER', 'FLING', 'FLINT', 'FLOAT', 'FLOCK', 'FLOOD', 'FLOOR',
    'FLORA', 'FLOSS', 'FLOUR', 'FLOWN', 'FLUID', 'FLUKE', 'FLUSH',
    'FLUTE', 'FOCAL', 'FOCUS', 'FOGGY', 'FORCE', 'FORGE', 'FORTY',
    'FORUM', 'FOUND', 'FRAME', 'FRANK', 'FRAUD', 'FRESH', 'FRONT',
    'FROST', 'FROZE', 'FRUIT', 'FULLY', 'FUNGI', 'FUNNY', 'FUZZY',
    # 6-letter words
    'ABSORB', 'ACCENT', 'ACCEPT', 'ACCESS', 'ACROSS', 'ACTING',
    'ACTION', 'ACTIVE', 'ACTUAL', 'ADVENT', 'ADVICE', 'ADVISE',
    'AERIAL', 'AFFAIR', 'AFFIRM', 'AFFORD', 'AGENDA', 'ALMOST',
    'ANCHOR', 'ANIMAL', 'ANNUAL', 'ANSWER', 'ANYONE', 'APPEAL',
    'APPEAR', 'ARCHER', 'ARCTIC', 'ARRIVE', 'ARTIST', 'ASPECT',
    'ASSERT', 'ASSIGN', 'ASSIST', 'ASSUME', 'ASSURE', 'ATTAIN',
    'ATTEND', 'AUTUMN', 'AVENUE', 'BALLOT', 'BANDIT', 'BANNER',
    'BASKET', 'BATTLE', 'BEACON', 'BISHOP', 'BLANCH', 'BLOUSE',
    'BONNET', 'BORDER', 'BORROW', 'BOTANY', 'BOUNCE', 'BRANCH',
    'BREACH', 'BREATH', 'BREEZE', 'BRIDGE', 'BRIGHT', 'BRONZE',
    'BUBBLE', 'BUCKET', 'BUDGET', 'BUFFET', 'BUNDLE', 'BURDEN',
    'BUREAU', 'BUTTER', 'BUTTON', 'CACTUS', 'CANDLE', 'CANVAS',
    'CARBON', 'CARPET', 'CASTLE', 'CASUAL', 'CATTLE', 'CAUSAL',
    'CEASED', 'CEMENT', 'CENSUS', 'CHANCE', 'CHANGE', 'CHARGE',
    'CHOSEN', 'CHROME', 'CIRCLE', 'CIRCUS', 'CLAUSE', 'CLEVER',
    'CLIENT', 'CLOSET', 'COBALT', 'COFFEE', 'COLONY', 'COLUMN',
    'COMBAT', 'COMEDY', 'COMMON', 'COMMIT', 'COMPLY', 'CONVEX',
    'COOKIE', 'CORNER', 'COSMIC', 'COTTON', 'COURSE', 'COUSIN',
    'CRADLE', 'CREATE', 'CREDIT', 'CRISIS', 'CUSTOM', 'DAGGER',
    'DAMAGE', 'DAMPEN', 'DANCER', 'DANGER', 'DARING', 'DEBATE',
    'DECADE', 'DECENT', 'DECIDE', 'DECODE', 'DECREE', 'DEFEAT',
    'DEFEND', 'DEFINE', 'DEGREE', 'DELETE', 'DELUXE', 'DEMAND',
    'DENIAL', 'DEPLOY', 'DEPTH', 'DEPUTY', 'DERIVE', 'DESERT',
    'DESIGN', 'DESIRE', 'DETAIL', 'DETECT', 'DEVICE', 'DEVOTE',
    'DIESEL', 'DIFFER', 'DIGEST', 'DINNER', 'DIRECT', 'DISARM',
    'DIVIDE', 'DIVINE', 'DOMAIN', 'DONATE', 'DOUBLE', 'DRAGON',
    'DRAWER', 'DRIVER', 'DROUGHT', 'DUPLEX', 'DURING', 'EASILY',
    'EATING', 'EDITOR', 'EFFECT', 'EFFORT', 'EIGHTH', 'ELEVEN',
    'EMERGE', 'EMPIRE', 'ENABLE', 'ENDURE', 'ENERGY', 'ENGAGE',
    'ENGINE', 'ENOUGH', 'ENSURE', 'ENTIRE', 'ENTITY', 'ERRAND',
    'ESCAPE', 'ESPRIT', 'ESTATE', 'ESTEEM', 'ETHICS', 'EVOLVE',
    'EXCEED', 'EXCEPT', 'EXCESS', 'EXCITE', 'EXCUSE', 'EXEMPT',
    'EXHALE', 'EXPAND', 'EXPECT', 'EXPERT', 'EXPORT', 'EXPOSE',
    'EXTEND', 'EXTENT', 'FABRIC', 'FACIAL', 'FACTOR', 'FALCON',
    'FAMINE', 'FAMOUS', 'FATHOM', 'FELINE', 'FELLOW', 'FIGURE',
    'FILTER', 'FINALE', 'FINGER', 'FINISH', 'FISCAL', 'FLAVOR',
    'FLIGHT', 'FLOWER', 'FLYING', 'FOLLOW', 'FORBID', 'FORCED',
    'FOREST', 'FORGET', 'FORMAL', 'FORMAT', 'FORMER', 'FOSSIL',
    'FOSTER', 'FOURTH', 'FREEZE', 'FRENZY', 'FRIDGE', 'FRIEND',
    'FROZEN', 'FUTILE', 'FUTURE', 'GALAXY', 'GALLON', 'GAMBLE',
    'GARAGE', 'GARDEN', 'GARLIC', 'GATHER', 'GAZING', 'GENTLY',
    'GLOBAL', 'GLOSSY', 'GOVERN', 'GRAVEL', 'GROUND', 'GROWTH',
    # 8-letter words
    'ABSOLUTE', 'ABSTRACT', 'ACADEMIC', 'ACCURATE', 'ACHIEVED', 'ACQUIRED',
    'ACTIVELY', 'ACTUALLY', 'ADDITION', 'ADEQUATE', 'ADJUSTED', 'ADMITTED',
    'ADVANCED', 'ADVISORY', 'ADVOCATE', 'AFFECTED', 'AFFORDED', 'AIRPLANE',
    'ALLIANCE', 'ALTHOUGH', 'ALTITUDE', 'ALUMINUM', 'AMBITION', 'ANALYSIS',
    'ANCESTOR', 'ANNOUNCE', 'ANNUALLY', 'ANSWERED', 'ANYTHING', 'ANYWHERE',
    'APPARENT', 'APPETITE', 'APPLAUSE', 'APPROACH', 'APPROVAL', 'ARGUMENT',
    'ARTISTIC', 'ASSEMBLY', 'ASSUMING', 'ATHLETIC', 'ATTACHED', 'ATTACKED',
    'ATTAINED', 'ATTORNEY', 'AUDIENCE', 'BACKWARD', 'BALANCED', 'BANKRUPT',
    'BATHROOM', 'BECOMING', 'BEFRIEND', 'BEHAVIOR', 'BELIEVED', 'BELONGED',
    'BETRAYAL', 'BIRTHDAY', 'BLANKETS', 'BLEEDING', 'BLESSING', 'BLOCKING',
    'BORROWED', 'BOUNDARY', 'BREAKING', 'BREEDING', 'BRIEFING', 'BRINGING',
    'BROTHERS', 'BROWSING', 'BUILDING', 'BULLETIN', 'BUSINESS', 'CALENDAR',
    'CAMPAIGN', 'CAPTURED', 'CARDINAL', 'CARELESS', 'CARNIVAL', 'CARRYING',
    'CASUALTY', 'CATCHING', 'CATEGORY', 'CATERING', 'CAUTIOUS', 'CEREMONY',
    'CHAIRMAN', 'CHAMPION', 'CHANGING', 'CHAPTERS', 'CHARMING', 'CHEAPEST',
    'CHEERFUL', 'CHEMICAL', 'CHILDREN', 'CHOOSING', 'CIRCULAR', 'CITATION',
    'CIVILIAN', 'CLAIMING', 'CLEANING', 'CLEAREST', 'CLIMBING', 'CLINICAL',
    'CLOTHING', 'COACHING', 'COCKTAIL', 'COLLAPSE', 'COLONIAL', 'COLORFUL',
    'COMBINED', 'COMEBACK', 'COMEDIAN', 'COMMONLY', 'COMMUNAL', 'COMPARED',
    'COMPETES', 'COMPLETE', 'COMPOSED', 'COMPOUND', 'COMPUTER', 'CONCEIVE',
    'CONCLUDE', 'CONCRETE', 'CONFRONT', 'CONFUSED', 'CONGRESS', 'CONQUEST',
    'CONSIDER', 'CONSISTS', 'CONSTANT', 'CONSUMED', 'CONSUMER', 'CONTAINS',
    'CONTEMPT', 'CONTINUE', 'CONTRACT', 'CONTRAST', 'CONTROLS', 'CONVINCE',
    'COOKBOOK', 'CORRIDOR', 'COUNTING', 'COUNTIES', 'COUPLING', 'COURTESY',
    'COVERAGE', 'COVERING', 'COWARDLY', 'CRASHING', 'CREATION', 'CREATIVE',
    'CREATURE', 'CRIMINAL', 'CRITICAL', 'CROSSING', 'CULTURAL', 'CURRENCY',
    'CUSTOMER', 'CYLINDER', 'DARKNESS', 'DATABASE', 'DAUGHTER', 'DEADLINE',
    'DEALINGS', 'DECEMBER', 'DECIDING', 'DECISION', 'DECLARED', 'DECREASE',
    'DEFEATED', 'DEFENDER', 'DEFINITE', 'DELICATE', 'DELIVERY', 'DEMANDED',
    'DEMOCRAT', 'DEMOLISH', 'DEPARTED', 'DEPICTED', 'DEPLETED', 'DEPLOYED',
    'DEPRIVED', 'DESCRIBE', 'DESIGNER', 'DETAILED', 'DETECTED', 'DEVOTION',
    'DIAGONAL', 'DIALOGUE', 'DIAMONDS', 'DICTATOR', 'DIFFERED', 'DIPLOMAT',
    'DIRECTED', 'DIRECTOR', 'DISABLED', 'DISAGREE', 'DISASTER', 'DISCLOSE',
    'DISCOUNT', 'DISCOVER', 'DISCRETE', 'DISORDER', 'DISPATCH', 'DISPOSAL',
    'DISPOSED', 'DISTANCE', 'DISTINCT', 'DISTRICT', 'DIVIDEND', 'DIVISION',
    'DOCTRINE', 'DOCUMENT', 'DOMESTIC', 'DOMINANT', 'DONATION', 'DOORSTEP',
    'DOUBTFUL', 'DOWNLOAD', 'DOWNTOWN', 'DRAMATIC', 'DREADFUL', 'DRESSING',
    'DRINKING', 'DROPPING', 'DURATION', 'DWELLING', 'DYNAMICS', 'EARNINGS',
    'ECONOMIC', 'EDUCATED', 'EDUCATOR', 'EIGHTEEN', 'ELECTION', 'ELEGANCE',
    'ELEVATOR', 'ELIGIBLE', 'EMBEDDED', 'EMERGING', 'EMISSION', 'EMOTIONS',
    'EMPHASIS', 'EMPLOYED', 'EMPLOYEE', 'EMPLOYER', 'ENABLING', 'ENCLOSED',
    'ENCODING', 'ENORMOUS', 'ENROLLED', 'ENSEMBLE', 'ENTERING', 'ENTIRELY',
    'ENTITLED', 'ENTRANCE', 'ENVELOPE', 'EQUIPPED', 'ESCALATE', 'ESTIMATE',
    'EVALUATE', 'EVENTUAL', 'EVIDENCE', 'EXAMINED', 'EXAMPLES', 'EXCEEDED',
    'EXCHANGE', 'EXCITING', 'EXCLUDED', 'EXERCISE', 'EXISTING', 'EXPANDED',
    'EXPECTED', 'EXPENSES', 'EXPLICIT', 'EXPLORED', 'EXPLORER', 'EXPORTED',
    'EXTENDED', 'EXTERNAL', 'EXTRACTS', 'EXTREMES', 'FABULOUS', 'FACILITY',
    'FAITHFUL', 'FAMILIES', 'FAMILIAR', 'FAREWELL', 'FEATURED', 'FEATURES',
    'FEBRUARY', 'FEEDBACK', 'FESTIVAL', 'FIGHTING', 'FINALIST', 'FINANCES',
    'FINDINGS', 'FINISHED', 'FIREARMS', 'FLAGSHIP', 'FLEXIBLE', 'FLOATING',
    'FLOODING', 'FLOURISH', 'FOCUSING', 'FOLLOWED', 'FOLLOWER', 'FOOTBALL',
    'FORECAST', 'FOREMOST', 'FORGIVEN', 'FORMALLY', 'FORMERLY', 'FORTRESS',
    'FOURTEEN', 'FRACTION', 'FRAGMENT', 'FRANKLIN', 'FREEZING', 'FREQUENT',
    'FRIENDLY', 'FRONTIER', 'FRUITFUL', 'FUNCTION', 'FURTHEST', 'GAMBLING',
    'GARMENTS', 'GATHERED', 'GENERATE', 'GENEROUS', 'GLANCING', 'GLOBALLY',
    'GORGEOUS', 'GOVERNED', 'GOVERNOR', 'GRACEFUL', 'GRACIOUS', 'GRADUATE',
    'GRAPHICS', 'GRATEFUL', 'GRIPPING', 'GROUNDED', 'GUARDIAN', 'GUIDANCE',
    'HABITUAL', 'HALLMARK', 'HANDBOOK', 'HANDLING', 'HANDSOME', 'HAPPENED',
    'HARDWARE', 'HARMLESS', 'HAUNTING', 'HEADLINE', 'HEAVENLY', 'HERITAGE',
    'HESITANT', 'HIGHLAND', 'HIGHWAYS', 'HISTORIC', 'HOMEPAGE', 'HOMEWORK',
    'HONESTLY', 'HONORARY', 'HOPELESS', 'HORIZONS', 'HORRIBLE', 'HORRIFIC',
    'HOSPITAL', 'HUMANITY', 'HUNDREDS', 'HYDROGEN', 'IDENTITY', 'IGNORANT',
    'ILLUSION', 'IMAGINED', 'IMMATURE', 'IMMUNITY', 'IMPERIAL', 'IMPLICIT',
    'IMPORTED', 'IMPOSING', 'IMPROVED', 'INCIDENT', 'INCLUDED', 'INCREASE',
    'INDICATE', 'INDIRECT', 'INDUSTRY', 'INFERIOR', 'INFINITE', 'INFORMED',
    'INHERENT', 'INNOCENT', 'INNOVATE', 'INSPIRED', 'INSTANCE', 'INSTINCT',
    'INTENDED', 'INTERACT', 'INTEREST', 'INTERIOR', 'INTERNAL', 'INTERNET',
    'INTERVAL', 'INTIMATE', 'INVENTED', 'INVESTED', 'INVESTOR', 'INVOLVES',
    'ISOLATED', 'JUDGMENT', 'KEYBOARD', 'KINDNESS', 'KNOCKING', 'LABELING',
    'LANGUAGE', 'LAUGHING', 'LAUNCHED', 'LAWFULLY', 'LEARNING', 'LEFTOVER',
    'LEVERAGE', 'LIFETIME', 'LIGHTING', 'LIKEWISE', 'LIMITING', 'LISTENER',
    'LITERACY', 'LITERARY', 'LITIGANT', 'LOCATION', 'LONESOME', 'LONGTIME',
    'LOUDNESS', 'LOYALTY', 'MAGNETIC', 'MAINTAIN', 'MAJORITY', 'MANAGING',
    'MANIFEST', 'MANIPULATE', 'MANUALLY', 'MARATHON', 'MARGINAL', 'MARRIAGE',
    'MATERIAL', 'MATURITY', 'MAXIMIZE', 'MEASURED', 'MECHANIC', 'MEDICINE',
    'MEDIEVAL', 'MEMBRANE', 'MEMORIAL', 'MERCHANT', 'METAPHOR', 'MIDNIGHT',
    'MILITANT', 'MILITARY', 'MINIMIZE', 'MINISTER', 'MINISTRY', 'MINORITY',
    'MODERATE', 'MODELING', 'MOMENTUM', 'MONARCHY', 'MONETARY', 'MONUMENT',
    'MORTGAGE', 'MOVEMENT', 'MULTIPLE', 'MULTIPLY', 'MURDERED', 'MUSCULAR',
    'MUTATION', 'MYSTICAL', 'NATIONAL', 'NAVIGATE', 'NEGATIVE', 'NEIGHBOR',
    'NETWORKS', 'NORMALLY', 'NORTHERN', 'NOTEBOOK', 'NUMEROUS', 'OBSTACLE',
    'OBTAINED', 'OCCUPIED', 'OCCURRED', 'OFFERING', 'OFFICIAL', 'OFFSHORE',
    'ONCOLOGY', 'OPENINGS', 'OPERATED', 'OPERATOR', 'OPPONENT', 'OPPOSITE',
    'OPTIMISM', 'OPTIONAL', 'ORDERING', 'ORDINARY', 'ORGANIZE', 'ORIGINAL',
    'OUTDOORS', 'OUTLINED', 'OUTREACH', 'OVERCOME', 'OVERLOOK', 'OVERSEAS',
    'PAINTING', 'PAMPHLET', 'PANORAMA', 'PARALLEL', 'PARENTAL', 'PARTICLE',
    'PASSIONS', 'PATIENCE', 'PEACEFUL', 'PECULIAR', 'PEDALING', 'PENALIZE',
    'PENDULUM', 'PERCEIVE', 'PERSONAL', 'PETITION', 'PHYSICAL', 'PILOTING',
    'PIPELINE', 'PLATFORM', 'PLEASANT', 'PLEASURE', 'PLUNGING', 'POINTED',
    'POLISHED', 'POLITELY', 'POLITICS', 'POPULACE', 'PORTRAIT', 'POSITION',
    'POSITIVE', 'POSSIBLE', 'POWERFUL', 'PRACTICE', 'PRECIOUS', 'PREDATOR',
    'PRESSING', 'PRESTIGE', 'PRESUMED', 'PRETENDS', 'PREVIOUS', 'PRINCESS',
    'PRINTING', 'PRIORITY', 'PROBABLE', 'PROBABLY', 'PRODUCED', 'PRODUCER',
    'PROFOUND', 'PROGRESS', 'PROJECTS', 'PROLIFIC', 'PROMISED', 'PROMPTLY',
    'PROPERLY', 'PROPERTY', 'PROPOSAL', 'PROPOSED', 'PROSPECT', 'PROSPER',
    'PROTOCOL', 'PROVIDED', 'PROVIDER', 'PROVINCE', 'PUBLICLY', 'PUNISHED',
    'PURCHASE', 'PURSUING', 'PUZZLING', 'QUALIFIES', 'QUARTERS', 'RAILROAD',
    'RANDOMLY', 'REACHING', 'REACTION', 'READABLE', 'REALIZED', 'REASONED',
    'RECEIVED', 'RECENTLY', 'RECKONED', 'RECLINED', 'RECORDED', 'RECOVERY',
    'REDUCING', 'REFERRAL', 'REFERRED', 'REFORMED', 'REGIONAL', 'REGISTER',
    'REGULATE', 'REJECTED', 'RELATING', 'RELATION', 'RELATIVE', 'RELEASED',
    'RELEVANT', 'RELIABLE', 'RELIEVED', 'RELIGION', 'REMAINED', 'REMEMBER',
    'REMINDER', 'RENDERED', 'RENOWNED', 'REPORTED', 'REPORTER', 'REPUBLIC',
    'REQUIRED', 'RESEARCH', 'RESERVED', 'RESIGNED', 'RESOLVED', 'RESOURCE',
    'RESPONDS', 'RESPONSE', 'RESTORED', 'RETAILER', 'RETAINED', 'RETIRING',
    'RETRIEVE', 'REVEALED', 'REVERSED', 'REVIEWED', 'REVISION', 'REVOLTED',
    'RHETORIC', 'RIGOROUS', 'ROMANTIC', 'SAMPLING', 'SANDWICH', 'SCENARIO',
    'SCHEDULE', 'SCHOLARS', 'SCIENCES', 'SCOTLAND', 'SEASONAL', 'SECONDLY',
    'SECURING', 'SECURITY', 'SELECTED', 'SEMESTER', 'SENTENCE', 'SEPARATE',
    'SEQUENCE', 'SERGEANT', 'SERVICES', 'SESSIONS', 'SETTINGS', 'SETTLING',
    'SEVERELY', 'SHIPPING', 'SHOCKING', 'SHORTAGE', 'SHOULDER', 'SIDEWALK',
    'SIGNALED', 'SILENTLY', 'SIMPLEST', 'SIMULATE', 'SITUATED', 'SKELETAL',
    'SLEEPING', 'SLIGHTLY', 'SMALLEST', 'SMOOTHLY', 'SNEAKERS', 'SOCIALLY',
    'SOFTWARE', 'SOLDIERS', 'SOMEWHAT', 'SOUTHERN', 'SPEAKING', 'SPECIFIC',
    'SPENDING', 'SPIRITED', 'SPLENDID', 'SPORTING', 'STANDARD', 'STANDING',
    'STARTING', 'STATIONS', 'STEADILY', 'STEERING', 'STEPPING', 'STIMULUS',
    'STOPPING', 'STRAIGHT', 'STRANGER', 'STRATEGY', 'STRENGTH', 'STRICTLY',
    'STRIKING', 'STRONGER', 'STRONGLY', 'STRUGGLE', 'STUDYING', 'STUNNING',
    'SUBJECTS', 'SUBURBAN', 'SUDDENLY', 'SUFFERED', 'SUGGESTS', 'SUITABLE',
    'SUNLIGHT', 'SUPERIOR', 'SUPPLIED', 'SUPPLIER', 'SUPPORTS', 'SUPPOSED',
    'SUPPRESS', 'SURGICAL', 'SURPRISE', 'SURROUND', 'SURVIVAL', 'SUSPENSE',
    'SWEEPING', 'SWIMMING', 'SWITCHED', 'SYLLABLE', 'SYMBOLIC', 'SYMPATHY',
    'SYNDROME', 'TACTICAL', 'TAKEAWAY', 'TALENTED', 'TEACHING', 'TEAMMATE',
    'TEAMWORK', 'TERMINAL', 'TERRIFIC', 'THANKFUL', 'THEATERS', 'THINKING',
    'THOROUGH', 'THOUSAND', 'THRILLER', 'TOPOLOGY', 'TOUCHING', 'TRACKING',
    'TRAINING', 'TRANSFER', 'TRANSMIT', 'TRAVELED', 'TREASURE', 'TREATING',
    'TRIBUNAL', 'TROPICAL', 'TROUBLED', 'TUTORIAL', 'THIRTEEN', 'UMBRELLA',
    'UNCOMMON', 'UNDERWAY', 'UNIVERSE', 'UNLIKELY', 'UNLOCKED', 'UNNOTICE',
    'UPCOMING', 'UPDATING', 'UPLIFTD', 'URBANIZE', 'UTILIZED', 'VACATION',
    'VALIDATE', 'VALUABLE', 'VARIABLE', 'VENTURES', 'VETERANS', 'VIOLENCE',
    'VIRGINIA', 'VIRTUOUS', 'VOLCANIC', 'VOLATILE', 'WHATEVER', 'WHENEVER',
    'WHEREVER', 'WILDFIRE', 'WILDLIFE', 'WINDMILL', 'WIRELESS', 'WITHDRAW',
    'WITHHELD', 'WIZARDRY', 'WONDERED', 'WOODLAND', 'WORKSHOP', 'WOULDN',
    'YEARBOOK', 'YIELDING',
    # 7+ letter words
    'ABANDON', 'ABILITY', 'ABOLISH', 'ABSENCE', 'ABSOLVE', 'ABSTAIN',
    'ACADEMY', 'ACCOUNT', 'ACHIEVE', 'ACQUIRE', 'ADDRESS', 'ADJOURN',
    'ADMIRAL', 'ADVANCE', 'ADVERSE', 'AFFABLE', 'AGILITY', 'AILMENT',
    'AIRPORT', 'ALCHEMY', 'ALGEBRA', 'ALMANAC', 'ALREADY', 'AMAZING',
    'AMBIENT', 'AMPLIFY', 'ANALYST', 'ANATOMY', 'ANCIENT', 'ANGULAR',
    'ANTENNA', 'ANXIETY', 'ANYTIME', 'APERTURE', 'APPAREL', 'APPLIED',
    'ARRANGE', 'ARTICLE', 'ASHAMED', 'ASSAULT', 'ATTEMPT', 'ATTRACT',
    'AUCTION', 'AUDIBLE', 'AUSTERE', 'AVERAGE', 'BALANCE', 'BALLOON',
    'BARGAIN', 'BARRIER', 'BATTERY', 'BEARING', 'BECAUSE', 'BEDROOM',
    'BELIEVE', 'BENEATH', 'BENEFIT', 'BETWEEN', 'BILLION', 'BLANKET',
    'BLOSSOM', 'BORDERS', 'BOULDER', 'BREATHE', 'CABINET', 'CALCIUM',
    'CALIBER', 'CAMPING', 'CAPABLE', 'CAPITAL', 'CAPTAIN', 'CAPTURE',
    'CAUTION', 'CENTRAL', 'CENTURY', 'CERAMIC', 'CERTAIN', 'CHAMBER',
    'CHANNEL', 'CHAPTER', 'CHARIOT', 'CHARITY', 'CHARTER', 'CHIMNEY',
    'CIRCUIT', 'CITIZEN', 'CLARIFY', 'CLASSIC', 'CLIMATE', 'CLUSTER',
    'COASTAL', 'COLLECT', 'COLLEGE', 'COMFORT', 'COMMAND', 'COMMENT',
    'COMPACT', 'COMPARE', 'COMPEL', 'COMPETE', 'COMPLEX', 'COMPOSE',
    'CONCEPT', 'CONCERN', 'CONDUCT', 'CONFIRM', 'CONFUSE', 'CONNECT',
    'CONSENT', 'CONSIST', 'CONSULT', 'CONTACT', 'CONTAIN', 'CONTENT',
    'CONTEST', 'CONTEXT', 'CONTROL', 'CONVERT', 'COOKING', 'CORRECT',
    'COSTUME', 'COTTAGE', 'COUNCIL', 'COUNTER', 'COUNTRY', 'COURAGE',
    'CREATOR', 'CRUCIAL', 'CRYSTAL', 'CULTURE', 'CURRENT', 'CURTAIN',
    'CUSHION', 'CUSTOMS', 'DAMAGED', 'DEALING', 'DEFAULT', 'DEFENCE',
    'DEFICIT', 'DELIGHT', 'DELIVER', 'DENSITY', 'DEPOSIT', 'DESSERT',
    'DESTINY', 'DESTROY', 'DEVOTED', 'DIALECT', 'DIAMOND', 'DIGITAL',
    'DIGNITY', 'DILEMMA', 'DIPLOMA', 'DISABLE', 'DISCARD', 'DISCUSS',
    'DISEASE', 'DISGUST', 'DISMISS', 'DISPLAY', 'DISPUTE', 'DISTURB',
    'DIVERSE', 'DONATED', 'DRAWING', 'DURABLE', 'DYNAMIC', 'EARNEST',
    'ECONOMY', 'EDITION', 'EDUCATE', 'ELEGANT', 'ELEMENT', 'ELEVATE',
    'EMPEROR', 'EMPOWER', 'ENDLESS', 'ENFORCE', 'ENHANCE', 'EPISODE',
    'ESSENCE', 'ETERNAL', 'EVENING', 'EVIDENT', 'EXAMINE', 'EXAMPLE',
    'EXCITED', 'EXECUTE', 'EXHIBIT', 'EXPENSE', 'EXPLAIN', 'EXPLOIT',
    'EXPLORE', 'EXPOSED', 'EXPRESS', 'EXTREME', 'FASHION', 'FEATURE',
    'FICTION', 'FIFTEEN', 'FINANCE', 'FISHERY', 'FITNESS', 'FLAVOUR',
    'FLORIDA', 'FOOLISH', 'FOREIGN', 'FOREVER', 'FORMULA', 'FORTUNE',
    'FORWARD', 'FOUNDED', 'FREEDOM', 'FREIGHT', 'FULFILL', 'FUNERAL',
    'FURTHER', 'GALLERY', 'GENERAL', 'GENUINE', 'GESTURE', 'GLIMPSE',
    'GOODNESS', 'GRADUAL', 'GRAVITY', 'GROCERY', 'HABITAT', 'HANDFUL',
    'HARBOUR', 'HARMONY', 'HARVEST', 'HEADING', 'HEALTHY', 'HEATING',
    'HEAVILY', 'HELPFUL', 'HEROISM', 'HIGHWAY', 'HIMSELF', 'HISTORY',
    'HOLIDAY', 'HORIZON', 'HOSTILE', 'HOUSING', 'HOWEVER', 'IMAGINE',
    'IMMENSE', 'IMPEACH', 'IMPLORE', 'IMPRESS', 'IMPULSE', 'INCLUDE',
    'INFLICT', 'INHABIT', 'INHERIT', 'INITIAL', 'INQUIRE', 'INSIGHT',
    'INSPECT', 'INSTALL', 'INSTANT', 'INTEGER', 'INTENSE', 'INTERIM',
    'INTERNS', 'INVOLVE', 'ISOLATE', 'JANITOR', 'JOURNAL', 'JOURNEY',
    'JUSTICE', 'JUSTIFY', 'KEYNOTE', 'KINGDOM', 'KITCHEN', 'LANDING',
    'LASTING', 'LATERAL', 'LEADING', 'LEARNED', 'LECTURE', 'LEISURE',
    'LIBERTY', 'LIBRARY', 'LIMITED', 'LOGICAL', 'LUGGAGE', 'MACHINE',
    'MANAGER', 'MANDATE', 'MANSION', 'MARTIAL', 'MASSIVE', 'MASTERY',
    'MEASURE', 'MEDICAL', 'MEETING', 'MENTION', 'MINERAL', 'MINIMUM',
    'MIRACLE', 'MISSION', 'MIXTURE', 'MONITOR', 'MONSTER', 'MONTHLY',
    'MORNING', 'MYSTERY', 'NATURAL', 'NEITHER', 'NETWORK', 'NEUTRAL',
    'NOTABLE', 'NOTHING', 'NUCLEAR', 'NUMERAL', 'NURTURE', 'OBVIOUS',
    'OFFENSE', 'OFFICER', 'OPERATE', 'OPINION', 'ORGANIC', 'OUTCOME',
    'OUTDOOR', 'OUTLINE', 'OUTLOOK', 'OVERALL', 'PAINTER', 'PAINFUL',
    'PARKING', 'PARTIAL', 'PARTNER', 'PASSAGE', 'PASSING', 'PATIENT',
    'PATTERN', 'PENALTY', 'PERCENT', 'PERFECT', 'PERFORM', 'PERSIST',
    'PICTURE', 'PIONEER', 'PLASTIC', 'PLASTER', 'PLAYOFF', 'PLEASANT',
    'PLENARY', 'POINTED', 'POLITIC', 'POLLUTE', 'POPULAR', 'PORTION',
    'POTTERY', 'POVERTY', 'PRECISE', 'PREDICT', 'PREMIER', 'PREMIUM',
    'PREPARE', 'PRESENT', 'PREVENT', 'PRIMARY', 'PRINTER', 'PRIVACY',
    'PRIVATE', 'PROBLEM', 'PROCEED', 'PROCESS', 'PRODUCE', 'PRODUCT',
    'PROFILE', 'PROGRAM', 'PROJECT', 'PROMISE', 'PROMOTE', 'PROLONG',
    'PROSPER', 'PROTECT', 'PROTEIN', 'PROTEST', 'PROVIDE', 'PROVOKE',
    'PUBLISH', 'PURSUIT', 'QUALIFY', 'QUALITY', 'QUANTUM', 'QUARTER',
    'RADICAL', 'RAILWAY', 'REALISE', 'REALIZE', 'RECEIPT', 'RECEIVE',
    'RECOVER', 'RECRUIT', 'REFLECT', 'REFUGEE', 'REGULAR', 'RELATED',
    'RELEASE', 'REMAINS', 'REMOVAL', 'RENEWAL', 'REPLACE', 'REPLICA',
    'REQUEST', 'REQUIRE', 'RESERVE', 'RESOLVE', 'RESPECT', 'RESPOND',
    'RESTORE', 'RESULTS', 'RETREAT', 'REUNION', 'REVENUE', 'REVERSE',
    'REVOLVE', 'ROUTINE', 'ROYALTY', 'RUSHING', 'SAILING', 'SATISFY',
    'SCATTER', 'SCHOLAR', 'SCIENCE', 'SECTION', 'SEGMENT', 'SERIOUS',
    'SERVICE', 'SESSION', 'SETTING', 'SEVERAL', 'SHELTER', 'SILENCE',
    'SIMILAR', 'SITUATE', 'SKILLED', 'SOCIETY', 'SOLDIER', 'SOMEHOW',
    'SPEAKER', 'SPECIAL', 'SPONSOR', 'STADIUM', 'STATION', 'STORAGE',
    'STRANGE', 'SUBJECT', 'SUCCESS', 'SUGGEST', 'SUMMARY', 'SUPPORT',
    'SURFACE', 'SURGEON', 'SURPLUS', 'SURVIVE', 'SUSPECT', 'SUSTAIN',
    'TEACHER', 'TENSION', 'TERRIFY', 'THEATER', 'THERAPY', 'THERMAL',
    'THOUGHT', 'TICKETS', 'TONIGHT', 'TOURISM', 'TRAFFIC', 'TRAINER',
    'TRANSIT', 'TROUBLE', 'TURNING', 'TYPICAL', 'UNDERGO', 'UNIFORM',
    'UNKNOWN', 'UNUSUAL', 'UPGRADE', 'UPRIGHT', 'UTILITY', 'VACANCY',
    'VARIETY', 'VEHICLE', 'VENTURE', 'VERSION', 'VETERAN', 'VICTORY',
    'VILLAGE', 'VINTAGE', 'VIOLENT', 'VIRTUAL', 'VISIBLE', 'VISITOR',
    'VITALLY', 'VOLCANO', 'VOLTAGE', 'WARRANT', 'WARRIOR', 'WEATHER',
    'WEBSITE', 'WEDDING', 'WEEKEND', 'WELCOME', 'WELFARE', 'WESTERN',
    'WHISPER', 'WILLING', 'WINNING', 'WORRIED', 'WORSHIP', 'WRITTEN',
]


class WordList:
    """Provides crossword fill words with pattern-matching capability."""

    def __init__(self):
        # Build lookup by length
        self._by_length = {}  # length -> set of uppercase words
        self._load_curated()
        self._load_system_dict()

    def _load_curated(self):
        for word in _CURATED_WORDS:
            w = word.upper().strip()
            if w.isalpha() and 3 <= len(w) <= 15:
                self._by_length.setdefault(len(w), set()).add(w)

    @staticmethod
    def _is_quality_word(w):
        """Filter out gibberish and overly obscure words.

        Tuned for college-level vocabulary: stricter vowel requirements
        and pattern checks to exclude Latin/Greek academic terms.
        """
        vowels = set('AEIOUY')
        vowel_count = sum(1 for ch in w if ch in vowels)
        if vowel_count == 0:
            return False
        # Must have at least 1 vowel per 4 letters (college-level filter)
        if len(w) >= 4 and vowel_count < len(w) / 4:
            return False
        # No 4+ consecutive consonants
        consec_consonants = 0
        for ch in w:
            if ch in vowels:
                consec_consonants = 0
            else:
                consec_consonants += 1
                if consec_consonants >= 4:
                    return False
        # No 3+ consecutive same letter
        for i in range(len(w) - 2):
            if w[i] == w[i+1] == w[i+2]:
                return False
        # No 3+ consecutive vowels (filters Latin/Greek words like AEON, GEOMOROI)
        consec_vowels = 0
        for ch in w:
            if ch in vowels:
                consec_vowels += 1
                if consec_vowels >= 3:
                    return False
            else:
                consec_vowels = 0
        return True

    def _load_system_dict(self):
        """Load common words from system dictionary as supplement.

        Currently disabled — the curated list provides enough vocabulary
        at college-level quality. The system dictionary (/usr/share/dict/words)
        contains too many obscure words even at short lengths (e.g. CHAA,
        AGAMID, BEGAD) that make puzzles less solvable.
        """
        # Intentionally not loading system dict to keep vocabulary
        # at college level. All fill words come from the curated list.
        pass

    def match_pattern(self, pattern, exclude=None):
        """Find words matching a pattern like '_A_E' (underscore = unknown).

        Args:
            pattern: string of uppercase letters and underscores
            exclude: set of words to exclude (already used)

        Returns:
            list of matching words, sorted by frequency preference
            (curated words first, then dictionary words)
        """
        length = len(pattern)
        candidates = self._by_length.get(length, set())
        if not candidates:
            return []

        exclude = exclude or set()

        # Build regex from pattern
        regex_parts = []
        for ch in pattern:
            if ch == '_':
                regex_parts.append('[A-Z]')
            else:
                regex_parts.append(re.escape(ch))
        regex = re.compile('^' + ''.join(regex_parts) + '$')

        curated_set = {w.upper() for w in _CURATED_WORDS if len(w) == length}

        matches_curated = []
        matches_dict = []
        for word in candidates:
            if word in exclude:
                continue
            if regex.match(word):
                if word in curated_set:
                    matches_curated.append(word)
                else:
                    matches_dict.append(word)

        # Return curated first (better fill words), then dictionary
        return matches_curated + matches_dict

    def has_words_of_length(self, length):
        """Check if any words of a given length exist."""
        return length in self._by_length and len(self._by_length[length]) > 0

    def word_count(self):
        """Total number of unique words available."""
        return sum(len(words) for words in self._by_length.values())

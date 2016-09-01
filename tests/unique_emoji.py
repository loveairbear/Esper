from esper.database import emoji_word as emoj
vals = emoj.emoji_english.values()
uniques = set(vals)
if len(vals) == len(list(uniques)):
    print('True')
else:
    print('False')
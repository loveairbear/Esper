from collections import Counter
import uuid
from esper.messaging import fb_msgr
import base64
emoji_word = dict(a='😍', A='🐼',
                  b='😂', B='🐩',
                  c='😀', C='💨',
                  d='😈', D='🔥',
                  e='💩', E='🍀',
                  f='😺', F='🗝',
                  g='👌', G='❇',
                  h='❤', H='⛄',
                  i='😘', I='⌚',
                  j='😒', J='🍎',
                  k='☺', K='🍅',
                  l='😊', L='🌠',
                  m='😩', M='⚽',
                  n='😭', N='🐳',
                  o='😁', O='🐡',
                  p='🙈', P='😛',
                  q='😳', Q='👼',
                  r='😴', R='💍',
                  s='😵', S='🐅',
                  t='🐧', T='👑',
                  u='🐙', U='🐊',
                  v='😕', V='🌵',
                  w='👍', W='⚓',
                  x='😇', X='🐘',
                  y='😯', Y='🐨',
                  z='☮', Z='🐻')

'',
emoji_num = {'0': '🙂',
             '1': '😏',
             '2': '✌',
             '3': '🎓',
             '4': '🐥',
             '5': '🔑',
             '6': '💘',
             '7': '😆',
             '8': '😋',
             '9': '😑'

             }

emoji_english = {**emoji_word, **emoji_num}


def word_to_emoji(txt):
    emoji_string = []
    for letter in txt:
        try:
            emoji_string.append(emoji_english[letter])
        except KeyError:
            emoji_string.append(letter)
    return ''.join(emoji_string)


def emoji_to_word(emojis):
    english_emoji = {val: key for key, val in emoji_english.items()}
    word_string = []
    for emoj in emojis:
        try:
            word_string.append(english_emoji[emoj])
        except KeyError:
            word_string.append(emoj)
    return ''.join(word_string)

def emoji_encode64(hex_id):
    id = uuid.UUID(hex=hex_id)
    tmp = base64.urlsafe_b64encode(id.bytes).decode(
        'utf-8').rstrip('=\n').replace('/', '_')
    return word_to_emoji(tmp)


def emoji_decode64(emoji):
    tmp1 = emoji_to_word(emoji)
    tmp = uuid.UUID(
        bytes=base64.urlsafe_b64decode((tmp1 + '==').replace('_', '/')))
    return tmp.hex
code = emoji_encode64(id)
a.say(code)
print(emoji_decode64(code))

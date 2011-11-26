import re
from pygments.lexer import Lexer
from pygments.lexers.templates import HtmlDjangoLexer
from pygments.lexers.agile import PythonLexer
from pygments.token import Text

class KeystoneLexer(Lexer):
    name = 'keystone'
    aliases = []
    filenames = ['*.ks']

    def __init__(self, **options):
        self.options = options.copy()
        super(KeystoneLexer, self).__init__(**options)

    def get_tokens_unprocessed(self, text):
        offset = 0
        if re.search(r'^----\s*$', text, re.MULTILINE):
            py, _, text = text.partition('----')

            lexer = PythonLexer(**self.options)
            for i, token, value in lexer.get_tokens_unprocessed(py):
                yield i, token, value

            offset = i + 1
            yield offset, Text, u'----'
            offset += 1

        lexer = HtmlDjangoLexer(**self.options)
        for i, token, value in lexer.get_tokens_unprocessed(text):
            yield offset + i, token, value


def setup(sphinx):
    lexer = KeystoneLexer()
    for alias in [KeystoneLexer.name] + KeystoneLexer.aliases:
        sphinx.add_lexer(alias, lexer)


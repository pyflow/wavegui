
from wavegui.template import SimpleTemplate, TemplateError, template, touni, tob, html_quote
import re, os
import traceback
import pytest

class chdir(object):
    def __init__(self, dir):
        if os.path.isfile(dir):
            dir = os.path.dirname(dir)
        self.wd = os.path.abspath(dir)
        self.old = os.path.abspath('.')

    def __enter__(self):
        os.chdir(self.wd)

    def __exit__(self, exc_type, exc_val, tb):
        os.chdir(self.old)

def test_template_1():
    assert template('<b>Hello {{name}}</b>!', name="World") == '<b>Hello World</b>!'

def test_string():
    """ Templates: Parse string"""
    assert template('start {{var}} end', var='var') == 'start var end'

def test_self_as_variable_name():
    assert template('start {{self}} end', {'self':'var'}) == 'start var end'

def assert_renders(tpl, to, *args, **vars):
    if isinstance(tpl, str):
        tpl = SimpleTemplate(tpl, lookup=[os.path.join(os.path.dirname(__file__), 'views')])
    assert touni(to) == tpl.render(*args, **vars)

def test_file():
    with chdir(__file__):
        t = SimpleTemplate(name='./templates/stpl_simple.tpl', lookup=['.'])
        assert_renders(t, 'start var end\n', var='var')

def test_name():
    with chdir(__file__):
        t = SimpleTemplate(name='stpl_simple', lookup=['./templates/'])
        assert_renders(t, 'start var end\n', var='var')

def test_unicode():
    assert_renders('start {{var}} end', 'start äöü end', var=touni('äöü'))
    assert_renders('start {{var}} end', 'start äöü end', var=tob('äöü'))

def test_unicode_code():
    """ Templates: utf8 code in file"""
    with chdir(__file__):
        t = SimpleTemplate(name='./templates/stpl_unicode.tpl', lookup=['.'])
        assert_renders(t, 'start ñç äöü end\n', var=touni('äöü'))

def test_import():
    """ Templates: import statement"""
    t = '%from base64 import b64encode\nstart {{b64encode(var.encode("ascii") if hasattr(var, "encode") else var)}} end'
    assert_renders(t, 'start dmFy end', var='var')

def test_data():
    """ Templates: Data representation """
    t = SimpleTemplate('<{{var}}>')
    assert_renders('<{{var}}>', '<True>', var=True)
    assert_renders('<{{var}}>', '<False>', var=False)
    assert_renders('<{{var}}>', '<>', var=None)
    assert_renders('<{{var}}>', '<0>', var=0)
    assert_renders('<{{var}}>', '<5>', var=5)
    assert_renders('<{{var}}>', '<b>', var=tob('b'))
    assert_renders('<{{var}}>', '<1.0>', var=1.0)
    assert_renders('<{{var}}>', '<[1, 2]>', var=[1,2])

def test_htmlutils_quote():
    assert '"&lt;&#039;&#13;&#10;&#9;&quot;\\&gt;"' == html_quote('<\'\r\n\t"\\>')

def test_escape():
    assert_renders('<{{var}}>', '<b>', var='b')
    assert_renders('<{{var}}>', '<&lt;&amp;&gt;>',var='<&>')

def test_noescape():
    assert_renders('<{{!var}}>', '<b>',   var='b')
    assert_renders('<{{!var}}>', '<<&>>', var='<&>')

def test_noescape_setting():
    t = SimpleTemplate('<{{var}}>', noescape=True)
    assert_renders(t, '<b>', var='b')
    assert_renders(t, '<<&>>', var='<&>')
    t = SimpleTemplate('<{{!var}}>', noescape=True)
    assert_renders(t, '<b>', var='b')
    assert_renders(t, '<&lt;&amp;&gt;>', var='<&>')

def test_blocks():
    """ Templates: Code blocks and loops """
    t = "start\n%for i in l:\n{{i}} \n%end\nend"
    assert_renders(t, 'start\n1 \n2 \n3 \nend', l=[1,2,3])
    assert_renders(t, 'start\nend', l=[])
    t = "start\n%if i:\n{{i}} \n%end\nend"
    assert_renders(t, 'start\nTrue \nend', i=True)
    assert_renders(t, 'start\nend', i=False)

def test_elsebug():
    ''' Whirespace between block keyword and colon is allowed '''
    assert_renders("%if 1:\nyes\n%else:\nno\n%end\n", "yes\n")
    assert_renders("%if 1:\nyes\n%else     :\nno\n%end\n", "yes\n")

def test_commentbug():
    ''' A "#" sign within an string is not a comment '''
    assert_renders("%if '#':\nyes\n%end\n", "yes\n")

def test_multiline():
    ''' Block statements with non-terminating newlines '''
    assert_renders("%if 1\\\n%and 1:\nyes\n%end\n", "yes\n")

def test_newline_in_parameterlist():
    ''' Block statements with non-terminating newlines in list '''
    assert_renders("%a=[1,\n%2]\n{{len(a)}}", "2")

def test_dedentbug():
    ''' One-Line dednet blocks should not change indention '''
    t = '%if x: a="if"\n%else: a="else"\n%end\n{{a}}'
    assert_renders(t, "if", x=True)
    assert_renders(t, "else", x=False)
    t = '%if x:\n%a="if"\n%else: a="else"\n%end\n{{a}}'
    assert_renders(t, "if", x=True)
    assert_renders(t, "else", x=False)
    t = SimpleTemplate('%if x: a="if"\n%else: a="else"\n%end')
    with pytest.raises(NameError):
         t.render()

def test_onelinebugs():
    ''' One-Line blocks should not change indention '''
    t = '%if x:\n%a=1\n%end\n{{a}}'
    assert_renders(t, "1", x=True)
    t = '%if x: a=1; end\n{{a}}'
    assert_renders(t, "1", x=True)
    t = '%if x:\n%a=1\n%else:\n%a=2\n%end\n{{a}}'
    assert_renders(t, "1", x=True)
    assert_renders(t, "2", x=False)
    t = '%if x:   a=1\n%else:\n%a=2\n%end\n{{a}}'
    assert_renders(t, "1", x=True)
    assert_renders(t, "2", x=False)
    t = '%if x:\n%a=1\n%else:   a=2; end\n{{a}}'
    assert_renders(t, "1", x=True)
    assert_renders(t, "2", x=False)
    t = '%if x:   a=1\n%else:   a=2; end\n{{a}}'
    assert_renders(t, "1", x=True)
    assert_renders(t, "2", x=False)

def test_onelineblocks():
    """ Templates: one line code blocks """
    t = "start\n%a=''\n%for i in l: a += str(i); end\n{{a}}\nend"
    assert_renders(t, 'start\n123\nend', l=[1,2,3])
    assert_renders(t, 'start\n\nend', l=[])

def test_escaped_codelines():
    assert_renders('\\% test', '% test')
    assert_renders('\\%% test', '%% test')
    assert_renders('    \\% test', '    % test')

def test_nobreak():
    """ Templates: Nobreak statements"""
    assert_renders("start\\\\\n%pass\nend", 'startend')

def test_nonobreak():
    """ Templates: Escaped nobreak statements"""
    assert_renders("start\\\\\n\\\\\n%pass\nend", 'start\\\\\nend')

def test_include():
    """ Templates: Include statements"""
    with chdir(__file__):
        t = SimpleTemplate(name='stpl_include', lookup=['./templates/'])
        assert_renders(t, 'before\nstart var end\nafter\n', var='var')

def test_rebase():
    """ Templates: %rebase and method passing """
    with chdir(__file__):
        t = SimpleTemplate(name='stpl_t2main', lookup=['./templates/'])
        result='+base+\n+main+\n!1234!\n+include+\n-main-\n+include+\n-base-\n'
        assert_renders(t, result, content='1234')

def test_get():
    assert_renders('{{get("x", "default")}}', '1234', x='1234')
    assert_renders('{{get("x", "default")}}', 'default')

def test_setdefault():
    t = '%setdefault("x", "default")\n{{x}}'
    assert_renders(t, '1234', x='1234')
    assert_renders(t, 'default')

def test_defnied():
    assert_renders('{{x if defined("x") else "no"}}', 'yes', x='yes')
    assert_renders('{{x if defined("x") else "no"}}', 'no')

def test_notfound():
    """ Templates: Unavailable templates"""
    with pytest.raises(TemplateError):
        SimpleTemplate(name="abcdef", lookup=['.'])

def test_error():
    """ Templates: Exceptions"""
    with pytest.raises(SyntaxError):
        SimpleTemplate('%for badsyntax').co
    with pytest.raises(IndexError):
        SimpleTemplate('{{i[5]}}', lookup=['.']).render(i=[0])

def test_winbreaks():
    """ Templates: Test windows line breaks """
    assert_renders('%var+=1\r\n{{var}}\r\n', '6\r\n', var=5)

def test_winbreaks_end_bug():
    d = { 'test': [ 1, 2, 3 ] }
    assert_renders('%for i in test:\n{{i}}\n%end\n', '1\n2\n3\n', **d)
    assert_renders('%for i in test:\n{{i}}\r\n%end\n', '1\r\n2\r\n3\r\n', **d)
    assert_renders('%for i in test:\r\n{{i}}\n%end\r\n', '1\n2\n3\n', **d)
    assert_renders('%for i in test:\r\n{{i}}\r\n%end\r\n', '1\r\n2\r\n3\r\n', **d)

def test_commentonly():
    """ Templates: Commentd should behave like code-lines (e.g. flush text-lines) """
    t = SimpleTemplate('...\n%#test\n...')
    assert '#test' != t.code.splitlines()[0]

def test_global_config():
    SimpleTemplate.global_config('meh', 1)
    t = SimpleTemplate('anything')
    assert touni('anything') == t.render()


def test_bug_no_whitespace_before_stmt():
    assert_renders('\n{{var}}', '\nx', var='x')

def test_bug_block_keywords_eat_prefixed_code():
    ''' #595: Everything before an 'if' statement is removed, resulting in
        SyntaxError. '''
    tpl = "% m = 'x' if True else 'y'\n{{m}}"
    assert_renders(tpl, 'x')


def fix_ident(string):
    lines = string.splitlines(True)
    if not lines: return string
    if not lines[0].strip(): lines.pop(0)
    whitespace = re.match('([ \t]*)', lines[0]).group(0)
    if not whitespace: return string
    for i in range(len(lines)):
        lines[i] = lines[i][len(whitespace):]
    return lines[0][:0].join(lines)

def assert_tpl_enders(source, result, syntax=None, *args, **vars):
    source = fix_ident(source)
    result = fix_ident(result)
    tpl = SimpleTemplate(source, syntax=syntax)
    try:
        tpl.co
        assert touni(result) == tpl.render(*args, **vars)
    except SyntaxError:
        pytest.fail('Syntax error in template:\n%s\n\nTemplate code:\n##########\n%s\n##########' %
                    (traceback.format_exc(), tpl.code))

def test_multiline_block():
    source = '''
        <% a = 5
        b = 6
        c = 7 %>
        {{a+b+c}}
    '''; result = '''
        18
    '''
    assert_tpl_enders(source, result)
    source_wineol = '<% a = 5\r\nb = 6\r\nc = 7\r\n%>\r\n{{a+b+c}}'
    result_wineol = '18'
    assert_tpl_enders(source_wineol, result_wineol)

def test_multiline_ignore_eob_in_string():
    source = '''
        <% x=5 # a comment
            y = '%>' # a string
            # this is still code
            # lets end this %>
        {{x}}{{!y}}
    '''; result = '''
        5%>
    '''
    assert_tpl_enders(source, result)

def test_multiline_find_eob_in_comments():
    source = '''
        <% # a comment
            # %> ignore because not end of line
            # this is still code
            x=5
            # lets end this here %>
        {{x}}
    '''; result = '''
        5
    '''
    assert_tpl_enders(source, result)

def test_multiline_indention():
    source = '''
        <%   if True:
                a = 2
                    else:
                    a = 0
                        end
        %>
        {{a}}
    '''; result = '''
        2
    '''
    assert_tpl_enders(source, result)

def test_multiline_eob_after_end():
    source = '''
        <%   if True:
                a = 2
                end %>
        {{a}}
    '''; result = '''
        2
    '''
    assert_tpl_enders(source, result)

def test_multiline_eob_in_single_line_code():
    # eob must be a valid python expression to allow this test.
    source = '''
        cline eob=5; eob
        xxx
    '''; result = '''
        xxx
    '''
    assert_tpl_enders(source, result, syntax='sob eob cline foo bar')

def test_multiline_strings_in_code_line():
    source = '''
        % a = """line 1
                line 2"""
        {{a}}
    '''; result = '''
        line 1
                line 2
    '''
    assert_tpl_enders(source, result)

def test_multiline_comprehensions_in_code_line():
    assert_tpl_enders(source='''
        % a = [
        %    (i + 1)
        %    for i in range(5)
        %    if i%2 == 0
        % ]
        {{a}}
    ''', result='''
        [1, 3, 5]
    ''')


def test_end_keyword_on_same_line():
    assert_tpl_enders('''
        % if 1:
        %    1; end
        foo
    ''', '''
        foo
    ''')
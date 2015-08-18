from django.utils.html import conditional_escape, escape
import re
#_nsre = re.compile(ur'(?iu)([0-9]+|(?:\b[mdclxvi]+\b))')
_nsre_romans = re.compile(ur'(?iu)(?:\.\s*)([ivxlcdm]+\b)')
_nsre = re.compile(ur'(?iu)([0-9]+)')

def sorted_natural(l, roman_numbers=False):
    '''Sorts l and returns it. Natural sorting is applied.'''
    ret = sorted(l, key=lambda e: natural_sort_key(e, roman_numbers))
    # make sure the empty values are at the end
    for v in [None, u'', '']:
        if v in ret:
            ret.remove(v)
            ret.append(v)
    return ret

def natural_sort_key(s, roman_numbers=False):
    '''
        Returns a list of tokens from a string.
        This list of tokens can be feed into a sorting function to come up with a natural sorting.
        Natural sorting is number-aware: e.g. 'word 2' < 'word 100'.
        
        If roman_numbers is True, roman numbers will be converted to ints.
        Note that there is no fool-proof was to detect roman numerals
        e.g. MS A; MS B; MS C. In this case C is a letter and not 500.
            MS A.ix In this case ix is a number
        So as a heuristic we only consider roman number if preceded by '.'
    '''
    
    if roman_numbers:
        while True:
            m = _nsre_romans.search(s)
            if m is None: break
            # convert the roman number into base 10 number
            number = get_int_from_roman_number(m.group(1))
            if number:
                # substition
                s = s[:m.start(1)] + str(number) + s[m.end(1):]
                
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]

def plural(value, count=2):
    '''
    Usage:
            {{ var|plural }}
            {{ var|plural:count }}
            
            If [count] > 1 or [count] is not specified, the filter returns the plural form of [var].
            Plural form is generated by sequentially applying the following rules:
                * convert 'y' at the end into 'ie'               (contry -> contrie)
                * convert 'ss' at the end into 'e'               (witness -> witnesse)
                * add a 's' at the end is none already there     (nation -> nations)
    '''
    
    if count is not None:
        try:
            count = int(float(count))
        except ValueError:
            pass
        except TypeError:
            pass
        try:
            count = len(count)
        except TypeError:
            pass
    
    words = value.split(' ')
    if len(words) > 1:
        # We got a phrase. Pluralise each word separately.
        ret = ' '.join([plural(word, count) for word in words])
    else:
        ret = value
        if ret in ['of']: return ret
        if count != 1:
            if ret in ['a', 'an']: return ''
            if ret[-1:] == 'y':
                ret = ret[:-1] + 'ie'
            if ret[-2:] == 'ss':
                ret = ret + 'e'
            if not ret[-1:] == 's':
                ret = ret + 's'
    return ret

def update_query_string(url, updates, url_wins=False):
    '''
        Replace parameter values in the query string of the given URL.
        If url_wins is True, the query string values in [url] will always supersede the values from [updates].
        
        E.g.
        
        >> _update_query_string('http://www.mysite.com/about?category=staff&country=UK', 'who=bill&country=US')
        'http://www.mysite.com/about?category=staff&who=bill&country=US'

        >> _update_query_string('http://www.mysite.com/about?category=staff&country=UK', {'who': ['bill'], 'country': ['US']})
        'http://www.mysite.com/about?category=staff&who=bill&country=US'
        
    '''
    show = url == '?page=2&amp;terms=%C3%86thelstan&amp;repository=&amp;ordering=&amp;years=&amp;place=&amp;basic_search_type=hands&amp;date=&amp;scribes=&amp;result_type=' and updates == 'result_type=manuscripts'
    
    ret = url.strip()
    if ret and ret[0] == '#': return ret

    from urlparse import urlparse, urlunparse, parse_qs
    
    # Convert string format into a dictionary
    if isinstance(updates, basestring):
        updates_dict = parse_qs(updates, True)
    else:
        from copy import deepcopy
        updates_dict = deepcopy(updates)
        
    # Merge the two query strings (url and updates)
    # note that urlparse preserves the url encoding (%, &amp;)
    parts = [p for p in urlparse(url)]
    # note that parse_qs converts u'terms=%C3%86thelstan' into u'\xc3\x86thelstan'
    # See http://stackoverflow.com/questions/16614695/python-urlparse-parse-qs-unicode-url
    # for the reaon behind the call to encode('ASCII')
    query_dict = parse_qs(parts[4].encode('ASCII'))
    if url_wins:
        updates_dict.update(query_dict)
        query_dict = updates_dict
    else:
        query_dict.update(updates_dict)
    
    # Now query_dict is our updated query string as a dictionary
    # Parse and unparse it again to remove the empty values
    query_dict = parse_qs(urlencode(query_dict, True))
    
    # Convert back into a string
    parts[4] = urlencode(query_dict, True)
    
    # Place the query string back into the URL
    ret = urlunparse(parts)
    
    ret = escape(ret)
    
    if len(ret) == 0:
        ret = '?'
        
    # We mark this safe so django template renderer won't try to escape it a second time
    # This would generate something like this in the html output: '?k1=v1&amp;amp;k2=v'
    from django.utils.safestring import mark_safe
    ret = mark_safe(ret)
    
    return ret

def get_str_from_call_stack():
    ret = ''
    import traceback, re
    tb = traceback.extract_stack()
    #ret = '; '.join(['%s (%s:%s)' % (call[2], re.sub(ur'^.*[\\/]([^/\\]+)\.py$', ur'\1', call[0]), call[1]) for call in tb])
    ret = '; '.join(['%s (%s:%s)' % (call[2], call[0], call[1]) for call in tb])
    return ret

def urlencode(dict, doseq=0):
    ''' This is a unicode-compatible wrapper around urllib.urlencode()
        See http://stackoverflow.com/questions/3121186/error-with-urlencode-in-python
    '''
    import urllib
    d = {}
    for k,v in dict.iteritems():
        d[k] = []
        for v2 in dict[k]:
            if isinstance(v2, unicode):
                v2 = v2.encode('utf=8')
            d[k].append(v2)
    ret = urllib.urlencode(d, doseq)
    return ret

def get_json_response(data):
    '''Returns a HttpResponse with the given data variable encoded as json'''
    import json
    from django.http import HttpResponse
    return HttpResponse(json.dumps(data), mimetype="application/json")

def get_tokens_from_phrase(phrase, lowercase=False):
    ''' Returns a list of tokens from a query phrase.
    
        Discard stop words (NOT, OR, AND)
        Detect quoted pieces ("two glosses")
        Remove field scopes. E.g. repository:London => London
    
        e.g. "ab cd" ef-yo NOT (gh)
        => ['ab cd', 'ef', 'yo', 'gh']
    '''
    ret = []
    
    if lowercase:
        phrase = phrase.lower()
        
    # Remove field scopes. E.g. repository:London => London
    phrase = re.sub(ur'(?u)\w+:', ur'', phrase)
    
    phrase = phrase.strip()
    
    # extract the quoted pieces
    for part in re.findall(ur'"([^"]+)"', phrase):
        ret.append(part)
    
    # remove them from the phrase
    phrase = re.sub(ur'"[^"]+"', '', phrase)
    
    # JIRA 358: search for 8558-8563 => no highlight if we don't remove non-characters before tokenising
    # * is for searches like 'digi*'
    phrase = re.sub(ur'(?u)[^\w*]', ' ', phrase)
    
    # add the remaining tokens
    if phrase:
        ret.extend([t for t in re.split(ur'\s+', phrase.lower().strip()) if t.lower() not in ['and', 'or', 'not']])
    
    return ret

def get_regexp_from_terms(terms, as_list=False):
    ''' input: list of query terms, e.g. ['ab', cd ef', 'gh']
        output: a regexp, e.g. '\bab\b|\bcd\b...
                if as_list is True: ['\bab\b', '\bcd\b']
    '''
    ret = []
    if terms:
        # create a regexp
        for t in terms:
            t = re.escape(t)

            if t[-1] == u's':
                t += u'?'
            else:
                t += u's?'
#             if len(t) > 1:
#                 t += ur'?'
#             t = ur'\b%ss?\b' % t
            t = ur'\b%s\b' % t
            
            # convert all \* into \W*
            # * is for searches like 'digi*'
            t = t.replace(ur'\*', ur'\w*')
            
            ret.append(t)

    if not as_list:
        ret = ur'|'.join(ret)
    
    return ret

def find_first(pattern, text, default=''):
    ret = default
    matches = re.findall(pattern, text)
    if matches: ret = matches[0]
    return ret

def get_int_from_roman_number(input):
    """
    From
    http://code.activestate.com/recipes/81611-roman-numerals/
    
    Convert a roman numeral to an integer.
    
    >>> r = range(1, 4000)
    >>> nums = [int_to_roman(i) for i in r]
    >>> ints = [roman_to_int(n) for n in nums]
    >>> print r == ints
    1
    
    >>> roman_to_int('VVVIV')
    Traceback (most recent call last):
    ...
    ValueError: input is not a valid roman numeral: VVVIV
    >>> roman_to_int(1)
    Traceback (most recent call last):
    ...
    TypeError: expected string, got <type 'int'>
    >>> roman_to_int('a')
    Traceback (most recent call last):
    ...
    ValueError: input is not a valid roman numeral: A
    >>> roman_to_int('IL')
    Traceback (most recent call last):
    ...
    ValueError: input is not a valid roman numeral: IL
    """
    if not isinstance(input, basestring):
        return None
    input = input.upper()
    nums = ['M', 'D', 'C', 'L', 'X', 'V', 'I']
    ints = [1000, 500, 100, 50,  10,  5,   1]
    places = []
    for c in input:
        if not c in nums:
            #raise ValueError, "input is not a valid roman numeral: %s" % input
            return None
    for i in range(len(input)):
        c = input[i]
        value = ints[nums.index(c)]
        # If the next place holds a larger number, this value is negative.
        try:
            nextvalue = ints[nums.index(input[i +1])]
            if nextvalue > value:
                value *= -1
        except IndexError:
            # there is no next place.
            pass
        places.append(value)
    sum = 0
    for n in places: sum += n
    return sum

def get_plain_text_from_html(html):
    '''Returns the unencoded text from a HTML fragment. No tags, no entities, just plain utf-8 text.
        Add spaces after </p>s.
    '''
    ret = html
    if ret:
        # JIRA 522
        ret = ret.replace('</p>', '</p> ')
        #
        from django.utils.html import strip_tags
        import HTMLParser
        html_parser = HTMLParser.HTMLParser()
        #ret = strip_tags(html_parser.unescape(ret))
        ret = html_parser.unescape(strip_tags(ret)).strip()
    else:
        ret = u''
    return ret

def set_left_joins_in_queryset(qs):
    qs.query.promote_joins(qs.query.alias_map.keys(), True)
    #pass
#     for alias in qs.query.alias_map:
#         qs.query.promote_alias(alias, True)

def get_str_from_queryset(queryset):
    ret = unicode(queryset.query)
    ret = re.sub(ur'(INNER|FROM|AND|OR|WHERE|GROUP|ORDER|LEFT|RIGHT|HAVING)', ur'\n\1', ret)
    ret = re.sub(ur'(INNER|AND|OR|LEFT|RIGHT)', ur'\t\1', ret)
    return ret.encode('ascii', 'ignore')

def remove_accents(input_str):
    '''Returns the input string without accented character.
        This is useful for accent-insensitive matching (e.g. autocomplete).
        >> remove_accents(u'c\u0327   \u00c7')
        u'c   c'
    '''
    import unicodedata
    # use 'NFD' instead of 'NFKD'
    # Otherwise the ellipsis \u2026 is tranformed into '...' and the output string will have a different length
    #return remove_combining_marks(unicodedata.normalize('NFKD', unicode(input_str)))
    return remove_combining_marks(unicodedata.normalize('NFD', unicode(input_str)))

def remove_combining_marks(input_str):
    '''Returns the input unicode string without the combining marks found as 'individual character'
        >> remove_combining_marks(u'c\u0327   \u00c7')
        u'c   \u00c7'
    '''
    import unicodedata
    return u"".join([c for c in unicode(input_str) if not unicodedata.combining(c)])

def write_file(file_path, content):
    f = open(file_path, 'wb')
    f.write(content.encode('utf8'))
    f.close()

def get_bool_from_string(string):
    ret = False
    if string in ['1', 'True', 'true']:
        ret = True
    return ret

def get_one2one_object(model, field_name):
    '''Returns model.field_name where field_name is a one2one relation.
        This function till return None if there no related object.
    '''
    ret = None
    
    if model:
        from django.core.exceptions import ObjectDoesNotExist
        try:
            getattr(model, field_name)
        except ObjectDoesNotExist, e:
            pass
    
    return ret

def get_xml_from_unicode(document):
    import lxml.etree as ET
    from io import BytesIO
    d = BytesIO(document.encode('utf-8'))
    ret = ET.parse(d)
    
    return ret

def get_xslt_transform(source, template, error=None):
    import lxml.etree as ET
    
    dom = get_xml_from_unicode(source)
    xslt = get_xml_from_unicode(template)
    transform = ET.XSLT(xslt)
    newdom = transform(dom)
    #print(ET.tostring(newdom, pretty_print=True))
    ret = newdom
            
    return ret

def recreate_whoosh_index(path, index_name, schema):
    import os.path
    from whoosh.index import create_in
    if not os.path.exists(path):
        os.mkdir(path)
    path = os.path.join(path, index_name)
    if os.path.exists(path):
        import shutil
        shutil.rmtree(path)
    os.mkdir(path)
    print '\tCreated index under "%s"' % path
    # TODO: check if this REcreate the existing index
    index = create_in(path, schema)
    
    return index

def get_int(obj, default=0):
    '''Returns an int from an obj (e.g. string)
        If the conversion fails, returns default.
    '''
    try:
        ret = int(obj)
    except:
        ret = default
    return ret

def get_int_from_request_var(request, var_name, default=0):
    obj = None
    if request:
        obj = request.REQUEST.get(var_name, None)
    return get_int(obj, default)

MAX_DATE_RANGE = [-5000, 5000]

def is_max_date_range(rng):
    return rng and rng[0] == MAX_DATE_RANGE[0] and rng[1] == MAX_DATE_RANGE[1]

def get_midpoint_from_date_range(astr=None, arange=None):
    '''
    Returns a numeric date which is the midpoint of a date range expressed in astr
    The midpoint is not always the average of the range, it is biased
    towards the date mentioned in the label.
    e.g. get_range_from_date('940x956') => 948
    e.g. get_range_from_date('Ca 1075') => 1075
    
    Returns None for unknown date
    '''
    ret = None
    
    if arange is None:
        arange = get_range_from_date(astr)
    
    if is_max_date_range(arange):
        return ret
    
    # by default we take the middle point
    ret = (arange[1] + arange[0]) / 2

    if astr:
        # try harder... if we have a single date in the input we pick that one
        # Ca. 1090 => 1090
        patterns = [ur'(?i)^(?:c|ca)\.? (\d+)$']
        for pattern in patterns:
            s = re.sub(pattern, ur'\1', astr.strip())
            if s != astr:
                ret = int(s)
                break
    
    return ret

def get_range_from_date(str):
    '''
    Returns a range of numeric dates from a string expression
    e.g. get_range_from_date('940x956') => [940, 956]
    e.g. get_range_from_date('Ca 1075') => [1070, 1080]
    '''
    ret = MAX_DATE_RANGE[:]
    
    if not str:
        return ret
    
    # expand s. => Saec.
    str = re.sub(ur'\bs\.\s', u'Saec. ', str)
    
    # expand c. => ca
    str = re.sub(ur'\bc\.\s', u'Ca ', str)

    # remove prob.
    str = re.sub(ur'(prob.|probably|by)\s', '', str).strip()
    
    # remove ?, A.D.
    str = re.sub(ur'\?|A\.D\.', '', str).strip()

    # remove (...)
    str = re.sub(ur'\([^)]+\)', '', str).strip()
    
    # 845 for 830 => 830
    str = re.sub(ur'.*\sfor\s', '', str).strip()

    str = str.strip()
    
    # 1080
    if re.match(ur'\d+$', str):
        return [int(str), int(str)]

    # 1035/6 => (1035, 1036)
    m = re.match(ur'(\d+)/(\d+)$', str)
    if m:
        ret = [int(m.group(1)), int(m.group(1))]
        if len(m.group(2)) < len(m.group(1)):
            ret[1] = int(m.group(1)[0:-len(m.group(2))] + m.group(2))
    
    m = re.match(ur'(?iu)(before|after)\s(\d+)$', str)
    if m:
        if m.group(1) == 'before':
            ret[1] = int(m.group(2))
        else:
            ret[0] = int(m.group(2))
    
    # Saec. x/xi or xi in. [  980.0,  1030.0]
    parts = re.split(ur'\bor\b', str)
    if len(parts) == 1:
        parts = re.split(ur'and', str)
    if len(parts) > 1:
        # combine different dates
        #dates = [ret]
        ret = get_range_from_date(parts[0].strip())
        for part in parts[1:]:
            part = part.strip()
            if not part.lower().startswith('saec.') and str.lower().startswith('saec.'):
                part = 'Saec. ' + part
            # combine the dates
            reti = get_range_from_date(part)
            ret = [min(ret[0], reti[0]), max(ret[1], reti[1])]
        return ret
    
    # Ca 1075 [ 1070.0,  1080.0]
    # Ca 1086 [ 1080.0,  1090.0]
    m = re.match(ur'(?iu)ca\.?\s?(\d+)$', str)
    if m:
        n = int(m.group(1))
        str = 'Ca %sx%s' % (n-5, n+5)
    
    # 1066x1087 => [1066, 1087]
    # Ca 820x840 => [820, 840]
    m = re.match(ur'(?iu)(?:ca\s)?(\d+)\s?[-x\xd7]\s?(\d+)$', str)
    if m:
        ret = [int(m.group(1)), int(m.group(2))]
        
        # case for '950x68' => 950x968
        if len(m.group(2)) < len(m.group(1)):
            ret[1] = int(m.group(1)[0:-len(m.group(2))] + m.group(2))
        
        if str.lower().startswith('ca '):
            # Ca 1002x1023 [ 1000.0,  1025.0]
            ret[0] = ret[0] - (ret[0] % 5)
            if ret[1] % 5:
                ret[1] = ret[1] - (ret[1] % 5) + 5
    #107    1080s    1080.0    1085.0    1090.0
    m = re.match(ur'(?iu)(\d+0)s$', str)
    if m:
        ret = [int(m.group(1)), int(m.group(1)) + 10]
    
    # Saec. x1
    m = re.match(ur'(?iu)Saec. ([ivx]+)(.*)$', str)
    if m:
        mod = m.group(2).strip()
        century = get_int_from_roman_number(m.group(1))
        ret = [(century - 1) * 100, century * 100]
        # Saec. x1/3 [  900.0,   933.0]
        m2 = re.match(ur'(\d)/(\d)$', mod)
        if m2:
            dur = 100.0 / int(m2.group(2))
            ret[1] = ret[0] + (int(m2.group(1)) * dur)
            ret[0] = ret[1] - dur
    
        # in./med./ex.
        # digipal_date is not consistent for "ex."
        # it can be the last 20 or 30 years
        #139    Saec. viii ex.    780.0    790.0    800.0
        #137    Saec. vii ex.    670.0    690.0    700.0
        # => take last 30 years
        ex_duration = 30
        if mod == 'ex.':
            ret[0] = ret[1] - ex_duration
        if mod == 'in.':
            ret[1] = ret[0] + ex_duration
        if mod == 'med.':
            ret[1] = ret[0] + 66
            ret[0] = ret[0] + 33
        
        # Saec. xi1 => 1000, 1050
        if mod == '1':
            ret[1] = ret[0] + 50
        if mod == '2':
            ret[0] = ret[0] + 50

        #Saec. x/xi [  980.0,  1020.0]
        m2 = re.match(ur'/([ivx]+)$', mod)
        if m2:
            century2 = get_int_from_roman_number(m2.group(1))
            if century2 == century + 1:
                ret = [ret[1] - 20, ret[1] + 20]
            

        #if m.group(2) == '':
    
    ret = [int(ret[0]), int(ret[1])]
        
    return ret

def get_all_files_under(root, file_types='fd', filters=[], extensions=[], direct_children=False, can_return_root=False):
    '''Returns a list of absolute paths to all the files under root.
        root is an absolute path
        file_types = types of files to return: f for files, d for directories
        extensions = only files with those extension will be returned
        filters = only files with those keywords anywhere in the path will be returned
    '''
    import os
    ret = []
    root = root.rstrip(os.path.sep)
    to_process = [root]
    
    filters = get_dict_from_string(filters)
    extensions = get_dict_from_string(extensions)
    
    while to_process:
        path = to_process.pop(0)
        file_type = 'd' if os.path.isdir(path) else 'f'
        if (file_type in file_types) and \
            (can_return_root or path != root) and \
            (not filters or any([filter.lower() in path.lower() for filter in filters])) and \
            (not extensions or any([path.endswith('.' + ext.strip('.')) for ext in extensions])):
                ret.append(path)
        
        if file_type == 'd' and (path == root or not direct_children):
            for file_name in os.listdir(path):
                to_process.append(os.path.join(path, file_name))
    return ret

def get_cms_page_from_title(title):
    from mezzanine.pages.models import Page as MPage
    from django.utils.text import slugify
    for page in MPage.objects.filter(slug__iendswith=slugify(unicode(title))):
        return page
    return None

def get_cms_url_from_slug(title):
    page = get_cms_page_from_title(title)
    if page:
        return page.get_absolute_url()
    from django.utils.text import slugify
    return u'/%s' % slugify(unicode(title))

def remove_param_from_request(request, key):
    ret = request
    #print dir(ret.GET)
    ret.GET = ret.GET.copy()
    if ret.GET.has_key('jx'):
        del ret.GET['jx']
    ret.META = ret.META.copy()
    ret.META['QUERY_STRING'] = re.sub(ur'\Wjx=1($|&|#)', ur'', ret.META.get('QUERY_STRING', ''))
    return ret

def read_file(filepath):
    import codecs
    f = codecs.open(filepath, 'r', "utf-8")
    ret = f.read()
    f.close()
    
    return ret

def get_dict_from_string(string, sep=',', keep_blanks=False):
    '''Return an array of string
        If the input is already an array, return it as is
        If the input is a string, split it around the commas
    '''
    ret = []
    if string:
        if isinstance(string, basestring):
            ret = string.split(sep)
        if isinstance(string, list) or isinstance(string, tuple):
            ret = string

    if not keep_blanks:
        ret = [r.strip() for r in ret]
    
    return ret

def get_normalised_path(path):
    ''' Turn the path and file names into something the image server won't complain about
        Extension is preserved.'''
    import os
    (file_base_name, extension) = os.path.splitext(path)
    file_base_name = re.sub(r'(?i)[^a-z0-9\\/]', '_', file_base_name)
    file_base_name = re.sub(r'_+', '_', file_base_name)
    file_base_name = re.sub(r'_?(/|\\)_?', r'\1', file_base_name)
    return file_base_name + extension

def add_keywords(obj, keywords='', remove=False):
    # add or remove Mezzanine keywords on a model instance
    # keywords is a comma separated list of keywords or an array
    ret = False
    keywords = get_dict_from_string(keywords)
    
    # read the keywords from the DB
    from mezzanine.generic.models import Keyword, AssignedKeyword
    existing_keywords = {}
    for kw in Keyword.objects.extra(where=["lower(title) in (%s)" % ', '.join(["'%s'" % kw.lower() for kw in keywords])]):
        existing_keywords[kw.title.lower()] = kw
    
    if remove:
        # TODO
        pass
    else:
        # add ids from assigned keywords
        for kw in [ak.keyword for ak in obj.keywords.all()]:
            existing_keywords[kw.title.lower()] = kw
        # create missing keywords
        for kw in keywords:
            if kw.lower() not in existing_keywords:
                print 'create %s' % kw
                existing_keywords[kw.lower()] = Keyword(title=kw)
                existing_keywords[kw.lower()].save()
    
        # now existing_keywords has all the requested keywords
        # assign them to the object
        from mezzanine.generic.fields import KeywordsField
        for field in [f for f in obj._meta.virtual_fields if f.__class__ == KeywordsField]:
            field.save_form_data(obj, u','.join([unicode(kw.id) for kw in existing_keywords.values()]))

    return ret

def read_all_lines_from_csv(file_path):
    '''
        Read a CSV file and returns an array where
        each entry correspond to a line in the file.
        It is assumed that the first line of the CSV
        contains the headings.
        Each entry in the returned array is a dictionary
        where the keys are the column headings and the
        values in the corresponding line in the file.
    '''
    ret = []
    
    import csv
    csv_path = file_path
    line_index = 0
    with open(csv_path, 'rb') as csvfile:
        csvreader = csv.reader(csvfile)
        
        columns = None
        
        for line in csvreader:
            line_index += 1
            line = [v.decode('latin-1') for v in line]
            if not columns:
                columns = [re.sub(ur'[^a-z]', '', c.lower()) for c in line]
                continue
            
            rec = dict(zip(columns, line))
            rec['_line_index'] = line_index
        
            ret.append(rec)
    
    return ret

def expand_folio_range(frange, errors=None):
    '''
        Returns an array of locus from a folio range expression
        If the expression is not valid it return []
        E.g.
        input: '140r20-1r2'
        output: ['140r', '140v', '141r']
    '''
    ret = []
    
    if errors is None:
        errors = []
    
    import re
    match = re.match(ur'(\d+)(r|v)(\d+)?(?:-(?:(\d+)(r|v))?(\d+)?)?', frange)
    if match:
        # frange = '140r20-1r2'
        # match.groups() = ('140', 'r', '20', '1', 'v', '2')
        
        # => fs = [140, 1]
        fs = [match.group(1), match.group(4)]
        if fs[1] is None:
            fs[1] = fs[0]
        # => fs = [140, 141]
        fs[1] = fs[0][0:(len(fs[0]) - len(fs[1]))] + fs[1]
        fs = [int(f) for f in fs]
        
        # => ret = [140r, 140v, 141r, 141v]
        
        if fs[1] < fs[0]:
            errors.append(u'Unrecognised folio range: %s' % frange)
        else:
            for f in range(fs[0], fs[1] + 1):
                ret.append('%sr' % f)
                ret.append('%sv' % f)
                
            # => ret = [140r, 140v, 141r]
            if match.group(2) == 'v':
                ret.pop(0)
            s = match.group(5) or match.group(2)
            if s == 'r':
                ret.pop()
    
    return ret

def is_model_visible(model, request):
    # Returns True if <model> is visible to the user
    # See setting.py:MODELS_PUBLIC and MODELS_PRIVATE
    # If request is not provided we assume public user
    # If request == True, returns true
    
    if request == True:
        return True
    
    if not model: return False
    
    # resolve model instance -> model
    from django.db.models.base import ModelBase
    meta = getattr(model, '_meta', None)
    if meta:
        model = getattr(model, 'model', meta)
    
    # resolve model -> string
    if isinstance(model, ModelBase):
        model = model.__name__
    
    # normalise model name
    model = ('%s' % model).lower()
    model = model.split('.')[-1]
    
    # check permissions from settings.py MODELS_PUBLIC|PRIVATE
    from django.conf import settings
    ret = (model in settings.MODELS_PUBLIC) or (request and request.user and request.user.is_staff and (model in settings.MODELS_PRIVATE))
    
    return ret

def is_staff(request=None):
    # returns True if the request user is a staff
    if request == True:
        return True
    
    return request and request.user and is_user_staff(request.user)
    
def is_user_staff(user=None):
    # returns True if the request user is a staff
    if user == True:
        return True
    
    return user and user.is_staff

def raise_404(message=None):
    from django.http import Http404
    options = []
    if message:
        options.append(message)
    raise Http404(*options)

def request_invisible_model(model, request, model_label=None):
    # Raise 404 if the model is not visible
    if not is_model_visible(model, request):
        message = None
        if model_label:
            message = u'''You don't have access to this %s record.''' % model_label
        raise_404(message)

def convert_xml_to_html(xml):
    ret = xml
    
    # todo:
    # () 4. add buttons to editor
    # () 5. display notes at the bottom of the desc
    
    ret = re.sub(ur'<c>', ur'<span data-dpt="record" data-dpt-model="character">', ret)
    
    for el in re.findall(ur'(?ui)<[^>]+>', xml):
        if re.search(ur'(?ui)</?(p|div|span)\b', el): continue
        
        nel = el
        nel = re.sub(ur'(?ui)([^\s>]+)(\s*=\s*")', ur'data-dpt-\1\2', nel)
        nel = re.sub(ur'(?ui)</([^\s>]+)', ur'</span', nel)
        nel = re.sub(ur'(?ui)<([^/\s>]+)', ur'<span data-dpt="\1"', nel)
        
        ret = ret.replace(el, nel)
    
    return ret
    
def re_sub_fct(content, apattern, fct, are=None):
    # Replace every occurrence of apattern in content with fct(match)
    # Return the resulting content
    if not are:
        are = re
    pattern = are.compile(apattern)
    pos = 0
    while True:
        match = pattern.search(content, pos)
        if not match: break

        replacement = fct(match)
        content = content[0:match.start(0)] + replacement + content[match.end(0):]
        pos = match.start(0) + len(replacement)
        
    return content

def dplog(message, level='DEBUG'):
    import logging
    dplog = logging.getLogger('digipal_debugger')
    dplog.debug(message)

    from datetime import datetime
    #print '[%s] %s' % (datetime.now(), message)

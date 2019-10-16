import io
import os
import re
import nltk
import spacy
import pandas as pd
import docx2txt
from datetime import datetime
from dateutil import relativedelta
from . import constants as cs
from spacy.matcher import Matcher
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords


def extract_text_from_pdf(pdf_path):
    '''
    Helper function to extract the plain text from .pdf files

    :param pdf_path: path to PDF file to be extracted
    :return: iterator of string of extracted text
    '''
    # https://www.blog.pythonlibrary.org/2018/05/03/exporting-data-from-pdfs-with-python/
    with open(pdf_path, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            resource_manager = PDFResourceManager()
            fake_file_handle = io.StringIO()
            converter = TextConverter(
                resource_manager, fake_file_handle, codec='utf-8', laparams=LAParams())
            page_interpreter = PDFPageInterpreter(resource_manager, converter)
            page_interpreter.process_page(page)

            text = fake_file_handle.getvalue()
            yield text

            # close open handles
            converter.close()
            fake_file_handle.close()


def extract_text_from_docx(docx_path):
    '''
    Helper function to extract plain text from .doc or .docx files

    :param docx_path: path to .doc or .docx file to be extracted
    :return: string of extracted text
    '''
    temp = docx2txt.process(docx_path)
    text = [line.replace('\t', ' ') for line in temp.split('\n') if line]
    return ' '.join(text)


def extract_text_from_doc(doc_path):
    # converting .doc to .docx
    doc_file = doc_path
    docx_file = doc_path + 'x'
    if not os.path.exists(docx_file):
        os.system('antiword ' + doc_file + ' > ' + docx_file)
        with open(docx_file) as f:
            text = f.read()
        os.remove(docx_file)  # docx_file was just to read, so deleting
    else:
        # already a file with same name as doc exists having docx extension,
        # which means it is a different file, so we cant read it
        print('Info : file with same name of doc exists having docx extension, so we cant read it')
        text = ''
    return text


def extract_text(file_path, extension):
    '''
    Wrapper function to detect the file extension and call text extraction function accordingly

    :param file_path: path of file of which text is to be extracted
    :param extension: extension of file `file_name`
    '''
    text = ''
    if extension == '.pdf':
        for page in extract_text_from_pdf(file_path):
            text += ' ' + page
    elif extension == '.docx':
        text = extract_text_from_docx(file_path)
    elif extension == '.doc':
        text = extract_text_from_doc(file_path)
    return text


def extract_email(text):
    '''
    Helper function to extract email id from text

    :param text: plain text extracted from resume file
    '''
    email = re.findall("([^@|\s]+@[^@]+\.[^@|\s]+)", text)
    if email:
        try:
            return email[0].split()[0].strip(';')
        except IndexError:
            return None


def extract_name(nlp_text, matcher):
    '''
    Helper function to extract name from spacy nlp text

    :param nlp_text: object of `spacy.tokens.doc.Doc`
    :param matcher: object of `spacy.matcher.Matcher`
    :return: string of full name
    '''
    pattern = [cs.NAME_PATTERN]

    matcher.add('NAME', None, *pattern)

    matches = matcher(nlp_text)

    for match_id, start, end in matches:
        span = nlp_text[start:end]
        return span.text


def extract_mobile_number(text):
    '''
    Helper function to extract mobile number from text

    :param text: plain text extracted from resume file
    :return: string of extracted mobile numbers
    '''
    # Found this complicated regex on : https://zapier.com/blog/extract-links-email-phone-regex/
    phone = re.findall(re.compile(
        r'(?:(?:\+?([1-9]|[0-9][0-9]|[0-9][0-9][0-9])\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{7})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'), text)
    phone1 = re.findall(re.compile(
        r'(?:(?:\+?([1-9]|[0-9][0-9]|[0-9][0-9][0-9])\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{0})\s*(?:[.-]\s*)?([0-9]{9})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'), text)
    if phone1:
        number = ''.join(phone1[0])
        number = number.replace(" ", "")
        if len(number) >= 10:
            if number[0:3] == '+91':
                number = number
            elif number[0:2] == '91':
                number = "+91" + number[2:12]
            else:
                number = "+91" + number
        else:
            return("Invalid number")
        return number


def extract_skills(nlp_text, noun_chunks):
    '''
    Helper function to extract skills from spacy nlp text

    :param nlp_text: object of `spacy.tokens.doc.Doc`
    :param noun_chunks: noun chunks extracted from nlp text
    :return: list of skills extracted
    '''
    tokens = [token.text for token in nlp_text if not token.is_stop]
    data = pd.read_csv(os.path.join(os.path.dirname(__file__), 'skills.csv'))
    skills = list(data.columns.values)
    skillset = []
    # check for one-grams
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)

    # check for bi-grams and tri-grams
    for token in noun_chunks:
        token = token.text.lower().strip()
        if token in skills:
            skillset.append(token)
    return [i.capitalize() for i in set([i.lower() for i in skillset])]


def cleanup(token, lower=True):
    if lower:
        token = token.lower()
    return token.strip()


def extract_education(nlp_text):
    '''
    Helper function to extract education from spacy nlp text

    :param nlp_text: object of `spacy.tokens.doc.Doc`
    :return: tuple of education degree and year if year if found else only returns education degree
    '''
    edu = {}
    # Extract education degree
    for index, text in enumerate(nlp_text):
        for tex in text.split():
            tex = re.sub(r'[?|$|.|!|,]', r'', tex)
            if tex.upper() in cs.EDUCATION and tex not in cs.STOPWORDS:
                edu[tex] = text + nlp_text[index + 1]
    education = []
    for key in edu.keys():
        year = re.search(re.compile(cs.YEAR), edu[key])
        if year:
            education.append((key, ''.join(year.group(0))))
        else:
            education.append(key)
    return education


def extract_year(nlp_text):
    edus = {}
    # Extract education degree
    for index, text in enumerate(nlp_text):
        for tex in text.split():
            tex = re.sub(r'[?|$|.|!|,]', r'', tex)
            if tex.upper() in cs.EDUCATION and tex not in cs.STOPWORDS:
                edus[tex] = text + nlp_text[index + 1]
    # Extract year
    educations = []
    for key in edus.keys():
        year = re.search(re.compile(cs.YEAR), edus[key])
        if year:
            educations.append((key, ''.join(year.group(0))))
        else:
            educations.append(key)
    return educations


def extract_experience(resume_text):
    '''
    Helper function to extract experience from resume text

    :param resume_text: Plain resume text
    :return: list of experience
    '''
    wordnet_lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))

    # word tokenization
    word_tokens = nltk.word_tokenize(resume_text)

    # remove stop words and lemmatize
    filtered_sentence = [
        w for w in word_tokens if not w in stop_words and wordnet_lemmatizer.lemmatize(w) not in stop_words]
    sent = nltk.pos_tag(filtered_sentence)

    # parse regex
    cp = nltk.RegexpParser('P: {<NNP>+}')
    cs = cp.parse(sent)

    # for i in cs.subtrees(filter=lambda x: x.label() == 'P'):
    #     print(i)

    test = []

    for vp in list(cs.subtrees(filter=lambda x: x.label() == 'P')):
        test.append(" ".join([i[0]
                              for i in vp.leaves() if len(vp.leaves()) >= 2]))
    # Search the word 'experience' in the chunk and then print out the text after it
    x = [x[x.lower().index('experience') + 10:]
         for i, x in enumerate(test) if x and 'experience' in x.lower()]
    return x


def extract_exp_year(resume_text):
    wordnet_lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))

    # word tokenization
    word_tokens = nltk.word_tokenize(resume_text)

    # remove stop words and lemmatize
    filtered_sentence = [
        w for w in word_tokens if not w in stop_words and wordnet_lemmatizer.lemmatize(w) not in stop_words]
    sent = nltk.pos_tag(filtered_sentence)
    # parse regex
    # cp = nltk.RegexpParser("NP: {<[CDJNP].*>+}")
    # check
    cp = nltk.RegexpParser("P: {<[CDNNS].*>+}")
    cs = cp.parse(sent)

    test = []
    for vp in list(cs.subtrees(filter=lambda x: x.label() == 'P')):
        test.append(" ".join([i[0]
                              for i in vp.leaves() if len(vp.leaves()) >= 2]))

    # Search the word 'year' in the chunk and then print out the text before it
    x = [x[x.lower().index('years') - 68:]
         for i, x in enumerate(test) if x and 'years' in x.lower()]
    number = ""
    for s in x:
        number += s
    if number == str:
        pass
    else:
        number = re.findall('\d+\.\d+|\d+', number)
        results = list(map(float, number))
        x = 0
        for i in results:
            if i <= 20:
                x = x + i
            else:
                pass
    return x

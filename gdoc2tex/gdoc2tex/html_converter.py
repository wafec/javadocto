import xml.etree.ElementTree as ET
from io import StringIO
import argparse
import logging
from bs4 import BeautifulSoup

LOG = logging.getLogger('html_converter')

def prep_step(html_filepath):
    content = ''
    with open(html_filepath) as f:
        soup = BeautifulSoup(f, 'html.parser')
        content = soup.prettify()
    return content

def convert_googledoc_html_to_tex(html_filepath):
    LOG.debug('GDoc entered: ' + html_filepath)
    content = prep_step(html_filepath)
    root = ET.fromstring(content)

    body = root.find('body')
    output = StringIO()
    accept_googledoc_html(body, output)

    textext = output.getvalue()
    output.close()
    return textext

def accept_googledoc_html(element, output):
    if element.tag == 'span':
        output.write(element.text)
        print("//" + element.tostring() + "//")
        input()
    else:
        if element.tag == 'p':
            output.write('\n\n')
        for child in element:
            accept_googledoc_html(child, output)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', default=False, action='store_true')
    parser.add_argument('htmlfilepath', type=str)
    parser.add_argument('output', type=argparse.FileType('w', encoding='utf-8'))
    args = parser.parse_args()
    if args.debug:
        LOG.setLevel(logging.DEBUG)
    res = convert_googledoc_html_to_tex(args.htmlfilepath)
    args.output.write(res)

if __name__ == '__main__':
    main()
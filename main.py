import sys
import html
import pytesseract
import json
import threading
import os
import uuid
import pdftotree
import re

from pdf2image import convert_from_path
from bs4 import BeautifulSoup, BeautifulStoneSoup
from lxml.html.clean import unicode
from datetime import datetime
try:
    from PIL import Image
except ImportError:
    import Image


class PDFLoader(threading.Thread):
    running = True
    type_ = "file"
    file = None
    file_ = None
    images = None
    text = None
    pages = {}
    uuid = None
    datetime_file_prefix = None
    pdf_html = None
    pdf_html_parsed = None
    file_prefix = "page_"
    
    def __init__(self, file_path, type=None, running=None):
        if os.path.isfile(file_path):
            self.file = file_path
            self.file_ = {
                "name": os.path.basename(self.file),
                "dir": os.path.dirname(self.file)
            }
            self.pdf_html = self.convert_pdf_to_html(self.file)

        self.uuid = str(uuid.uuid4())
        self.datetime_file_prefix = datetime.now().strftime("%Y%m%d")
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isdir(os.path.join(self.base_path, "data")):
            os.mkdir(os.path.join(self.base_path, "data"))

        self.data_path = os.path.join(self.base_path, "data")

        if type is not None and type != "file":
            self.type_ = type
        if running is not None and self.running is not running:
            self.running = running

        super(PDFLoader, self).__init__()

    def write_content_file_header(self, f):
        if f is not None:
            f.write("------------------------------------------------------------------- \n\n")
            f.write("file: " + self.file_["name"] + "\n")
            f.write("dir : " + self.file_["dir"] + "\n")
            f.write("date: " + datetime.now().strftime("%d.%m.%Y %H:%M:%S") + "\n")
            f.write("------------------------------------------------------------------- \n\n")

        else:
            return
            
    html_start_with_Artikel = []
    html_start_with_SN = []
    html_start_with_Number = []
    
    def get_linenumber_of_span_start(self, span_tag, html_):
        search_ = span_tag.prettify().splitlines()[0]
        html_lines = html_.splitlines()
        
        html_text = span_tag.get_text().strip() \
                                .replace(r"\\n", " ") \
                                .replace("\n", " ")
                                
        
        marked_number = False
        m_1 = re.search(r"^(\d+)", html_text, re.DOTALL)
        if m_1 is not None:
            # print(m_1.group(1))
            marked_number = True
                                
        marked = False
        if html_text.startswith("Artikel"):
            marked = True
        
        marked_sn = False
        if html_text.startswith("SN"):
            marked_sn = True
        
        
        found_i = 0
        for i_line in range(0, len(html_lines)):
            line = html_lines[i_line]
            if search_ in line:
                if marked is True:
                    self.html_start_with_Artikel.append(i_line)
                if marked_sn is True:
                    self.html_start_with_SN.append(i_line)
                if marked_number is True:
                    self.html_start_with_Number.append(i_line)
                return i_line
        return False

    def write_page_contents_to_file(self):
        if len(self.pdf_html) > 0:
            soup = BeautifulSoup(self.pdf_html, "lxml")
            if not os.path.isdir(os.path.join(self.data_path, self.datetime_file_prefix)):
                os.mkdir(os.path.join(self.data_path, self.datetime_file_prefix))
            
            current_folder = os.path.join(self.data_path, self.datetime_file_prefix)
            html_filename = (self.date_prefix() + self.uuid + "-" + self.file_prefix).rstrip("_page").rstrip("-") + ".html"
            json_filename = html_filename.rstrip(".html")+"_html.json"
                
            all_spans = soup.find_all("span", {"class": "ocrx_line"})
            
            span_contents_i = 0
            found_contents_i = 0
            span_contents = {}
            
            for span_i in range(0, len(all_spans)):
                current_span = all_spans[span_i]
                if len(current_span.get_text()) > 0:
                    span_content = self.unicode_to_html_entities(current_span.get_text().strip() \
                                .replace(r"\\n", " ") \
                                .replace("\n", " "))
                    
                    line_number = self.get_linenumber_of_span_start(current_span, self.pdf_html)
                    if line_number is not False:
                        found_i = line_number
                    else:
                        sys.exit(1)
                    if str(found_i) not in span_contents.keys():
                        span_contents[str(found_i)] = span_content
                    else:
                        if span_contents[str(found_i)] != span_content:                        
                            tmp_ = []
                            tmp_.append(span_contents[str(found_i)])
                            tmp_.append(span_content)
                            span_contents[str(found_i)] = tmp_
                        else:
                            span_contents[str(found_i)] = span_content
                
                    span_contents_i += 1            
            if span_contents_i > 0:
                json_filename = html_filename.rstrip(".html")+"_spans_html.json"
                with open(os.path.join(current_folder, json_filename), "w") as json_span_f:
                    json_span_f.write(json.dumps(span_contents, indent=4))
                    json_span_f.close()
   
            all_tr = soup.find("table").find_all("tr")
            contents = {}
            for ri in range(0, len(all_tr)):
                if str(ri) not in contents.keys():
                    contents[str(ri)] = {}
                current_tr = all_tr[ri]
                all_tds = current_tr.find_all("td")
                if len(all_tds) > 0:
                    for itd in range(0, len(all_tds)):
                        current_td = all_tds[itd]
                        if len(current_td.get_text()) > 0:
                            uni = current_td.get_text().strip() \
                                .replace(r"\\n", " ") \
                                .replace("\n", " ")
                            text_content = self.unicode_to_html_entities(uni)
                            contents[str(ri)][str(itd)] = text_content

            with open(os.path.join(current_folder, json_filename), "w") as json_f:
                json_f.write(json.dumps(contents, indent=4))
                json_f.close()
            
            with open(os.path.join(current_folder, html_filename), "w") as html_f:
                html_f.write(self.pdf_html)
                html_f.close()
            
            
            for p in self.pages.keys():
                page_id = p
                current_page = self.pages[page_id]
                current_filename = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + \
                                   self.uuid + "-" + self.file_prefix + str(page_id) + ".txt"

                with open(os.path.join(current_folder, current_filename), "w", encoding="utf-8") as current_page_f:
                    self.write_content_file_header(current_page_f)
                    current_page_f.write(current_page)
                    current_page_f.close()
                    
        else:
            print("no html")
            #print(current_filename)
            
            
    def run(self) -> None:
        try:
            self.images = self.pdf_to_img()
            self.get_pages()
            if len(self.pages.keys()) > 0:
                print("got some pages: " + str(len(self.pages.keys())))
                # for p in self.pages.keys():
                #    print(self.pages[p])
                self.write_page_contents_to_file()
        except TypeError:
            if self.images is None:
                print("error: no file")
                sys.exit(1)

    def ocr_core(self, image):
        return pytesseract.image_to_string(image)

    def get_pages(self):
        if self.images is not None:
            for pg, img in enumerate(self.images):
                if pg not in self.pages:
                    self.pages[pg] = self.ocr_core(img)
        else:
            print("error! is None")

    def pdf_to_img(self):
        return convert_from_path(self.file, poppler_path="/usr/bin")

    @staticmethod
    def date_prefix():
        return datetime.now().strftime("%Y%m%d_%H%M%S") + "_"

    @staticmethod
    def html_entities_to_unicode(text):
        """Converts HTML entities to unicode.  For example '&amp;' becomes '&'."""
        return unicode(BeautifulStoneSoup(text, convertEntities=BeautifulStoneSoup.ALL_ENTITIES))
    @staticmethod
    def unicode_to_html_entities(text):
        """Converts unicode to HTML entities.  For example '&' becomes '&amp;'."""
        return html.escape(text).encode('ascii', 'xmlcharrefreplace').decode()

    @staticmethod
    def convert_pdf_to_html(filepath_):
        return pdftotree.parse(filepath_)
        # , html_path=None, model_type=None, model_path=None, visualize=False


if __name__ == '__main__':
    if len(sys.argv) > 0:
        pdf_loader = PDFLoader(sys.argv[1])
        pdf_loader.start()
        pdf_loader.running = False
        pdf_loader.join()
    else:
        print("error: no input filepath specified")

'''
# img = cv2.imread('image.jpg')


# get grayscale image
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


# noise removal
def remove_noise(image):
    return cv2.medianBlur(image, 5)


# thresholding
def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


# dilation
def dilate(image):
    kernel = np.ones((5, 5), np.uint8)
    return cv2.dilate(image, kernel, iterations=1)


# erosion
def erode(image):
    kernel = np.ones((5, 5), np.uint8)
    return cv2.erode(image, kernel, iterations=1)


# opening - erosion followed by dilation
def opening(image):
    kernel = np.ones((5, 5), np.uint8)
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)


# canny edge detection
def canny(image):
    return cv2.Canny(image, 100, 200)


# skew correction
def deskew(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated


# template matching
def match_template(image, template):
    return cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED) 
'''

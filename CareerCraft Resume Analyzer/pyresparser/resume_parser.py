import os
import multiprocessing as mp
import io
import spacy
import pprint
from spacy.matcher import Matcher
from . import utils


class ResumeParser:
    def __init__(self, resume, skills_file=None, custom_regex=None):
        self.__nlp = spacy.load('en_core_web_sm')  # Load NLP model once
        self.__matcher = Matcher(self.__nlp.vocab)
        self.__skills_file = skills_file
        self.__custom_regex = custom_regex
        self.__details = {
            'name': None,
            'email': None,
            'mobile_number': None,
            'skills': None,
            'degree': None,
            'no_of_pages': None,
        }

        self.__resume = resume
        self.__process_resume()

    def __process_resume(self):
        """ Extract text and process resume """
        if isinstance(self.__resume, io.BytesIO):
            ext = self.__resume.name.split('.')[-1]
        else:
            ext = os.path.splitext(self.__resume)[1].lstrip('.')

        self.__text_raw = utils.extract_text(self.__resume, '.' + ext)
        self.__text = ' '.join(self.__text_raw.split())
        self.__nlp_doc = self.__nlp(self.__text)

        self.__noun_chunks = list(self.__nlp_doc.noun_chunks)
        self.__extract_basic_details()

    def __extract_basic_details(self):
        """ Extract details from resume """
        custom_nlp = self.__nlp(self.__text_raw)
        cust_ent = utils.extract_entities_wih_custom_model(custom_nlp)

        self.__details['name'] = cust_ent.get('Name', [None])[0] or utils.extract_name(self.__nlp_doc, self.__matcher)
        self.__details['email'] = utils.extract_email(self.__text)
        self.__details['mobile_number'] = utils.extract_mobile_number(self.__text, self.__custom_regex)
        self.__details['skills'] = utils.extract_skills(self.__nlp_doc, self.__noun_chunks, self.__skills_file)
        self.__details['no_of_pages'] = utils.get_number_of_pages(self.__resume)
        self.__details['degree'] = cust_ent.get('Degree')

    def get_extracted_data(self):
        return self.__details


def resume_result_wrapper(resume):
    return ResumeParser(resume).get_extracted_data()


if __name__ == '__main__':
    mp.freeze_support()
    pool = mp.Pool(mp.cpu_count())

    resumes = [os.path.join(root, file) for root, _, files in os.walk('resumes') for file in files]

    results = [pool.apply_async(resume_result_wrapper, args=(resume,)) for resume in resumes]
    results = [p.get() for p in results]

    pool.close()
    pool.join()

    pprint.pprint(results)

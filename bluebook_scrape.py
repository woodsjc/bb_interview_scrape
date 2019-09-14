##!#/usr/bin/python3
import os
import sys
#import json
import requests


API_URL = 'https://www.healthcarebluebook.com/api/HcbbUI/'
#API_URL = 'https://www.healthcarebluebook.com/api/'
APP_INIT = 'https://www.healthcarebluebook.com/api/HcbbUI/applicationinit'
GET_SEARCH_RESULTS = '{}GetSearchResults'.format(API_URL)
GET_PROCEDURE_DETAIL = '{}GetProcedureDetail'.format(API_URL)


def search_results(session, category=213, search_type=1):
    url = '{}?CategoryId={}&SearchType={}'.format(GET_SEARCH_RESULTS,
                                                  category, 
                                                  search_type)
    response = session.get(url)

    return response


def get_procedure_detail(session, language='en', ctf_id=50):
    '''Might be able to skip get search results and just go by ctf_id

    Also could combine different get functions with error checking
    '''
    url = '{}?Language={}&CftId={}'.format(GET_PROCEDURE_DETAIL,
                                           language,
                                           ctf_id)
    response = session.get(url)

    return response



def write_content(content, name='error.html'):
    '''debugging
    '''
    with open(name, 'w') as f:
        f.write(str(content))



if __name__ == '__main__':
    session = requests.session()
    #response = session.get(API_URL)
    response = session.get(GET_SEARCH_RESULTS)
    if response.status_code != 200:
        print("Could not connect to api: \n{}".format(r.content))
        sys.exit(1)

    response = session.get(APP_INIT)
    response = session.get("{}/CheckIdentCookie".format(API_URL))

    url = '{}?CategoryId={}&SearchType={}'.format(GET_SEARCH_RESULTS, 213, 1)
    response = session.get(url)

    if response != 200:
        print("Couldn't connect to get search results: \n{}".format(r.content))    
        sys.exit(1)
    
    data = response.json()
    results = data.get('SearchResults')
    search_info = results.get('SearchInformation')
    procedures = results.get('Procedures')

    for p in procedures:
        ctf_id = p.get('AnalyticsCftId')
        if not ctf_id:
            continue

        response = get_procedure_detail(session, 
                                        ctf_id=ctf_id
                                        )

        

    #response = search_results(session)
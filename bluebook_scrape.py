#!/usr/bin/env python3
import os
import sys
import csv
from time import sleep
import requests


API_URL = 'https://www.healthcarebluebook.com/api/HcbbUI/'
APP_INIT = 'https://www.healthcarebluebook.com/api/HcbbUI/applicationinit'
GET_SEARCH_RESULTS = '{}GetSearchResults'.format(API_URL)
GET_PROCEDURE_DETAIL = '{}GetProcedureDetails'.format(API_URL)


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


def get_facility_detail(data):
    '''
    gather facility
    name, address, and phone number 
    with a green cost ranking 
    '''
    if data.get('HasErrors'):
        return

    detail = data.get('ProcedureDetails')
    # pricing = detail.get('PricingInformations')
    # content_list = detail.get('ContentList')
    # module =  detail.get('ModuleConfigurations')
    facility_info = detail.get('FacilityInformation')
    facility = facility_info.get('Facilities')

    #print(detail['ProcedureName'])
    #print('\n'.join(("{}: {}".format(key, item) for key, item in pricing[0].items())))

    if not facility:
        print("{} - No facilities list".format(detail.get('ProcedureName')))
        return 
    
    good_deals = []
    for f in facility:
        if f.get('CostIndicator') == 1:
            address = '{}{}\n{}, {} {}'.format(
                f.get('Street1'), 
                '\n{}'.format(f.get('Street2')) if len(f.get('Street2')) > 0 else '',
                f.get('City'),
                f.get('State'),
                f.get('ZipCode'),
                )
            
            good_deals.append([detail.get('ProcedureName'),
                               f.get('DisplayName'),
                               address,
                               f.get('Phone'), 
                               ])

    return good_deals


def connect_to_api(session, zip_code, category):
    '''Had some trouble with session cookies gettings set to zip code
    So manually removed and set that entry
    '''
    response = session.get(GET_SEARCH_RESULTS)
    if response.status_code != 200:
        print("Could not connect to api: \n{}".format(response.content))
        sys.exit(1)

    response = session.get(APP_INIT)
    response = session.get("{}/CheckIdentCookie".format(API_URL))

    url = '{}?CategoryId={}&SearchType={}'.format(GET_SEARCH_RESULTS, category, 1)

    #cookie not updating
    del session.cookies['hcbb']
    session.cookies['hcbb'] = "cust=hcbb_prod&language=English&zip={}".format(zip_code)

    response = session.get(url)
    if response.status_code != 200:
        print("Couldn't connect to get search results: \n{}".format(response.content))    
        sys.exit(1)

    return response


def export_deals(detail, name='tmp.csv'):
    if len(detail) < 1:
        print('Nothing to write - {}'.format(name))
        return
    
    with open(name, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(detail)

    print("Wrote {}".format(name))
    return


if __name__ == '__main__':
    '''take in category & zip then return procedure info

    reread directions and asked for mri so dont need all categories
    also just around nashville

    mri_category = 39
    '''
    mri_category = 39
    zip_code = 37211
    session = requests.session()
    response = connect_to_api(session, zip_code=zip_code, category=mri_category)

    data = response.json()
    results = data.get('SearchResults')
    search_info = results.get('SearchInformation')
    procedures = results.get('Procedures')

    good_deals = [['Procedure', 'Name', 'Address', 'Phone Number']]
    for p in procedures:
        ctf_id = p.get('AnalyticsCftId')
        if not ctf_id:
            continue

        response = get_procedure_detail(session, ctf_id=ctf_id)
        if response.status_code == 200:
             tmp = get_facility_detail(response.json())
             if tmp:
                 good_deals += tmp

        sleep(30) 
        
    export_deals(good_deals, 'bluebook_scrape_data.csv')
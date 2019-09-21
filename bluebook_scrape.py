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


def patch_cookie(session, zip_code):
    '''The hcbb cookie keeps breaking on multiple requests
    '''
    del session.cookies['hcbb']
    session.cookies['hcbb'] = "cust=hcbb_prod&language=English&zip={}".format(zip_code)
    return


def search_results(session, category=213, search_type=1):
    url = '{}?CategoryId={}&SearchType={}'.format(GET_SEARCH_RESULTS,
                                                  category, 
                                                  search_type)
    sleep(1)
    response = session.get(url)
    
    if response.status_code != 200:
        print("Couldn't connect to get search results: \n{}".format(response.content))    
        sys.exit(1)

    return response


def get_procedure_detail(session, language='en', ctf_id=50, zip_code=37211):
    '''Have to init app
    then set zip
    then set marketplace
    and have list of procedures to run this
    '''
    url = '{}?Language={}&CftId={}&DirectSearch=true'.format(
        GET_PROCEDURE_DETAIL,
        language,
        ctf_id)
    #session.headers['Referer'] = "https://www.healthcarebluebook.com/ui/proceduredetails/{}".format(ctf_id)
    #patch_cookie(session, zip_code)
    response = session.get(url)

    return response


def set_zip(session, zip_code):
    url = '{}GetZipLocation?request.ZipCode={}'.format(API_URL, zip_code)
    sleep(1)
    response = session.get(url)

    if response.status_code != 200:
        print("Error initiating zip code \n{}".format(response.content))
        sys.exit(1)

    return response


def set_marketplace(session):
    url = '{}SetMarketplaceMedicare?Medicare=false'.format(API_URL)
    sleep(1)
    response = session.get(url)

    if response.status_code != 200:
        print("Error setting marketplace \n{}".format(response.content))
        sys.exit(1)

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
    if not facility_info:
        print("{} - No facilitiy Information".format(detail.get('ProcedureName')))
        return 

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

    left out initial zip code setting when setting up app in set_zip function
    and caused lots of downstream errors
    '''
    session.headers['Host'] = 'www.healthcarebluebook.com'
    session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0'
    session.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    session.headers['Accept-Language'] = 'en-US,en;q=0.5'
    session.headers['Accept-Encoding'] =  'gzip, deflate, br'
    session.headers['DNT'] = '1'
    session.headers['Connection'] = 'keep-alive'
    session.headers['Upgrade-Insecure-Requests'] = '1'
    
    response = session.get(APP_INIT)
    if response.status_code != 200:
        print("Error initiating app \n{}".format(response.content))

    response = session.get("{}/CheckIdentCookie".format(API_URL))
    if response.status_code != 200:
        print("Error initiating check indent cookie \n{}".format(response.content))
    
    response = set_zip(session, zip_code)
    response = set_marketplace(session)
    response = search_results(session, category=category)
    
    return response


def make_log_request(session, zip_code, category):
    '''Not sure why facility info not always returned
    trying to do this log posting in hope it will generate

    dont think this part required
    '''
    url = '&'.join(("{}Log?request.level=5".format(API_URL),
                    "request.pageName=searchresults",
                    "request.url=https://www.healthcarebluebook.com/ui/searchresults?CatId={}".format(category),
                    "Tab=ShopForCare",
                    "request.zipCode={}".format(zip_code),
                    "request.isMobileBrowser=false",
                    "request.userAgent={}".format(session.headers['User-Agent']),
                    "request.customerCode=hcbb_provmarket",
                    "request.language=en"
                    ))

    response = session.get(url)

    if response.status_code != 200:
        return response

    url = "{}PostLog".format(API_URL)
    ref_url = "https://www.healthcarebluebook.com/ui/consumerfront"
    post_data = {
        "Level":6,
        "pageName":"searchresults",
        "url":"https://www.healthcarebluebook.com/ui/searchresults?CatId={}&Tab=ShopForCare".format(category),
        "activityId":13,
        "activityDetails": '{"ReferringUrl":"' + ref_url + '"}',
    }
    response = session.post(url, data=post_data)

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

    if not results:
        print("Unable to pull data from api \n{}".format(data))
        sys.exit(1)
    elif results.get('DisplayCaptcha'):
        print("Site is serving captcha \n{}".format(results))
        sys.exit(1)

    search_info = results.get('SearchInformation')
    procedures = results.get('Procedures')

    sleep(1)
    good_deals = [['Procedure', 'Name', 'Address', 'Phone Number']]
    for p in procedures:
        ctf_id = p.get('AnalyticsCftId')
        if not ctf_id:
            continue

        response = get_procedure_detail(session, ctf_id=ctf_id, zip_code=37211)
        if response.status_code == 200:
             tmp = get_facility_detail(response.json())
             if tmp:
                 good_deals += tmp

        sleep(45) 
        
    export_deals(good_deals, 'bluebook_scrape_data.csv')
# #!/usr/bin/env python3
import os
import sys
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


def bad_code():
    '''tried spoofing user agent but had bad url for procedure query. Left off the s on on details

    hopefully dont need to use this section
    TODO
    delete me
    '''
    # headers = {
    #     'Host': 'www.healthcarebluebook.com',
    #     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0',
    #     'Accept': 'application/json, text/plain, */*',
    #     'Accept-Language': 'en-US,en;q=0.5',
    #     'Accept-Encoding': 'gzip, deflate, br',
    #     'DNT': '1',
    #     'Connection': 'keep-alive',
    # }

    # session.headers = headers
    ref_url = "https://www.healthcarebluebook.com/ui/proceduredetails/{}".format(ctf_id)
    post_data = {
        "Level":6,
        "pageName":"searchresults",
        "url":"https://www.healthcarebluebook.com/ui/searchresults?CatId={}&Tab=ShopForCare".format(cat_id),
        "activityId":13,
        "activityDetails": {"ReferringUrl": ref_url} 
    }

    #this part now working
    response = session.get('&'.join(("{}Log?request.level=5".format(API_URL),
                                        "request.pageName=searchresults",
                                        "request.url=https://www.healthcarebluebook.com/ui/searchresults?CatId={}".format(cat_id),
                                        "Tab=ShopForCare",
                                        "request.zipCode={}".format(zip_code),
                                        "request.isMobileBrowser=false",
                                        "request.userAgent=Mozilla/5.0%20(X11;%20Linux%20x86_64;%20rv:70.0)%20Gecko/20100101%20Firefox/70.0",
                                        "request.customerCode=hcbb_provmarket",
                                        "request.language=en"
                                        )))

    #response = session.post("{}PostLog".format(API_URL), data=post_data)
    #session.headers['Referer'] = "https://www.healthcarebluebook.com/ui/proceduredetails/{}".format(ctf_id)
    #still failing with 404 error but prints out huge page                                        

    return


def show_procedures(data):
    '''not sure what all to print out
    looks like a lot of stuff in html

    TODO 
    check out  details.get('ModuleConfigurations')

    data requested is actually in FacilityInformation and then under Facilities
    not sure why facility not populating
    '''
    if data.get('HasErrors'):
        return

    detail = data.get('ProcedureDetails')
    pricing = detail.get('PricingInformations')
    content_list = detail.get('ContentList')
    module =  detail.get('ModuleConfigurations')
    facility = detail.get('FacilityInformation')

    print(detail['ProcedureName'])
    print('\n'.join(("{}: {}".format(key, item) for key, item in pricing[0].items())))

    facility_detail = facility.get('Facilities')
    if not facility_detail:
        print("No facilities list")
        return
    ###maybe write here to csv/json


    return


if __name__ == '__main__':
    '''take in category & zip then return procedure info

    reread directions and asked for mri so dont need all categories
    also just around nashville

    mri_category = 39
    '''
    session = requests.session()
    response = session.get(GET_SEARCH_RESULTS)
    if response.status_code != 200:
        print("Could not connect to api: \n{}".format(response.content))
        sys.exit(1)

    response = session.get(APP_INIT)
    response = session.get("{}/CheckIdentCookie".format(API_URL))

    mri_category = 39
    zip_code = 37211
    url = '{}?CategoryId={}&SearchType={}'.format(GET_SEARCH_RESULTS, mri_category, 1)
    response = session.get(url)

    if response != 200:
        print("Couldn't connect to get search results: \n{}".format(response.content))    
        sys.exit(1)
    
    data = response.json()
    results = data.get('SearchResults')
    search_info = results.get('SearchInformation')
    procedures = results.get('Procedures')

    for p in procedures:
        ctf_id = p.get('AnalyticsCftId')
        if not ctf_id:
            continue

        response = get_procedure_detail(session, ctf_id=ctf_id)
        if response.status_code == 200:
            show_procedures(response.json())

        #sleep(1) 
        #doesnt go super fast with print statements

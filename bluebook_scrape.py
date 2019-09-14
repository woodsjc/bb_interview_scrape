##!#/bin/python3
import requests


GET_SEARCH_RESULTS = r'https://www.healthcarebluebook.com/api/HcbbUI/GetSearchResults'
API_ULR = 'https://www.healthcarebluebook.com/api/HcbbUI/'


def search_results(session, category=213, search_type=1):
    url = '{}?CategoryId={}&SearchType={}'.format(GET_SEARCH_RESULTS,
                                                  category, 
                                                  search_type)
    response = session.post(url)

    return response


if __name__ == '__main__':
    session = requests.session()
    response = session.get(API_URL)
    response = search_results(session)
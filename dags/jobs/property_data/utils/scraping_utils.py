import os
import sys
from bs4 import BeautifulSoup
import subprocess
from requests import get
import requests
from datetime import datetime, timedelta
import time
from dateutil import parser
import logging

def df_filename():
    """This returns csv filename for today

    Keyword arguments:
        None

    Returns:
        df_filename: [string] csv filename data_[todays_date].csv
    """
    now = datetime.now()
    datestr = now.strftime('%Y%m%d')
    df_filename = 'data_{}.csv'.format(datestr)
    return df_filename

def find_latest_soldpx_csvname(specific_date='<YYYYMMDD>'):
    """Finds the newest csv name in the drive.  Can pull a specific date
       by filling in the specific date field.

    Keyword arguments:
        specific date: [string in YYYYMMDD date format ] This is optional.  Standard it to leave blank and it will 
                        pull the latest.

    Returns:
        returns a csv filename to pull from google storage bucket.
    """
    command = ['sudo','gsutil','ls','gs://rooftop-data/sold_home_data/']
    out = subprocess.check_output(command)
    csv_list = str(out).split('\n')
    parsed_csv_list = [x[x.find('data_')+5:-4] for x in csv_list]
    date_csv_list = [x for x in parsed_csv_list if len(x)==8]
    dates = [parser.parse(x) for x in date_csv_list]
    now = datetime.now()
    newest = max(dt for dt in dates if dt < now)
    csv_filename = 'soldhomedata_{}.csv'.format(newest.strftime('%Y%m%d'))
    return csv_filename

def find_latest_csvname(specific_date='<YYYYMMDD>'):
    """Finds the newest csv name in the drive.  Can pull a specific date
       by filling in the specific date field.

    Keyword arguments:
        specific date: [string in YYYYMMDD date format ] This is optional.  Standard it to leave blank and it will 
                        pull the latest.

    Returns:
        returns a csv filename to pull from google storage bucket.
    """
    command = ['sudo','gsutil','ls','gs://rooftop-data/properties_data/']
    out = subprocess.check_output(command)
    csv_list = str(out).split('\\n')
    parsed_csv_list = [x[x.find('data_')+5:-4] for x in csv_list]
    print(parsed_csv_list)
    date_csv_list = [x for x in parsed_csv_list if len(x)==8]
    print(date_csv_list)
    dates = [parser.parse(x) for x in date_csv_list]
    print(dates)
    now = datetime.now()
    newest = max(dt for dt in dates if dt < now)
    csv_filename = 'data_{}.csv'.format(newest.strftime('%Y%m%d'))
    return csv_filename

def fetch_from_google_storage(google_storage_bucket, path_to_file, filename, destination_folder):
    """Pulls file from google cloud storage bucket
    
    Keyword arguments:
        google_storage_bucket: [string] name of google storage bucket e.g. django-uploads
        path_to_file: [string] path to the folder of the file you want to pull from
        google storage
        filename: [string] name of the file you want to pull e.g. data_<YYYYMMDD>.csv
        destination_folder: [string] path to the folder you want to save the pulled file in
    
    Returns:
    returns success status if successful
    """
    pull_path = 'gs://{}/{}/{}'.format(google_storage_bucket, path_to_file, filename)
    print('pull path is {}'.format(pull_path))
    destination_path = os.getcwd() + '/{}/{}'.format(destination_folder, filename)
    print('destination path is {}'.format(destination_path))
    gsutil_command = ['sudo','gsutil', 'cp', pull_path,destination_path]
    try:
        subprocess.call(gsutil_command)
        print('pulled file {} successfully from the {} google storage bucket'.format(filename,google_storage_bucket))
    except Exception as e:
        print('pull failed. error message: {}'.format(e))

def generate_csv_filename(last_run_date_str):
    """Generates name of csv file given a date
    
    Keyword arguments:
        last_run_date_str: [string] the last run date for the cron job, as a string

    Returns:
        csv_filename: [string] the filename for the csv file with the data stored in it
    """
    csv_filename = 'data_{}.csv'.format(last_run_date_str)
    return csv_filename

def send_to_google_storage(google_storage_bucket, path_to_file, filename, destination_folder):
    """Sends a file to google cloud storage bucket from local drive
    
    Keyword arguments:
        google_storage_bucket: [string] name of google storage bucket e.g. django-uploads
        path_to_file: [string] path to the folder of the file you want to pull from
        google storage
        filename: [string] name of the file you want to pull e.g. data_<YYYYMMDD>.csv
        destination_folder: [string] path to the folder you want to save the pulled file in
    
    Returns:
    returns success status if successful
    """
    gs_path = 'gs://{}/{}/{}'.format(google_storage_bucket, path_to_file, filename)
    print('google storage path is {}'.format(gs_path))
    local_path = os.getcwd() + '/{}/{}'.format(destination_folder, filename)
    print('local file path is {}'.format(local_path))
    gsutil_command = ['sudo', 'gsutil', 'cp', local_path, gs_path]
    try:
        subprocess.call(gsutil_command)
        print('sent {} successfully to the {} google storage bucket'.format(filename,google_storage_bucket))
    except Exception as e:
        print('pull failed. error message: {}'.format(e))


def find_remax_urls(soup):
    """
    soup:  bs4 soup -  BeautifulSoup object of a url of a remax search result page
    BASE_URL: string - the beginning of the URL that remax uses
    -
    returns: list - a list of all URLs of homes on the given page  
    """
    BASE_URL='https://leadingedge-northcarolina.remax.com'
    remax_urls = []
    linksoup = soup.find_all('a',class_='listing-pane-info js-detaillink')
    for crouton in linksoup:
        remax_urls.append(BASE_URL+crouton['href'])
    return remax_urls

def pull_image_urls_from_slideshow(soup):
    """
    soup: [bs4 soup object]  the soup object of the website that we are going to be scraping from.
    
    returns: [list] a list of urls of images of the house of a given webpage
    """
    imglist = []
    for noodle in soup.find_all('figure',class_='figure figure__slideshow'):
        if len(noodle) == 3:
            imglist.append(noodle['data-href'])
    return imglist

def pull_home_data(home_url):
    """
    home_url - string: url of the remax home from which we wish to extract data
    - 
    returns: home_dict: dict {
    
            address:{
                    address_line1: [string] - street number, street
                    unit: [string] - optional, apartment number, extra info
                    state: [string] - state abbreviation (two letter)
                    city: [string]
                    country: [string] - country str
                    zipcode: [string] - five number zipcode
                    }
                    
            listing_data: {
            
                    list_price: int - home listing price (in USD)
                    num_bedrooms: float - number of bedrooms (1 decimal)
                    num_bathrooms: float - number of bathrooms (1 decimal)
                    building_area_sq_ft: positive int in SQUARE FEET
            
            }
            
            valuation: {
          
            }
            
            features: {
                
                lot_size: float - size of the yard, in ACRES
                floors: int - number of floors of the house
                garage: int - is there a garage (not quite sure what this one is tbh)
                date_listed_on_site: [datetime] date that the house was listed on the site 
                school: [text] - average rating of all nearby schools
                coords: [tuple] a tuple of the latitude and longitude of the address
                desc: [text] a paragraph description of the home
                mls: [int] MLS listing number
                recent_selling_history: [list of tuples] list of tuples of buying history
                is_foreclosure: [boolean] is this a foreclosure home?
                
            }
            
            images: {
            
                image_list: list - a list of all the image urls associated with this house
            
            }
    }       
    
    """
    temp_dir = os.getcwd()+'/data/temp/'
    scrape_address = {}
    print (home_url)
    homepage = ''
    while homepage == '':
        try:
            homepage = get(home_url,verify=False)
        except:
            print('Connection refused!')
            print('Let me sleep for 10 seconds')
            print('Zzzzzzzz.....')
            time.sleep(10)
            print('I woke up, now let me try this again.')
    homesoup = BeautifulSoup(homepage.text,'html.parser')
    scrape_address['address_line1']  = homesoup.find_all('li',attrs={'hmsitemprop':'Address'})[0].text.strip()
    addr = homesoup.find_all('li',attrs={'hmsitemprop':'Address'})[0].text.strip()
    if '#' in addr:
        idx = addr.find('#')
        scrape_address['address_line1'] = str(addr[:idx-1])
        scrape_address['unit'] = 'Unit '+str(addr[idx+1:])
    else:
        scrape_address['address_line1']  = homesoup.find_all('li',attrs={'hmsitemprop':'Address'})[0].text.strip()
    scrape_address['city']  = homesoup.find_all('li',attrs={'hmsitemprop':'City'})[0].text.strip()
    scrape_address['state']  = homesoup.find_all('li',attrs={'hmsitemprop':'State'})[0].text.strip()
    scrape_address['zipcode']  = homesoup.find_all('li',attrs={'hmsitemprop':'Zip'})[0].text.strip()
    try:
        response = canonicalizeAddress(scrape_address)[0]
    except:
        print('response has failed')
    try:
        address={}
        address['address_line1'] = str(response['address_info']['address'])
        address['city'] = str(response['address_info']['city'])
        address['zipcode'] = str(response['address_info']['zipcode'])
        address['state'] = str(response['address_info']['state'])
        address['unit'] = str(response['address_info']['unit'])
        address['lat'] = str(response['address_info']['lat'])
        address['lon'] = str(response['address_info']['lng'])
        address['slug'] = str(response['address_info']['slug'])
    except:
        address={}
    try: 
        if str(response['address_info']['status']['details'][0])=='Address fully verified':
            print ("verified address with house canary API")
        else:
            print( 'error for address %s %s %s' % (address['address_line1'],address['city'],address['state']))       
    except:
        print ('error for address')
    # GET LISTING DATA
    listing_data = {}
    try:
        listing_data['num_bedrooms'] = int(homesoup.find_all('span',class_='listing-detail-beds-val')[0].text.strip())
    except:
        listing_data['num_bedrooms'] = None
    try:
        listing_data['num_bathrooms'] = int(homesoup.find_all('span',class_='listing-detail-baths-val')[0].text.strip())
    except:
        listing_data['num_bathrooms'] = None
    try:
        listing_data['building_area_sq_ft'] = int(homesoup.find_all('span',class_='listing-detail-sqft-val')[0].text.strip().replace(',',''))
    except:
        listing_data['building_area_sq_ft'] = None
    listing_data['list_price'] = int(homesoup.find_all('span',class_='listing-detail-price-amount pad-half-right')[0].text.strip().replace(',',''))
    print(listing_data['list_price'])
    try:
        listing_data['home_type'] = find_nested_info(homesoup,'Listing Type')
    except:
        listing_data['home_type'] = None
    # GET HOME FEATURES
    features = {}
    try:
        features['MLS'] = int(homesoup.find_all('li',attrs={'hmsitemprop':'MLSNumber'})[0].text.strip())
    except:
        features['MLS'] = None
    features['is_foreclosure'] = str(homesoup.find_all('li',attrs={'hmsitemprop':'IsForeclosure'})[0].text.strip()) == 'True'
    try:
        features['desc'] = homesoup.find_all('p',class_="listing-bio")[0].text.strip()
    except:
        features['desc'] = None
    try:
        features['year_built'] = find_nested_info(homesoup,'Year Built')
    except:
        features['year_built'] = None
    try:
        school_score = get_average_school_rating(homesoup)
    except:
        school_score = None
    try:
        features['school_score'] = school_score
    except:
        features['school_score'] = None
    try:
        features['floors'] = find_nested_info(homesoup,'Floors')
    except:
        features['floors'] = None
    try:
        garage = find_nested_info(homesoup,'Garage')
        if garage>0:
            features['garage_detail'] = str(garage)
            features['has_garage'] = True
        else:
            features['garage_detail'] = None
            features['has_garage'] = False
    except:
        features['garage_detail'] = None
        features['has_garage'] = False
    try:
        if find_extra_nested_info(homesoup,'Sewer') == 'City Sewer':
            features['has_septic'] = False
        else:
            features['has_septic'] = True
    except:
        features['has_septic'] = None
    try:
        if find_extra_nested_info(homesoup,'Water') == 'City Water':
            features['has_well'] = False
        else:
            features['has_well'] = True
    except:
        features['has_well'] = None
    try:
        if ' pool ' in features['desc']:
            features['has_pool'] = True
        else:
            features['has_pool'] = False
    except:
        features['has_pool'] = None

    if features['has_well'] == False and features['has_septic'] == False and features['has_pool'] == False:
        features['no_pool_well_septic'] = True
    else:
        features['no_pool_well_septic'] = False
    try:
        subdiv = find_nested_info(homesoup,'Subdivision')
        features['has_established_subdivision'] = True
        features['subdivision'] = subdiv
    except:
        features['has_established_subdivision'] = False
        features['subdivision'] = None
    try:
        features['listing_status'] = find_nested_info(homesoup,'Listing Status')
    except:
        features['listing_status'] = None
    try:
        features['num_full_bath'] = find_nested_info(homesoup,'Full Bath')
    except:
        features['num_full_bath'] = 0
    try:
        features['num_half_bath'] = find_nested_info(homesoup,'Half Bath')
    except:
        features['num_half_bath'] = 0
    dos = homesoup.find_all('span',attrs={'title':'DOS'})[0].text.strip()[14:]
    if '<' in dos:
        features['days_on_site'] = 1
    else:
        features['days_on_site'] = int(dos)
    starting_date = datetime.today() - timedelta(days=int(features['days_on_site']))
    features['start_date_on_site'] = starting_date.strftime('%Y-%m-%d')
    try:
        features['interior_features'] = find_extra_nested_info(homesoup,'Interior Features')
    except:
        features['interior_features'] = None
    try:
        features['flooring'] = find_extra_nested_info(homesoup,'Flooring')
    except:
        features['flooring'] = None
    try:
        features['remax_url'] = home_url
    except:
        features['remax_url'] = None
    # GET IMAGE DATA
    images={}
    imglist = pull_image_urls_from_slideshow(homesoup)
    images['img_gallery'] = ';'.join(imglist)
    try:
        images['image_header'] = imglist[0]
    except:
        images['image_header'] = None
    home_dict = {}
    home_dict['address'] = address
    home_dict['listing_data'] = listing_data
    home_dict['images'] = images
    home_dict['features'] = features
    return home_dict
    
def get_average_school_rating(soup,radius=5):
    """
    this querys the remax API endpoint and 
    
    inputs
    soup: [bs4 soup object] soup object of webpage for home we are scraping
    
    -
    output
    returns [int] an integer of how good the school is, on a scale of 0 to 100
    A+ 100
    A 95
    A- 91
    B+ 88
    B 85
    B- 81
    C+ 78
    C 75
    C- 71
    D+ 68
    D 65
    D- 61
    F 50
    
    this rating excludes and schools that have an 'N/A' rating in the average
    
    
    """
    API_call_BASE = "https://leadingedge-northcarolina.remax.com/api/homefacts/"
    
    lat = float(soup.find_all('li',attrs={ 'hmsitemprop':"Latitude"})[0].text.strip())
    lon = float(soup.find_all('li',attrs={ 'hmsitemprop':"Longitude"})[0].text.strip())
    zipcode  = soup.find_all('li',attrs={'hmsitemprop':'Zip'})[0].text.strip()
    
    API_call = API_call_BASE + '?&radius={}&lat={}&long={}&schoolspergrades=true&zipcode={}'.format(str(radius),str(lat),str(lon),str(zipcode))
    
    response = get(API_call)
    response.raise_for_status()
    
    home_stats = response.json()
    
    school_grade = 0
    count=0
    for idx, school in enumerate(home_stats['HFSchools']):
        gradestr = school['SchoolGrade']
        if gradestr == 'Unavailable':
            count+=1
        else:
            score = gradeToScore(gradestr)
            school_grade += score
    adj_idx = idx+1-count
    avg_school_score = float(school_grade)/float(adj_idx)
    
    
    
    return avg_school_score
    

def gradeToScore(gradestr):
    """
    takes a string of the grade of a school as an input, returns a number fr 0 to 100
    
    input
    gradestr: [string] string of the grade of the school pulled from the remax API
    
    returns school_score [float] a number fr 0 to 100 that is the converted school grade
    """
    
    
    grade2score = {
        'Aplus': 100,
        'A': 95,
        'Aminus':91,
        'Bplus':88,
        'B':85,
        'Bminus':81,
        'Cplus':78,
        'C':75,
        'Cminus':71,
        'Dplus':68,
        'D':65,
        'Dminus':61,
        'F':50,
    }
    
    school_score = grade2score[gradestr]
    return school_score
    
def fetchremaxJSON(lat,lon,radius=5):
    """
    takes a coords and an option radius (mi) and returns a json filled with neighborhood stats.  school stuff, incomes, earthquake frequencies, etc
    
    inputs
    lat: [float] latitude of location you want to search from
    lon: [float] longitude of location you want to search from
    radius: [int] (optional) radius from coordinates from which to scrape data
    
    """
    
    API_call_BASE = "https://leadingedge-northcarolina.remax.com/api/homefacts/"
    API_call = API_call_BASE + '?&radius={}&lat={}&long={}&schoolspergrades=true'.format(str(radius),str(lat),str(lon))
    response = get(API_call)
    response.raise_for_status()
    home_stats = response.json()
    return home_stats
    
    

def find_nested_info(soup,info):
    """
    soup: [bs4 soup obj] the soup obj of webpage to scrape
    
    returns: [int] year the house was built
    
    """

    for idx, noodle in enumerate(soup.find_all('dt',class_='listing-detail-stats-main-key')):
        if info in noodle.text.strip():
            data = soup.find_all('dd',class_="listing-detail-stats-main-val")[idx]
            data= data.text.strip()
    return data


def canonicalizeAddress(remax_address_dict):
    """
    this takes a dictionary of address data scraped from the remax website and calls the housecanary API
    to make sure that all of the data is standardized
    
    input
    
    remax_address_dict [dict] {
        address_line1: [string] steet number, street
        unit: [int] (optional) unit no
        state: [string] state, two letter abbreviation
        zipcode: [int] - five number zipcode
    }
    
    returns [dict] of street address info from the house canary API 
    
    """
    hc_key = '9SJCA9DISJVUAVAS4QQQ'
    hc_secret = '80vGOq9qYEy46a53XsUReFKpyvPK1owG' 
    if 'unit' in remax_address_dict:
        params = {
        'address': remax_address_dict['address_line1'],
        'state': remax_address_dict['state'],
        'zipcode': remax_address_dict['zipcode'],
        'city': remax_address_dict['city'],
        'unit':remax_address_dict['unit']
        }
    else:
        params = {
            'address': remax_address_dict['address_line1'],
            'state': remax_address_dict['state'],
            'zipcode': remax_address_dict['zipcode'],
            'city': remax_address_dict['city'],
        }
    geocode_url = 'https://api.housecanary.com/v2/property/geocode'
    response = requests.get(geocode_url, params=params, auth=(hc_key, hc_secret))
    response = response.json()
    return response

def find_extra_nested_info(soup,info):
    """Find the nested info in the remax site
    Keyword arguments:
        soup: [bs4 soup obj] the soup obj of webpage to scrape
    Returns: 
        data: [int] year the house was built
    """
    for idx, noodle in enumerate(soup.find_all('dt',class_='listing-detail-stats-more-key')):
        if info in noodle.text.strip():
            data = soup.find_all('dd',class_="listing-detail-stats-more-val")[idx]
            data= data.text.strip()
    return data
    
def flatten_dict(dd, separator='_', prefix=''):
    return { prefix + separator + k if prefix else k : v
             for kk, vv in dd.items()
             for k, v in flatten_dict(vv, separator, kk).items()
             } if isinstance(dd, dict) else { prefix : dd }

def create_remax_city_url(city,state,page):
    BASE = 'https://executive3-northcarolina.remax.com/realestatehomesforsale/'
    url = BASE + '-'.join([city,state,'p{0:03d}'.format(page)])+'.html'
    print(url)
    return url

def get_crime_index(block_id):
    """
    this takes an address dictionary that has already been validated.

    it returns a crime index, where the property falls on the national crime index
    """
    hc_key = '9SJCA9DISJVUAVAS4QQQ'
    hc_secret = '80vGOq9qYEy46a53XsUReFKpyvPK1owG' 
    params = {
        'block_id': block_id,
    }
    crime_url = 'https://api.housecanary.com/v2/block/crime'
    response = requests.get(crime_url,params=params,auth=(hc_key,hc_secret))
    response = response.json()
    all_crime = response[0]['block/crime']['result']['all']['nation_percentile']
    violent_crime = response[0]['block/crime']['result']['violent']['nation_percentile']
    return all_crime,violent_crime

def find_sale_history(soup):
    
    sale_list = soup.find_all('td',class_='hv-price--results title-50')
    reformatted_list = [str(x.text.replace(",",'').replace("$",'').strip()) for x in sale_list]
    salestring = ';'.join(reformatted_list)
    return salestring

def pull_sold_home_data(home_url):
    """
    Keyword arguments:
        home_url - string: url of the remax home from which we wish to extract data
    - 
    returns: home_dict: dict {
    
            address:{
                    address_line1: [string] - street number, street
                    unit: [string] - optional, apartment number, extra info
                    state: [string] - state abbreviation (two letter)
                    city: [string]
                    country: [string] - country str
                    zipcode: [string] - five number zipcode
                    }
                    
            listing_data: {
            
                    list_price: int - home listing price (in USD)
                    num_bedrooms: float - number of bedrooms (1 decimal)
                    num_bathrooms: float - number of bathrooms (1 decimal)
                    building_area_sq_ft: positive int in SQUARE FEET
            
            }
            features: {
                
                lot_size: float - size of the yard, in ACRES
                floors: int - number of floors of the house
                garage: int - is there a garage (not quite sure what this one is tbh)
                date_listed_on_site: [datetime] date that the house was listed on the site 
                school: [text] - average rating of all nearby schools
                coords: [tuple] a tuple of the latitude and longitude of the address
                desc: [text] a paragraph description of the home
                mls: [int] MLS listing number
                recent_selling_history: [list of tuples] list of tuples of buying history
                is_foreclosure: [boolean] is this a foreclosure home?
                
            }
            
            images: {
            
                image_list: list - a list of all the image urls associated with this house
            
            }
    }       
    """
    scrape_address = {}
    print(home_url)
    homepage = ''
    while homepage == '':
        try:
            homepage = get(home_url,verify=False)
        except:
            print('Connection refused!')
            print('Let me sleep for 10 seconds')
            print('Zzzzzzzz.....')
            time.sleep(10)
            print('I woke up, now let me try this again.')
    homesoup = BeautifulSoup(homepage.text,'html.parser')
    scrape_address['address_line1']  = homesoup.find_all('li',attrs={'hmsitemprop':'Address'})[0].text.strip()
    addr = homesoup.find_all('li',attrs={'hmsitemprop':'Address'})[0].text.strip()
    if '#' in addr:
        idx = addr.find('#')
        scrape_address['address_line1'] = str(addr[:idx-1])
        scrape_address['unit'] = 'Unit '+str(addr[idx+1:])
    else:
        scrape_address['address_line1']  = homesoup.find_all('li',attrs={'hmsitemprop':'Address'})[0].text.strip()
    scrape_address['city']  = homesoup.find_all('li',attrs={'hmsitemprop':'City'})[0].text.strip()
    scrape_address['state']  = homesoup.find_all('li',attrs={'hmsitemprop':'State'})[0].text.strip()
    scrape_address['zipcode']  = homesoup.find_all('li',attrs={'hmsitemprop':'Zip'})[0].text.strip()
    try:
        response = canonicalizeAddress(scrape_address)[0]
    except:
        response = canonicalizeAddress(scrape_address)[0]
        print(response)
        print('response has failed')
    
    address={}
    address['address_line1'] = str(response['address_info']['address'])
    address['city'] = str(response['address_info']['city'])
    address['zipcode'] = str(response['address_info']['zipcode'])
    address['state'] = str(response['address_info']['state'])
    address['unit'] = str(response['address_info']['unit'])
    address['lat'] = str(response['address_info']['lat'])
    address['lon'] = str(response['address_info']['lng'])
    address['slug'] = str(response['address_info']['slug'])
    try: 
        if str(response['address_info']['status']['details'][0])=='Address fully verified':
            print ("verified address with house canary API")
        else:
            print ('error for address %s %s %s' % (address['address_line1'],address['city'],address['state']))
            
    except:
        print( 'error for address %s %s %s' % (address['address_line1'],address['city'],address['state']))
 
    listing_data = {}
    try:
        listing_data['num_bedrooms'] = int(homesoup.find_all('span',class_='listing-detail-beds-val')[0].text.strip())
    except:
        listing_data['num_bedrooms'] = None
    try:
        listing_data['num_bathrooms'] = int(homesoup.find_all('span',class_='listing-detail-baths-val')[0].text.strip())
    except:
        listing_data['num_bathrooms'] = None
    try:
        listing_data['building_area_sq_ft'] = int(homesoup.find_all('span',class_='listing-detail-sqft-val')[0].text.strip().replace(',',''))
    except:
        listing_data['building_area_sq_ft'] = None

    try:
        listing_data['sale_price'] =  float(homesoup.find_all('li',attrs={'hmsitemprop':'Price'})[0].text.strip().replace(",",''))
    except:
        print('NO SALE PX!')
        listing_data['sale_price'] = None

    try:
        listing_data['home_type'] = find_nested_info(homesoup,'Listing Type')
    except:
        listing_data['home_type'] = None
 
    listing_data['sale_history'] = find_sale_history(homesoup)
    
    features = {}
   
    features['is_foreclosure'] = str(homesoup.find_all('li',attrs={'hmsitemprop':'IsForeclosure'})[0].text.strip()) == 'True'
    try:
        features['desc'] = homesoup.find_all('p',class_="listing-bio")[0].text.strip()
    except:
        features['desc'] = None
    try:
        features['year_built'] = find_nested_info(homesoup,'Year Built')
    except:
        features['year_built'] = None

    try:
        features['lot_size'] = str(find_nested_info(homesoup,'Lot Size'))
    except:
        features['lot_size'] = None

    try:
        features['house_size'] = find_nested_info(homesoup,'House Size')
    except:
        features['house_size'] = None

    try:
        features['floors'] = find_nested_info(homesoup,'Floors')
    except:
        features['floors'] = None

    try:
        garage = find_nested_info(homesoup,'Garage')
        if garage>0:
            features['garage_detail'] = str(garage)
            features['has_garage'] = True
        else:
            features['garage_detail'] = None
            features['has_garage'] = False
    except:
        features['garage_detail'] = None
        features['has_garage'] = False

    try:
        if find_extra_nested_info(homesoup,'Sewer') == 'City Sewer':
            features['has_septic'] = False
        else:
            features['has_septic'] = True
    except:
        features['has_septic'] = None

    try:
        if find_extra_nested_info(homesoup,'Water') == 'City Water':
            features['has_well'] = False
        else:
            features['has_well'] = True
    except:
        features['has_well'] = None
    try:
        if ' pool ' in features['desc']:
            features['has_pool'] = True
        else:
            features['has_pool'] = False
    except:
        features['has_pool'] = None

    if features['has_well'] == False and features['has_septic'] == False and features['has_pool'] == False:
        features['no_pool_well_septic'] = True
    else:
        features['no_pool_well_septic'] = False

    try:
        subdiv = find_nested_info(homesoup,'Subdivision')
        features['has_established_subdivision'] = True
        features['subdivision'] = subdiv
    except:
        features['has_established_subdivision'] = False
        features['subdivision'] = None
    try:
        features['listing_status'] = find_nested_info(homesoup,'Listing Status')
    except:
        features['listing_status'] = None

    try:
        features['num_full_bath'] = find_nested_info(homesoup,'Full Bath')
    except:
        features['num_full_bath'] = 0
    try:
        features['num_half_bath'] = find_nested_info(homesoup,'Half Bath')
    except:
        features['num_half_bath'] = 0

    try:
        features['interior_features'] = find_extra_nested_info(homesoup,'Interior Features')
    except:
        features['interior_features'] = None
    try:
        features['flooring'] = find_extra_nested_info(homesoup,'Flooring')
    except:
        features['flooring'] = None
    try:
        features['remax_url'] = home_url
    except:
        features['remax_url'] = None
    images={}
    imglist = pull_image_urls_from_slideshow(homesoup)
    images['img_gallery'] = ';'.join(imglist)
    try:
        images['image_header'] = imglist[0]
    except:
        images['image_header'] = None

    home_dict = {}
    home_dict['address'] = address
    home_dict['listing_data'] = listing_data
    home_dict['images'] = images
    home_dict['features'] = features

    print(home_dict)     
    return home_dict

    
def createSoldHomeURL(page):
    
    url = 'https://metrorealty1-northcarolina.remax.com/realestatehomesforsale/charlotte-nc-p{0:03d}.html?query=minprice-50000/maxprice-2000000/'.format(page)
    
    return url

def create_sold_home_url_no_filter(page):
    
    url = 'https://metrorealty1-northcarolina.remax.com/realestatehomesforsale/charlotte-nc-p{0:03d}.html'.format(page)
    
    return url

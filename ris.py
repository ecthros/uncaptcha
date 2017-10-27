# import image_slicer
import requests
import os
import time
import random
import json
import threading
import multiprocessing
import time
import copy
import pickle

from PIL import Image
from thesaurus import get_synonyms
from clarifai.rest import ClarifaiApp
from clarifai.rest import Image as ClImage
from os import walk
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TASK = "task2"
IMAGE_NAME = 'image2'
FILE_TYPE = "jpeg"
TEST_IMAGE = "images/task2/image2_04_01.png"
CLARIFAI_APP_ID="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
CLARIFAI_APP_SECRET="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
DEBUG=0

# image_slicer.slice(IMAGE_NAME + "." + FILE_TYPE, 16)
# os.system("mv %s_* images/%s" % (IMAGE_NAME, TASK))

# images = []
# f = []
# for (_, _, filenames) in walk("images/"+TASK+"/"):
#     f.extend(filenames)

def parse_test_file(test_filename):
    return json.loads(open(test_filename, "r").read())

def test_all():
    dirs = list()
    test_root = "images"
    for (dirName, subDir, _) in walk(test_root):
        dirs.extend(subDir)
        break
    for d in dirs:
        full_path = os.path.join(test_root, d)
        try:
            search_directory(full_path)
        except Exception as exc:
            print("test %s failed" % full_path)
            print(exc.message)

def search_directory(directory, target_keyword=None, width=4):
    f = []
    trues = 0
    threads = []
    oracle = None
    try:
        oracle = parse_test_file(os.path.join(directory, "oracle.json"))
        if target_keyword == None:
            target_keyword = oracle["target_keyword"]
    except IOError as err:
        print("no oracle file found")
    manage_vars = multiprocessing.Manager()
    for (_, _, filenames) in walk(directory):
        f.extend([file for file in filenames if "image" in file or "output" in file])
    i = 0
    ret_vals = manage_vars.dict()
    target_syns = list()
    for targ_key in target_keyword.split():
        target_syns.extend(get_synonyms(targ_key))
        target_syns.append(targ_key)

    print("testing " + directory)
    for img_file in f:
        t = multiprocessing.Process(target=reverse_search2, args=(os.path.join(directory, img_file), img_file, ret_vals, target_syns))
        threads.append(t)
        t.start()
        i+=1
    for j in range(0, i-1):
        threads[j].join()
    print("")
    # print ret_vals
    # print oracle
    if oracle: # local testing only
        for img_file in ret_vals.keys():
            # print str(ret_vals[img_file]) + " " + str(oracle[img_file])
            if(ret_vals[img_file] == oracle[img_file]):
                trues += 1
        print("  %s correct out of %s" % (str(trues), len(ret_vals)))
        return ret_vals
    else: # live testing only

        return get_coor(ret_vals, width)

def reverse_search2(img_file, filename, ret_vals, target_keyword="vehicle"):
    ret_vals[filename] = reverse_search(img_file, target_keyword)

def start_captcha():
    driver = webdriver.Firefox()
    driver.get("http://reddit.com")
    driver.find_element(By.XPATH, "//*[@id=\"header-bottom-right\"]/span[1]/a").click()
    time.sleep(1)
    driver.find_element(By.ID, "user_reg").send_keys("qwertyuiop091231")
    driver.find_element(By.ID, "passwd_reg").send_keys("THISISMYPASSWORD!!$")
    driver.find_element(By.ID, "passwd2_reg").send_keys("THISISMYPASSWORD!!$")
    driver.find_element(By.ID, "email_reg").send_keys("biggie.smalls123@gmail.com")
    #driver.find_element_by_tag_name("body").send_keys(Keys.COMMAND + Keys.ALT + 'k')
    iframeSwitch = driver.find_element(By.XPATH, "//*[@id=\"register-form\"]/div[6]/div/div/div/iframe")
    driver.switch_to.frame(iframeSwitch)
    driver.find_element(By.ID, "recaptcha-anchor").click()
    # download captcha image
    # 
    # split payload
    # 
    # reverse_search
    # 
    # driver.quit()

# determines if an image keywords matches the target keyword
# uses the synonyms of the image keyword
def check_image(img_keywords, target_syns, syn_image=False):
    #print ("Checking keywords against: " + target_keyword)

    for k in img_keywords:
        #print(k)
        if syn_image:
            image_syns = get_synonyms(k)
            if image_syns:
                for image_s in image_syns:
                    for target_s in target_syns:
                        # print("- %s" % (target_s))
                        if target_s == image_s:
                            return True
        else:
            for target_s in target_syns:
                # print("- %s" % (target_s))
                if target_s == k:
                    if (DEBUG > 0):
                        print("Found " + target_s + " equal to " + k)
                    return True
    return False

def get_coor(click_dict, width=4):
    x = 1
    y = 1
    coor_dict = dict()
    for key in sorted(click_dict.keys()):
        coor_dict[(x, y)] = click_dict[key]
        y += 1
        if y > width:
            x += 1
            y = 1
    return coor_dict

# returns an array of possible subjects of the image
def reverse_search(img_file, target_syns):
    json_arr = clarifai(img_file)
    keyword_arr = parse_clarifai(json_arr)
    correct_image = check_image(keyword_arr, target_syns)
    #print(correct_image)
    return correct_image

# sumbit a request to clarifai for reverse image search
# returns json object
def clarifai(img_file):
    # print("Querying clarifai..." + img_file)
    success = False
    model = None
    while not success:
        try:
            img = ClImage(filename=img_file)
            app = ClarifaiApp(CLARIFAI_APP_ID, CLARIFAI_APP_SECRET)
            model = app.models.get('general-v1.3')
            success = True
        except Exception as e:
            time.sleep(0.5)
            print(e)
    print("."),
    return model.predict([img])
    
def pprint(matrix):
    s = [[str(e) for e in row] for row in matrix]
    lens = [max(map(len, col)) for col in zip(*s)]
    fmt = '\t'.join('{{:{}}}'.format(x) for x in lens)
    table = [fmt.format(*row) for row in s]
    print '\n'.join(table)
# parse the json array from clarifai into a single dict of names->values
# returns array sorted by rank (value)
def parse_clarifai(json_arr):
    # array = json.loads(json_arr)
    # print("- parsing json")
    ret_arr = list()
    #outputs > data > concepts > name & value
    for data in json_arr["outputs"][0]["data"]["concepts"]:
        # ret_arr[data["name"]] = data["value"]
        ret_arr.append(data["name"])
    return ret_arr

if __name__ == "__main__":
    x_sections = 4
    y_sections = 4
    TASK_PATH = "images/taskg"
    IMAGE_PATH = "images/taskg/payload2.jpeg"
    CACHE_PATH = TASK_PATH+"/cache2.pickle"
    FROM_CACHE = False
    if os.path.exists(CACHE_PATH):
        print("Found saved cache, reading")
        with open(CACHE_PATH, 'rb') as handle:
            cache = pickle.load(handle)
        FROM_CACHE = True
    else:
        cache = []
    with Image.open(IMAGE_PATH) as img:
        width, height = img.size
        x_window = width/x_sections
        y_window = height/y_sections 
        winstep = 1
        ans = [[False for z in range(0,int(x_sections*winstep*2))] for z in range(0,int(y_sections*winstep*2))]
        toclick = [[False for z in range(0,x_sections)] for z in range(0,y_sections)]
        pprint(ans)
        curx, cury = 0, 0
        pid = 0
        xidx, yidx = 0, 0
        for curx in range(0, width - int(x_window*winstep), x_window/2):
            yidx = 0
            for cury in range(0, height-int(y_window*winstep), y_window/2):
                major_box = (curx % x_window == 0 and cury % y_window == 0)
                 
                i = img.crop((curx, cury, curx + int(x_window*winstep), cury + int(y_window*winstep)))
                i.save(TASK_PATH+"/slice2_%03d.jpeg"%pid, "jpeg")
                if FROM_CACHE:
                    answers = cache[pid] 
                else:
                    answers = parse_clarifai(clarifai(TASK_PATH+"/slice2_%03d.jpeg"%pid))
                    cache.append(answers)
                print answers
                decision = "symbol" in answers or "signalise" in answers or "picture frame" in answers
                ans[yidx][xidx] = decision
                if major_box:
                    toclick[yidx/2][xidx/2] = decision

                print "%d: %s" % (pid, decision)
                pprint(toclick)
                #i.show()
                #time.sleep(0.5)
                #raw_input("")
                
                print "IDX %dx%d [pid %d]: IMAGE %dx%d (%d by %d sections) with window sizes %d x %d" % (xidx, yidx, pid, width, height, x_sections, y_sections, x_window, y_window)
                yidx += 1
                pid += 1
            xidx += 1
    with open(CACHE_PATH, 'wb') as handle:
        pickle.dump(cache, handle)
    pprint(toclick)
    print("")
    pprint(ans)

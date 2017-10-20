import speech_recognition as sr
import os
import time
import json
import logging, sys
import multiprocessing 
import pprint
import csv
import new_filter_function
import threading
import googleapiclient
from collections import Counter

# Set up logging and pretty printing
LEVEL = logging.INFO
logging.basicConfig(stream=sys.stderr, level=LEVEL)
logging.getLogger('oauth2client.transport').setLevel(logging.ERROR)
logging.getLogger('googleapiclient.discovery').setLevel(logging.CRITICAL)  
logging.getLogger('oauth2client.client').setLevel(logging.ERROR)
pp = pprint.PrettyPrinter(indent=4)

# Set up default guess
#DEFAULT = "X" # all un-identified digits remain unknown
DEFAULT = "6" # all un-identified digits are mapped to "6"

# Set up api list
apis = ["googleCloud", "wit", "bing", "ibm", "google", "sphinx"]

# Simple homophone mapping, taking any exact matches and returning the digit (layer one mapping)
def homophone(num):
	if num in ["one", "1", "won"]:
		return "1"
	elif num in ["two", "to", "too", "2"]:
		return "2"
	elif num in ["three", "3"]:
		return "3"
	elif num in ["four", "for", "4", "fore"]:
		return "4"
	elif num in ["five", "5"]:
		return "5"
	elif num in ["six", "6"]:
		return "6"
	elif num in ["seven", "7"]:
		return "7"
	elif num in ["eight", "ate", "8"]:
		return "8"
	elif num in ["nine", "9"]:
		return "9"
	elif num in ["zero", "0"]:
		return "0"
	return DEFAULT

# Apply both layers of phonetic mapping
# More complex mapping, where homophones and near-homophones are used in conjunction
# Heigher weights are given to words that are phonetically close to a digit
def text_to_num(num, source_name="", results_dict={}):
	num = num.strip()
	if not source_name in results_dict:
		results_dict[source_name] = [str(num)]
	if not source_name + "_fil" in results_dict:
		results_dict[source_name + "_fil"] = list()

	digits = list()
	########## FIRST LAYER MAPPING ##########
	# These match correspond to exact homophone matches
	if num in ["one", "won" "1"]:
		digits.append(1)
	if num in ["two", "to", "too", "2"]:
		digits.append(2)
	if num in ["three", "3"]:
		digits.append(3)
	if num in ["four", "for", "fore", "4"]:
		digits.append(4)
	if num in ["five", "5"]:
		digits.append(5)
	if num in ["six", "6"]:
		digits.append(6)
	if num in ["six", "6"]:
		digits.append(6)
	if num in ["seven", "7"]:
		digits.append(7)
	if num in ["eight", "ate", "8"]:
		digits.append(8)
	if num in ["nine", "9"]:
		digits.append(9)
	if num in ["zero", "0"]:
		digits.append(0)
	########## SECOND LAYER MAPPING ##########
	# These match correspond to near homophone matches
	if num in ["one", "1", "juan", "Warren", "fun", "who won"]:
		digits.append(1)
	if num in ["to", "two", "too", "2", "who", "true", "do", "so", "you", "hello", "lou"] or num.endswith("ew") or num.endswith("do"):
		digits.append(2)
	if num in ["during", "three", "3", "tree", "free", "siri", "very", "be", "wes", "we", "really", "hurry"] or "ee" in num:
		digits.append(3)
	if num in ["four", "for", "fourth", "4", "oar", "or", "more", "porn"] or "oor" in num:
		digits.append(4)
	if num in ["five", "5", "hive", "fight", "fifth", "why", "find"] or "ive" in num:
		digits.append(5)
	if num in ["six", "6", "sex", "big", "sic", "set", "dicks", "it", "thank"] or num.endswith("icks") or num.endswith("ick") or num.endswith("inks") or num.endswith("ex"):
		digits.append(6)
	if num in ["get in", "seven", "7", "heaven", "Frozen", "Allen", "send","weather", "that in", "ten"] or "ven" in num:
		digits.append(7)
	if num in ["eight hundred", "o. k.", "eight", "8", "hate", "fate", "hey", "it", "they", "a", "A", "they have", "then"] or "ate" in num:
		digits.append(8)
	if num in ["yeah I", "no", "nine", "i'm", "9", "mine", "brian", "now i", "no i", "no I", "during", "now I", "no", "night", "eyes", "none", "non", "bind", "nice", "no i'm"] or "ine" in num:
		digits.append(9)
	if num in ["a hero", "the euro", "the hero", "Europe", "yeah well", "the o.", "hey oh", "zero", "hero", "0", "yeah","here", "well", "yeah well", "euro", "yo", "hello", "arrow", "Arrow", "they don't", "girl", "bill", "you know"] or "ero" in num:
		digits.append(0)
	if num in ["hi", "i", "I", "bye", "by", "buy"]:
		digits.append(5)
		digits.append(9)
	# Combine the output of the filters
	retStr = ''.join([str(x) for x in digits])
	if (retStr == '' or retStr == None):
		# Digit could not be classified
		results_dict[source_name + "_fil"] += DEFAULT
		return DEFAULT
	else:
		results_dict[source_name + "_fil"] += str(digits[0])
		return retStr

#################### SPEECH-TO-TEXT WEB APIS ####################
###### The following functions interact with the APIs we used to query for each segment ########
###### Keys have been removed from this section #######
#Query Sphinx
def sphinx(audio, vals, i, results_dict, timing):
	try:
		#print("Sphinx: ")
				s = time.time()
		vals[i] = text_to_num(r.recognize_sphinx(audio), "sphinx", results_dict)
				timing["sphinx"].append(time.time() - s)
				print "timing2", timing
	except sr.UnknownValueError:
		logging.debug("Sphinx could not understand audio")
		results_dict["sphinx"] = [DEFAULT]
		results_dict["sphinx_fil"] = [DEFAULT]
	except sr.RequestError as e:
		logging.debug("Sphinx error; {0}".format(e))
		results_dict["sphinx"] = [DEFAULT]
		results_dict["sphinx_fil"] = [DEFAULT]
#Query Google Cloud
def googleCloud(audio, vals, i, results_dict, timing):
	# recognize speech using Google Cloud Speech
	GOOGLE_CLOUD_SPEECH_CREDENTIALS = r"""{
	"type": "service_account",
	"project_id": "XXXXXX",
	"private_key_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
	"private_key": "-----BEGIN PRIVATE KEY-----\nxxxxxxxxxxxxxxxxxxxxxxxxxx\n-----END PRIVATE KEY-----\n",
	"client_email": "",
	"client_id": "XXXXXXXXXXXXXXXXXXXXXX",
	"auth_uri": "https://accounts.google.com/o/oauth2/auth",
	"token_uri": "https://accounts.google.com/o/oauth2/token",
	"auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
	"client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/audio-539%40XXXXXXXXXXX.iam.gserviceaccount.com"
	}"""
	try:
		s = time.time()
				#print("Google Cloud Speech: ")
		vals[i] = text_to_num(r.recognize_google_cloud(audio, \
			preferred_phrases=["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"],\
			 credentials_json=GOOGLE_CLOUD_SPEECH_CREDENTIALS), "googleCloud", results_dict)
				timing["googleCloud"].append(time.time() - s)
				print "timing", timing["googleCloud"]
		#print("Google Cloud " + str(vals[i]))
	except sr.UnknownValueError:
		logging.debug("Google Cloud Speech could not understand audio")
		results_dict["googleCloud"] = [DEFAULT]
		results_dict["googleCloud_fil"] = [DEFAULT]
	except sr.RequestError as e:
		logging.debug("Could not request results from Google Cloud Speech service; {0}".format(e))
		results_dict["googleCloud"] = [DEFAULT]
		results_dict["googleCloud_fil"] = [DEFAULT]
		except:
			pass
#Query Wit
def wit(audio, vals, i, results_dict, timing):
	# recognize speech using Wit.ai
	WIT_AI_KEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx"  # Wit.ai keys are 32-character uppercase alphanumeric strings
	try:
				s = time.time()
		#print("Wit.ai: ")
		vals[i] = text_to_num(r.recognize_wit(audio, key=WIT_AI_KEY), "wit", results_dict)
				timing["wit"].append(time.time() - s)
		#print("Wit " + str(vals[i]))
	except sr.UnknownValueError:
		logging.debug("Wit.ai could not understand audio")
		results_dict["wit"] = [DEFAULT]
		results_dict["wit_fil"] = [DEFAULT]
	except sr.RequestError as e:
		logging.debug("Could not request results from Wit.ai service; {0}".format(e))
		results_dict["wit"] = [DEFAULT]
		results_dict["wit_fil"] = [DEFAULT]
#Query Bing
def bing(audio, vals, i, results_dict, timing):
	# recognize speech using Microsoft Bing Voice Recognition
	# Microsoft Bing Voice Recognition API keys 32-character lowercase hexadecimal strings
		
	BING_KEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
	try:
				s = time.time()
		#print("Microsoft Bing Voice Recognition: ")
		vals[i] = text_to_num(r.recognize_bing(audio, key=BING_KEY), "bing", results_dict)
				timing["bing"].append(time.time() - s)
	except sr.UnknownValueError:
		logging.debug("Microsoft Bing Voice Recognition could not understand audio")
		results_dict["bing"] = [DEFAULT]
		results_dict["bing_fil"] = [DEFAULT]
	except sr.RequestError as e:
		logging.debug("Could not request results from Microsoft Bing Voice Recognition service; {0}".format(e))
		results_dict["bing"] = [DEFAULT]
		results_dict["bing_fil"] = [DEFAULT]
# Query IBM
def ibm(audio, vals, i, results_dict, timing, show_all=False):
	# recognize speech using IBM Speech to Text
	IBM_USERNAME = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"  # IBM Speech to Text usernames are strings of the form XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
	IBM_PASSWORD = "XXXXXXXXXX"  # IBM Speech to Text passwords are mixed-case alphanumeric strings
	try:
				s = time.time()
		#print("IBM Speech to Text: ")
		vals[i] = text_to_num(r.recognize_ibm(audio, username=IBM_USERNAME, \
			password=IBM_PASSWORD, show_all=False), "ibm", results_dict)
				timing["ibm"].append(time.time() - s)
	except sr.UnknownValueError:
		logging.debug("IBM Speech to Text could not understand audio")
		results_dict["ibm"] = [DEFAULT]
		results_dict["ibm_fil"] = [DEFAULT]
	except sr.RequestError as e:
		logging.debug("Could not request results from IBM Speech to Text service; {0}".format(e))
		results_dict["ibm"] = [DEFAULT]
		results_dict["ibm_fil"] = [DEFAULT]
#Query Google Speech-To-Text
def google(audio, vals, i, results_dict, timing):
	try:
		#print("Google: ")
				s= time.time()
		vals[i] = text_to_num(r.recognize_google(audio), "google", results_dict)
				timing["google"].append(time.time() - s)
	except:
		logging.debug("Google could not understand")
		results_dict["google"] = [DEFAULT]
		results_dict["google_fil"] = [DEFAULT]
#Query Houndify. This was not used as we found Houndify difficult to incorportate.
def houndify(audio, vals, i, results_dict, timing):
	# recognize speech using Houndify
	HOUNDIFY_CLIENT_ID = "XXXXXXXXXXXXXXXXXXXXX=="  # Houndify client IDs are Base64-encoded strings
	HOUNDIFY_CLIENT_KEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX=="  # Houndify client keys are Base64-encoded strings
	try:
		#print("Houndify: ")
		vals[i] = text_to_num(r.recognize_houndify(audio, client_id=HOUNDIFY_CLIENT_ID,\
		client_key=HOUNDIFY_CLIENT_KEY), "houndify", results_dict)
		# vals[i] = None
	except sr.UnknownValueError:
		logging.debug("Houndify could not understand audio")
		results_dict["houndify"] = [DEFAULT]
		results_dict["houndify_fil"] = [DEFAULT]
	except sr.RequestError as e:
		logging.debug("Could not request results from Houndify service; {0}".format(e))
		results_dict["houndify"] = [DEFAULT]
		results_dict["houndify_fil"] = [DEFAULT]

# Apply a new phonetic mapping to the saved data
def re_test(new_fil, base_dir="data"):
	try:
		tasks = os.listdir(base_dir)
	except OSError:
		print("no such directory")
		return None
	for task in tasks:
		new_final = ""
		task_path = os.path.join(base_dir, task)
		logging.info(task_path)
		csv_log = open(os.path.join(task_path, "results_%s.csv" % new_fil.__name__), "wb")
		csv_writer = csv.writer(csv_log)
		try:
			with open(os.path.join(task_path, "results.json"), "r") as log:
				json_str = log.read()
			results_dict = json.loads(json_str)
			with open(os.path.join(task_path, "oracle"), "r") as log:
				oracle = log.read()
		except:
			continue

		new_results_dict = dict()
		for api in apis:
			new_results_dict[api + "_fil"] = list()
			new_results_dict[api] = results_dict[api] # copy the unfiltered results
		for dig_count in xrange(0,10):
			csv_row = list()
			i = 0
			new_dig_guess = [0] * len(apis)
			csv_row.append(oracle[dig_count])
			# re-filter each api for digit dig_count
			for api in apis:
								#print api, results_dict[api], dig_count
				csv_row.append(results_dict[api][dig_count])
				new_dig_guess[i] = new_fil(results_dict[api][dig_count]) # apply new filter
				new_results_dict[api + "_fil"].append(new_dig_guess[i])
				i += 1
			logging.debug(new_dig_guess)
			resultsFiltered = filter(None, new_dig_guess)
			resultsFiltered = filter(lambda x: x != DEFAULT, new_dig_guess)
			results = []
			for result in resultsFiltered:
				digits = [digit for digit in str(result)]
				results += digits
			logging.debug(results)
			results = sorted(results, key=results.count, reverse=True)
			logging.debug(results)
			if not results:
				logging.debug("FOUND NOTHING: DEFAULTING TO %s" % DEFAULT)
				new_final += DEFAULT # seems good enough
			else:
				logging.debug("DETERMINED AS: " + str(results[0]))
				new_final += results[0]
			csv_row.append(new_final[-1])
			csv_writer.writerow(csv_row)
		logging.debug(new_final)
		new_results_dict["final"] = new_final
		new_final_log = os.path.join(task_path, "results_%s.json" % new_fil.__name__)
		with open(new_final_log, "w") as log:
			json.dump(new_results_dict, log)
		csv_log.close()
def getNums(task_path, audio_files):
	print audio_files
	num_str = ""
	results_dict = dict()
	start = time.time()
	i = 0
	ts = []
	ans = ["X" for j in range(0, 11)]
	print ans
	for f in sorted(audio_files):
		ts.append(multiprocessing.Process(target=getNum, args=((f, results_dict, i, ans))))
		logging.debug(f)
		#num_str += str(getNum(f, results_dict, i, ans))
		i += 1
		print ts
		for t in ts:
			t.start()
		for t in ts:
			t.join()
		end = time.time()
		print ans
		print end-start
	results_dict["total_time"] = end - start
	logging.debug(num_str)
	results_dict["final"] = num_str
	logging.debug(results_dict)
	# save the results in a log file
	#with open(os.path.join(task_path, "results.json"), "w") as log:
	#	json.dump(results_dict, log)
	logging.debug("results recorded for %s" % task_path)
	return num_str, end-start

def getNum(audio_file, results_dict, digit_num=0, ans=[]):
	global r
	r = sr.Recognizer()

	with sr.AudioFile(audio_file) as source:
		audio = r.record(source)  # read the entire audio file

	manage_vars = multiprocessing.Manager()
	ret_vals = manage_vars.dict()
	results_dict_threaded = manage_vars.dict()
	results = []
	threads = []
		timed = manage_vars.dict()
		for api in apis:
			timed[api] = manage_vars.list()
	apis_func = [googleCloud, sphinx, wit, bing, google, ibm]
	i = 0
	start = time.time()
	for api in apis_func:
		t = multiprocessing.Process(target=api, args=(audio, ret_vals, i, results_dict_threaded, timed))
		threads.append(t)
		t.start()
		i += 1
		
	for thread in threads:
		thread.join()
	end = time.time()
		print "getnumtime", end-start
		print timed
	results_dict["time" + str(digit_num)] = end - start
	# merge the results with the past results
	for name in results_dict_threaded.keys():
		if name in results_dict:
			results_dict[name] += results_dict_threaded[name]
		else:
			results_dict[name] = results_dict_threaded[name]
	#print(ret_vals)
	i = 0
	for key in ret_vals.keys():
		results.append(ret_vals[key])
	# logging.debug(results)
	resultsFiltered = filter(None, results)
	results = []
	for result in resultsFiltered:
		digits = [digit for digit in str(result)]
		results += digits

	# logging.debug(results)
	results = sorted(results, key=results.count, reverse=True)
	if not results:
		logging.debug("FOUND NOTHING")
				ans[digit_num] = DEFAULT
		return DEFAULT
	else:
		# print(results[0])
		logging.info("DETERMINED AS: " + str(results[0]))
				print ans
				print digit_num
				ans[digit_num] = results[0]
		return results[0]

def test_dir(directory):
	try:
		audio_files = [os.path.join(directory,f) for f in os.listdir(directory) if "_0" in f]
		getNums(directory, audio_files)
	except OSError:
		print("%s does not exist" % directory)

def test_all(start_dir="data"):
	tasks = os.listdir(start_dir)
	for task in tasks:
		test_dir(os.path.join(start_dir, task))

def test_some(start_dir="data", start=1, end=2):
	logging.basicConfig(stream=sys.stderr, level=LEVEL)
	for task_num in range(start, end+1):
		task = "task"+str(task_num)
		task_path = os.path.join(start_dir, task)
		test_dir(task_path)

NEW_FILTER = text_to_num

if __name__ == "__main__":
	re_test(NEW_FILTER, "new_data")

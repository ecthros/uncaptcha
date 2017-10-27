import requests
from bs4 import BeautifulSoup


def _get_soup_object(url, parser="html.parser"):
	return BeautifulSoup(requests.get(url).text, parser)

#Takes in a word (string) and returns a list of synonyms

def getSynonyms(term, formatted=False, max=100):
	if len(term.split()) > 1:
		print("Error: A Term must be only a single word")
	else:
		try:
			data = _get_soup_object("http://www.thesaurus.com/browse/{0}".format(term))
			terms = data.select("div#filters-0")[0].findAll("li")
			if len(terms) > max:
				terms = terms[:max:]
			li = []
			for t in terms:
				li.append(t.select("span.text")[0].getText())
			if formatted:
				return {term: li}
			return li
		except:
			print("{0} has no Synonyms in the API".format(term))


#EXAMPLE
#for wrd in getSynonyms("car"):
#	print wrd

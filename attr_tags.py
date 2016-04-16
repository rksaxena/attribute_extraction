# coding=UTF-8
import nltk
import re
import operator
import html_strip
from nltk.corpus import brown
import logging

# Speech tagger
#############################################################################
brown_train = brown.tagged_sents(categories='reviews')
default_tagger = nltk.data.load(nltk.tag._POS_TAGGER)
model_tag = {'round' : 'NN',
             'front':'JJ',
             'back':'JJ',
             'loops':'NN',
             'belt':'NN',
             'washed' : 'NN',
             'wear' : 'VB',
             'Made' : 'VBD',
             'printed' : 'JJ'
            }
unigram_tagger = nltk.UnigramTagger(model=model_tag, backoff=default_tagger)
bigram_tagger = nltk.BigramTagger(brown_train, backoff=unigram_tagger)
#############################################################################


# This is our semi-CFG
#############################################################################
cfg = {}
cfg["NNP+NNP"] = "NNP"
cfg["NN+NN"] = "NNI"
#cfg["NN+NNP"] = "NN"
#cfg["NNP+NN"] = "NN"
cfg["NNI+NN"] = "NNI"
cfg["JJ+JJ"] = "JJ"
cfg["JJ+NN"] = "NNP"
cfg["NN+JJ"] = "NNI"
cfg["RB+NN"] = "NN"
cfg["NN+RB"] = "NN"
#############################################################################


class NPExtractor(object):

    def __init__(self, sentence):
        self.sentence = sentence

    # Split the sentence into singlw words/tokens
    def tokenize_sentence(self, sentence):
        tokens = nltk.word_tokenize(sentence)
        return tokens

    # Normalize brown corpus' tags ("NN", "NN-PL", "NNS" > "NN")
    def normalize_tags(self, tagged):
        n_tagged = []
        for t in tagged:
            #print str(t[0]) + "Tag: " + str(t[1])
            if t[1] == "NP-TL" or t[1] == "NP":
                n_tagged.append((t[0], "NNP"))
                continue
            if t[1].endswith("-TL-HL"):
                n_tagged.append((t[0], t[1][:-6]))
                continue
            if t[1].endswith("-TL") or  t[1].endswith("-HL"):
                n_tagged.append((t[0], t[1][:-3]))
                continue
            if t[1].endswith("S"):
                n_tagged.append((t[0], t[1][:-1]))
                continue
            n_tagged.append((t[0], t[1]))
        return n_tagged

    # Extract the main topics from the sentence
    def extract(self):

        tokens = self.tokenize_sentence(self.sentence)
        tags = self.normalize_tags(bigram_tagger.tag(tokens))
        #print tags

        merge = True
        while merge:
            merge = False
            for x in range(0, len(tags) - 1):
                t1 = tags[x]
                t2 = tags[x + 1]
                key = "%s+%s" % (t1[1], t2[1])
                value = cfg.get(key, '')
                if value:
                    merge = True
                    tags.pop(x)
                    tags.pop(x)
                    match = "%s %s" % (t1[0], t2[0])
                    pos = value
                    tags.insert(x, (match, pos))
                    break

        matches = []
        for t in tags:
            #if t[1] == "NNP" or t[1] == "NNI":
            if t[1] == "NNP" or t[1] == "NNI" or t[1] == "NN":
                matches.append(t[0])
        return matches

def get_attr_tags_array(req_data):
    response_arr = []
    for d in req_data:
       	res = get_attr_tags(d)
	response_arr.append(res)
    return response_arr

def get_attr_tags(d):
        res = {}
        if "id" in d:
		res["id"] = d["id"]
        res["data"] = {}
        if "payload" in d:
		if "entity_id" in d["payload"]:
			res["data"]["entity_id"] = d["payload"]["entity_id"]
		res["data"]["tags"] = get_tags(d)
	return res
 

def get_tags(req_data):
        ignore_phrases = [ "clubbed with",
                   "team it",
                   "pair it",
                   "team this",
                   "play this",
                   "pair this",
                   "match it",
                   "match this",
                   "club this",
                   "club it",
                   "warranty",
                   "go perfectly with",
                   "worn with",
                   "style it",
                   "paired with",
                   "team them",
                   "team up",
                   "carry it",
                   "with this",
                   "go well with",
                   "with a matching",
                   "with matching",
                   "Furthermore",
                   "teamed with",
                   "played with"]
	all_tags = {}
	if "payload" in req_data:
		data = req_data["payload"]
		if "text_to_enrich" in data:
			text = data["text_to_enrich"]
			t = html_strip.strip_tags(text)
			t = re.split(", |\. |,|\.", t)
			for sentence in t:
				ignore_phrase = False
				for ignore in ignore_phrases:
					if ignore in sentence.lower(): 
						ignore_phrase = True
						break
				if(ignore_phrase == True):
					continue
				if("pair of") in sentence:
                                    sentence =sentence.replace("pair of", "")
                                np_extractor = NPExtractor(sentence)
				result = np_extractor.extract()
				for r in result:
					if(r in all_tags):
						all_tags[r] +=1
					else:
						all_tags[r] = 1;
			
	logging.debug("Tags Found: " + str(all_tags.keys()))
	return (all_tags.keys())

#if __name__ == '__main__':
#    main()

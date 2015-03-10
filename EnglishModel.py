
#Class built to rate the likelihood of different translations of the same sentence, 
# where the sentence under question is formatted as a list of word indices in the sentence
# and at each indice there is a sub-array containing the various possible words at that position.
# The model is built to find the likelihood of various configurations of that sentence. However,
# it can also be used simply to look at the probability of a single fully-formed sentence.
#
# This model uses bigrams sourced from the Corpus of Contemporary American English

import math, collections, sys
UNK= "UNK"
class EnglishModel:
    def __init__(self, filename = None):
        self.return_top_k = 15
        self.bigramCounts = collections.defaultdict(lambda: collections.Counter())
        self.unigramCounts = collections.Counter()
        self.unigramCounts[UNK] = 1.0
        self.total_words = 0
        self.V = 0

        if filename:
        	self.load_bigrams(filename)
       
    def load_bigrams(self, filename):
      def extract(line, pos):
          ret= line.strip().partition("\t")[pos]
          ret = ret.replace("\t", " ")
          return ret
      with open(filename) as f:
          l = [(extract(line, 2), extract(line, 0)) for line in f]
          for entry in l:
            word1, word2 = entry[0].split()
            self.bigramCounts[word1][word2] += int(entry[1])
            self.unigramCounts[word1] += int(entry[1])
            self.unigramCounts[word2] += int(entry[1])
      self.total_words += sum(self.unigramCounts.values())
      self.V += sum([1 for w in self.unigramCounts])
      print "\n-Bigrams loaded from %s" % filename.rpartition("/")[2]

    #Tokenizes sentence and replaces any words that aren't in the training corpus with the UNK token
    def process_sentence(self, sentence):
      def process(word):
        if word in self.unigramCounts:
          return word
        else:
          return UNK 
      return map(process, sentence.split())

    #Gets the LOG probability of a sentence. Employs a cache that is reinitialized every time a new batch of sentences are rated
    def prob_of(self, sentence):
      words = self.process_sentence(sentence) 
      if len(words) == 0:
        print "No sentence!"
        return 0.0
      last_word = words[0]#STILL NEEDS HANDLING TO DETERMINE PROB OF THAT WORD STARTING A SENTENCE
      prob = math.log(self.unigramCounts[last_word]+1) - math.log(self.total_words+self.V) #QUESTIONABLE WAY OF HANDLING ABOVE NOTE
      for i in range(1, len(words)): #Starts after the first word (each bigram token includes the last word)
        word = words[i]
        if " ".join(words[i-1:i+1]) in self.prob_cache:
          prob += self.prob_cache[" ".join(words[i-1:i+1])]
          last_word = word
          continue
        last_uni_count = self.unigramCounts[last_word] + self.V #SHOULD IT BE ONE OR SHOULD IT BE THE VOCAB SIZE?????
        bi_count = self.bigramCounts[last_word][word]
        pprob = 0
        if bi_count > 0:
          pprob += math.log(bi_count+1.0)
          pprob -= math.log(last_uni_count)
        elif word == last_word and word != UNK: #repeated words are pretty rare, cubes unigram probability for each
          uni_count = self.unigramCounts[word]
          pprob += math.log(uni_count+1)*3 #cubed equivalent
          pprob -= math.log(self.total_words + self.V)*3 #cubed
        else: #else use unigram probs
          pprob += .4
          uni_count = self.unigramCounts[word]
          pprob += math.log(uni_count+1)
          pprob -= math.log(self.total_words + self.V)
        #print "Prob of", last_word, word, "is:", 1.0*pprob
        if True:#i < len(words)/1.5:
          self.prob_cache[" ".join(words[i-1:i+1])] = pprob #CACHE IT
        prob += pprob
        last_word = word
      return prob


    def recurse_possible_sentences(self, sentence_grid, sentence_so_far=""):
      if len(sentence_grid) == 0:
        return [sentence_so_far,]
      else:
        potential_sentences = []
        potential_words = sentence_grid[0]
        new_grid = sentence_grid[1:]
        for word in potential_words:
          if sentence_so_far != "":
            new_sentence = " ".join([sentence_so_far, word]).strip()
          else:
            new_sentence = word.capitalize()
          potential_sentences.extend(self.recurse_possible_sentences(new_grid, new_sentence)) #add in the possible sentences if the above word was chosen
        return potential_sentences

    # NB returns the PERCENT RATING of the top rated sentences, probability is 
    # the percent of all the sentence probabilities
    # SEE Example at bottom of page of a passed in "translated_structure". It is a 2D array of possible word choices at each position in the sentence
    def rate_sentences(self, translated_structure):
      self.prob_cache = collections.defaultdict(lambda: 0)
      pos_sentences = self.recurse_possible_sentences(translated_structure)
      rated_sentences = map(lambda s: (s, math.exp(self.prob_of(s))), pos_sentences)
      rated_sentences.sort(key = lambda x: x[1], reverse= True) #sorts by probability
      total_probs = sum([prob for s, prob in rated_sentences])
      #return rated_sentences[0:self.return_top_k]
      #should always add a period!!!!!!!! << TODO
      percent_rated_sentences = map(lambda R: (R[0]+".", 1.0*R[1]/total_probs), rated_sentences)
      return percent_rated_sentences[0:self.return_top_k]


test = EnglishModel()
test.load_bigrams("w2Caps")
def PRINT(x):
  print x[0], "(relative prob: %.4f percent)" % (x[1]*100)
map(PRINT, test.rate_sentences([["this"],["is", "issss", "that"],["a", "not", "maid"],["hit", "great", "a", "maid"],["sentence", "mermaid"]]))

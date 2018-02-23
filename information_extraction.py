#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 15:39:12 2018

@author: pouria
"""

from __future__ import print_function
import re
import spacy

from pyclausie import ClausIE


nlp = spacy.load('en')
re_spaces = re.compile(r'\s+')


class Person(object):
    def __init__(self, name, likes=None, has=None, travels=None):
        """
        :param name: the person's name
        :type name: basestring
        :param likes: (Optional) an initial list of likes
        :type likes: list
        :param dislikes: (Optional) an initial list of likes
        :type dislikes: list
        :param has: (Optional) an initial list of things the person has
        :type has: list
        :param travels: (Optional) an initial list of the person's travels
        :type travels: list
        """
        self.name = name
        self.likes = [] if likes is None else likes
        self.has = [] if has is None else has
        self.travels = [] if travels is None else travels

    def __repr__(self):
        return self.name


class Pet(object):
    def __init__(self, pet_type, name=None):
        self.name = name
        self.type = pet_type


class Trip(object):
    def __init__(self,person, location, time):
        self.time = time
        self.location = location
        self.person = person


persons = []
pets = []
trips = []

def list_maker(doc):
    words = [ str(word) for word in doc]
    return words

def process_data_from_input_file(file_path='./assignment_01.data'):
#def get_data_from_file(file_path='./chatbot_data.txt'):
    with open(file_path) as infile:
        cleaned_lines = [line.strip() for line in infile if not line.startswith(('$$$', '###', '==='))]

    return cleaned_lines


def select_person(name):
    for person in persons:
        if person.name == name:
            return person


def add_person(name):
    person = select_person(name)

    if person is None:
        new_person = Person(name)
        persons.append(new_person)

        return new_person

    return person


def select_pet(name):
    for pet in pets:
        if pet.name == name:
            return pet



        
def add_pet(type, name=None):
    pet = None

    if name:
        pet = select_pet(name)

    if pet is None:
        pet = Pet(type, name)
        pets.append(pet)

    return pet

def select_trip(person = None, location=None, time=None):
    for trip in trips:
        if trip.person == person:
            if trip.location == location or any([l == None for l in [location, trip.location]]):
                if trip.time == time or any([l == None for l in [time, trip.time]]):
                    if trip.time == None : #and trip.location == location:
                        trip.time = time
                    if trip.location == None : #and trip.time == time:
                        trip.location = location
                    return trip
                
def add_trip(person = None, location=None, time=None):
    trip = None

    if person:
        trip = select_trip(person, location, time)

    if trip is None:
        trip = Trip(person, location, time)
        trips.append(trip)

    return trip
def get_persons_pet(person_name):

    person = select_person(person_name)

    for thing in person.has:
        if isinstance(thing, Pet):
            return thing


def check_chunk(name):
    chunk = [name]
    children = [ child for child in name.children]
    if len(children)>0:
        chunk = [children[0].lemma_, name]
    return chunk
def process_relation_triplet(triplet):
    """
    Process a relation triplet found by ClausIE and store the data
    find relations of types:
    (PERSON, likes, PERSON)
    (PERSON, has, PET)
    (PET, has_name, NAME)
    (PERSON, travels, TRIP)
    (TRIP, departs_on, DATE)
    (TRIP, departs_to, PLACE)
    :param triplet: The relation triplet from ClausIE
    :type triplet: tuple
    :return: a triplet in the formats specified above
    :rtype: tuple
    """

    sentence = triplet.subject + ' ' + triplet.predicate + ' ' + triplet.object

    doc = nlp(unicode(sentence))
    root = None
    for t in doc:
        if t.pos_ == 'VERB' and t.head == t:
            root = t
            break

         #elif t.pos_ == 'NOUN'
             
    if root == None:
        return
    # also, if only one sentence
    # root = doc[:].root


    """
    CURRENT ASSUMPTIONS:
    - People's names are unique (i.e. there only exists one person with a certain name).
    - Pet's names are unique
    - The only pets are dogs and cats
    - Only one person can own a specific pet
    - A person can own only one pet
    """


    # Process (PERSON, likes, PERSON) relations
    if root.lemma_ == 'like' and "n't" not in triplet.predicate:
        if triplet.subject in [e.text for e in doc.ents if e.label_ == 'PERSON' or "ORG"] and triplet.object in [e.text for e in doc.ents if e.label_ == 'PERSON' or "ORG"]:
            if triplet.subject not in [pet.name for pet in pets] or triplet.object not in [pet.name for pet in pets]:
                s = add_person(triplet.subject)
                o = add_person(triplet.object)
                s.likes.append(o)
            
    if root.lemma_ == 'leave' :
        if triplet.subject in [e.text for e in doc.ents if e.label_ == 'PERSON' or "ORG"]:
            person = triplet.subject
            
            rdoc = nlp(unicode(triplet.object))
            tlocation = None
            date = None
            for_tokens = [t for t in rdoc if t.text == 'for']
            if len(for_tokens) > 0:
                for_token = for_tokens[0]
                tlocation = [t for t in for_token.children if t.dep_ == 'pobj'][0].text
                
            on_tokens = [t for t in rdoc if t.text == 'on']
            if len(on_tokens)>0:
                on_token = on_tokens[0]
                day = [t for t in on_token.children if t.dep_ == 'pobj'][0]
                month = [t for t in day.children if t.dep_ == 'compound'][0]
                date=' '.join([str(month), str(day)])
                
                
            in_tokens = [t for t in rdoc if t.text == 'in']
            if len(on_tokens)>0 and date == None:
                in_token = in_tokens[0]
                day = [t for t in in_token.children if t.dep_ == 'pobj'][0]
                month = [t for t in day.children if t.dep_ == 'compound'][0]
                date=' '.join([str(month), str(day)])
            
            s = add_person(triplet.subject)
                           
            trip = add_trip(person,tlocation,date)
 
            s.travels.append(trip)

    if root.lemma_ == 'fly' or root.lemma_ =='go':  
        passengers = [ str(name) for name in doc.ents if str(name) in triplet.subject]
        tlocation = None
        date = None
        rdoc = nlp(unicode(triplet.object))
            
        to_tokens = [t for t in rdoc if t.text == 'to']
        if len(to_tokens) > 0:
            to_token = to_tokens[0]
            possible_location = [t for t in to_token.children if t.dep_ == 'pobj']
            tlocation = possible_location[0].text if len(possible_location)>0 else None 
            
        on_tokens = [t for t in rdoc if t.text == 'on']
        if len(on_tokens)>0:
            on_token = on_tokens[0]
            day = [t for t in on_token.children if t.dep_ == 'pobj'][0]
            month = [t for t in day.children if t.dep_ == 'compound'][0]
            date=' '.join([str(month), str(day)])
            
        in_tokens = [t for t in rdoc if t.text == 'in']   
        if len(in_tokens)>0 and date == None:
            #in_token = in_tokens[0]
            words = list_maker(doc)
            #day = [t for t in in_token.children if t.dep_ == 'pobj'][0]
            #month = [t for t in day.children if t.dep_ == 'compound'][0]
            date = ' '.join(words[words.index("in")+1:])
 
        next_tokens = [t for t in rdoc if t.text == 'next']   
        if len(next_tokens)>0 and date == None:
            #in_token = in_tokens[0]
            words = list_maker(doc)
            #day = [t for t in in_token.children if t.dep_ == 'pobj'][0]
            #month = [t for t in day.children if t.dep_ == 'compound'][0]
            date = ' '.join(words[words.index("next"):])
            
        for passenger in passengers:
            s = add_person(passenger)
                           
            trip = add_trip(passenger,tlocation,date)
 
            s.travels.append(trip)
                    
    if root.lemma_ == 'take' and 'trip' in str(doc):  
     
        
        passengers = [ str(name) for name in doc.ents if str(name) in triplet.subject]
        tlocation = None
        date = None
        rdoc = nlp(unicode(triplet.object))
            
        to_tokens = [t for t in rdoc if t.text == 'to']
        if len(to_tokens) > 0:
            to_token = to_tokens[0]
            tlocation = [t for t in to_token.children if t.dep_ == 'pobj'][0].text
            
        on_tokens = [t for t in rdoc if t.text == 'on']
        if len(on_tokens)>0:
            on_token = on_tokens[0]
            day = [t for t in on_token.children if t.dep_ == 'pobj'][0]
            month = [t for t in day.children if t.dep_ == 'compound'][0]
            date=' '.join([str(month), str(day)])

        in_tokens = [t for t in rdoc if t.text == 'in']
        
        if len(in_tokens)>0 and date == None:
            #in_token = in_tokens[0]
            words = list_maker(doc)
            #day = [t for t in in_token.children if t.dep_ == 'pobj'][0]
            #month = [t for t in day.children if t.dep_ == 'compound'][0]
            date = ' '.join(words[words.index("in")+1:])
            
        for passenger in passengers:
            s = add_person(passenger)
                           
            trip = add_trip(passenger,tlocation,date)
 
            s.travels.append(trip)
                    
                                      
                    
            
    if root.lemma_ == 'be' and triplet.object.startswith('friends with'):
        fw_doc = nlp(unicode(triplet.object))
        with_token = [t for t in fw_doc if t.text == 'with'][0]
        fw_who = [t for t in with_token.children if t.dep_ == 'pobj'][0].text
        # fw_who = [e for e in fw_doc.ents if e.label_ == 'PERSON'][0].text
        fw_who = [name for name in doc if str(name) in triplet.object and name.pos_=="PROPN"]

        #if triplet.subject in [e.text for e in doc.ents if e.label_ == 'PERSON' or "ORG"] and fw_who in [e.text for e in doc.ents if e.label_ == 'PERSON' or "ORG"]:
   
        
        if triplet.subject not in [pet.name for pet in pets]:
            s = add_person(triplet.subject)        
            for friend in fw_who:
                if str(friend) not in [pet.name for pet in pets]:
                    o = add_person(str(friend))
                    if o not in s.likes:
                        s.likes.append(o)
                    if s not in o.likes:
                        o.likes.append(s)


    if root.lemma_ == 'be' and 'friends' in triplet.object and 'and' in triplet.subject:
        fw_doc = nlp(unicode(triplet.subject))
        #and_token = [t for t in fw_doc if t.text == 'and'][0]
        #fw_who = [t for t in and_token.children if t.dep_ == 'pobj'][0].text
        #fw_who = [e for e in fw_doc.ents if e.label_ == 'PERSON'][0].text
        #fw_who = fw_doc[-1]
        #if triplet.subject in [e.text for e in doc.ents if e.label_ == 'PERSON'] and fw_who in [e.text for e in doc.ents if e.label_ == 'PERSON']:
        first = str(doc.ents[0])
        second = str(doc.ents[1])
        if first not in [pet.name for pet in pets] or second not in [pet.name for pet in pets]:
            s = add_person(first)
            o = add_person(second)
            if o not in s.likes:
                s.likes.append(o)
            if s not in o.likes:
                o.likes.append(s)



    # Process (PET, has, NAME)
    if triplet.subject.endswith('name') and ('dog' in triplet.subject or 'cat' in triplet.subject):
        obj_span = doc.char_span(sentence.find(triplet.object), len(sentence))

        # handle single names, but what about compound names? Noun chunks might help.
        if len(obj_span) == 1 and obj_span[0].pos_ == 'PROPN':
            name = str(obj_span[-1])
            subj_start = sentence.find(triplet.subject)
            subj_doc = doc.char_span(subj_start, subj_start + len(triplet.subject))

            s_people = [token.text for token in subj_doc if token.ent_type_ == 'PERSON']
            assert len(s_people) == 1
            s_person = select_person(s_people[0])

            s_pet_type = 'dog' if 'dog' in triplet.subject else 'cat'

            pet = add_pet(s_pet_type, name)

            s_person.has.append(pet)
            
            
        
    if str(root) == 'has' and doc[0].pos_ == 'PROPN' and ('dog' in triplet.object or 'cat' in triplet.object):
        obj_span = doc.char_span(sentence.find(triplet.object), len(sentence))
        subj_span = doc.char_span(sentence.find(triplet.subject), len(sentence))

        #print(triplet.subject)
        # handle single names, but what about compound names? Noun chunks might help.
        if obj_span[-1].pos_ == 'PROPN':
            name =  " ".join([str(part) for part in check_chunk(obj_span[-1])]).capitalize()
            subj_start = sentence.find(triplet.subject)
            subj_doc = doc.char_span(subj_start, subj_start + len(triplet.subject))

            s_people = [token.text for token in subj_doc if token.ent_type_ == 'PERSON']
            assert len(s_people) == 1
            s_person = select_person(s_people[0])

            s_pet_type = 'dog' if 'dog' in triplet.object else 'cat'


            s = add_person(triplet.subject)
            pet = add_pet(s_pet_type, name)
            
            s.has.append(pet)      
        
    if root.lemma_ == 'be' and doc[0].pos_ == 'PROPN' and ('dog' in triplet.subject or 'cat' in triplet.subject):
        obj_span = doc.char_span(sentence.find(triplet.object), len(sentence))
        subj_span = doc.char_span(sentence.find(triplet.subject), len(sentence))

        # handle single names, but what about compound names? Noun chunks might help.
        if obj_span[-1].pos_ == 'PROPN':
            name = " ".join([str(part) for part in check_chunk(obj_span[-1])]).capitalize()
            subj_start = sentence.find(triplet.subject)
            subj_doc = doc.char_span(subj_start, subj_start + len(triplet.subject))

            s_people = [token.text for token in subj_doc if token.ent_type_ == 'PERSON']
            assert len(s_people) == 1
            s_person = select_person(s_people[0])

            s_pet_type = 'dog' if 'dog' in triplet.subject else 'cat'
            
            pet = add_pet(s_pet_type, name)
     
            
            s_person.has.append(pet)  

 

def preprocess_question(question):
    # remove articles: a, an, the

    q_words = question.split(' ')

    # when won't this work?
    for article in ('a', 'an', 'the',):
        try:
            q_words.remove(article)
        except:
            pass
    if('visiting' in q_words):
        q_words.insert(q_words.index('visiting')+1,'to')
    return re.sub(re_spaces, ' ', ' '.join(q_words))


def has_question_word(string):
    # note: there are other question words
    for qword in ('who', 'what'):
        if qword in string.lower():
            return True

    return False



def main(question):
    sents = process_data_from_input_file()

    cl = ClausIE.get_instance()

    triples = cl.extract_triples(sents)

    for t in triples:
        r = process_relation_triplet(t)
    
    answers = []
        
    
    #question = '?'

    #question = raw_input("Please enter your question: [type exit to finish the query] \n")

    
    if question[-1] != '?':
        answers.append('This is not a question... please try again')
    else:

        ques = nlp(unicode(question))        
        if "What" not in [str(word) for word in ques]:
            q_trip = cl.extract_triples([preprocess_question(question)])[0]
        else:
            q_trip = cl.extract_triples(["Hamid likes Ali"])[0]
            
    
    
    
    
        # 1. Who has a <pet_type>?
        if q_trip.subject.lower() == 'who' and q_trip.object == 'dog':
    
            for person in persons:
                pet = get_persons_pet(person.name)
                if pet and pet.type == 'dog':
                    answers.append('{} has a {} named {}.'.format(person.name, 'dog', pet.name))
    
        # here's one just for cats
        if q_trip.subject.lower() == 'who' and q_trip.object == 'cat':
       
            for person in persons:
                pet = get_persons_pet(person.name)
                if pet and pet.type == 'cat':
                    answers.append('{} has a {} named {}.'.format(person.name, 'cat', pet.name))
    
    
        # 2. Who is [going to/flying to/traveling to/visiting] <place>?
        if q_trip.subject.lower() == 'who':
            check_list = (('going to' in question),('flying to' in question),
                          ('traveling to' in question),('visiting' in question))
            if any(check_list):
                accepted_trips = [trip for trip in trips if trip.location in q_trip.object]
                
                if len(accepted_trips) > 0:
                    for asked_trip in accepted_trips:
                        passenger = asked_trip.person
                        location = asked_trip.location
                        answers.append('{} is going to {}.'.format(passenger,asked_trip.location))
    
                else:
                    answers.append("I don't know")
                    
        # 3. (does <person> like <person>?)
        if str(ques[0]).lower() == 'does':
            accepted_subject = [person for person in persons if person.name in q_trip.subject]
            if len(accepted_subject) > 0:
                first = accepted_subject[0]
                accepted_object = [person for person in persons if person.name in q_trip.object]
                if len(accepted_object) > 0:
                    second = accepted_object[0]  
                    if second in first.likes:
                        answers.append('Yes! {} likes {}.'.format(first, second))
                    else:
                        answers.append('No! {} does not like {}.'.format(first, second))
                else:
                    answers.append("I don't know")
            else:
                answers.append("I don't know".format(ques.ents[0]))        
                    
                
        # 4. (What's the name of <person>'s <pet_type>?)
        if  'What' in [str(word) for word in ques] and 'dog' in [str(word) for word in ques]:
            name = str(ques.ents[0])
            accepted_names = [person for person in persons if person.name == name]
            
            if len(accepted_names) > 0:
                owner = accepted_names[0]
                #print(owner.name)
                if len(owner.has) > 0 and owner.has[0].type == "dog":
                    answers.append( "{}'s {}'s name is {}.".format(owner.name,"dog",owner.has[0].name) )
    
                else:
                    answers.append("{} does not have a pet".format(owner))
    
            else:
                answers.append("We have no information about this person")
        #cat
        if  'What' in [str(word) for word in ques] and 'cat' in [str(word) for word in ques]:
            name = str(ques.ents[0])
            accepted_names = [person for person in persons if person.name == name]
            
            if len(accepted_names) > 0:
                owner = accepted_names[0]
                #print(owner.name)
                if len(owner.has) > 0 and owner.has[0].type == "cat":
                    answers.append( "{}'s {}'s  name is {}.".format(owner.name,"cat",owner.has[0].name) )
    
                else:
                    #answers.append("{} does not have a pet".format(owner))
                    answers.append("I don't know")
    
            else:
                answers.append("I don't know")
                
                
                        
                
        # 5. When is <person> [going to/flying to/traveling to/visiting] <place>?
        if 'When' in list_maker(ques):
            check_list = (('going to' in question),('flying to' in question),
                          ('traveling to' in question),('visiting' in question))
            if any(check_list):
                accepted_trips = [trip for trip in trips if trip.location in q_trip.object]
                
                if len(accepted_trips) > 0:
                    for asked_trip in accepted_trips:
                        if asked_trip.person in question.split(' '):
                            time = asked_trip.time
                            answers.append('In {}.'.format(time))
                else:
                    answers.append("I don't know")  
    
    
        # 6. (Who likes <person>?)
        if q_trip.subject.lower() == 'who' and str(q_trip.predicate) =='likes':
            accepted_names = [person for person in persons if person.name == q_trip.object]
            
            if len(accepted_names) > 0:
                loved = accepted_names[0]
                lovers = []
                
                for person in persons:
                    if loved in person.likes:
                        lovers.append(person)
                if len(lovers) > 1 :
                    answers.append('{},and {} like {}.'.format(', '.join([str(name) for name in lovers[0:-1]]), lovers[-1] ,loved))
                elif len(lovers) == 1 :
                    answers.append('{} likes {}.'.format(lovers[0], loved))
                else:
                    answers.append('{} likes {}.'.format("no one", loved))
            else:
                answers.append("I don't know")
           
                   
    
        #  7. (Who does <person> like?)
        if q_trip.object.lower() == 'who' and q_trip.predicate =='does like':
            accepted_names = [person for person in persons if person.name == q_trip.subject]
            if len(accepted_names) > 0:
                lover = accepted_names[0]
     
                if len(lover.likes) > 1 :
                    answers.append( '{} likes {},and {}.'.format(lover, ', '.join([str(name) for name in lover.likes[0:-1]]), lover.likes[-1]) )
                elif len(lover.likes) == 1 :
                    answers.append( '{} likes {}.'.format(lover, lover.likes[0]) )
                else:
                    answers.append( '{} likes {}.'.format("no one", loved) )
            else:
                lover = None
                answers.append( "I don't know" )
           
    return answers

def answer_question(question_string):
    answers = main(question_string)
    for answer in answers:
        print(answer)  
          
#if __name__ == '__main__':
# It is just to check something
#    pass

import json
import unicodecsv
import Orange
import os.path

# http://www.tfidf.com/
# http://stackoverflow.com/questions/21844546/forming-bigrams-of-words-in-list-of-sentences-with-python
# http://pages.stern.nyu.edu/~churvich/Regress/Handouts/Chapt2.pdf

# This function maps one set of numbers in a given number range to another set of numbers
# in a given number range.
# Wikipedia (Linear Interpolation):nhttps://en.wikipedia.org/wiki/Linear_interpolation
def calculate_ntile_category(old_min, old_max, new_min, new_max, old_value):
    old_range = old_max - old_min
    new_range = new_max - new_min
    new_value = (((old_value - old_min) * new_range)/ old_range) + new_min

    return new_value

def create_sparse_basket( listing, key, my_dict):
    feature_list = None
    element = None
    old_max = None
    old_min = None

    for dic_key in my_dict:
        if dic_key in listing:
            feature_list = listing[dic_key]

            if 'created' in key:
                element = key + str(my_dict[dic_key].split('-')[1])
            elif 'price' in key:
                if old_max is None and old_min is None:
                    old_min = min(my_dict.values())
                    old_max = max(my_dict.values())
                element = key + str(calculate_ntile_category(old_min, old_max, 1, 10, my_dict[dic_key]))
            elif 'photos' in key:
                dic_length = len(my_dict[dic_key])
                element = key + str(dic_length)
            elif 'features' in key:
                new_feature_list = map(lambda x: x.replace(" ", "").replace(";", "").replace(" \'", ""), my_dict[dic_key])
                element = []
                for ftr in new_feature_list:
                    element.append(key+ftr)
            else:
                element = key + str(my_dict[dic_key])

            if isinstance(element, list):
                for item in element:
                    feature_list.append(item)
            else:
                feature_list.append(element)
        else:
            insert_list = []
            feature_list = listing[dic_key]
            element = key + my_dict[dic_key]
            insert_list.append(element)
            listing.update({dic_key : insert_list})

    return listing

def calculate_distance(lat, long):
    lower_manhattan_lat = 40.7230
    lower_manhattan_long = 74.0006

#def split_listings(listings, names):
#    for name in names:
#        file_name = 'file_'+name
#         open(file_name, 'w')


def generate_rules(name_of_basket_file, support, confidence):
    rule_dict = {}
    basket_data = Orange.data.Table(name_of_basket_file)
    rules = Orange.associate.AssociationRulesSparseInducer(basket_data, support=support, confidence=confidence)
    for r in rules:
        split_rule = str(r).split("->")
        if r.n_right == 1:
            if ('interest_levellow' in split_rule[1] or 'interest_levelmedium' in split_rule[1] or 'interest_levelhigh' in split_rule[1]):
                rule_dict.update({(str(split_rule[0])): r.support})

    return rule_dict

def compare_listing_to_rules(listing, rule_set):

    maximum = 0
    for key in rule_set:
        listing_set = set()
        ind_rule_set = set()

        for element in listing:
            listing_set.add(element)

        for rule in key.strip().split(" "):
            ind_rule_set.add(rule)

        difference = ind_rule_set.difference(listing_set)
        if len(difference) == 0:
            if rule_set[key] > maximum:
                maximum = rule_set[key]

    return maximum




#if not os.path.isfile('high_sparse_basket.basket') or \
#   not os.path.isfile('medium_sparse_basket.basket') or \
#   not os.path.isfile('low_sparse_basket.basket'):
#read in the training data from the json file
with open('train.json') as data_file:
    data = json.load(data_file)

    listings = {}

    #get the first list of listing id's and create a dictionary of lists with
    # listing ids as the keys.
    cycle_list = data['listing_id']
    for element in cycle_list:
        listings.update({element : []})


    bin_data = data['price']

    # then use this dictionary of lists to create your sparse basket
    for key in data:

        # These fields are either not being used or need special treatment
        if 'listing_id' not in key and \
           'description' not in key and \
           'address' not in key and \
           'manager_id' not in key and \
           'latitude' not in key and \
           'building_id' not in key and \
           'longitude' not in key:
            listings = create_sparse_basket(listings, key, data[key])

    # write basket to file
    sparse_files = {'high_sparse_basket': open('high_sparse_basket.basket', 'w'),
                     'medium_sparse_basket': open('medium_sparse_basket.basket', 'w'),
                     'low_sparse_basket': open('low_sparse_basket.basket', 'w')}

    high_writer = unicodecsv.writer(sparse_files['high_sparse_basket'], delimiter=",")
    medium_writer = unicodecsv.writer(sparse_files['medium_sparse_basket'], delimiter=",")
    low_writer = unicodecsv.writer(sparse_files['low_sparse_basket'], delimiter=",")

    for dic_key in listings:
        data = set(listings[dic_key])
        if 'interest_levellow' in data:
            low_writer.writerow(data)
        elif 'interest_levelmedium' in data:
            medium_writer.writerow(data)
        else:
            high_writer.writerow(data)
name_list = ["high_sparse_basket.basket", "medium_sparse_basket.basket","low_sparse_basket.basket"]

classification_rules = {}

for name in name_list:
    for_name_dic = name.split("_")
    classification_rules.update({str(for_name_dic[0]): generate_rules(name, 0.1, 0.3)})


## Now we need to test the rules
with open('test.json') as testing_file:
    testing_data = json.load(testing_file)

    test_listings = {}

    #get the first list of listing id's and create a dictionary of lists with
    # listing ids as the keys.
    test_list = testing_data['listing_id']
    final_results = {}

    for element in test_list:
        test_listings.update({element : []})
        final_results.update({element : []})

    bin_data = testing_data['price']
    for key in testing_data:
        if 'listing_id' not in key and \
           'description' not in key and \
           'address' not in key and \
           'manager_id' not in key and \
           'latitude' not in key and \
           'building_id' not in key and \
           'longitude' not in key:
           test_listings = create_sparse_basket(test_listings, key, testing_data[key])

    results_header = ['listing_id', 'high', 'medium', 'low']

    results_file = open('results.csv', 'a')
    results_writer = unicodecsv.DictWriter(results_file, lineterminator='\n', escapechar='\\', fieldnames=results_header)
    results_writer.writeheader()

    for key in test_listings:

        score = compare_listing_to_rules(test_listings[key], classification_rules['high'])
        final_results[key].append(score)
        score = compare_listing_to_rules(test_listings[key], classification_rules['medium'])
        final_results[key].append(score)
        score = compare_listing_to_rules(test_listings[key], classification_rules['low'])
        final_results[key].append(score)

        results_writer.writerow({'listing_id': key, 'high': final_results[key][0], 'medium': final_results[key][1], 'low': final_results[key][2]})
        print({'listing_id': key, 'high': final_results[key][0], 'medium': final_results[key][1], 'low': final_results[key][2]})
import json
import unicodecsv
import Orange

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
                new_feature_list = map(lambda x: x.replace(" ", ""), my_dict[dic_key])
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
high_sparse_basket = open('high_sparse_basket.basket', 'w')
medium_sparse_basket = open('medium_sparse_basket.basket', 'w')
low_sparse_basket = open('low_sparse_basket.basket', 'w')

high_writer = unicodecsv.writer(high_sparse_basket, delimiter=",")
medium_writer = unicodecsv.writer(medium_sparse_basket, delimiter=",")
low_writer = unicodecsv.writer(low_sparse_basket, delimiter=",")

for dic_key in listings:
    data = listings[dic_key]
    if 'interest_levellow' in data[0]:
        low_writer.writerow(data)
    elif 'interest_levelmedium' in data[0]:
        medium_writer.writerow(data)
    else:
        high_writer.writerow(data)

high_basket_data = Orange.data.Table("high_sparse_basket.basket")
medium_basket_data = Orange.data.Table("medium_sparse_basket.basket")
low_basket_data = Orange.data.Table("low_sparse_basket.basket")

rules = Orange.associate.AssociationRulesSparseInducer(high_basket_data, support=0.1, confidence=0.3)

for r in rules:
    if r.n_right == 1:
        print r.right
        if ('interest_levellow' in r.right or 'interest_levelmedium' in r.right or 'interest_levelhigh' in r.right):
            print r
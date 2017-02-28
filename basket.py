import json


# http://www.tfidf.com/
# http://stackoverflow.com/questions/21844546/forming-bigrams-of-words-in-list-of-sentences-with-python
# http://pages.stern.nyu.edu/~churvich/Regress/Handouts/Chapt2.pdf
def calculate_ntile_category(old_min, old_max, new_min, new_max, old_value):
    old_range = old_max - old_min
    new_range = new_max - new_min
    new_value = (((old_value - old_min) * new_range)/ old_range) + new_min

    return new_value


def turn_to_list( listing, key, my_dict):
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
            else:
                element = key + str(my_dict[dic_key])

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



with open('train.json') as data_file:
    data = json.load(data_file)

listings = {}

#get the first list of listing id's
# and create a dictionary of lists with
# listing ids as the keys.
cycle_list = data['listing_id']
for element in cycle_list:
    listings.update({element : []})

bin_data = data['price']

for key in data:

    if 'listing_id' not in key and \
       'description' not in key and \
       'address' not in key and \
       'manager_id' not in key and \
       'latitude' not in key and \
       'longitude' not in key:
        listings = turn_to_list(listings, key, data[key])
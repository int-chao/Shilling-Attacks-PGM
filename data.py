from __future__ import print_function
import sys
import numpy as np
import pandas as pd

from SDLib.shillingmodels.averageAttack import AverageAttack
from SDLib.shillingmodels.bandwagonAttack import BandWagonAttack
from SDLib.shillingmodels.randomAttack import RandomAttack
from SDLib.shillingmodels.RR_Attack import RR_Attack
from SDLib.shillingmodels.hybridAttack import HybridAttack

np.set_printoptions(threshold=np.inf)


label_name = 'labels-rand-s10-f5-t10'
profile_name = 'profiles-rand-s10-f5-t10'

def simulate_shilling_attack(label_name, profile_name):
    # attack = AverageAttack('./config/config-100k.conf')
    attack = RandomAttack('./config/config-100k.conf')
    # attack = BandWagonAttack('./config/config-100k.conf')
    # attack = HybridAttack('./config/config-100k.conf')
    # attack = RR_Attack('./config/config-100k.conf')
    attack.insertSpam()
    # attack.farmLink()
    attack.generateLabels(label_name)
    attack.generateProfiles(profile_name)
    # attack.generateSocialConnections('relations.txt')

def build_movies_dict(movies_file):
    movie_id_dict = {}
    with open(movies_file, 'r') as f:
        next(f)
        for i, line in enumerate(f):
            movie_id, title, genres = line.split(',')
            movie_id_dict[int(movie_id)] = i
    return movie_id_dict

def generate_matrix_from_csv(input_file, movies_dict):
    users = 671
    movies = len(movies_dict)
    
    X = np.zeros(shape=(users,movies))
    with open(input_file, 'r') as f:
        next(f)
        for i,line in enumerate(f):
            user, movie_id, rating, timestamp = line.split(',')
            id = movies_dict[int(movie_id)]
            X[int(user)-1, id] = float(rating)
    return X

def generate_100k_matrix(input_file):
    users = 943
    movies = 1682

    X = np.zeros(shape=(users, movies))
    with open(input_file, 'r') as f:
        for i, line in enumerate(f):
            user, movie_id, rating, timestamp = line.split('\t')
            # id = movies_dict[int(movie_id)]
            X[int(user)-1, int(movie_id)-1] = float(rating)
    return X

def generate_dirty_matrix(input_file):
    users = 1036
    # users = 989
    movies = 1682

    X = np.zeros(shape=(users, movies))
    with open(input_file, 'r') as f:
        for i, line in enumerate(f):
            # print(line)
            user, movie_id, rating= line.split(' ')
            # id = movies_dict[int(movie_id)]
            X[int(user)-1, int(movie_id)-1] = float(rating)
    return X

def generate_user_spam_list(input_file):

    # 10%
    spam_users = np.zeros((1036, 1))
    # 5%
    # spam_users = np.zeros((989, 1))
    with open(input_file, 'r') as f:
        for i,line in enumerate(f):
            user, is_spam = line.split(' ')
            spam_users[int(user)-1] = int(is_spam)
            # print(i)
    return spam_users

if __name__ == '__main__':
    
    # Specify data paths

    #movies_file = 'Data/MovieLens/small/movies.csv'
    # ratings_file = 'Data/MovieLens/100k/u.data'
    # dirty_ratings_file = 'Data/dirty/MovieLens/100k/' + profile_name
    # spam_users_file = 'Data/dirty/MovieLens/100k/' + label_name

    simulate_shilling_attack(label_name, profile_name)
    # movies_dict = build_movies_dict(movies_file)
    # R = generate_100k_matrix(ratings_file)
    # R = generate_dirty_matrix(dirty_ratings_file)
    # spam_users = generate_user_spam_list(spam_users_file)
    # print(spam_users_file)

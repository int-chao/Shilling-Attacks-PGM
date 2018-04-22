from __future__ import print_function
from __future__ import division
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

import factorgraph as fg

from data import build_movies_dict, generate_100k_matrix, generate_dirty_matrix, simulate_shilling_attack
import features

# Hyper-parameters
# Negative if we want less than, positive if we want greater than

alpha_t = -3
delta_r = 0.35
beta_1 = -1
tau_1 = 0.5
beta_2 = 1
tau_2 = 1.5
min_rating = 0.5
max_rating = 5
small = 1e-9

D = 8

print('\nSimulating Shilling Attack...')

label_name = 'labels-0.1-10-50'
profile_name = 'profiles-0.1-10-50'

simulate_shilling_attack(label_name, profile_name)

print('Generating User-Item Matrix...\n')

# Set paths
# movies_data = './Data/MovieLens/small/movies.csv'
# ratings_data = './Data/MovieLens/small/ratings.csv'
# ratings_data = './Data/MovieLens/100k/u.data'
# dirty_ratings_data = './Data/dirty/MovieLens/small/' + profile_name
dirty_ratings_data = './Data/dirty/MovieLens/100k/' + profile_name

# User-item rating matrix
# movies_dict = build_movies_dict(movies_data)
# R = generate_matrix(clean_ratings_data, movies_dict)
# R = generate_100k_matrix(ratings_data)
R = generate_dirty_matrix(dirty_ratings_data)

# Data Statistics
num_users = np.shape(R)[0]
num_items = np.shape(R)[1]

print('Initializing...\n')
# Initialize Factor Graph
Graph = fg.Graph()

# Create nodes : node_list = ['m1', 'm2', 'm3', 't1', 't2', 't3']
user_nodes = []
for i in range(num_users):
    user_nodes.append('m' + str(i))

item_nodes = []
for i in range(num_items):
    item_nodes.append('t' + str(i))

# Spam Users and Target Items Initializations
m = np.random.rand(num_users)
m = [0 if i > 0.5 else 0 for i in np.random.rand(num_users)]

t = np.random.rand(num_items)
t = [0 if i > 0.5 else 0 for i in np.random.rand(num_items)]


# Dict to map nosed to their values
user_dict = {}
item_dict = {}

for user_id, user_node in enumerate(user_nodes):
    user_dict[user_node] = m[user_id]

for item_id, item_node in enumerate(item_nodes):
    item_dict[item_node] = t[item_id]

user_rv_list = []
# Add Nodes to Factor Graph
for user_node in user_nodes:
    user_rv_list.append(Graph.rv(user_node, 2))
item_rv_list = []
for item_node in item_nodes:
   item_rv_list.append(Graph.rv(item_node, 2))


# Factor Helper Functions
def almost_sigmoid(x, scale, feature, threshold):
    return 1/(1 + np.exp(np.power(-1, (1-x)) * scale * (feature - threshold)))

print('Building Unary Factors...\n')
# Init factors and factor_vals
g = []
h = []

# Features
# rating_bias = features.item_rating_bias(R, m, num_users, num_items)
psi_i = features.variance(R, num_users, num_items)
phi_u = features.mean_var(R, num_users, num_items)

# Define Factor Distributions
def g_dist(user_node, user_id):
    return almost_sigmoid(user_node, beta_1, phi_u[user_id], tau_1)

def h_dist(item_node, item_id):
    return almost_sigmoid(item_node, beta_2, psi_i[item_id], tau_2)


# Create Factors
for user_id, user_node in enumerate(user_nodes):
    Graph.factor([user_node], potential=np.array([g_dist(0, user_id), g_dist(1, user_id)]))


for item_id, item_node in enumerate(item_nodes):
    Graph.factor([item_node], potential=np.array([h_dist(0, item_id), h_dist(1, item_id)]))


def split_list(list, jump):
    temp = []
    for i in range(0, len(list), jump):
        temp.append(list[i:i+jump])
    return temp

def group_rating_bias(R, num_users, item, m_i_k):

    group_len = len(m_i_k)
    U_i_cap = [R[u, item] for u in range(num_users) if R[u, item] != 5 and R[u, item] != 0] #Ui and Uicap
    R_i_cap = sum(U_i_cap)
    w_i_k = group_len/len(M_i)
    first = (R_i_cap * w_i_k + max_rating * group_len) / (len(U_i_cap) * w_i_k + group_len)
    second = (R_i_cap * w_i_k + max_rating * sum(m_i_k)) / (len(U_i_cap) * w_i_k + sum(m_i_k))

    rating_bias = np.abs(first - second)
    return rating_bias

# Calc Mi
M_i = []
M_i_Users = []
for i in range(num_items):
    m_i = [m[u] for u in range(num_users) if R[u,i] == 5]
    m_i_users = [u for u in range(num_users) if R[u,i] == 5]
    M_i_Users.append(m_i_users)
    M_i.append(m_i)

M_i_k = []
M_i_k_users = []
G_i_vec =[]
for m_idx in M_i:
    # Divide users into groups
    l = len(m_idx)
    G_i = int(np.abs(l) / D) + 1 # Randomly divide user nodes in M_i into G_i groups
    G_i_vec.append(G_i)
    M_i_k.append(split_list(m_idx, G_i))

for m_idx_usr in M_i_Users:
    # Divide users into groups
    l = len(m_idx_usr)
    G_i = int(np.abs(l) / D) + 1 # Randomly divide user nodes in M_i into G_i groups
    G_i_vec.append(G_i)
    M_i_k_users.append(split_list(m_idx_usr, G_i))

def get_potential(group_length, item):

    if group_length == 1:
        potential_i = np.zeros((2,2))

        for v0 in range(2):
            for v1 in range(2):
                m_i_k = [v1]
                rating_bias_i = group_rating_bias(R, num_users, item, m_i_k)
                potential_i[v0, v1] = almost_sigmoid(v0, alpha_t, rating_bias_i, delta_r)

    elif group_length == 2:
        potential_i = np.zeros((2, 2, 2))

        for v0 in range(2):
            for v1 in range(2):
                for v2 in range(2):
                    m_i_k = [v1, v2]
                    rating_bias_i = group_rating_bias(R, num_users, item, m_i_k)
                    potential_i[v0, v1, v2] = almost_sigmoid(v0, alpha_t, rating_bias_i, delta_r)

    elif group_length == 3:
        potential_i = np.zeros((2, 2, 2, 2))

        for v0 in range(2):
            for v1 in range(2):
                for v2 in range(2):
                    for v3 in range(2):
                        m_i_k = [v1, v2, v3]
                        rating_bias_i = group_rating_bias(R, num_users, item, m_i_k)
                        potential_i[v0, v1, v2, v3] = almost_sigmoid(v0, alpha_t, rating_bias_i, delta_r)

    elif group_length == 4:
        potential_i = np.zeros((2, 2, 2, 2, 2))

        for v0 in range(2):
            for v1 in range(2):
                for v2 in range(2):
                    for v3 in range(2):
                        for v4 in range(2):
                            m_i_k = [v1, v2, v3, v4]
                            rating_bias_i = group_rating_bias(R, num_users, item, m_i_k)
                            potential_i[v0, v1, v2, v3, v4] = almost_sigmoid(v0, alpha_t, rating_bias_i, delta_r)

    elif group_length == 5:
        potential_i = np.zeros((2, 2, 2, 2, 2, 2))

        for v0 in range(2):
            for v1 in range(2):
                for v2 in range(2):
                    for v3 in range(2):
                        for v4 in range(2):
                            for v5 in range(2):
                                m_i_k = [v1, v2, v3, v4, v5]
                                rating_bias_i = group_rating_bias(R, num_users, item, m_i_k)
                                potential_i[v0, v1, v2, v3, v4, v5] = almost_sigmoid(v0, alpha_t, rating_bias_i, delta_r)

    elif group_length == 6:
        potential_i = np.zeros((2, 2, 2, 2, 2, 2, 2))

        for v0 in range(2):
            for v1 in range(2):
                for v2 in range(2):
                    for v3 in range(2):
                        for v4 in range(2):
                            for v5 in range(2):
                                for v6 in range(2):
                                    m_i_k = [v1, v2, v3, v4, v5, v6]
                                    rating_bias_i = group_rating_bias(R, num_users, item, m_i_k)
                                    potential_i[v0, v1, v2, v3, v4, v5, v6] = almost_sigmoid(v0,alpha_t,rating_bias_i,delta_r)

    elif group_length == 7:
        potential_i = np.zeros((2, 2, 2, 2, 2, 2, 2, 2))

        for v0 in range(2):
            for v1 in range(2):
                for v2 in range(2):
                    for v3 in range(2):
                        for v4 in range(2):
                            for v5 in range(2):
                                for v6 in range(2):
                                    for v7 in range(2):
                                        m_i_k = [v1, v2, v3, v4, v5, v6, v7]
                                        # print(m_i_k)
                                        rating_bias_i = group_rating_bias(R, num_users, item, m_i_k)
                                        potential_i[v0, v1, v2, v3, v4, v5, v6, v7] = almost_sigmoid(v0,alpha_t,rating_bias_i,delta_r)

    elif group_length == 8:
        potential_i = np.zeros((2, 2, 2, 2, 2, 2, 2, 2, 2))

        for v0 in range(2):
            for v1 in range(2):
                for v2 in range(2):
                    for v3 in range(2):
                        for v4 in range(2):
                            for v5 in range(2):
                                for v6 in range(2):
                                    for v7 in range(2):
                                        for v8 in range(2):
                                            m_i_k = [v1, v2, v3, v4, v5, v6, v7, v8]
                                            # print(m_i_k)
                                            rating_bias_i = group_rating_bias(R, num_users, item, m_i_k)
                                            potential_i[v0, v1, v2, v3, v4, v5, v6, v7, v8] = almost_sigmoid(v0,alpha_t,rating_bias_i,delta_r)


    return potential_i


user_id_list =[]
for u in M_i_k_users[0][5]:
    user_id_list.append('m' + str(u))

print('Building Binary Factors...')

now = time.time()
for item_id, item_node in enumerate(item_nodes):
    for group in M_i_k_users[item_id]:
        for u in group:
            user_id_list.append('m' + str(u))

        if len(user_id_list)==8:
            Graph.factor(
                [item_node, user_id_list[0], user_id_list[1], user_id_list[2], user_id_list[3], user_id_list[4], user_id_list[5],
                 user_id_list[6], user_id_list[7]], potential=get_potential(8, item_id))
        elif len(user_id_list)==7:
            Graph.factor(
                [item_node, user_id_list[0], user_id_list[1], user_id_list[2], user_id_list[3], user_id_list[4], user_id_list[5],
                 user_id_list[6]], potential=get_potential(7, item_id))
        elif len(user_id_list)==6:
            Graph.factor(
                [item_node, user_id_list[0], user_id_list[1], user_id_list[2], user_id_list[3], user_id_list[4], user_id_list[5]],
                potential=get_potential(6, item_id))
        elif len(user_id_list)==5:
            Graph.factor(
                [item_node, user_id_list[0], user_id_list[1], user_id_list[2], user_id_list[3], user_id_list[4]],
                potential=get_potential(5, item_id))
        elif len(user_id_list)==4:
            Graph.factor(
                [item_node, user_id_list[0], user_id_list[1], user_id_list[2], user_id_list[3]],
                potential=get_potential(4, item_id))
        elif len(user_id_list)==3:
            Graph.factor(
                [item_node, user_id_list[0], user_id_list[1], user_id_list[2]],
                potential=get_potential(3, item_id))
        elif len(user_id_list)==2:
            Graph.factor(
                [item_node, user_id_list[0], user_id_list[1]],
                potential=get_potential(2, item_id))
        elif len(user_id_list) == 1:
            Graph.factor(
                [item_node, user_id_list[0]],
                potential=get_potential(1, item_id))

# print('_______________%f seconds__________' % (time.time() - now))

# # Run (loopy) belief propagation (LBP)
now2 = time.time()
iters, converged = Graph.lbp(normalize=True)
print('LBP ran for %d iterations. Converged = %r' % (iters, converged))
print('_______________%f seconds__________' % (time.time() - now2))

#
# # Print out the final messages from LBP
# Graph.print_messages()
#
#
# # Print out the final marginals
for stuff in user_rv_list:
    Graph.print_rv_marginals([stuff])

# print('Done dana done done \n')

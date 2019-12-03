'''
@Author: Yu Di
@Date: 2019-12-02 13:15:44
@LastEditors: Yudi
@LastEditTime: 2019-12-03 14:20:00
@Company: Cardinal Operation
@Email: yudi@shanshu.ai
@Description: This module contains data loader for experiments
'''
import os
import gc
import json
import random
import numpy as np
import pandas as pd
import scipy.io as sio

from collections import defaultdict
from sklearn.model_selection import KFold, train_test_split

def load_rate(src='ml-100k', prepro='origin', binary=False):
    # which dataset will use
    if src == 'ml-100k':
        df = pd.read_csv(f'./data/{src}/u.data', sep='\t', header=None, 
                        names=['user', 'item', 'rating', 'timestamp'], engine='python')

    elif src == 'ml-1m':
        df = pd.read_csv(f'./data/{src}/ratings.dat', sep='::', header=None, 
                        names=['user', 'item', 'rating', 'timestamp'], engine='python')
        # only consider rating >=4 for data density
        df = df.query('rating >= 4').reset_index(drop=True).copy()

    elif src == 'ml-10m':
        df = pd.read_csv(f'./data/{src}/ratings.dat', sep='::', header=None, 
                        names=['user', 'item', 'rating', 'timestamp'], engine='python')
        df = df.query('rating >= 4').reset_index(drop=True).copy()

    elif src == 'ml-20m':
        df = pd.read_csv(f'./data/{src}/ratings.csv')
        df.rename(columns={'userId':'user', 'movieId':'item'}, inplace=True)
        df = df.query('rating >= 4').reset_index(drop=True)

    elif src == 'netflix':
        df = pd.DataFrame()
        cnt = 0
        for f in os.listdir(f'./data/{src}/training_set/'):
            cnt += 1
            if not cnt % 5000:
                print(f'Finish Process {cnt} file......')
            txt_file = open(f'./data/{src}/training_set/{f}', 'r')
            contents = txt_file.readlines()
            item = contents[0].strip().split(':')[0]
            for val in contents[1:]:
                user, rating, timestamp = val.strip().split(',')
                tmp = pd.DataFrame([[user, item, rating, timestamp]], 
                                columns=['user', 'item', 'rating', 'timestamp'])
                df.append(tmp, ignore_index=True)
            txt_file.close()
        df['rating'] = df.rating.astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    elif src == 'lastfm':
        # user_artists.dat
        df = pd.read_csv(f'./data/{src}/user_artists.dat', sep='\t')
        df.rename(columns={'userID':'user', 'artistID':'item', 'weight':'rating'}, inplace=True)
        # treat weight as interaction, as 1
        df['rating'] = 1.0
        # fake timestamp column
        df['timestamp'] = 1

    elif src == 'bx':
        df = pd.read_csv(f'./data/{src}/BX-Book-Ratings.csv', delimiter=";", encoding="latin1")
        df.rename(columns={'User-ID': 'user', 'ISBN': 'item', 'Book-Rating': 'rating'}, inplace=True)
        # fake timestamp column
        df['timestamp'] = 1

    elif src == 'pinterest':
        pass

    elif src == 'amazon-cloth':
        df = pd.read_csv(f'./data/{src}/ratings_Clothing_Shoes_and_Jewelry.csv', 
                        names=['user', 'item', 'rating', 'timestamp'])

    elif src == 'amazon-electronic':
        df = pd.read_csv(f'./data/{src}/ratings_Electronics.csv', 
                        names=['user', 'item', 'rating', 'timestamp'])

    elif src == 'amazon-book':
        df = pd.read_csv(f'./data/{src}/ratings_Books.csv', 
                        names=['user', 'item', 'rating', 'timestamp'], low_memory=False)

    elif src == 'amazon-music':
        df = pd.read_csv(f'./data/{src}/ratings_Digital_Music.csv', 
                        names=['user', 'item', 'rating', 'timestamp'])

    elif src == 'epinions':
        d = sio.loadmat(f'./data/{src}/rating_with_timestamp.mat')
        prime = []
        for val in d['rating_with_timestamp']:
            user, item, rating, timestamp = val[0], val[1], val[3], val[5]
            prime.append([user, item, rating, timestamp])
        df = pd.DataFrame(prime, columns=['user', 'item', 'rating', 'timestamp'])
        del prime
        gc.collect()

    elif src == 'yelp':
        json_file_path = f'./data/{src}/yelp_academic_dataset_review.json'
        prime = []
        for line in open(json_file_path, 'r', encoding='UTF-8'):
            val = json.loads(line)
            prime.append([val['user_id'], val['business_id'], val['stars'], val['date']])
        df = pd.DataFrame(prime, columns=['user', 'item', 'rating', 'timestamp'])
        df['timestamp'] = pd.to_datetime(df.timestamp)
        del prime
        gc.collect()

    elif src == 'citeulike':
        user = 0
        dt = []
        for line in open(f'./data/{src}/users.dat', 'r'):
            val = line.split()
            for item in val:
                dt.append([user, item])
            user += 1
        df = pd.DataFrame(dt, columns=['user', 'item'])
        # fake timestamp column
        df['timestamp'] = 1

    else:
        raise ValueError('Invalid Dataset Error')

    # reset rating to interaction, here just treat all rating as 1
    if binary:
        df['rating'] = 1.0
    # encoding user_id and item_id
    df['user'] = pd.Categorical(df['user']).codes
    df['item'] = pd.Categorical(df['item']).codes

    # which type of pre-dataset will use
    if prepro == 'origin':
        user_num = df['user'].nunique()
        item_num = df['item'].nunique()

        return df, user_num, item_num
    elif prepro == '5core':
        tmp1 = df.groupby(['user'], as_index=False)['item'].count()
        tmp1.rename(columns={'item': 'cnt_item'}, inplace=True)
        tmp2 = df.groupby(['item'], as_index=False)['user'].count()
        tmp2.rename(columns={'user': 'cnt_user'}, inplace=True)
        df = df.merge(tmp1, on=['user']).merge(tmp2, on=['item'])
        df = df.query('cnt_item >= 5 and cnt_user >= 5').reset_index(drop=True).copy()
        df.drop(['cnt_item', 'cnt_user'], axis=1, inplace=True)
        del tmp1, tmp2
        gc.collect()

        user_num = df['user'].nunique()
        item_num = df['item'].nunique()

        return df, user_num, item_num
    elif prepro == '10core':
        tmp1 = df.groupby(['user'], as_index=False)['item'].count()
        tmp1.rename(columns={'item': 'cnt_item'}, inplace=True)
        tmp2 = df.groupby(['item'], as_index=False)['user'].count()
        tmp2.rename(columns={'user': 'cnt_user'}, inplace=True)
        df = df.merge(tmp1, on=['user']).merge(tmp2, on=['item'])
        df = df.query('cnt_item >= 10 and cnt_user >= 10').reset_index(drop=True).copy()
        df.drop(['cnt_item', 'cnt_user'], axis=1, inplace=True)
        del tmp1, tmp2
        gc.collect()

        user_num = df['user'].nunique()
        item_num = df['item'].nunique()
        
        return df, user_num, item_num
    else:
        raise ValueError('Invalid dataset preprocess type, origin/5core/10core expected')

def negative_sampling(ratings, num_ng=999):
    item_pool = set(ratings.item.unique())

    interact_status = ratings.groupby('user')['item'].apply(set).reset_index()
    interact_status.rename(columns={'item': 'inter_items'}, inplace=True)
    interact_status['neg_items'] = interact_status['inter_items'].apply(lambda x: item_pool - x)
    interact_status['neg_samples'] = interact_status['neg_items'].apply(lambda x: random.sample(x, num_ng))
    
    return interact_status[['user', 'neg_samples']]

def split_test(df, test_method='fo', test_size=.2):
    if test_method == 'tfo':
        df = df.sample(frac=1)
        df = df.sort_values(['timestamp']).reset_index(drop=True)
        split_idx = int(np.ceil(len(df) * (1 - test_size)))
        train_set, test_set = df.iloc[:split_idx, :].copy(), df.iloc[split_idx:, :].copy()

    elif test_method == 'fo':
        train_set, test_set = train_test_split(df, test_size=test_size, random_state=2019)

    elif test_method == 'tloo':
        df = df.sample(frac=1)
        df = df.sort_values(['timestamp']).reset_index(drop=True)
        df['rank_latest'] = df.groupby(['user'])['timestamp'].rank(method='first', ascending=False)
        train_set, test_set = df[df['rank_latest'] > 1].copy(), df[df['rank_latest'] == 1].copy()
        del train_set['rank_latest'], test_set['rank_latest']

    elif test_method == 'loo':
        test_set = df.groupby(['user']).apply(pd.DataFrame.sample, n=1).reset_index(drop=True)
        test_key = test_set[['user', 'item']].copy()
        train_set = df.set_index(['user', 'item']).drop(pd.MultiIndex.from_frame(test_key)).reset_index().copy()
    
    else:
        raise ValueError('Invalid data_split value, expect: loo, fo, tloo, tfo')

    return train_set, test_set

def split_validation(train_set, val_method='fo', fold_num=5):
    if val_method in ['tloo', 'tfo', 'loo']:
        cnt = 1
    elif val_method == 'cv':
        cnt = fold_num
    else:
        raise ValueError('Invalid val_method value, expect: cv, loo, tloo, tfo')
    
    train_set_list, val_set_list = [], []
    if val_method == 'cv':
        kf = KFold(n_splits=fold_num, shuffle=False, random_state=2019)
        for train_index, val_index in kf.split(train_set):
            train_set_list.append(train_set.iloc[train_index, :])
            val_set_list.append(train_set.iloc[val_index, :])
    elif val_method == 'tfo':
        train_set = train_set.sample(frac=1)
        train_set = train_set.sort_values(['timestamp']).reset_index(drop=True)

        split_idx = int(np.ceil(len(train_set) * 0.9))

        train_set_list.append(train_set.iloc[:split_idx, :])
        val_set_list.append(train_set.iloc[split_idx:, :])
    elif val_method == 'loo':
        val_set = train_set.groupby(['user']).apply(pd.DataFrame.sample, n=1).reset_index(drop=True)
        val_key = val_set[['user', 'item']].copy()
        train_set = train_set.set_index(['user', 'item']).drop(pd.MultiIndex.from_frame(val_key)).reset_index().copy()

        train_set_list.append(train_set)
        val_set_list.append(val_set)
    elif val_method == 'tloo':
        train_set = train_set.sample(frac=1)
        train_set = train_set.sort_values(['timestamp']).reset_index(drop=True)

        train_set['rank_latest'] = train_set.groupby(['user'])['timestamp'].rank(method='first', ascending=False)
        new_train_set = train_set[train_set['rank_latest'] > 1].copy()
        val_set = train_set[train_set['rank_latest'] == 1].copy()
        del new_train_set['rank_latest'], val_set['rank_latest']

        train_set_list.append(new_train_set)
        val_set_list.append(val_set)

    return train_set_list, val_set_list, cnt

def get_ur(df):
    ur = defaultdict(set)
    for _, row in df.iterrows():
        ur[int(row['user'])].add(int(row['item']))

    return ur

def get_ir(df):
    ir = defaultdict(set)
    for _, row in df.iterrows():
        ir[int(row['item'])].add(int(row['user']))

    return ir
"""
Aggregates analytics on Facebook Messenger usage. 

Usage:
    counter.py aggregate [-c | --rolling=<window>] <self> <dir>
    counter.py single [-c|--rolling=<window>] <self> <chat_name> <dir> 


Options:
    -h --help                Help
    -c --cumulative          Cumulative
    -r --rolling=<window>    Rolling sum with window

"""
import shutil, sys, os
from datetime import datetime, timezone
import json
from typing import List, Union
from collections import defaultdict, Counter


import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from docopt import docopt
import argparse


class FacebookCounter:

    def __init__(self, inbox_dir, self_name):
        self.inbox_dir = inbox_dir
        self.self_name = self_name


    def graph(self, df, columns, cumulative = False, rolling: Union[int, bool] = False):
        # TODO refactor using functional to make this easier to work with? 
        if cumulative:
            for col in columns:
                df[f"{col} Cumulative"] = df[col].cumsum()
            ax = df.plot(y = [f"{col} Cumulative" for col in columns])
        else:
            print(rolling)
            if rolling:
                for col in columns:
                    df[f"{col} {rolling}-day Rolling Average"] = df[col].rolling(window = rolling).mean()
            ax = df.plot(y = [f"{col} {rolling}-day Rolling Average" for col in columns])
        fig = ax.get_figure()
        fig.savefig('test.png')

    def query_single(self, query, start = '01-01-2019', end = '01-25-2021', test: Union[int, bool] = False, cumulative = False, rolling = Union[int, bool]):
        inbox_dir = os.listdir(self.inbox_dir)
        query = ''.join([x.lower() for x in query if x!= ' '])

        found = False
        print(query)
        for convo_dir in inbox_dir:
            print(''.join(convo_dir.split('_')[:-1]))
            if query == ''.join(convo_dir.split('_')[:-1]):
                chatlog = ChatLog(f"{self.inbox_dir}/{convo_dir}")
                found = True
                break
        if found:
            self.process_df(chatlog.df, start, end, cumulative, rolling)
        else:
            raise KeyError(f"chat {query} not found")

    def query_aggregate(self, start = '05-01-2020', end = '01-25-2021', test: Union[int, bool] = False, cumulative = False, rolling : Union[int, bool] = False):
        aggregate_df = pd.DataFrame()
        inbox_dir = os.listdir(self.inbox_dir)
        if test:
            inbox_dir = inbox_dir[:test]
        for convo_dir in inbox_dir:
            chatlog = ChatLog(f"{self.inbox_dir}/{convo_dir}")
            # fix this to do a deep update
            aggregate_df = aggregate_df.add(chatlog.df, fill_value = 0)
        self.process_df(aggregate_df, start, end, cumulative, rolling)
            
    def process_df(self, aggregate_df, start, end, cumulative, rolling):
        
        aggregate_df['Total'] = aggregate_df.sum(axis=1)
        aggregate_df['Other'] = aggregate_df['Total'] - aggregate_df[self.self_name]
        aggregate_df.index = pd.DatetimeIndex(aggregate_df.index)
        
        # augment for graphing
        full_index = pd.date_range(start, end)
        aggregate_df = aggregate_df.reindex(full_index, fill_value = 0)
        aggregate_df.fillna(0, inplace= True)
        
        self.graph(aggregate_df, columns = ['Total', 'Other', self.self_name], cumulative = cumulative, rolling =rolling)
        

class ChatLog:

    def __init__(self, search_dir: str):
        file_list = os.listdir(search_dir)
        json_list = [f"{search_dir}/{file}" for file in file_list if "json" in file]
        self.messages = []
        for json_file in json_list:
            with open(json_file, 'r') as in_json:
                file_data = json.load(in_json) 
                self.messages.extend(file_data['messages'])
                self.participants = file_data['participants']
        self.message_counter = defaultdict(lambda: Counter())
        self.process_chat_data()

    def process_chat_data(self):
        for message in self.messages:
            message_time = datetime.fromtimestamp(message['timestamp_ms']/1000, tz=timezone.utc)
            message_time = pd.Timestamp(message_time)
            self.message_counter[message_time.date()][message['sender_name']] += 1
        # print(self.participants, len(self.message_counter.keys()))

    @property
    def df(self):
        return pd.DataFrame.from_dict(self.message_counter, orient='index')

    @property
    def dict(self):
        return self.message_counter



    
    

if __name__ == "__main__":
    args = docopt(__doc__)
    print(args)
    counter = FacebookCounter(args['<dir>'], args['<self>'])
    if args['single']:
        counter.query_single(query = args['<chat_name>'], test = 10, cumulative = args['--cumulative'], rolling = int(args['--rolling']))
    elif args['aggregate']:
        counter.query_aggregate(cumulative = args['--cumulative'], rolling = int(args['--rolling']))
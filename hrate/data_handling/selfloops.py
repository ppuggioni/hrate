import pandas as pd
import numpy as np
import logging

def read_selfloops_file(path, skiprows=30, skipfooter=30):
    """
    it parses the file and returns a pandas df
    :param path:
    :param skiprows: how many rows of data to skip at the beginning
    :param skipfooter: how many rows of data to skip at the end
    :return:
    """
    with open(path, 'r') as f:
        logging.info('Opening file {}'.format(path))
        first_line = f.readline().strip('\n')

    start_time = pd.to_datetime(first_line, format='%d %B %Y %H:%M:%S')


    df = pd.read_csv(path,
                     names=['Time', 'HR', 'RR'], skiprows=skiprows+2, skipfooter=skipfooter,
                     dtype={'Time': np.float, 'HR': np.float, 'RR': np.float},
                     engine='python'
                     )



    df['Time_stamp'] = start_time + pd.to_timedelta(df['Time'], unit='ms')
    df['Time_lapsed'] = df['Time_stamp'] - df['Time_stamp'].min()
    columns = ['Time_stamp', 'Time_lapsed', 'HR', 'RR']

    return df[columns]
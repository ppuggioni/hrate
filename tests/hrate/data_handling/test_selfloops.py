import logging
from hrate.data_handling.selfloops import read_selfloops_file
FORMAT = '%(asctime)-15s  %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)


def test_read_selfloops_file():

    logging.info('\nTesting read_selfloops_file')
    filename = './data/sample/selfloops/20170804001r.txt'

    df = read_selfloops_file(filename, skiprows=30, skipfooter=30)
    assert len(df.index) == 38235
    required_columns = ['Time_stamp', 'Time_lapsed', 'HR', 'RR']
    for col in required_columns:
        assert col in df.columns
    logging.info('read_selfloops_file tested successfully')

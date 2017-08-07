
Installation
------------

Suggested installation in a virtual environment. It should be both python 2.7 and 3.5 compatible.

```
python setup.py install
pip install -r requirements.txt
```

**Other tools - not needed now!**

To read some of the files you might need to install [wfdb](https://www.physionet.org/physiotools/wfdb-darwin-quick-start.shtml)

Dataset
-------

Folder structure:

- data
    - sample: contains data to test the functions
        - selfloops: data exported from [selfloops app](https://www.selfloops.com/products/heart-rate-variability.html)
        - wfdb: data from the [physiobank dataset](https://www.physionet.org/physiobank/database/crisdb/e/)
    - selfloops: it is the default folder for files.


Running the app
---------------
1. To analyse new selfloops files, simply add them to `data/selfloops` and make sure they have txt extension.
2. `python app.py` 
3. Open Chrome at `http://127.0.0.1:8050/`





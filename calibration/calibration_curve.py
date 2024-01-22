# curve fitting support library
from scipy.optimize import curve_fit

# graphing library
import matplotlib.pyplot as plt

# data science tools
import pandas as pd
import numpy as np

# lin = a * x + b
# exp = c * np.exp((x-f)/100*h) + g
# return np.where(x < f, lin, exp)

def licor(filename : str) -> pd.DataFrame:
    """Parses data from Licor file and
    generates a data frame containing only
    valid datetime and par information.

    Args:
        filename (str): file name w/ extension

    Returns:
        pd.DataFrame: valid Licor dataframe
    """
    
    # create dataframe from txt file
    df = pd.read_csv(filepath_or_buffer=filename,
                     usecols=(range(3)),
                     header=None,
                     sep='\t')

    # rename columns for clarity
    df.columns = ['valid','datetime','par']

    # convert PAR column into numeric datatype
    df['par'] = pd.to_numeric(errors='coerce', arg=df['par'])
    
    # remove all invalid and irrelevant data
    df.drop(labels=df[df.iloc[:, 0] != 1].index, inplace=True)
    df.dropna(subset=['par'], inplace=True)
    df.drop(labels='valid', axis=1, inplace=True)

    # convert datetime column into datetime datatype
    df['datetime'] = pd.to_datetime(arg=df['datetime'].str[:-3])
    df['datetime'] = df['datetime'].dt.tz_localize('America/Los_Angeles')

    # recalculate indices
    df.reset_index(drop=True, inplace=True)

    return df

def adafruit(filename : str) -> pd.DataFrame:
    """Parses data from AdaFruitIO file and
    generates a data frame containing only
    valid datetime and voltage information

    Args:
        filename (str): file name w/ extension

    Returns:
        pd.DataFrame: valid AdaFruit dataframe
    """

    # create dataframe from csv file
    df = pd.read_csv(filename, usecols=([1,3]))

    # rename columns for clarity
    df.columns = ['mv', 'datetime']
    df = df[['datetime', 'mv']]
    
    # convert mv into numerical data
    df['mv'] = pd.to_numeric(df['mv'])

    # convert datetime column into datetime datatype
    df['datetime'] = pd.to_datetime(arg=df['datetime'].str[:-7])
    df['datetime'] = df['datetime'].dt.tz_localize('UTC')

    # convert to correct time zone
    df['datetime'] = df['datetime'].dt.tz_convert('America/Los_Angeles')

    return df

def func(x, a, b, c, d):
    log = a * np.log(x + b) + c
    return log

def match(licor_filename : str, ada_filename) -> pd.DataFrame:
    # parse data from given source files
    licor_df = licor(licor_filename)
    ada_df = adafruit(ada_filename)

    # perform data point matching
    df = pd.merge_asof(ada_df, licor_df, on='datetime')

    # customizable noise threshold
    par_threshold = 1
    mv_threshold = 1

    # remove dead data points
    df = df[df['par'].diff().abs() > par_threshold]
    df = df[df['mv'].diff().abs() > mv_threshold]
    df = df.reset_index(drop=True)
    
    # sort data frame in-place based on mv
    df.sort_values(by='mv', inplace=True)
    
    # group data based on threshold proximity
    threshold = 5
    
    bins = np.arange(df['mv'].min(), 
                     df['mv'].max() + threshold, 
                     threshold)
    
    df['bin'] = pd.cut(df['mv'], bins=bins, labels=False)
    
    df = df.groupby('bin').mean().reset_index()
    
    plt.scatter(df['mv'], df['par'], s=1)
    
    # curve fitting
    params, covariance = curve_fit(func, df['mv'], df['par'], method='lm', ftol=1e-32, maxfev=1000000)
    a, b, c, d = params
    
    plt.plot(df['mv'], func(df['mv'], a, b, c, d), 'k')
    plt.title(f'Photodiode-to-Par: {a}*log({d} * x + {b}) + {c}')
    plt.show()

match("test_0830_2.txt", "pv.csv")
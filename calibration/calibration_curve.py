# curve fitting support library
from scipy.optimize import curve_fit

# graphing library
import matplotlib.pyplot as plt

# data science tools
import pandas as pd
import numpy as np

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

def func(x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
    """
    Helper function for relating AdafruitIO
    photodiode values to Licor PAR data
    
    Args:
        x (np.ndarray): photodiode values
        a (float): scalar
        b (float): log scalar
        c (float): log offset
        d (float): offset
    
    Returns:
        np.ndarray: estimated par values
    
    """
    
    return a * np.log(b * x + c) + d

def match(licor_filename : str, ada_filename : str, par_threshold : float = 1, pho_threshold : float = 1, smoothing_factor : int = 5, display : bool = False) -> np.ndarray:
    """
    Parent function for automatic calibration of photodiode output to equivalent \n
    PAR measurements with simple pruning and smoothing factored in.
    
    Args:
        licor_filename (str): licor data file w/ extension
        ada_filename (str): photodiode data file w/ extension
        par_threshold (float): removal region (default = 1)
        pho_threshold (float): removal region (default = 1)
        smoothing_factor (int): smooth out data via averaging (default = 5)
        display (bool): display results as graph
    
    Returns:
        ???
    """
    
    # parse data from given source files
    licor_df = licor(licor_filename)
    ada_df = adafruit(ada_filename)
    
    # perform data point matching
    df = pd.merge_asof(ada_df, licor_df, on='datetime')
    
    # remove dead data points
    df = df[df['par'].diff().abs() > par_threshold]
    df = df[df['mv'].diff().abs() > pho_threshold]
    df = df.reset_index(drop=True)
    
    # sort data frame in-place based on photodiode data
    df.sort_values(by='mv', inplace=True)
    
    # group and average data based on threshold proximity
    bins = np.arange(df['mv'].min(), 
                     df['mv'].max() + smoothing_factor, 
                     smoothing_factor)
    
    df['bin'] = pd.cut(df['mv'], bins=bins, labels=False)    
    df = df.groupby('bin').mean().reset_index()
    
    # curve fitting
    params, covariance = curve_fit(func, df['mv'], df['par'], method='lm', ftol=1e-32, maxfev=1000000)
    a, b, c, d = params
    
    # display results
    if(display):
        plt.scatter(df['mv'], df['par'], s=1)
        plt.plot(df['mv'], func(df['mv'], a, b, c, d))
        plt.title(f'{a} * log({b} * x + {c}) + {d}')
        plt.show()







# def match(licor_filename : str, ada_filename : str, par_threshold : float = 1, pho_threshold : float  = 1, smoothing_factor : int = 5) -> pd.DataFrame:
#     """
    
    
    
#     """
    
#     # parse data from given source files
#     licor_df = licor(licor_filename)
#     ada_df = adafruit(ada_filename)

#     # perform data point matching
#     df = pd.merge_asof(ada_df, licor_df, on='datetime')

#     # customizable noise threshold
#     par_threshold = 1
#     mv_threshold = 1

#     # remove dead data points
#     df = df[df['par'].diff().abs() > par_threshold]
#     df = df[df['mv'].diff().abs() > mv_threshold]
#     df = df.reset_index(drop=True)
    
#     # sort data frame in-place based on mv
#     df.sort_values(by='mv', inplace=True)
    
#     # group data based on threshold proximity
#     threshold = 5
    
#     bins = np.arange(df['mv'].min(), 
#                      df['mv'].max() + threshold, 
#                      threshold)
    
#     df['bin'] = pd.cut(df['mv'], bins=bins, labels=False)
    
#     df = df.groupby('bin').mean().reset_index()
    
#     # curve fitting
#     params, covariance = curve_fit(func, df['mv'], df['par'], method='lm', ftol=1e-32, maxfev=1000000)
#     a, b, c, d = params
    
#     return a, b, c, d




if __name__ == "__main__":
    match("demo_data/licor_demo.txt", "demo_data/photodiode_demo.csv", display=True)
import pandas as pd
import numpy as np
import time
import datetime
import concurrent.futures
from loguru import logger
from termcolor import colored
from oandapyV20 import API
import oandapyV20.endpoints.accounts as accounts
from src.fetch_historical_data import FetchHistoricalData
from src.streaming_pipeline import StreamingDataPipeline
from src.utils import parse_yml, calculate_indicators
from dotenv import load_dotenv
import os

load_dotenv()


# Global variables
accountID = os.getenv("OANDA_ACCOUNT_ID")
token = os.getenv("OANDA_ACCESS_TOKEN")


def get_config(path):
    return parse_yml(path)


def get_account_summary():
    api = API(access_token=token)
    r = accounts.AccountSummary(accountID)
    api.request(r)
    account_info = r.response["account"]
    print(
        colored("Account ID: ", "green")
        + f"{account_info['id']}"
        + "\n"
        + colored("Account Balance: ", "green")
        + f"{account_info['balance']}"
        + "\n"
        + f"As of: {datetime.datetime.now()}"
    )


def fetch_historical_candles(cfg, instrument):
    fetcher = FetchHistoricalData(
        instrument,
        cfg["candlestick"]["granularity"],
        token,
        cfg["candlestick"]["count"],
    )
    df = fetcher.fetch_data()
    df = fetcher.process_data(df)
    return df


def start_streaming_pipeline(instrument, df, precision, stop_loss, take_profit):
    client = API(access_token=token)
    params = {"instruments": instrument}
    pipeline = StreamingDataPipeline(
        accountID, params, client, df, precision, stop_loss, take_profit
    )
    pipeline.run()


def select_currency_pair(round_number):
    print(f"Select the currency pair to trade in round {round_number}:")
    print("1: EUR/USD")
    print("2: GBP/USD")
    print("3: USD/JPY")
    print("4: AUD/USD")
    currency_pair = input("Enter the number corresponding to your choice: ")

    if currency_pair == "1":
        return "EUR_USD"
    elif currency_pair == "2":
        return "GBP_USD"
    elif currency_pair == "3":
        return "USD_JPY"
    elif currency_pair == "4":
        return "AUD_USD"
    else:
        print("Invalid selection. Defaulting to EUR/USD.")
        return "EUR_USD"


def main():
    logger.info("Starting the pipeline...")
    cfg = get_config("./cfg/parameters.yaml")
    # Get account summary before starting the pipeline
    get_account_summary()
    time.sleep(3)
    instrument1 = select_currency_pair(1)
    instrument2 = select_currency_pair(2)

    while instrument1 == instrument2:
        print("Duplicate pairs are not allowed. Please select again.")
        instrument2 = select_currency_pair(2)

    print(f"Selected currency pairs: {instrument1}, {instrument2}")

    precision_1 = cfg["instrument_precision"][instrument1]
    stoploss_1 = cfg["stop_loss"][instrument1]
    takeprofit_1 = cfg["take_profit"][instrument1]
    precision_2 = cfg["instrument_precision"][instrument2]
    stoploss_2 = cfg["stop_loss"][instrument2]
    takeprofit_2 = cfg["take_profit"][instrument2]
    df_1 = calculate_indicators(fetch_historical_candles(cfg, instrument1))
    df_1.dropna(inplace=True)
    df_2 = calculate_indicators(fetch_historical_candles(cfg, instrument2))
    df_2.dropna(inplace=True)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future1 = executor.submit(
            start_streaming_pipeline,
            instrument1,
            df_1,
            precision_1,
            stoploss_1,
            takeprofit_1,
        )
        future2 = executor.submit(
            start_streaming_pipeline,
            instrument2,
            df_2,
            precision_2,
            stoploss_2,
            takeprofit_2,
        )

        try:
            result1 = future1.result()
            result2 = future2.result()
        except Exception as e:
            print(f"An exception occurred: {e}")
    # precision = cfg["instrument_precision"][instrument]
    # stoploss = cfg["stop_loss"][instrument]
    # takeprofit = cfg["take_profit"][instrument]
    # df = calculate_indicators(fetch_historical_candles(cfg, instrument))
    # df.dropna(inplace=True)
    # logger.success(f"Historical candlestick data fetched successfully:\n{df.tail()}")
    # start_streaming_pipeline(instrument, df, precision, stoploss, takeprofit)
    # logger.info("Pipeline completed.")


if __name__ == "__main__":
    main()

from autotrader import AutoTraderScraper
from kijijiauto import KijijiAutoScraper
from time import sleep


if __name__ == "__main__":
    trader = AutoTraderScraper()
    kijiji = KijijiAutoScraper()
    while True:
        try:
            trader.main()
            kijiji.main()
            print("Wait 10 min!")
            print("To stop script press Ctrl+C")
            sleep(60*10)
        except Exception as err:
            print(err)
            break
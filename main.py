import yfinance as yf
import requests
from dotenv import dotenv_values
import time
import pytz
import datetime

config = dotenv_values(".env")

# Define start and end times for the desired time range (8:45 to 15:40 IST)
start_time = datetime.time(8, 55)
end_time = datetime.time(15, 35)
timer = 60.0

# Configuring Telegram Bot
BOT_TOKEN, CHAT_ID = config["BOT_TOKEN"], config["CHAT_ID"]


def is_between(start_time, end_time):
    """Check if the current time is between start_time and end_time."""
    now = datetime.datetime.now(pytz.timezone("Asia/Kolkata")).time()
    return start_time <= now <= end_time

# Function to check if the current day is a weekday
def is_weekday():
    """Check if the current day is a weekday."""
    today = datetime.date.today()
    return today.weekday() in range(0, 5)

def IST(message):
    # Returns the current time in IST (India Standard Time) along with a given message, including the day of the week.
    now = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
    return f"{now.strftime('%A, %Y-%m-%d %H:%M:%S')} -- {message}"


def send(message):
    """Send a message to the Telegram bot."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
        requests.get(url).json()  # this sends the message
        return True
    except Exception as error:
        print(f"Telegram message error: {error}")
        return False


def get_targets():
    """Fetch the targets from telegram."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1"
        response = requests.get(url).json()

        if response["result"]:
            last_message = (response["result"][0])["message"]["text"]
            last_message_target = last_message.split("=")[-1]
            # print(last_message)

            ref = last_message_target.split("\n")
            CE = int(ref[0].replace("CE : ", "").strip())
            PE = int(ref[1].replace("PE : ", "").strip())
            BUFFER = int(ref[2].replace("BUFFER : ", "").strip())
            RADAR = ref[3].replace("RADAR : ", "").strip() == "Yes"  # Convert to boolean

            return (CE, PE, BUFFER, RADAR)

    except Exception as error:
        send(f"received error : {error}")
        return (0, 0, 0, False)


def calculation(latest_price, CE, PE, BUFFER):
    """Calculate index price to target price CE and PE chance

    Args:
        latest_price (int): price of index in int
        CE (int): price of call option target
        PE (int): price of call option target
        BUFFER (int): number of buffer zone

    Returns:
        bool: true if the index entered buffer or crossed, false otherwise
    """
    # CE_chance, PE_chance = latest_price - CE, latest_price - PE
    approach_CE, approach_PE = CE - BUFFER, PE + BUFFER

    if( (latest_price >= approach_CE) or (latest_price<=approach_PE) ):
        send("Index entered Buffer Zone")

    elif latest_price >= CE + BUFFER:
        send("Index Crossed CE Buffer Zone")

    elif latest_price <=  PE - BUFFER:
        send("Index Crossed PE Buffer Zone")


def get_nifty_price():
    """Fetch the data of the price using yfinance library"""
    # start_time = time.time()  # Start the timer

    nifty = yf.Ticker("^NSEI")  # NIFTY 50 index symbol
    nifty_data = nifty.history(period="1d")

    if not nifty_data.empty:
        latest_price = nifty_data["Close"].iloc[-1]
        # print(f"Latest NIFTY 50 Index Price: {latest_price}")
        return int(latest_price)
    else:
        return "Failed to fetch"


if __name__ == "__main__":
    while True:
        # Check if it's a weekday and current time is within the desired range
        if is_between(start_time, end_time) and is_weekday():
            CE, PE, BUFFER, RADAR = get_targets()
            
            starttime = time.monotonic()
            send("rader started")
            print(IST("Radar Started"))
            while RADAR:
                latest_price = get_nifty_price()
                calculation(latest_price, CE, PE, BUFFER)
                time.sleep(timer - ((time.monotonic() - starttime) % timer))

                if not is_between(start_time, end_time):
                    send("⏸ Radar Stopped")
                    print(IST("Radar stopped"))
                    time.sleep(17*15*60)
                    break
 
            send("failed to fetch, update the targets")
            time.sleep(5*60)

        # If it's not a weekday, print "not now" and wait 24 hours
        elif(is_weekday() == False):
            # it's weekend, check in after 24 hours
            send("----weekend----")
            time.sleep(24 * 60 * 60)
        
        # let check again for the time range after 30 sec delay
        else:
            time.sleep(30)

import requests, json, sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from dateutil import parser
from time import sleep
import dwConfig


def main():
    # Check for command line argument override of plot point count
    overRide = False
    nightCalc = False
    l = len(sys.argv)
    if l > 1:
        arg = sys.argv[1]
        if arg == '-h' or arg == '--help':
            print("\nUsage options:")
            print("python DiscWeather.py            :uses settings as defined in dwConfig.py")
            print("python DiscWeather.py -p=num     :plots num points, 12 <= num <= 156")
            print("python DiscWeather.py -plot=num  :plots num points, 12 <= num <= 156")
            print("python DiscWeather.py -n         :enables night time Quality index calculation")
            print("python DiscWeather.py -night     :enables night time Quality index calculation")
            print("python DiscWeather.py -help      :prints usage help to the console")
            print("python DiscWeather.py -H         :prints usage help to the console\n")
            sys.exit()
        elif arg == '-n' or arg == '--night':
            nightCalc = True
        elif arg.startswith('-p=') or arg.startswith('--plot='):
            ag = arg.split('=')
            try:
                numHrs = int(ag[1])
                if numHrs >= 12 and numHrs <= 156:
                    overRide = True
                    print(f"\nCommand line override. Number of plot points = {numHrs}")
                else:
                    print("\nCommand line argument value out of range. Using default plot values.")
            except ValueError:
                print("\nInvalid command line argument value. Using default plot values.")
        else:
            print("\nInvalid command line argument format. Using default plot values.")

    # Check thresholds in dwConfig.py. Exit if not valid.
    checkThresh()
    # Get favorite locations from 'favorites.txt' if it exists. Check latitude/longitude values.
    faves = []
    favesExist = False
    try:
        with open("favorites.txt", "r") as f:
            print('File favorites.txt found.')
            for line in f:
                line = line.strip()
                if not line.startswith('#') and len(line) != 0:     # Ignore comments and blank lines
                    favesExist = True
                    items = line.split(',')
                    alias = items[0]
                    try:
                        lat = float(items[1])
                    except ValueError:
                        print(f"Latitude value error in favorites.txt for course {items[0]}. Please correct.")
                        sys.exit("Program Ended\n")
                    try:
                        lon = float(items[2])
                    except ValueError:
                        print(f"Longitude value error in favorites.txt for course {items[0]}. Please correct.")
                        sys.exit("Program Ended\n")
                    location = (lat, lon)
                    faveLine = [alias, location]
                    faves.append(faveLine)
    except FileNotFoundError:
        print("No favorites found.")
    
    # Print favorites to console for user selection
    if favesExist:
        askString = 'Enter Course Number, C(Custom Address) or Q(Quit)'
        i = 0
        print()
        for location in faves:          # I should use enumerate here...
            print(i+1, location[0])
            i += 1
        print()
    else:
        askString = 'Enter C(Custom Address) or Q(Quit)'

    # Get User Selection: favorite course, custom address or quit?
    asking = True
    while asking:
        inp = input(askString).strip().upper()
        if inp == 'Q':
            sys.exit('\nUser exited program.\n')
        elif inp == 'C':
            print('Please enter a US address:\n')
            Street = input('Enter Street number and name: ').strip()
            City = input('Enter US City: ').strip()
            State = input('Enter US State: ').strip()
            Z = input('Enter ZIP Code: ').strip()
            Zip = int(Z)
            print()
            match, Lt, Ln = getLocation(Street, City, State, Zip)
            if match:
                asking = False
                courseName = Street
                LAT = Lt
                LON = Ln
                print("Geocoding of user address successfull.")
                # Ask if user wants to save user address to faves
                ask = True
                while ask:
                    inpt = input("Would you like to save this location to your favorites (Y/N)?").strip().upper()
                    if inpt == 'Y':
                        ask = False
                        addToFaves(str(LAT), str(LON))
                    elif inpt == 'N':
                        ask = False
                    else:
                        print("Invalid input. Try again.")
            else:
                print("Invalid entry. Try again.")
        elif inp.isdigit() and favesExist:
            course = int(inp)
            if course > 0 and course <= len(faves):
                asking = False
                courseName = faves[course-1][0]
                LAT = faves[course-1][1][0]
                LON = faves[course-1][1][1]
            else:
                print('Invalid entry. Try again.\n')
        else:
            print('Invalid entry. Try again.\n')
    print() 

    # If you get here, then courseName, LAT and LON should be correctly populated.
    # Use LAT/LON to get hourly forecast for specified geolocation

    # U.S. Weather Service API queries
    # See: https://www.weather.gov/documentation/services-web-api#/default/gridpoint_stations for API documentation
    BASE_URL = "https://api.weather.gov/points/"

    Lat = str(LAT)
    Lon = str(LON)
    url = BASE_URL + Lat + ',' + Lon

    try:
        resp = requests.get(url)
    except:
        sys.exit(f"NWS Points query using {LAT}, {LON} failed. Exiting program.")
    if resp.status_code == 200:
        jresp = resp.json()
    FcstURL = jresp["properties"]["forecastHourly"]
    
    # If you get here, then you have a valid URL for the hourly forecast of specified location.
    sleep(1)
    print(f"Retrieving Hourly Forecast for {courseName} at {LAT}, {LON} using:")
    print(FcstURL)
    print()

    try:
        fcstJSON = requests.get(FcstURL).json()
    except:
        sys.exit(f"NWS Hourly Forecast query using {FcstURL} failed. Exiting program.")
    
    # Save the hourly forecast json to a file
    with open("NWSForecast.txt", "w") as f:
        json.dump(fcstJSON, f, indent=3)
    
    # Prepare data to be plotted
    temp = []
    wind = []
    precip = []
    dayTime = []
    hours = []
    scores = []

    # Test if command line argument has overriden dWConfig.numHours
    if overRide:  
        NUMHRS = numHrs
    else:
        NUMHRS = dwConfig.numHours
    
    # Extract data from fcstJSON for the number of datapoints set by config.numHours
    for i in range(NUMHRS):
        period = fcstJSON["properties"]["periods"][i]
        t = period["temperature"]
        temp.append(t)
        p = period["probabilityOfPrecipitation"]["value"]
        precip.append(p)
        d = period["isDaytime"]
        dayTime.append(d)
        dts = parser.parse(period["startTime"][:19])
        hours.append(dts)
        windStr = period["windSpeed"]
        w1 = windStr.split(' ')
        w = int(w1[0])
        wind.append(w)
        scores.append(getScore(t,w,p,d or nightCalc)) #'d or nightCalc' lets -n cmd line override isDayTime in dwConfig

    # Plot the weather parameter and DiscWeather Forecasts using 4 subplots, aligned vertically
    fig, axs = plt.subplots(4, 1, sharex=True, figsize=(16,10))

    axs[0].plot(hours, temp, color='blue', marker='o', markersize=4, linestyle='-')
    axs[0].set_title('Hourly Temperature Forecast')
    axs[0].set_ylabel('Temperature(F)')
    axs[0].grid(True, which='major', color='lightgray')
    axs[0].axhline(y = dwConfig.LoT, color='red', linestyle='--')
    if min(temp) >= 25 and max(temp) <= 100:
        axs[0].set_ylim(25,100)
        axs[0].axhline(y = dwConfig.HiT, color='red', linestyle='--')
    elif max(temp) > 100:
        axs[0].axhline(y = dwConfig.HiT, color='red', linestyle='--')

    axs[1].plot(hours, wind, color='green', marker='o', markersize=4, linestyle='-')
    axs[1].set_title('Hourly Wind Forecast')
    axs[1].set_ylabel('Wind Speed(mpH)')
    axs[1].grid(True, which='major', color='lightgray')
    axs[1].axhline(y = dwConfig.HiW, color='red', linestyle='--')
    
    axs[2].plot(hours, precip, color='black', marker='o', markersize=4, linestyle='-')
    axs[2].set_title('Hourly Precipitation Forecast')
    axs[2].set_ylabel('Chance of Precipitation(%)')
    axs[2].grid(True, which='major', color='lightgray')
    axs[2].axhline(y = dwConfig.HiP, color='red', linestyle='--')

    axs[3].fill_between(hours, 0, scores, alpha=0.7)
    axs[3].set_title('DiscWeather Quality Index')
    axs[3].set_xlabel('Powered by the U.S. National Weather Service Web API', loc='right', size='large', weight='normal', style='italic')
    axs[3].set_ylabel('Weather Quality(1-100)')
    axs[3].tick_params(axis='x', which='major', labelsize=8, colors='b')
    axs[3].tick_params(axis='x', which='minor', labelsize=6)
    axs[3].grid(True, which='major', color='lightgray')
    axs[3].set_axisbelow(True)

    axs[3].set_ylim(0,100)
    axs[3].xaxis.set_major_locator(mdates.HourLocator(byhour=0))
    axs[3].xaxis.set_major_formatter(mdates.DateFormatter('%a %d'))
    axs[3].xaxis.set_minor_locator(mdates.HourLocator(byhour=range(24)))
    axs[3].xaxis.set_minor_formatter(mdates.DateFormatter('%I:%M%p'))
    for label in axs[3].get_xticklabels(which='both'):
        label.set(rotation=90, horizontalalignment='center')
    
    fig.suptitle(f"DiscWeather Forecast for {courseName}", x=0.05, y = 0.98, horizontalalignment='left', weight='bold', size='x-large')
    plt.tight_layout()
    print("Showing Plot...")
    plt.show()
    print("Program Ended\n")
# End main()

# Functions
def checkThresh():
    '''
    Checks logical relationship of threshold values in dwConfig. Exits with error message if invalid.
    '''
    if dwConfig.LoT >= dwConfig.MidLoT or dwConfig.MidLoT > dwConfig.MidHiT or dwConfig.MidHiT >= dwConfig.HiT:
        sys.exit('Invalid Temperature thresholds. Modify dwConfig.py to fix.')
    elif dwConfig.LoW >= dwConfig.HiW:
        sys.exit('Invalid Wind thresholds. Modify dwConfig.py to fix.')
    elif dwConfig.LoP >= dwConfig.HiP:
        sys.exit('Invalid Precipitation thresholds. Modify dwConfig.py to fix.')
    else:
        return

def getLocation(street, city, state, zp):
    '''
    Uses U.S. Census Bureau Geocoding API to get latitude/longitude of the street address params passesd in
    Returns a Boolean indicating successful geocoding of address and latitude / longitude values of address.
    Lat / Lon are in decimal degrees, represented as floats with 4 digits of precision
    '''
    LocBASE = "https://geocoding.geo.census.gov/geocoder/"
    return_type = 'locations'
    search_type = 'address'
    params = {
    'street': street,
    'city': city,
    'state': state,
    'zip': zp,
    'benchmark': 'Public_AR_Current',
    'format': 'json'
    }
    
    try:
        response = requests.get(f'{LocBASE}{return_type}/{search_type}', params=params)
    except:
        return False, 0.0, 0.0
    
    if response.status_code == 200:
        jresp = response.json()
        try:
            with open("GeoLocation.txt", "w") as f:
                json.dump(jresp, f, indent=3)
        except:
            print("Failed to write GeoLocation.txt")
        numMatch = len(jresp['result']['addressMatches'])
        if numMatch == 0:
            print("No matching address in US Census database.")
            return False, 0.0, 0.0
        else:
            Lt = jresp['result']['addressMatches'][0]['coordinates']['y']
            Ln = jresp['result']['addressMatches'][0]['coordinates']['x']
            Lat = round(Lt, 4)
            Lon = round(Ln, 4)
            # Confirm lat/lon is within continental U.S.
            if Lat < 49.0 and Lat > 24.54 and Lon < -67.0 and Lon > -124.7:
                return True, Lat, Lon
            else:
                print("Latitude and Longitude outside of continental US. Try again.")
                return False, 0.0, 0.0
    else:
        return False, 0.0, 0.0

def getScore(temp, wind, precip, daylight):
    '''
    Calculates relative contribution levels for temperature, wind and precipitation to the overall
    DiscWeather Quality Index based on settings / thresholds and returns a Quality Index value as a float. 
    '''
    MaxTScore = dwConfig.MaxTScore
    MaxWScore = dwConfig.MaxWScore
    MaxPScore = dwConfig.MaxPScore
    
    # Weather parameter thresholds for calculating DiscWeather scores
    LoT = dwConfig.LoT        # Below which temp score will be 0. Above which score increases to max at MidLoT.
    MidLoT = dwConfig.MidLoT  # Above which temp score will be max until MidHiT
    MidHiT = dwConfig.MidHiT  # Above which temp score decreases to 0 at HiT
    HiT = dwConfig.HiT        # Above which temp score will be 0
    LoW = dwConfig.LoW        # Below which wind score will be Max. Wind score attenuates to 0 at HiW.
    HiW = dwConfig.HiW        # Above which wind score will be 0
    LoP = dwConfig.LoP        # Below which precip score will be Max. Precip score attenuates to 0 at HiP.
    HiP = dwConfig.HiP        # Above which precip score will be 0
    
    # Calculate DiscWeather Quality Index:
    if dwConfig.daylightOnly and not daylight:
        return 0
    
    # Temp Score Calculation:
    d1 = temp - LoT
    span1 = MidLoT - LoT
    d2 = temp - MidHiT
    span2 = HiT - MidHiT
    if temp < LoT:
        return 0
    elif temp >= LoT and temp < MidLoT:
        tscore = MaxTScore * (d1/span1)
    elif temp >= MidLoT and temp < MidHiT:
        tscore = MaxTScore
    elif temp >= MidHiT and temp <= HiT:
        tscore = MaxTScore - (MaxTScore*(d2/span2))
    elif temp > HiT:
        return 0

    # Wind Score Calculation:
    w = wind - LoW
    wspan = HiW - LoW
    if wind <= LoW:
        wscore = MaxWScore
    elif wind > LoW and wind <= HiW:
        wscore = MaxWScore - (MaxWScore *(w/wspan))
    else:
        return 0

    # Precipitation Score Calculation:
    p = precip - LoP
    pspan = HiP - LoP
    if precip <= LoP:
        pscore = MaxPScore
    elif precip > LoP and precip <= HiP:
        pscore = MaxPScore - (MaxPScore *(p/pspan))
    else:
        return 0

    return tscore + wscore + pscore     # Return overall Quality Index 

def addToFaves(lat, lon):
    '''
    Adds a new entry to the favorites.txt file based on user-entered courseName and latitude/longitude
    values passed into the function.
    '''
    asking = True
    while asking:
        Alias = input("Input an alphanumeric alias for this location, such as the course name: ").strip()
        alias = Alias.replace(" ","")   # Remove spaces for testing with isalnum()
        if alias.isalnum():
            wString = f"\n{Alias},{lat},{lon}"
            try:
                with open("favorites.txt", "a") as f:
                    f.write(wString)
                    print(f"Location added to Favorites as {wString}")
            except FileNotFoundError:
                print("File not found. Creating favorites file.")
                with open("favorites.txt", "w") as f2:
                    f2.write("#Alias,Latitude,Longitude")
                    f2.write(wString)
                    print(f"Location added to Favorites as {wString}")
            asking = False
        else:
            print("Invalid alphanumeric input. Try again.")
    return


if __name__ == "__main__":
    main()


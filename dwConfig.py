
numHours = 144          # Number of hours to plot: (from 12 to 156)
daylightOnly = True     # Set to false to allow night predictions for glow disc play

# Thresholds for calculating hourly DiscWeather scores:

LoT = 45        # Below which score will be 0. Above which temp score increases to max at MidLoT.
MidLoT = 65     # Above which temp score will be max
MidHiT = 85     # Above which temp score attenuates to 0 at HiT
HiT = 95        # Above which temp score will be 0
LoW = 8         # Below which wind score will be Max. Wind score attenuates to 0 at HiW.
HiW = 17        # Above which wind score will be 0
LoP = 15         # Below which precip score will be Max. Precip score attenuates to 0 at HiP.
HiP = 65        # Above which precip score will be 0

# Relative contributions for temperature, wind and precipitation to overall score / Quality Factor.
# The total for all 3 must add up to 100.
MaxTScore = 40
MaxWScore = 35
MaxPScore = 100 - (MaxTScore + MaxWScore)

# Course info now in favorites.txt
'''
CourseList = [['Franklin Park',(39.1302, -77.7435)],
                ['Clarkes Gap', (39.2292, -77.5505)],
                ['Ditto Farms', (39.6146, -77.6711)],
                ['Seneca Creek', (39.1368, -77.2597)],
                ['Heritage Park', (39.5025, -77.3493)],
                ['Woodsboro Park', (39.5333, -77.3074)],
                ['Riverwalk Park', (39.4335, -77.3891)],
                ['Middletown Park', (39.4495, -77.5279)],
                ['Sam Michaels', (39.3433, -77.8095)],
                ['Sherando', (39.0830, -78.1804)],
                ['Emmitsburg', (39.7036, -77.3327)],
                ['Hal and Berni Hanson', (39.9819, -77.5459)],
                ['Bull Run', (38.8077, -77.4775)],
                ['Burke Lake', (38.7637, -77.3042)],
                ]
'''

"""Fictional MVP scenarios, not reports of actual weather or scheduled events.

Rules apply to occurrence dates, not just the forecast's starting month.
A single scenario chooses at most one weather, event and commercial signal.
"""
SIGNALS = []


def add(key, country, group, label, months, impact, target='all', cities=(), formats=(), weekdays=(), icon='event'):
    SIGNALS.append(dict(id=key, country=country, group=group, label=label,
        months=tuple(months), impact_pct=impact, target=target, cities=tuple(cities),
        formats=tuple(formats), weekdays=tuple(weekdays), icon=icon))


ALL = range(1, 13)
CA_INLAND = ('Toronto','Mississauga','Ottawa','Hamilton','Montreal','Quebec City','Calgary','Edmonton','Winnipeg')
CA_COAST = ('Vancouver','Surrey','Halifax')
INDIA_NORTH = ('New Delhi','Noida','Gurugram','Chandigarh')
# Weather scenarios are mutually exclusive by group, including across a month boundary.
add('ca_winter_cold','CA','weather','Cold spell lifts hot-drink demand',(11,12,1,2,3),12,'hot',CA_INLAND,icon='ac_unit')
add('ca_autumn_cool','CA','weather','Cool autumn days favour hot drinks',(9,10,11),8,'hot',icon='thermostat')
add('ca_spring_cool','CA','weather','Cool spring mornings favour hot drinks',(3,4,5),6,'hot',icon='thermostat')
add('ca_summer_warm','CA','weather','Warm summer afternoons lift cold drinks',(6,7,8),12,'cold',icon='wb_sunny')
add('ca_inland_heat','CA','weather','Summer heat spell lifts cold drinks',(7,8),16,'cold',CA_INLAND,icon='wb_sunny')
add('ca_coastal_rain','CA','weather','Wet coastal days soften walk-in demand',(10,11,12,1,2,3,4),-7,'all',CA_COAST,icon='water_drop')
add('ca_spring_showers','CA','weather','Spring showers soften café traffic',(4,5,6),-5,icon='water_drop')
add('ca_late_summer','CA','weather','Mild late-summer days support cold drinks',(8,9),7,'cold',icon='wb_sunny')
add('ca_snow','CA','weather','Snowy conditions reduce discretionary visits',(12,1,2),-10,'all',CA_INLAND,icon='ac_unit')
add('ca_winter_cold_drinks','CA','weather','Winter chill softens cold-drink demand',(12,1,2),-9,'cold',icon='ac_unit')
add('in_hot','IN','weather','Hot afternoons lift chilled-drink demand',(4,5,6),14,'cold',icon='wb_sunny')
add('in_north_heat','IN','weather','Pre-monsoon heat lifts shake demand',(5,6),18,'cold',INDIA_NORTH,icon='thermostat')
add('in_monsoon','IN','weather','Monsoon showers soften walk-in demand',(7,8,9),-8,icon='water_drop')
add('in_pune_rain','IN','weather','Rainy Pune afternoons soften visits',(6,7,8,9),-7,'all',('Pune',),icon='water_drop')
add('in_north_winter','IN','weather','Cold winter days soften shake demand',(12,1,2),-9,'cold',INDIA_NORTH,icon='ac_unit')
add('in_autumn','IN','weather','Mild autumn afternoons support café visits',(10,11),5,icon='wb_sunny')
add('in_spring','IN','weather','Warmer spring days lift cold beverages',(2,3),8,'cold',icon='wb_sunny')
add('in_pune_winter','IN','weather','Mild Pune winter afternoons support visits',(12,1,2),4,'all',('Pune',),icon='wb_sunny')
# Fictional city events: never imply a verified schedule or an outlet next to a venue.
for key,city,venue in [
 ('toronto','Toronto','Rogers Centre'),('mississauga','Mississauga','Celebration Square'),
 ('ottawa','Ottawa','Lansdowne'),('hamilton','Hamilton','downtown Hamilton'),
 ('montreal','Montreal','Bell Centre'),('quebec','Quebec City','Videotron Centre'),
 ('vancouver','Vancouver','Rogers Arena'),('surrey','Surrey','Surrey Civic Plaza'),
 ('calgary','Calgary','downtown Calgary'),('edmonton','Edmonton','Rogers Place'),
 ('winnipeg','Winnipeg','Canada Life Centre'),('halifax','Halifax','downtown Halifax')]:
    add('ca_concert_'+key,'CA','event',f'Concert scenario · {venue}',ALL,8,cities=(city,),weekdays=(4,5,6),icon='music_note')
for key,city in [('delhi','New Delhi'),('noida','Noida'),('gurugram','Gurugram'),('chandigarh','Chandigarh'),('pune','Pune')]:
    add('in_concert_'+key,'IN','event',f'Indoor concert scenario · {city}',ALL,9,cities=(city,),weekdays=(4,5,6),icon='music_note')
add('ca_homecoming','CA','event','Student homecoming weekend',(9,),10,weekdays=(4,5,6),icon='school')
add('ca_term','CA','event','University term-time café visits',(1,2,3,4,9,10,11),6,weekdays=(0,1,2,3,4),icon='school')
add('ca_exams','CA','event','Exam study sessions favour coffee',(4,12),8,'hot',weekdays=(0,1,2,3,4),icon='school')
add('ca_tourism','CA','event','Summer tourism weekend',(6,7,8),9,weekdays=(5,6),icon='flight')
add('ca_winter_market','CA','event','Seasonal indoor market weekend',(11,12),7,weekdays=(5,6),icon='storefront')
add('ca_hockey','CA','event','Hockey watch-party scenario',(10,11,12,1,2,3,4),8,weekdays=(4,5,6),icon='sports_hockey')
add('ca_spring_fair','CA','event','Spring neighbourhood fair scenario',(4,5,6),6,weekdays=(5,6),icon='festival')
add('ca_fall_shopping','CA','event','Autumn shopping weekend',(9,10,11),7,formats=('Mall kiosk',),weekdays=(5,6),icon='shopping_bag')
add('in_campus','IN','event','College term-time café visits',(1,2,3,8,9,10,11),7,weekdays=(0,1,2,3,4),icon='school')
add('in_exam','IN','event','Campus study-break visits',(3,4,11),5,weekdays=(0,1,2,3,4),icon='school')
add('in_school_break','IN','event','Summer family outings',(5,6),9,weekdays=(5,6),icon='family_restroom')
add('in_wedding','IN','event','Wedding-season group orders',(11,12,1,2),8,'dessert',icon='celebration')
add('in_winter_fair','IN','event','Winter outdoor fair scenario',(11,12,1,2),7,weekdays=(5,6),icon='festival')
add('in_cricket','IN','event','Cricket watch-party scenario',(3,4,5),10,weekdays=(4,5,6),icon='sports_cricket')
add('in_autumn_shopping','IN','event','Autumn shopping promotion',(10,11),8,formats=('Mall kiosk',),weekdays=(5,6),icon='shopping_bag')
# Commercial scenarios can occur year-round, with weekday/format constraints.
for country in ('CA','IN'):
    for key,label,impact,target,formats,days in [
        ('delivery','Delivery-app promotion scenario',7,'all',(),(4,5,6)),
        ('loyalty','Loyalty-member offer scenario',5,'all',(),(0,1,2,3)),
        ('office','Office team-order scenario',6,'all',('High-street café','Premium café','Compact takeaway'),(1,2,3)),
        ('mall','Mall shopping offer scenario',8,'all',('Mall kiosk',),(5,6)),
        ('dessert','Dessert bundle offer scenario',8,'dessert',(),(4,5,6)),
        ('family','Family treat promotion scenario',6,'all',(),(5,6)),
        ('delivery_slow','Delivery promotion ending scenario',-4,'all',(),(0,1,2)),
        ('local_offer','Neighbourhood café offer scenario',5,'all',(),(2,3,4)),
    ]:
        add(country.lower()+'_'+key,country,'commercial',label,ALL,impact,target,formats=formats,weekdays=days,icon='local_offer')

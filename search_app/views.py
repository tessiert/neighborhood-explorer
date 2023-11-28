from datetime import datetime, timedelta

import requests
from django.shortcuts import render
from django.views.generic import View
from pytz import timezone

from api.models import Searches
from config.settings.base import MAP_KEY, WEATHER_KEY

# Select appropriate map zoom level based on search radius (in meters)
map_zoom = {"3219": "11", "8047": "10", "16093": "9", "40234": "8"}

def poi_search(request):  
    # Since user is doing a POI search, we've already pulled the geolocation
    # data.
    address = request.POST.get("address")
    latitude = request.POST.get("latitude")
    longitude = request.POST.get("longitude")
    #            display_order = request.POST.get('display_order')
    request.session["point_of_interest"] = request.POST.get("point_of_interest")
    request.session["radius"] = request.POST.get("radius")
    request.session["sort_method"] = request.POST.get("sort_method")

    places_URL = "https://www.mapquestapi.com/search/v4/place?key={map_key}&circle={lon},{lat},{rad}&q={search_term}&sort={sort_method}".format(
        map_key=MAP_KEY,
        lat=latitude,
        lon=longitude,
        rad=request.session["radius"],
        search_term=request.session["point_of_interest"],
        sort_method=request.session["sort_method"],
    )

    try:
        places_response = requests.get(places_URL).json()
    except requests.ConnectionError:
        context={"server": "Mapquest points of interest"}
        return (request, "500.html", context, 500)

    poi_info = []
    # Initialize with marker for home location
    place_markers = f"locations={latitude},{longitude}|via-sm-green||"
    count = 1
    for place in places_response["results"]:
        poi_description = place["displayString"] + "\n\n"
        poi_link = place["displayString"].replace(" ", "%20").replace(",", "%2C")
        poi_info.append({"description": poi_description, "link": poi_link})
        place_markers += (
            str(place["place"]["geometry"]["coordinates"][1])
            + ","
            + str(place["place"]["geometry"]["coordinates"][0])
            + "|"
            + "marker-sm-red-"
            + str(count)
            + "||"
        )
        count += 1
    place_markers = place_markers.rstrip("|")

    if not places_response["results"]:
        poi_info = [{"description": "No results found within the current search radius.", "link": ""}]


    map_URL = "https://www.mapquestapi.com/staticmap/v5/map?key={map_key}&center={lat},{lon}&size=260,200@2x&scalebar=true&&zoom={zoom}&declutter={declutter}&{places}".format(
        map_key=MAP_KEY,
        lat=latitude,
        lon=longitude,
        zoom=map_zoom[request.session["radius"]],
        declutter=request.session["declutter"],
        places=place_markers,
    )

    context = {
        "formatted_address": address,
        "latitude": latitude,
        "longitude": longitude,
        "temperature": request.POST.get("temperature"),
        "summary": request.POST.get("summary"),
        "days": request.session["days"],
        "map_url": map_URL,
        "poi_info": poi_info,
        "poi_start_val": request.session["point_of_interest"],
        "radius_start_val": request.session["radius"],
        "sort_start_val": request.session["sort_method"],
        "declutter_start_val": request.session["declutter"],
        "anchor": "poi_anchor",
    }
    return (request, "pages/update.html", context, 200)

class UpdateView(View):
    def post(self, request):
        # If declutter is checked, it will return a value, otherwise no
        # return value.  Input to mapper must be a 'boolean' text string.
        if request.POST.get("declutter"):
            declutter = "true"
        else:
            declutter = "false"
        request.session["declutter"] = declutter
            
        # Since we are updating, it must be a POI search
        request, template, context, status = poi_search(request)
        
        return render(request, template_name=template, context=context, status=status)

    
class SearchView(View):
    @classmethod
    def _get_weather_image(cls, weather_id):
        path = "/static/images/weather/"
        if weather_id in range(200, 300):
            return path + "stormy.png"
        if weather_id in range(300, 600):
            return path + "rain.png"
        if weather_id in range(600, 700):
            return path + "winter.png"
        if weather_id in range(700, 800):
            return path + "wind.png"
        if weather_id == 800:
            return path + "clear-day.png"
        if weather_id in [801, 802]:
            return path + "partly-cloudy-day.png"
        else:
            return path + "cloudy.png"

    # Forwarding GET to POST with included 'address' enables 'Top Searches' to
    # function as links
    def get(self, request, address):
        return self.post(request, address)

    def post(self, request, address=""):
        DAY_FORMAT = "%A,"
        DATE_FORMAT = "%b. %d"
        
        # If declutter is checked, it will return a value, otherwise no
        # return value.  Input to mapper must be a 'boolean' text string.
        if request.POST.get("declutter"):
            declutter = "true"
        else:
            declutter = "false"
        request.session["declutter"] = declutter
        
        if request.POST.get("poi_search"):
            request, template, context, status = poi_search(request)
                      
            return render(request, template_name=template, context=context, status=status)

        # If address is supplied, then user clicked a 'Top Searches' link.
        # If not, get address from posted search bar form data.
        if not address:
            address = request.POST.get("address", "")
            # If an address was not supplied in the search bar either, raise 404
            if not address:
                return render(request, template_name="404.html", status=404)

        encoded_address = address.replace(" ", "%20")
        geocode_URL = "https://www.mapquestapi.com/geocoding/v1/address?key={}&location={}".format(
            MAP_KEY, encoded_address
        )
        try:
            geo_response = requests.get(geocode_URL).json()
        except requests.ConnectionError:
            return render(request, template_name="500.html", context={"server": "Mapquest geolocation"}, status=500)

        location_data = geo_response["results"][0]["locations"][0]
        if (
            geo_response["info"]["statuscode"] != 0
            or location_data["adminArea3"] == ""
            or location_data["adminArea1"] != "US"
        ):
            return render(request, template_name="404.html", status=404)

        # Pull address data from response
        street = location_data["street"].title()
        city = location_data["adminArea5"].title()
        state = location_data["adminArea3"].upper()
        zip_code = location_data["postalCode"]

        # Format the address to contain as much data as possible, with no
        # hanging commas for missing pieces
        formatted_address = f"{street}, {city}, {state}, {zip_code}".lstrip(" ,").rstrip(" ,")

        # If the current search is being done at least at city level accuracy,
        # update count of, or add new record to top searches database
        try:       
            new_search = Searches()    
            city_search = new_search.__class__.objects.get(city=city, state=state)
            city_search.count += 1
        except new_search.DoesNotExist:
            city_search = Searches(city=city, state=state, count=1)
        city_search.save()

        # Get latitude and longitude for remaining API lookups
        latitude = location_data["latLng"]["lat"]
        longitude = location_data["latLng"]["lng"]
        # Get weather at given geolocation
        weather_URL = (
            "https://api.openweathermap.org/data/3.0/onecall?lat={}&lon={}&exclude={}&units={}&appid={}".format(
                latitude,
                longitude,
                "minutely,hourly,alerts",  # list (w/out spaces) of data to exclude
                "imperial",  # units for returned weather data
                WEATHER_KEY,
            )
        )

        try:
            weather_response = requests.get(weather_URL).json()
        except requests.ConnectionError:
            return render(request, template_name="500.html", context={"server": "Open Weather Map"}, status=500)

        # Get current date in time zone of address
        zone = weather_response["timezone"]
        today = datetime.now(timezone(zone))

        days = [{}, {}, {}]
        for i in range(3):
            cur_data = weather_response["daily"][i]
            cur_day = today + timedelta(days=i)  # today, tomorrow, day after

            # Store 3-day forecast info in class variable, so we don't have
            # to retreive it again if a POI search is performed
            days[i]["name"] = cur_day.strftime(DAY_FORMAT)
            days[i]["date"] = cur_day.strftime(DATE_FORMAT)
            days[i]["low"] = round(cur_data["temp"]["night"])
            days[i]["high"] = round(cur_data["temp"]["day"])
            days[i]["image"] = self._get_weather_image(cur_data["weather"][0]["id"])
            days[i]["text"] = cur_data["weather"][0]["main"]

        request.session["days"] = days
        map_URL = "https://www.mapquestapi.com/staticmap/v5/map?key={}&center={},{}&size=260,200@2x&scalebar=true&zoom=14&locations={},{}|via-sm-green&declutter=true".format(
            MAP_KEY, latitude, longitude, latitude, longitude
        )

        poi_info = [{"description": "Links for matched locations will appear here.", "link": ""}]

        context = {
            "formatted_address": formatted_address,
            "latitude": latitude,
            "longitude": longitude,
            "temperature": round(weather_response["current"]["temp"]),
            "summary": weather_response["current"]["weather"][0]["description"],
            "days": days,
            "map_url": map_URL,
            "poi_info": poi_info,
            "poi_start_val": "",
            "radius_start_val": "",
            "sort_start_val": "",
            "declutter_start_val": request.session["declutter"],
        }

        return render(request, template_name="pages/search.html", context=context)

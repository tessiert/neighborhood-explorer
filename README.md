# Neighborhood Explorer - A web app to explore key features of U.S. neighborhoods

## Video Demo (4 minutes)

https://github.com/tessiert/neighborhood-explorer/assets/39570561/3c97ade0-ba05-4ed7-80b6-1279a9f35847

# https://neighborhood-explorer.com

This site uses Python, Django, and a PostgreSQL database to integrate data from five different APIs, and also exposes its own API endpoint to provide access to the city/state search data that it tracks. It enables a user to enter some or all of a U.S. address, and then retrieves and displays information about the given location - a three-day weather forecast and a map and drop-down selection mechanism for the exploration of attractions and other points of interest in the area.

I start by using Mapquest's geocoding API to convert the input location into latitude and longitude coordinates, and then use these to pull weather information from the OpenWeather API. After that, and based on user selection criteria, I pull points of interest information from the Mapquest Place Search API and use this information to populate an appropriately scaled map from the Mapquest Static Map API with location markers, as well as to retrieve a text address of the site that is transformed into a link to further information using a Google Maps API.

This site also provides its own API endpoint at https://Neighborhood-Explorer.com/api which allows GET requests, and will return JSON containing information on how many times each City/State combination in the Postgres database has been searched. It is this API that is accessed by the home page in order to construct the "Top Searches" results - employing a very simple in-house microservices architecture approach.

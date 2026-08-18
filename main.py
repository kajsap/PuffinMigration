import pandas as pd
import folium
from folium.plugins import TimestampedGeoJson

data = pd.read_csv("puffin_data.csv")

data["timestamp"] = pd.to_datetime(data["timestamp"])

data = data.sort_values(["tag-local-identifier", "timestamp"])

puffins = data["tag-local-identifier"].unique()
colours = [
    "red",
    "blue", 
    "green",
    "purple",
    "orange",
    "darkred",
    "lightgreen", 
    "black",
    "pink",
    "yellow"
]

puffin_colours = {}

for i, puffin_id in enumerate(puffins):
    puffin_colours[puffin_id] = colours[i % len(colours)]

features = []

for _, row in data.iterrows():
    colour = puffin_colours[row["tag-local-identifier"]]

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [row["location-long"], row["location-lat"]]
        },
        "properties": {
            "tag-local-identifier": str(row["tag-local-identifier"]),
            "time": row["timestamp"].isoformat(),
            "icon": "circle",
            "iconstyle": {
                "color": colour,
                "fillColor": colour,
                "fillOpacity": 1,
                "radius": 6
            }
        }
    }
    features.append(feature)

geojson_data = {
    "type": "FeatureCollection",
    "features": features
}


centre_lat = data["location-lat"].mean()
centre_long = data["location-long"].mean()

m = folium.Map(
    location=[centre_lat, centre_long],
    zoom_start= 3
)

TimestampedGeoJson(
    geojson_data,
    period="P1D",
    add_last_point=True,
    auto_play=False,
    loop=False
).add_to(m)

m.save("puffin_map.html")

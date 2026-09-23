import pandas as pd
import folium
from folium.plugins import TimestampedGeoJson
import json
import math

def load_data():
    data = pd.read_csv("puffin_dataset.csv")

    data["timestamp"] = pd.to_datetime(data["timestamp"], format="%d/%m/%Y %H:%M:%S")

    data = data.sort_values(["tag-local-identifier", "timestamp"])

    return data

def assign_colours(data):
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
        puffin_colours[puffin_id] = colours[i % len(colours)] #colours to repeat

    return puffin_colours

def create_map(data):
    centre_lat = data["bas:compensated-latitute"].mean()
    centre_long = data["location-long"].mean()

    map = folium.Map(
        location=[centre_lat, centre_long],
        zoom_start= 2.5
    )

    return map

def create_timeline(data, map, puffin_colours):

    #store the data for javascript contains all the geographical points of each puffin
    puffin_data = {}

    for puffin_id, group in data.groupby("tag-local-identifier"):
        features = []

        for _, row in group.iterrows():
            colour = puffin_colours[puffin_id]

            popup_text = (
                f"<b>Puffin:</b> {puffin_id}<br>"
                f"<b>Latitude:</b> {row["bas:compensated-latitute"]:.4f}<br>"
                f"<b>Longitude:</b> {row["location-long"]:.4f}<br>"
                f"<b>Date:</b> {row["timestamp"].strftime('%Y-%m-%d')}<br>"
                f"<b>Time:</b> {row["timestamp"].strftime('%H:%M:%S')}"
            )

            feature = {
                "type": "Feature",

                "geometry": {
                    "type": "Point",
                    "coordinates": [row["location-long"], row["bas:compensated-latitute"]]
                },

                "properties": {
                    "time": row["timestamp"].isoformat(),
                    "puffin_id": str(puffin_id),
                    "popup": popup_text,
                    "icon": "circle",

                    "iconstyle": {
                        "color": colour,
                        "fillColor": colour,
                        "fillOpacity": 1,
                        "radius": 5
                    }
                }
            }

            features.append(feature)

        puffin_data[str(puffin_id)] = features

    #empty timeline
    empty_geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    timeline = TimestampedGeoJson(
        empty_geojson,
        period="P1D",
        add_last_point=True,
        auto_play=False,
        loop=False,
        max_speed=2,
        loop_button=True,
        date_options="YYYY-MM-DD",
        time_slider_drag_update=True
    )

    timeline.add_to(map)

    timeline_variable = timeline.get_name()
    map_variable = map.get_name()

    #convert python dict into javascript
    puffin_data_json = json.dumps(puffin_data)

    javascript = f"""
    <script>

    var puffinData = {puffin_data_json};

    var selectedPuffins = {{}};

    function togglePuffin(puffinID, checked) {{
        selectedPuffins[puffinID] = checked;
        updateTimeline();
    }}

    function updateTimeline(){{
        var selectedFeatures = []; 

        for (var puffinID in selectedPuffins){{
        
            if (selectedPuffins[puffinID] === true){{
                var features = puffinData[puffinID];

                if (features){{
                    selectedFeatures = selectedFeatures.concat(features);
                }}
            }}  
        }}

        var newGeoJSON = {{
            "type": "FeatureCollection",
            "features": selectedFeatures
        }};

        console.log("Selected puffin points:", selectedFeatures.length);

        var timeLayer = {timeline_variable};

        //if timeline exists then remove the current points and add the new points
        if (timeLayer && timeLayer._baseLayer){{
            timeLayer._baseLayer.clearLayers();

            timeLayer._baseLayer.addData(newGeoJSON);
        }}
    }}

    </script>
    """

    map.get_root().html.add_child(folium.Element(javascript))

    return timeline


def checkbox(puffin_colours, map):
    legend_items = ""

    for puffin_id, colour in puffin_colours.items():

        legend_items += f"""
        <label>
            <input type="checkbox"
                onchange="togglePuffin('{puffin_id}', this.checked)">
            <span style="
            display: inline-block;
            width: 10px;
            height: 10px;
            background: {colour};
            color:{colour}">
            </span>
            {puffin_id}
        </label><br>
        """

    checkbox_html = f"""
    <div style="
        position: fixed; 
        bottom: 200px; 
        left: 50px; 
        width: 130px; 
        height: 210px; 
        border:2px solid grey; 
        z-index:9999; 
        font-size:10px;
        background-color:white; 
        opacity: 0.85; 
        padding: 10px;">

        <b>Puffins</b><br>
        {legend_items}

    </div>
    """

    map.get_root().html.add_child(folium.Element(checkbox_html))


def distance_puffin(data):
    puffin_distance = {}
    R = 6_371

    for puffin, group in data.groupby("tag-local-identifier"):
        distance = 0

        for i in range(1, len(group)):
            point1 = group.iloc[i-1]
            point2 = group.iloc[i]

            lat1 = point1["bas:compensated-latitute"]
            long1 = point1["location-long"]

            lat2 = point2["bas:compensated-latitute"]
            long2 = point2["location-long"]

            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            d_phi = math.radians(lat2 - lat1)
            d_lambda = math.radians(long2 - long1)

            a = (math.sin(d_phi / 2) ** 2 +
                math.cos(phi1) * math.cos(phi2) *
                math.sin(d_lambda / 2) ** 2)

            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            d = c * R

            distance = distance + d

        puffin_distance[puffin] = distance

    return puffin_distance

def calculate_statistic(data, puffin_distance):
    birds_tracked = data["tag-local-identifier"].nunique()
    tracking_points = len(data)
    earliest_date = data["timestamp"].min()
    latest_date = data["timestamp"].max()
    total_distance = sum(puffin_distance.values())

    return {"birds_tracked": birds_tracked, "tracking_points": tracking_points, "total_distance": total_distance,
             "earliest_date": earliest_date, "latest_date": latest_date}


def add_statistic_box(map, overall):
    earliest = overall["earliest_date"].strftime('%Y-%m-%d')
    latest = overall["latest_date"].strftime('%Y-%m-%d')

    statistic_html = f"""
    <div style = "
        position: fixed;
        top: 100px;
        left: 20px;
        width: 180px;
        background-color: white;
        border: 2px solid grey;
        border-radius: 5px;
        z-index: 9999;
        font-size: 12px;
        padding: 10px;
        opacity: 0.85;">

        <b>Overall Migration Statistics:</b>
        <hr>

        <b>Birds Tracked: </b> 
        {overall["birds_tracked"]}
        <br><br>

        <b>Total tracking points: </b> 
        {overall["tracking_points"]}
        <br><br>

        <b>Total distance(km): </b> 
        {overall["total_distance"]}
        <br><br>

        <b>Earliest date: </b> 
        {earliest}
        <br><br>

        <b>Latest date: </b> 
        {latest}
        <br><br>
    </div>
    """
    map.get_root().html.add_child(folium.Element(statistic_html))


def main():
    data = load_data()
    puffin_colours = assign_colours(data)
    map = create_map(data)
    timeline = create_timeline(data, map, puffin_colours)
    checkbox(puffin_colours, map)

    puffin_distance = distance_puffin(data)
    overall = calculate_statistic(data, puffin_distance) 
    add_statistic_box(map, overall)

    map.save("puffin_map.html")

main()


import pandas as pd
import folium

def load_data():
    data = pd.read_csv("puffin_data.csv")

    data["timestamp"] = pd.to_datetime(data["timestamp"])

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
        puffin_colours[puffin_id] = colours[i % len(colours)]

    return puffin_colours

def create_map(data):
    centre_lat = data["location-lat"].mean()
    centre_long = data["location-long"].mean()

    map = folium.Map(
        location=[centre_lat, centre_long],
        zoom_start= 3
    )

    return map

def group_data(data, map, puffin_colours):
    puffin_groups = {}

    for puffin_id, puffin_data in data.groupby("tag-local-identifier"):
        colour = puffin_colours[puffin_id]
        group = folium.FeatureGroup(
            name=puffin_id,
            show=False
        )

        for _, row in puffin_data.iterrows():
            folium.CircleMarker(
                location=[row["location-lat"], row["location-long"]],
                fill_opacity = 1,
                fill = True,
                radius=5,
                fill_color = colour,
                color = colour
            ).add_to(group)

        group.add_to(map)

        puffin_groups[puffin_id] = group

    return puffin_groups


def checkbox(puffin_groups, puffin_colours, map):
    legend_items = ""
    map_variable = map.get_name()

    for puffin_id, colour in puffin_colours.items():
        layer_variable =  puffin_groups[puffin_id].get_name()

        legend_items += f"""
        <label>
            <input type="checkbox"
                onchange="togglePuffin('{layer_variable}', this.checked)">
            <span style="color:{colour}"></span>
            {puffin_id}
        </label><br>
    """

    checkbox_html = f"""
    <div style="
        position: fixed; 
        bottom: 200px; 
        left: 50px; 
        width: 100px; 
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

    <script>

    function togglePuffin(layerName, checked){{
        var layer = window[layerName];
        var map = {map_variable};

        if (checked){{
            map.addLayer(layer);
        }}
        else{{
            map.removeLayer(layer);
        }}
        
    }}
    </script>

    """

    map.get_root().html.add_child(folium.Element(checkbox_html))

def main():
    data = load_data()
    puffin_colours = assign_colours(data)
    map = create_map(data)
    puffin_groups = group_data(data, map, puffin_colours)
    checkbox(puffin_groups, puffin_colours, map)
    map.save("puffin_map.html")

main()


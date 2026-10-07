"""Reference data: the category bar and the amenity filters. (slug/key, label, icon_key[, group])"""

CATEGORIES = [
    ("amazing_views", "Amazing views", "view"),
    ("beachfront", "Beachfront", "beach"),
    ("cabins", "Cabins", "cabin"),
    ("farms", "Farms", "farm"),
    ("lakefront", "Lakefront", "lake"),
    ("mansions", "Mansions", "mansion"),
    ("countryside", "Countryside", "countryside"),
    ("tropical", "Tropical", "palm"),
    ("treehouses", "Treehouses", "treehouse"),
    ("heritage", "Heritage", "heritage"),
    ("houseboats", "Houseboats", "boat"),
    ("pools", "Amazing pools", "pool"),
    ("camping", "Camping", "tent"),
    ("design", "Design", "design"),
    ("tiny_homes", "Tiny homes", "tiny"),
    ("top_of_the_world", "Top of the world", "mountain"),
]

AMENITIES = [
    # essentials
    ("wifi", "Wifi", "wifi", "essentials"),
    ("kitchen", "Kitchen", "kitchen", "essentials"),
    ("washer", "Washing machine", "washer", "essentials"),
    ("ac", "Air conditioning", "ac", "essentials"),
    ("heating", "Heating", "heating", "essentials"),
    ("tv", "TV", "tv", "essentials"),
    ("hot_water", "Hot water", "hot_water", "essentials"),
    ("hair_dryer", "Hair dryer", "hair_dryer", "essentials"),
    ("iron", "Iron", "iron", "essentials"),
    ("workspace", "Dedicated workspace", "workspace", "essentials"),
    ("breakfast", "Breakfast included", "breakfast", "essentials"),
    # features
    ("pool", "Private pool", "pool", "features"),
    ("hot_tub", "Hot tub", "hot_tub", "features"),
    ("free_parking", "Free parking", "parking", "features"),
    ("gym", "Gym", "gym", "features"),
    ("bbq_grill", "BBQ grill", "bbq", "features"),
    ("balcony", "Patio or balcony", "balcony", "features"),
    ("bonfire", "Bonfire pit", "bonfire", "features"),
    ("garden", "Garden", "garden", "features"),
    # location
    ("beach_access", "Beach access", "beach", "location"),
    ("lake_access", "Lake access", "lake", "location"),
    ("sea_view", "Sea view", "sea_view", "location"),
    ("mountain_view", "Mountain view", "mountain", "location"),
    ("garden_view", "Garden view", "garden", "location"),
    # safety
    ("smoke_alarm", "Smoke alarm", "smoke_alarm", "safety"),
    ("first_aid_kit", "First aid kit", "first_aid", "safety"),
    ("fire_extinguisher", "Fire extinguisher", "extinguisher", "safety"),
    ("co_alarm", "Carbon monoxide alarm", "co_alarm", "safety"),
]

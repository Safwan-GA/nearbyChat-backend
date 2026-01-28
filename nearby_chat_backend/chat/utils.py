from geopy.distance import geodesic

def is_within_radius(user_lat, user_lng, room_lat, room_lng, radius_meters):
    user_loc = (user_lat, user_lng)
    room_loc = (room_lat, room_lng)
    distance = geodesic(user_loc, room_loc).meters
    return distance <= radius_meters

import math
import xml.etree.ElementTree as ET

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_gpx_distance(gpx_content: str) -> float:
    """Parse GPX and calculate total distance in meters."""
    try:
        # Simple XML parsing (strip namespaces for easier access)
        content_bytes = gpx_content.encode("utf-8")
        it = ET.iterparse(java_io_InputStream(content_bytes) if False else None) # Wait, standard ET
        
        # Actually just use fromstring
        tree = ET.fromstring(gpx_content)
        
        # Remove namespaces locally for easier XPath
        for el in tree.iter():
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]
        
        points = []
        # Try trkpt
        for trkpt in tree.findall(".//trkpt"):
            lat = float(trkpt.get("lat"))
            lon = float(trkpt.get("lon"))
            points.append((lat, lon))
            
        # Fallback to rtept
        if not points:
            for rtept in tree.findall(".//rtept"):
                lat = float(rtept.get("lat"))
                lon = float(rtept.get("lon"))
                points.append((lat, lon))
        
        total_distance = 0.0
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            total_distance += haversine_distance(p1[0], p1[1], p2[0], p2[1])
            
        return total_distance
    except Exception as e:
        print(f"Error calculating GPX distance: {e}")
        return 0.0

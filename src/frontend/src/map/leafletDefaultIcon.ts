/**
 * Vite breaks Leaflet's default marker asset paths; apply once before any MapContainer mounts.
 */
import L from 'leaflet';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import iconShadowUrl from 'leaflet/dist/images/marker-shadow.png';

const icon = L.icon({ iconUrl, shadowUrl: iconShadowUrl });
L.Marker.prototype.options.icon = icon;

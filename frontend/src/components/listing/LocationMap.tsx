"use client";

import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { MapContainer, Marker, TileLayer } from "react-leaflet";

const home = L.divIcon({
  className: "price-pin is-active",
  html: '<span style="padding:10px;font-size:18px;line-height:1">&#8962;</span>',
  iconSize: [0, 0],
});

/** A small map with one marker. Airbnb hides the exact address until booking; we show the area. */
export default function LocationMap({ latitude, longitude }: { latitude: number; longitude: number }) {
  return (
    <MapContainer center={[latitude, longitude]} zoom={13} scrollWheelZoom={false} className="size-full">
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={18}
      />
      <Marker position={[latitude, longitude]} icon={home} />
    </MapContainer>
  );
}

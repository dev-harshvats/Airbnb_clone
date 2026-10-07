"use client";

import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useMemo } from "react";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";

const pin = L.divIcon({
  className: "price-pin is-active",
  html: '<span style="padding:10px;font-size:18px;line-height:1">&#8962;</span>',
  iconSize: [0, 0],
});

type Props = {
  latitude: number;
  longitude: number;
  /** Zoomed out until the host has chosen a city. */
  zoom: number;
  onChange: (latitude: number, longitude: number) => void;
};

function Recenter({ latitude, longitude, zoom }: Omit<Props, "onChange">) {
  const map = useMap();
  useEffect(() => {
    map.setView([latitude, longitude], zoom);
    // Only re-centre when the city (zoom) changes, not on every nudge of the pin.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, zoom]);
  return null;
}

function ClickToMove({ onChange }: Pick<Props, "onChange">) {
  useMapEvents({ click: (event) => onChange(event.latlng.lat, event.latlng.lng) });
  return null;
}

/** A map whose pin can be dragged, or the map clicked, to set the listing's exact position. */
export default function PinPicker({ latitude, longitude, zoom, onChange }: Props) {
  const handlers = useMemo(
    () => ({
      dragend(event: L.LeafletEvent) {
        const { lat, lng } = (event.target as L.Marker).getLatLng();
        onChange(lat, lng);
      },
    }),
    [onChange],
  );
  return (
    <MapContainer center={[latitude, longitude]} zoom={zoom} scrollWheelZoom className="size-full">
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={18}
      />
      <Recenter latitude={latitude} longitude={longitude} zoom={zoom} />
      <ClickToMove onChange={onChange} />
      <Marker position={[latitude, longitude]} icon={pin} draggable eventHandlers={handlers} />
    </MapContainer>
  );
}

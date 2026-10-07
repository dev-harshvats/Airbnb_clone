/** Indian cities the location step offers, with a starting map position and a sample postal code. */
export type City = { city: string; state: string; latitude: number; longitude: number; postalCode: string };

export const CITIES: City[] = [
  { city: "Anjuna", state: "Goa", latitude: 15.5736, longitude: 73.741, postalCode: "403509" },
  { city: "Palolem", state: "Goa", latitude: 15.01, longitude: 74.0232, postalCode: "403702" },
  { city: "Mumbai", state: "Maharashtra", latitude: 19.076, longitude: 72.8777, postalCode: "400050" },
  { city: "Manali", state: "Himachal Pradesh", latitude: 32.2432, longitude: 77.1892, postalCode: "175131" },
  { city: "Shimla", state: "Himachal Pradesh", latitude: 31.1048, longitude: 77.1734, postalCode: "171001" },
  { city: "Leh", state: "Ladakh", latitude: 34.1526, longitude: 77.5771, postalCode: "194101" },
  { city: "Rishikesh", state: "Uttarakhand", latitude: 30.0869, longitude: 78.2676, postalCode: "249304" },
  { city: "Varanasi", state: "Uttar Pradesh", latitude: 25.3176, longitude: 82.9739, postalCode: "221001" },
  { city: "Darjeeling", state: "West Bengal", latitude: 27.036, longitude: 88.2627, postalCode: "734101" },
  { city: "Jaipur", state: "Rajasthan", latitude: 26.9124, longitude: 75.7873, postalCode: "302001" },
  { city: "Udaipur", state: "Rajasthan", latitude: 24.5854, longitude: 73.7125, postalCode: "313001" },
  { city: "Jaisalmer", state: "Rajasthan", latitude: 26.9157, longitude: 70.9083, postalCode: "345001" },
  { city: "Alleppey", state: "Kerala", latitude: 9.4981, longitude: 76.3388, postalCode: "688001" },
  { city: "Kochi", state: "Kerala", latitude: 9.9312, longitude: 76.2673, postalCode: "682001" },
  { city: "Munnar", state: "Kerala", latitude: 10.0889, longitude: 77.0595, postalCode: "685612" },
  { city: "Coorg", state: "Karnataka", latitude: 12.3375, longitude: 75.8069, postalCode: "571201" },
  { city: "Bengaluru", state: "Karnataka", latitude: 12.9716, longitude: 77.5946, postalCode: "560038" },
  { city: "Ooty", state: "Tamil Nadu", latitude: 11.4102, longitude: 76.695, postalCode: "643001" },
  { city: "Pondicherry", state: "Puducherry", latitude: 11.9416, longitude: 79.8083, postalCode: "605001" },
  { city: "Gokarna", state: "Karnataka", latitude: 14.5479, longitude: 74.3188, postalCode: "581326" },
];

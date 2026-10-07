import { api } from "@/lib/api/client";
import type {
  ExperienceCard,
  ExperienceDetail,
  Page,
  ServiceCard,
  ServiceDetail,
  ServiceTypeSummary,
} from "@/types/api";

export type CatalogQuery = {
  location?: string;
  category?: string;
  service_type?: string;
  sort?: "recommended" | "price_asc" | "price_desc" | "rating";
  page?: number;
  page_size?: number;
};

export const catalogApi = {
  experiences: (query: CatalogQuery) => api<Page<ExperienceCard>>("/experiences", { query }),
  experience: (id: number | string) => api<ExperienceDetail>(`/experiences/${id}`),
  services: (query: CatalogQuery) => api<Page<ServiceCard>>("/services", { query }),
  service: (id: number | string) => api<ServiceDetail>(`/services/${id}`),
  serviceTypes: (location?: string) => api<ServiceTypeSummary[]>("/services/types", { query: { location } }),
};

import { ServiceDetailView } from "@/components/detail/CatalogDetail";

export default async function ServicePage({ params }: { params: Promise<{ id: string }> }) {
  return <ServiceDetailView id={(await params).id} />;
}

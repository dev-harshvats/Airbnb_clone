import { ExperienceDetailView } from "@/components/detail/CatalogDetail";

export default async function ExperiencePage({ params }: { params: Promise<{ id: string }> }) {
  return <ExperienceDetailView id={(await params).id} />;
}

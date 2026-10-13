import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";

export function ComingSoonPage({ title }: { title: string }) {
  return (
    <>
      <PageHeader title={title} />
      <EmptyState title="Disponible en la siguiente entrega" hint="Este módulo se habilita en el segundo release." />
    </>
  );
}

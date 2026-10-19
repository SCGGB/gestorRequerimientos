interface PlaceholderPageProps {
  title: string;
}

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <section
      data-testid="placeholder-page"
      className="rounded-lg border border-border bg-surface p-6"
    >
      <h1 className="text-2xl font-semibold text-secondary">{title}</h1>
      <p className="mt-2 text-sm text-neutral-dark">
        Seccion en construccion. Estara disponible en una version posterior.
      </p>
    </section>
  );
}

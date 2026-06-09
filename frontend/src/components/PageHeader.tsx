type PageHeaderProps = {
  title: string;
  description: string;
};

export default function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <header className="page-header">
      <p className="eyebrow">MVP Workspace</p>
      <h2>{title}</h2>
      <p className="muted">{description}</p>
    </header>
  );
}


import { Icon } from "../components/Icons";
import PageHeader from "../components/PageHeader";
import TicketTable from "../components/TicketTable";
import { useAppState } from "../context/AppState";
import { exportTicketsUrl } from "../services/api";

export default function Tickets() {
  const { filters } = useAppState();
  return (
    <>
      <PageHeader
        eyebrow="Every ticket"
        title="Tickets"
        subtitle="Search, sort and page through the tickets that match your filters."
        actions={
          <a className="btn-primary" href={exportTicketsUrl(filters)} download title="Downloads every ticket matching the current filters, not only this page">
            <Icon name="download" /> Export CSV
          </a>
        }
      />
      <section className="card p-4">
        <TicketTable filters={filters} />
      </section>
    </>
  );
}

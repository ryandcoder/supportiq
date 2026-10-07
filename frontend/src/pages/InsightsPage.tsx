import InsightsPanel from "../components/InsightsPanel";
import PageHeader from "../components/PageHeader";

export default function InsightsPage() {
  return (
    <>
      <PageHeader eyebrow="What the data says" title="Insights & recommendations" subtitle="Generated from the filtered tickets. Change a filter and the sentences are recalculated." />
      <InsightsPanel />
    </>
  );
}

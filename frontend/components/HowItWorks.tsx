const concepts = [
  {
    term: "Liquidity runway",
    definition: "How many months of required spending could be covered by liquid assets."
  },
  {
    term: "Real dollars",
    definition: "Balances adjusted for inflation so future dollars are easier to compare with today."
  },
  {
    term: "Stress test",
    definition: "A deterministic downside case that asks what happens if one key assumption gets worse."
  },
  {
    term: "Mortgage recast",
    definition: "A principal paydown that lowers the payment without changing the interest rate."
  }
];

export function HowItWorks() {
  return (
    <section className="panel workflow-panel">
      <div>
        <strong>How to use this tool</strong>
        <p>
          Treat the overview as the decision read, not the audit trail. Change assumptions, recalculate,
          then use the detail tabs to inspect liquidity and simulation risk.
        </p>
      </div>
      <div className="concept-strip" aria-label="Key model concepts">
        {concepts.map((concept) => (
          <details key={concept.term}>
            <summary>{concept.term}</summary>
            <p>{concept.definition}</p>
          </details>
        ))}
      </div>
    </section>
  );
}

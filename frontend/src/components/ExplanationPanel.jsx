export default function ExplanationPanel({
  explanation,
  busy,
}) {
  return (
    <section aria-busy={busy === "explanation"}>
      <h2>Your explanation from Luna</h2>

      {busy === "explanation" ? (
        <p role="status">
          Generating a local explanation. The first request may take
          a few minutes.
        </p>
      ) : explanation ? (
        <div aria-live="polite">
          <p style={{ whiteSpace: "pre-wrap" }}>
            {explanation.explanation}
          </p>

          {!explanation.generation_complete && (
            <p>
              This explanation was cut short. You can generate it again.
            </p>
          )}

          <p>{explanation.note}</p>
        </div>
      ) : (
        <p>
          After finding your profile, ask Luna to explain its patterns.
        </p>
      )}
    </section>
  );
}